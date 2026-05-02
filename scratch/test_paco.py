import asyncio
import re
import uuid
import sys
import os
import unicodedata
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Ensure models are reachable
sys.path.append(os.path.join(os.getcwd(), 'scraper'))
from models import Event, Venue, Session

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
        print(f"H1 Text: {h1_text}")
        
        # Clean the H1 title as a base
        base_title = h1_text
        base_title = re.sub(r'^(?:DANZA|MUSICA|DANZA Y MUSICA|TEATRO|ACTIVIDADES|PROGRAMACION):\s*', '', base_title, flags=re.IGNORECASE)
        base_title = re.split(r'\s+-\s+(?:lunes|martes|miercoles|jueves|viernes|sabado|domingo)', base_title, flags=re.IGNORECASE)[0]
        base_title = re.split(r'\s+-\s+\d{1,2}\s+de\s+', base_title, flags=re.IGNORECASE)[0]
        base_title = base_title.split(' - ')[0].strip()
        print(f"Base Title: {base_title}")
        
        title = base_title
        company = ""
        
        # 2. Refined Extraction from Body H3
        if content_area:
            # Look for body divs
            body_divs = content_area.select('.field--name-body, .field--name-field-texto-explicativo')
            
            # Keywords that suggest a line is a COMPANY rather than a title
            company_keywords = r'Compa\u00f1\u00eda|C\u00eda\.?|Conservatorio|Ballet|Grupo|Escuela|Centro|Creaci\u00f3n|Profesora?|Director|Coreograf\u00eda|Direcci\u00f3n|Autora?'
            # Patterns to skip (schedules, pieces, etc)
            skip_patterns = r'\d+\s*a\s*\d+\s*h|lunes|martes|mi\u00e9rcoles|miercoles|jueves|viernes|s\u00e1bado|sabado|domingo|horas|precio|entradas|Coreograf\u00eda|M\u00fasica|Sinfon\u00eda|Pieza'

            for body_el in body_divs:
                h3_elements = body_el.select('h3')
                for h3_el in h3_elements:
                    h3_text = h3_el.get_text(separator="\n").strip()
                    print(f"Found H3: {h3_text}")
                    if not h3_text or len(h3_text) < 3: continue
                    
                    if re.search(skip_patterns, h3_text, re.IGNORECASE):
                        continue
                        
                    lines = [l.strip() for l in h3_text.split("\n") if l.strip()]
                    print(f"Lines in H3: {lines}")
                    
                    if len(lines) >= 2:
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
                                if re.search(company_keywords, next_text, re.IGNORECASE) or next_el.name in ['strong', 'em'] or next_el.find(['strong', 'em']):
                                    company = next_text
                                    break
                        
                        if is_company_like:
                            company = line
                            break
                    
                if title and company:
                    break

        print(f"Intermediate Title: {title}")
        print(f"Intermediate Company: {company}")

        # Final cleanup for titles
        if title:
            title = re.sub(r'^(?:DANZA|M\u00daSICA|TEATRO|ACTIVIDADES|PROGRAMACI\u00d3N):\s*', '', title, flags=re.IGNORECASE)
            days_regex = r'\s+-\s+(?:lunes|martes|mi\u00e9rcoles|miercoles|jueves|viernes|s\u00e1bado|sabado|domingo)'
            title = re.split(days_regex, title, flags=re.IGNORECASE)[0]
            title = re.split(r':\s+(?:lunes|martes|mi\u00e9rcoles|miercoles|jueves|viernes|s\u00e1bado|sabado|domingo)', title, flags=re.IGNORECASE)[0]
            title = re.sub(r'\s+\d{1,2}:\d{2}\s*h?$', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s+-\s+Paco Rabal.*$', '', title, flags=re.IGNORECASE)
            title = title.strip('• \t\n\r\xa0*!-–—,.')

        print(f"Final Title: {title}")
        print(f"Final Company: {company}")

    except Exception as e:
        print(f"Error: {e}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = "https://www.comunidad.madrid/actividades/2026/danza-aurunca-sabado-9"
        await scrape_event_details(page, url)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
