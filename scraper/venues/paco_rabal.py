import asyncio
import re
import uuid
import sys
import os
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

import unicodedata
# Force UTF-8 output for Windows
if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'UTF-8':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except Exception:
        pass # Fallback if above fails
# Ensure the models are reachable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Event, Venue, Session

def parse_sessions(soup, content_area):
    """
    Parses sessions from <time> tags with datetime attributes within the content area.
    """
    sessions = []
    if not content_area:
        return sessions
        
    time_tags = content_area.select('time[datetime]')
    
    for tag in time_tags:
        dt_str = tag.get('datetime')
        if not dt_str:
            continue
        
        try:
            # Format: 2026-05-16T17:00:00+02:00
            parts = dt_str.split('T')
            if len(parts) >= 2:
                date_part = parts[0]
                time_part = parts[1][:5] # HH:MM
                
                # Check if this date+time is already added
                if not any(s.date == date_part and s.time == time_part for s in sessions):
                    sessions.append(Session(date=date_part, time=time_part))
        except Exception as e:
            print(f"  Error parsing datetime {dt_str}: {e}")
            
    return sessions

async def scrape_event_details(page, url):
    """Scrapes a single event page."""
    print(f"Scraping event details: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(1000)
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Identify content area
        content_area = soup.select_one('#block-comunidad-madrid-content, .c-main-content, main')
        
        # --- EXTRACT TITLE AND COMPANY ---
        # 1. Base title from H1
        h1_el = soup.select_one('h1.heading, h1.c-title, h1')
        h1_text = h1_el.get_text().strip() if h1_el else ""
        
        def normalize_text(text):
            if not text: return ""
            text = text.replace('\xa0', ' ')
            text = unicodedata.normalize('NFC', text)
            text = " ".join(text.split())
            text = text.strip('• \t\n\r\xa0*!-–—,.')
            return text

        def clean_title_str(text):
            if not text: return ""
            # Remove "DANZA:", "TEATRO:", etc.
            text = re.sub(r'^(?:DANZA|M\u00daSICA|TEATRO|ACTIVIDADES|PROGRAMACI\u00d3N|DANZA Y M\u00daSICA):\s*', '', text, flags=re.IGNORECASE)
            # Remove day of week patterns and dates (e.g. - sábado 9, - 16 de mayo)
            days_regex = r'\s+-\s+(?:lunes|martes|mi\u00e9rcoles|miercoles|jueves|viernes|s\u00e1bado|sabado|domingo)(?:\s+\d{1,2})?'
            text = re.split(days_regex, text, flags=re.IGNORECASE)[0]
            text = re.split(r':\s+(?:lunes|martes|mi\u00e9rcoles|miercoles|jueves|viernes|s\u00e1bado|sabado|domingo)', text, flags=re.IGNORECASE)[0]
            # Remove " - 20:00 h" or similar
            text = re.sub(r'\s+\d{1,2}:\d{2}\s*h?$', '', text, flags=re.IGNORECASE)
            # Remove trailing " - Paco Rabal"
            text = re.sub(r'\s+-\s+Paco Rabal.*$', '', text, flags=re.IGNORECASE)
            return normalize_text(text)

        base_title = clean_title_str(h1_text)
        title = base_title
        company = ""
        
        # 2. Extraction from Content Body
        if content_area:
            body_divs = content_area.select('.field--name-body, .field--name-field-texto-explicativo')
            
            company_keywords = r'Compa\u00f1\u00eda|C\u00eda\.?|Conservatorio|Ballet|Grupo|Escuela|Centro|Creaci\u00f3n|Profesora?|Director|Coreograf\u00eda|Direcci\u00f3n|Autora?|Ensemble|Producc\u00f3n'
            skip_patterns = r'\d+\s*a\s*\d+\s*h|lunes|martes|mi\u00e9rcoles|miercoles|jueves|viernes|s\u00e1bado|sabado|domingo|horas|precio|entradas|M\u00fasica|Sinfon\u00eda|Pieza'
            institutional_names = r'Real Conservatorio Profesional de Danza Mariemma|Mariemma|Larreal|Tejido Conectivo|Antonio Gades|Rafaela Carrasco|Sara Baras'

            for body_el in body_divs:
                # 2a. Check for prominent headers (H3) first as they often contain Title <br> Company
                h3_elements = body_el.select('h3')
                for h3_el in h3_elements:
                    h3_text = h3_el.get_text(separator="\n").strip()
                    if not h3_text or len(h3_text) < 3: continue
                    if re.search(skip_patterns, h3_text, re.IGNORECASE): continue
                    
                    lines = [l.strip() for l in h3_text.split("\n") if l.strip()]
                    if len(lines) >= 2:
                        # Case: Title \n Company
                        potential_title = clean_title_str(lines[0])
                        potential_company = normalize_text(lines[1])
                        if potential_title and potential_company:
                            title = potential_title
                            company = potential_company
                            break
                    elif len(lines) == 1:
                        line = lines[0]
                        # If it's just one line, it could be the company
                        if re.search(company_keywords, line, re.IGNORECASE) or re.search(institutional_names, line, re.IGNORECASE):
                            company = line
                            # Check if title was just the base H1 and if this line is different
                            if title == base_title and clean_title_str(line) != base_title:
                                # Sometimes the H3 is the real title
                                pass 
                            break
                
                if company: break

                # 2b. Check first few paragraphs/bold elements
                first_elements = body_el.select('p, strong, b, h4')[:8]
                for el in first_elements:
                    text = el.get_text().strip()
                    if not text or len(text) < 3 or len(text) > 100: continue
                    if re.search(skip_patterns, text, re.IGNORECASE): continue
                    
                    if re.search(company_keywords, text, re.IGNORECASE) or re.search(institutional_names, text, re.IGNORECASE):
                        company = text
                        break
                
                if company: break

        # 3. Fallback for Company (Meta fields)
        if not company:
            company_el = soup.select_one('.field--name-field-compania, .field--name-field-autor, .field--name-field-artista')
            if company_el:
                company = company_el.text.strip()
        
        # --- FINAL CLEANUP ---
        title = clean_title_str(title)
        company = normalize_text(company)
        
        # Strip common prefixes from company name
        company_prefix_regex = r'^(?:Compa\u00f1\u00eda|C\u00eda\.?|Cia\.?|Profesora?|Director|Coreograf\u00eda|Direcci\u00f3n|Autora?|Conservatorio|Grupo|Escuela|Producci\u00f3n)(?::\s*|\s+)'
        company = re.sub(company_prefix_regex, '', company, flags=re.IGNORECASE)
        
        # If title matches company, or is redundant
        if company and title:
            # If title is part of company or vice-versa
            if company.lower() == title.lower():
                # Title is likely the work, and company is the artist. 
                # Keep both as is, or if they are identical, company is the entity.
                pass
            elif title.lower().startswith(company.lower()):
                # Remove company from title
                title = re.sub(r'^' + re.escape(company) + r'[:\s-]*', '', title, flags=re.IGNORECASE)
            elif company.lower().startswith(title.lower()) and len(company) > len(title) + 5:
                # Title is actually a prefix of the company name? 
                pass

        # Fallback: If company is empty, use title as company
        if not company or company == "":
            company = title
            
        # Ensure title isn't empty
        if not title:
            title = base_title
        
        # If title is still empty (shouldn't happen), use h1_text
        if not title:
            title = clean_title_str(h1_text)
        
        # Sessions
        sessions = parse_sessions(soup, content_area)
        
        if not sessions:
            # Fallback for date field
            date_field = soup.select_one('.field--name-field-fecha-actividad, .field--name-field-fecha')
            if date_field:
                date_text = date_field.text.strip()
                match = re.search(r'(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4}).*?(\d{2}):(\d{2})', date_text.lower())
                if match:
                    day = match.group(1).zfill(2)
                    month_name = match.group(2)
                    year = match.group(3)
                    hour = match.group(4)
                    minute = match.group(5)
                    months = {
                        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
                        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
                        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
                    }
                    month = months.get(month_name, '01')
                    sessions.append(Session(date=f"{year}-{month}-{day}", time=f"{hour}:{minute}"))

        if not sessions:
            print(f"  Warning: No sessions found for {url}")
            return None
            
        # Filter out old events (before 2025)
        if all(int(s.date.split('-')[0]) < 2025 for s in sessions):
            print(f"  Skipping old event: {url}")
            return None
            
        # Price
        price_range = "Consultar web"
        if content_area:
            body_text = content_area.text
            # Try to find price in various formats
            price_match = re.search(r'(?:Entradas|Precio|Coste):\s*(.*?)(?:\n|\.|$)', body_text, re.IGNORECASE)
            if not price_match:
                # Look for patterns like "10 €" or "8 euros"
                price_match = re.search(r'(\d+(?:[,.]\d+)?\s*(?:euros|€))', body_text, re.IGNORECASE)
                
            if price_match:
                price_range = price_match.group(1).strip()
                # Clean up the price string (remove trailing dots, etc)
                price_range = re.sub(r'[\.\s]+$', '', price_range)
                if len(price_range) > 60:
                    price_range = price_range[:57] + "..."
            
            # If price mentions "Gratis", mark it
            if "gratis" in body_text.lower() or "entrada libre" in body_text.lower() or "acceso libre" in body_text.lower():
                if price_range == "Consultar web" or len(price_range) < 2:
                    price_range = "Gratuito"
        
        # Image
        image_url = ""
        if content_area:
            img_el = content_area.select_one('img[src*="/assets/"], img[src*="/styles/"]')
            if img_el:
                image_url = img_el.get('src')
        
        if image_url and not image_url.startswith('http'):
            image_url = "https://www.comunidad.madrid" + image_url
            
        if not image_url or "administracion-digital" in image_url:
            og_img = soup.find('meta', property='og:image')
            if og_img:
                image_url = og_img.get('content', '')

        return Event(
            id=str(uuid.uuid4()),
            title=title,
            company=company,
            venue=Venue("Centro Cultural Paco Rabal", "Madrid"),
            type="Danza",
            price_range=price_range,
            is_free="gratis" in price_range.lower() or "gratuito" in price_range.lower(),
            image_url=image_url or "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=800&auto=format&fit=crop",
            url=url,
            sessions=sessions
        )
    except Exception as e:
        print(f"  Error scraping event details {url}: {e}")
        return None

async def scrape_paco_rabal():
    print("Starting Centro Cultural Paco Rabal Scraper...")
    events = []
    base_url = "https://www.comunidad.madrid"
    main_url = f"{base_url}/centros/centro-cultural-paco-rabal"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"Discovering events from: {main_url}")
        try:
            await page.goto(main_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(2000)
            
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            urls = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/actividades/' in href and ('danza' in href.lower() or 'baile' in href.lower()):
                    if not href.startswith('http'):
                        href = base_url + href
                    urls.append(href)
            
            urls = list(set(urls))
            print(f"Found {len(urls)} candidate dance events.")
            
            for url in urls:
                event = await scrape_event_details(page, url)
                if event:
                    events.append(event)
                    
        except Exception as e:
            print(f"Error in discovery phase: {e}")
            
        await browser.close()
        
    print(f"Paco Rabal Scraping finished. Total events: {len(events)}")
    return events

if __name__ == "__main__":
    res = asyncio.run(scrape_paco_rabal())
    for e in res:
        # Filter out old events (e.g. from 2021)
        if any(s.date.startswith('2021') for s in e.sessions):
            continue
        print(f"Result: {e.title} | Company: {e.company} | sessions: {len(e.sessions)} | Price: {e.price_range}")
