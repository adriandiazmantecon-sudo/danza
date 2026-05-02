from playwright.sync_api import sync_playwright
import uuid
import sys
import os
import re
import time
from datetime import datetime

# Ensure the models are reachable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Event, Venue, Session

def get_current_season():
    """Calculates the current season string (e.g., '2025-2026') based on current date."""
    now = datetime.now()
    year = now.year
    if now.month >= 9: # Season starts in September
        return f"{year}-{year + 1}"
    else:
        return f"{year - 1}-{year}"

def parse_spanish_month(month_name):
    months = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }
    return months.get(month_name.lower().strip(), '01')

def parse_zarzuela_dates(date_text, time_text):
    """
    Parses complex Zarzuela date strings.
    Examples:
    - "11, 12, 14, 15, 16, 17, 18, 19, 21 y 22 de julio de 2026"
    - "23, 24, 25 y 26 de octubre de 2025"
    Time example: "19:30 horas (domingos 18:00 horas)"
    """
    sessions = []
    try:
        # Extract base times
        base_time = "19:30"
        sunday_time = "18:00"
        
        # Look for times in the text
        time_matches = re.findall(r'(\d{1,2}:\d{2})', time_text)
        if len(time_matches) >= 1:
            base_time = time_matches[0]
        if "domingo" in time_text.lower() and len(time_matches) >= 2:
            sunday_time = time_matches[1]

        # Clean date text
        date_text = date_text.replace('\n', ' ').strip()
        
        # Check for simple range "X al Y de Mes de Año"
        range_match = re.search(r'(\d+)\s+al\s+(\d+)\s+de\s+(\w+)\s+de\s+(\d{4})', date_text, re.IGNORECASE)
        if range_match:
            start_day = int(range_match.group(1))
            end_day = int(range_match.group(2))
            month = parse_spanish_month(range_match.group(3))
            year = int(range_match.group(4))
            for day in range(start_day, end_day + 1):
                d = datetime(year, int(month), day)
                t = sunday_time if d.weekday() == 6 else base_time
                sessions.append(Session(date=d.strftime('%Y-%m-%d'), time=t))
            return sessions

        # Check for list "X, Y, Z y W de Mes de Año"
        parts = re.split(r'\s+de\s+', date_text, flags=re.IGNORECASE)
        if len(parts) >= 3:
            days_str = parts[0]
            month_name = parts[1]
            year_str = re.search(r'\d{4}', parts[2]).group(0)
            
            month = parse_spanish_month(month_name)
            year = int(year_str)
            
            # Clean days_str: replace ' y ' with ', '
            days_str = days_str.replace(' y ', ', ')
            days = [int(s.strip()) for s in days_str.split(',') if s.strip().isdigit()]
            
            for day in days:
                try:
                    d = datetime(year, int(month), day)
                    t = sunday_time if d.weekday() == 6 else base_time
                    sessions.append(Session(date=d.strftime('%Y-%m-%d'), time=t))
                except ValueError:
                    continue
                    
    except Exception as e:
        print(f"  Error parsing dates '{date_text}': {e}")
        
    return sessions

def scrape_event_details(browser, url):
    print(f"Scraping Zarzuela event details: {url}")
    page = browser.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Title
        title_el = page.query_selector('h3.titulo')
        title = title_el.inner_text().strip() if title_el else "Unknown Title"
        
        # Company/Subtitle
        # h4 often contains "Title. Company"
        subtitle_el = page.query_selector('h4')
        company = ""
        if subtitle_el:
            subtitle = subtitle_el.inner_text().strip()
            # If title is in subtitle, try to remove it
            if title.lower() in subtitle.lower():
                company = subtitle.lower().replace(title.lower(), "").replace(".", "").strip().title()
            else:
                company = subtitle
        
        # Image
        image_el = page.query_selector('img.fotoFicha')
        image_url = ""
        if image_el:
            image_url = image_el.get_attribute('src')
            if image_url and not image_url.startswith('http'):
                image_url = "https://teatrodelazarzuela.inaem.gob.es" + image_url
        
        # Sessions (Dates and Times)
        # They are usually in a <p> after a <div> with class 'encabezado-bloque' that contains 'Fechas y Horarios'
        date_text = ""
        time_text = ""
        
        blocks = page.query_selector_all('.bloque-ficha')
        headers = page.query_selector_all('.encabezado-bloque')
        for header in headers:
            if 'Fechas y Horarios' in header.inner_text():
                # The p tag is usually a sibling of the encabezado-bloque div inside a bloque-ficha div
                parent = header.query_selector('xpath=..')
                if parent:
                    p_els = parent.query_selector_all('p')
                    for p in p_els:
                        text = p.inner_text().strip()
                        # Dates usually contain month names
                        if any(m in text.lower() for m in ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']):
                            lines = text.split('\n')
                            date_text = lines[0].strip()
                            time_text = lines[1].strip() if len(lines) > 1 else ""
                            break
                break
        
        all_sessions = parse_zarzuela_dates(date_text, time_text)
        
        # Filter for future sessions only
        today = datetime.now().date()
        future_sessions = [s for s in all_sessions if datetime.strptime(s.date, '%Y-%m-%d').date() >= today]
        
        if not future_sessions:
            print(f"  Skipping event {title}: No future sessions found.")
            return None
            
        print(f"  Title: {title}")
        print(f"  Company: {company}")
        print(f"  Sessions: {len(future_sessions)} future sessions found")

        return Event(
            id=str(uuid.uuid4()),
            title=title,
            company=company,
            venue=Venue("Teatro de la Zarzuela", "Madrid"),
            type="Danza",
            price_range="Consultar precio",
            is_free=False,
            image_url=image_url,
            url=url,
            sessions=future_sessions
        )
    except Exception as e:
        print(f"  Error scraping details for {url}: {e}")
        return None
    finally:
        page.close()

def scrape_zarzuela():
    print("Starting Teatro de la Zarzuela Scraper...")
    season = get_current_season()
    base_url = f"https://teatrodelazarzuela.inaem.gob.es/es/temporada/danza-{season}"
    print(f"Base URL for this season: {base_url}")
    
    events = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
            
            # Find all links to work detail pages
            # Selector identified: ul.listadoObras li a
            links = page.query_selector_all('ul.listadoObras li a')
            urls = []
            for link in links:
                href = link.get_attribute('href')
                if href:
                    if not href.startswith('http'):
                        href = "https://teatrodelazarzuela.inaem.gob.es" + href
                    if href not in urls:
                        urls.append(href)
            
            print(f"Found {len(urls)} event URLs to inspect.")
            
            for url in urls:
                event = scrape_event_details(browser, url)
                if event:
                    events.append(event)
                time.sleep(1) # Be respectful
                
        except Exception as e:
            print(f"Error during Zarzuela discovery: {e}")
        finally:
            page.close()
            browser.close()
            
    print(f"Teatro de la Zarzuela Scraping finished. Total events: {len(events)}")
    return events

if __name__ == "__main__":
    res = scrape_zarzuela()
    for e in res:
        print(f"Result: {e.title} at {e.venue.name} - {len(e.sessions)} sessions")
