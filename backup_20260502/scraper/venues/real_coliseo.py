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
if sys.stdout.encoding != 'UTF-8':
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
        
        # Identify content area to avoid sidebar/menu dates
        content_area = soup.select_one('#block-comunidad-madrid-content, .c-main-content, main')
        
        # --- EXTRACT TITLE AND COMPANY ---
        # 1. Base title from H1
        h1_el = soup.select_one('h1.heading, h1.c-title, h1')
        h1_text = h1_el.get_text().strip() if h1_el else ""
        
        # Clean the H1 title as a base
        base_title = h1_text
        # Remove common prefixes
        base_title = re.sub(r'^(?:DANZA|MÚSICA|DANZA Y MÚSICA|TEATRO|ACTIVIDADES|PROGRAMACIÓN):\s*', '', base_title, flags=re.IGNORECASE)
        # Remove date suffixes if they exist in the H1
        base_title = re.split(r'\s+[-–—]\s+(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)', base_title, flags=re.IGNORECASE)[0]
        base_title = base_title.split(' - ')[0].strip()
        
        title = base_title
        company = ""
        
        # 2. Refined Extraction from Body H3 (common in Comunidad de Madrid pages)
        if content_area:
            body_divs = content_area.select('.field--name-body, .field--name-field-texto-explicativo')
            
            # Keywords that suggest a line is a COMPANY rather than a title
            company_keywords = r'Compañía|Cía\.?|Conservatorio|Ballet|Grupo|Escuela|Centro|Creación|Profesora?|Director|Coreografía|Dirección|Autora?'
            # Patterns to skip
            skip_patterns = r'\d+\s*a\s*\d+\s*h|lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo|horas|precio|entradas|Coreografía|Música|Sinfonía|Pieza'

            for body_el in body_divs:
                h3_elements = body_el.select('h3')
                for h3_el in h3_elements:
                    h3_text = h3_el.get_text(separator="\n").strip()
                    if not h3_text or len(h3_text) < 3: continue
                    
                    if re.search(skip_patterns, h3_text, re.IGNORECASE):
                        continue
                        
                    lines = [l.strip() for l in h3_text.split("\n") if l.strip()]
                    
                    if len(lines) >= 2:
                        # Case: Title \n Company
                        potential_title = lines[0]
                        potential_company = lines[1]
                        
                        if not re.search(skip_patterns, potential_title, re.IGNORECASE):
                            title = re.sub(r'^(?:DANZA|MÚSICA|TEATRO):\s*', '', potential_title, flags=re.IGNORECASE)
                            company = potential_company
                            break
                    elif len(lines) == 1:
                        line = lines[0]
                        is_company_like = re.search(company_keywords, line, re.IGNORECASE)
                        if (not title or title == base_title) and not is_company_like:
                            title = re.sub(r'^(?:DANZA|MÚSICA|TEATRO):\s*', '', line, flags=re.IGNORECASE)
                        
                        next_el = h3_el.find_next_sibling(['p', 'div', 'strong', 'em'])
                        if next_el:
                            next_text = next_el.get_text().strip()
                            if next_text and len(next_text) > 3 and not re.search(skip_patterns, next_text, re.IGNORECASE):
                                if re.search(company_keywords, next_text, re.IGNORECASE) or next_el.name in ['strong', 'em']:
                                    company = next_text
                                    break
                        if is_company_like:
                            company = line
                            break
                if title and company: break

        # 3. Fallback for Company
        if not company:
            company_el = soup.select_one('.field--name-field-compania, .field--name-field-autor, .field--name-field-artista')
            if company_el:
                company = company_el.text.strip()
            else:
                # Regex fallback in body
                if content_area:
                    body_text = content_area.get_text(separator="\n")
                    # Try to find "Compañía: Name"
                    comp_match = re.search(r'(?:Compañía|Cía\.?|Grupo|Ballet|Director|Coreografía):\s*([^.\n\r]{3,60})', body_text, re.IGNORECASE)
                    if comp_match:
                        company = comp_match.group(1).strip()

        # --- FINAL CLEANUP ---
        def normalize_text(text):
            if not text: return ""
            text = text.replace('\xa0', ' ')
            text = unicodedata.normalize('NFC', text)
            text = " ".join(text.split())
            text = text.strip('• \t\n\r\xa0*!-–—,.')
            return text

        title = normalize_text(title)
        company = normalize_text(company)
        
        # Remove day/date patterns from title
        if title:
            days_regex = r'\s*[-–—]\s*(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)'
            title = re.split(days_regex, title, flags=re.IGNORECASE)[0]
            months_regex = r'(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)'
            title = re.sub(rf'\s*\d+\s+de\s+{months_regex}.*$', '', title, flags=re.IGNORECASE)
            title = title.strip('• \t\n\r\xa0*!-–—,.')

        # Company prefix removal
        company_prefix_regex = r'^(?:Compañía|Cía\.?|Cia\.?|Profesora?|Director|Coreografía|Dirección|Autora?|Conservatorio|Grupo|Escuela)(?::\s*|\s+)'
        company = re.sub(company_prefix_regex, '', company, flags=re.IGNORECASE)
        
        if not company or company == "":
            company = title # Last fallback

        # Sessions
        sessions = parse_sessions(soup, content_area)
        
        if not sessions:
            date_field = soup.select_one('.field--name-field-fecha-actividad, .field--name-field-fecha')
            if date_field:
                date_text = date_field.text.strip()
                match = re.search(r'(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4}).*?(\d{2}):(\d{2})', date_text.lower())
                if match:
                    day, month_name, year, hour, minute = match.groups()
                    months = {
                        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
                        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
                        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
                    }
                    month = months.get(month_name, '01')
                    sessions.append(Session(date=f"{year}-{month}-{day}", time=f"{hour}:{minute}"))

        if not sessions:
            return None
            
        # Price
        price_range = "Consultar web"
        if content_area:
            body_text = content_area.text
            price_match = re.search(r'(?:Entradas|Precio|Coste):\s*(.*?)(?:\n|\.|$)', body_text, re.IGNORECASE)
            if not price_match:
                price_match = re.search(r'(\d+(?:[,.]\d+)?\s*(?:euros|€))', body_text, re.IGNORECASE)
            if price_match:
                price_range = price_match.group(1).strip()
                if len(price_range) > 60: price_range = price_range[:57] + "..."
            
            if "gratis" in body_text.lower() or "entrada libre" in body_text.lower() or "gratuito" in body_text.lower():
                price_range = "Gratuito"

        # Image
        image_url = ""
        if content_area:
            img_el = content_area.select_one('img[src*="/assets/"], img[src*="/styles/"]')
            if img_el: image_url = img_el.get('src')
        
        if not image_url:
            img_el = soup.select_one('.field--name-field-media-image img, .field--name-field-imagen-principal img')
            if img_el: image_url = img_el.get('src')
        
        if image_url and not image_url.startswith('http'):
            image_url = "https://www.comunidad.madrid" + image_url
            
        if not image_url or "administracion-digital" in image_url:
            og_img = soup.find('meta', property='og:image')
            if og_img: image_url = og_img.get('content', '')

        return Event(
            id=str(uuid.uuid4()),
            title=title,
            company=company,
            venue=Venue("Real Coliseo de Carlos III", "San Lorenzo de El Escorial"),
            type="Danza",
            price_range=price_range,
            is_free="gratis" in price_range.lower() or "gratuito" in price_range.lower() or price_range == "Gratuito",
            image_url=image_url or "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=800&auto=format&fit=crop",
            url=url,
            sessions=sessions
        )
    except Exception as e:
        print(f"  Error scraping event details {url}: {e}")
        return None

async def scrape_real_coliseo():
    print("Starting Real Coliseo de Carlos III Scraper...")
    events = []
    base_url = "https://www.comunidad.madrid"
    main_url = f"{base_url}/centros/real-coliseo-carlos-iii-san-lorenzo-escorial"
    
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
                if '/actividades/' in href:
                    text = a.get_text().lower()
                    if 'danza' in href.lower() or 'baile' in href.lower() or 'danza' in text or 'baile' in text:
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
        
    print(f"Real Coliseo Scraping finished. Total events: {len(events)}")
    return events

if __name__ == "__main__":
    res = asyncio.run(scrape_real_coliseo())
    for e in res:
        print(f"Result: {e.title} | Company: {e.company} | Sessions: {len(e.sessions)} | Price: {e.price_range}")

