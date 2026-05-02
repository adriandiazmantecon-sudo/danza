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

def parse_spanish_month(month_name):
    month_name = month_name.lower().strip().replace('.', '')
    months = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
        'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05', 'jun': '06',
        'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12'
    }
    return months.get(month_name, '01')

def parse_boadilla_date(date_text):
    """
    Parses Boadilla date strings like 'Sábado, 5 de Junio de 2026', '5 Junio, 2026' or 'Jun. 05, 2026'.
    """
    try:
        # Clean up: remove 'de', commas, and extra spaces
        clean_text = date_text.lower().replace(' de ', ' ').replace(',', ' ').strip()
        parts = clean_text.split()
        
        # Look for day, month, year
        day = ""
        month = ""
        year = ""
        
        for part in parts:
            clean_part = part.replace('.', '').strip()
            if clean_part.isdigit():
                if len(clean_part) <= 2:
                    day = clean_part.zfill(2)
                elif len(clean_part) == 4:
                    year = clean_part
            else:
                m = parse_spanish_month(clean_part)
                # Check if it matched a known month (by checking if the input part (without dot) is in the keys)
                # Actually parse_spanish_month returns '01' as default, which is dangerous.
                # Let's improve parse_spanish_month to return None if not found.
                pass 

        # Redefining logic here for clarity
        months_map = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
            'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05', 'jun': '06',
            'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12'
        }
        
        for part in parts:
            p = part.replace('.', '').strip()
            if p in months_map:
                month = months_map[p]
            elif p.isdigit():
                if len(p) <= 2:
                    day = p.zfill(2)
                elif len(p) == 4:
                    year = p
        
        if day and month and year:
            return f"{year}-{month}-{day}"
    except Exception as e:
        print(f"  Error parsing date '{date_text}': {e}")
    return None

def extract_time(text):
    # Search for HH:MM
    match = re.search(r'(\d{1,2}[:.]\d{2})', text)
    if match:
        return match.group(1).replace('.', ':')
    return "20:30"

def extract_price(text):
    text_lower = text.lower()
    if any(kw in text_lower for kw in ['entrada libre', 'gratuito', 'gratis']):
        return "Gratis", True
    
    price_match = re.search(r'(\d+[,.]?\d*\s*€)', text)
    if price_match:
        return price_match.group(1), False
        
    return "Consultar", False

def extract_venue(text):
    if "Palacio" in text and "Luis" in text:
        return "Jardines del Palacio del Infante Don Luis"
    if "Auditorio" in text:
        return "Auditorio Municipal"
    return "Boadilla del Monte (Varios)"

def scrape_event_details(browser, url):
    print(f"Scraping Boadilla event details: {url}")
    page = browser.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Title
        title_el = page.query_selector('h1.evento_title')
        if not title_el:
            title_el = page.query_selector('#page-title')
        title = title_el.inner_text().strip() if title_el else "Unknown Title"
        print(f"  Title found: {title}")
        
        # Check if it's dance related
        body_el = page.query_selector('.field-name-body .field-item')
        body_text = body_el.inner_text() if body_el else ""
        
        keywords = ['danza', 'baile', 'ballet', 'flamenco', 'coreografía']
        is_dance = any(kw in title.lower() for kw in keywords) or any(kw in body_text.lower() for kw in keywords)
        
        if not is_dance:
            print(f"  Skipping non-dance event: {title}")
            return None

        # Date
        # Boadilla often has dates in multiple places
        date_selectors = [
            '.field-name-field-evento-fechas .field-item',
            '.field-name-field-fecha-de-evento .field-item',
            '.field-name-field-fecha-evento .field-item',
            '.field-name-field-fecha-de-noticia .field-item'
        ]
        
        date_text = ""
        for sel in date_selectors:
            el = page.query_selector(sel)
            if el:
                date_text = el.inner_text().strip()
                break
            
        print(f"  Date text found: {date_text}")
        event_date = parse_boadilla_date(date_text)
        
        if not event_date:
            print(f"  Could not parse date for {title}")
            return None
            
        # Check if future
        today = datetime.now().date()
        try:
            if datetime.strptime(event_date, '%Y-%m-%d').date() < today:
                print(f"  Skipping past event: {title} ({event_date})")
                return None
        except:
            pass

        # Time
        event_time = extract_time(body_text)
        
        # Venue
        venue_name = extract_venue(body_text)
        
        # Price
        price_range, is_free = extract_price(body_text)
        
        # Image
        image_el = page.query_selector('.field-name-field-imagen-de-noticia img')
        if not image_el:
            image_el = page.query_selector('.field-name-field-imagen img')
            
        image_url = ""
        if image_el:
            image_url = image_el.get_attribute('src')
            if image_url and not image_url.startswith('http'):
                image_url = "https://www.ayuntamientoboadilladelmonte.org" + image_url

        # Company
        company = ""
        comp_match = re.search(r'(?:Compañía|Cía\.?|Escuela de)\s+([^.\n,]+)', body_text, re.IGNORECASE)
        if comp_match:
            company = comp_match.group(1).strip()

        print(f"  Final Event: {title} on {event_date} at {event_time}")

        return Event(
            id=str(uuid.uuid4()),
            title=title,
            company=company,
            venue=Venue(venue_name, "Boadilla del Monte"),
            type="Danza",
            price_range=price_range,
            is_free=is_free,
            image_url=image_url,
            url=url,
            sessions=[Session(date=event_date, time=event_time)]
        )
    except Exception as e:
        print(f"  Error scraping details for {url}: {e}")
        return None
    finally:
        page.close()

def scrape_boadilla():
    print("Starting Boadilla del Monte Scraper...")
    # Use search query to find dance events more reliably
    base_url = "https://www.ayuntamientoboadilladelmonte.org/boadilla-actualidad/agenda?items_per_page=100&field_tipo_de_evento_target_id=89&query=danza"
    
    events = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
            
            # Find all links to event detail pages
            links = page.query_selector_all('.field-name-title a')
            urls = []
            for link in links:
                href = link.get_attribute('href')
                if href:
                    if not href.startswith('http'):
                        href = "https://www.ayuntamientoboadilladelmonte.org" + href
                    if href not in urls:
                        urls.append(href)
            
            # Also try without the 'danza' query but with the 100 items limit to catch musicals or others
            page.goto("https://www.ayuntamientoboadilladelmonte.org/boadilla-actualidad/agenda?items_per_page=100&field_tipo_de_evento_target_id=89", wait_until="domcontentloaded", timeout=60000)
            links2 = page.query_selector_all('.field-name-title a')
            for link in links2:
                href = link.get_attribute('href')
                if href:
                    if not href.startswith('http'):
                        href = "https://www.ayuntamientoboadilladelmonte.org" + href
                    if href not in urls:
                        urls.append(href)

            print(f"Found {len(urls)} potential event URLs.")
            
            for url in urls:
                event = scrape_event_details(browser, url)
                if event:
                    events.append(event)
                time.sleep(1) # Be respectful
                
        except Exception as e:
            print(f"Error during Boadilla discovery: {e}")
        finally:
            page.close()
            browser.close()
            
    print(f"Boadilla Scraping finished. Total events: {len(events)}")
    return events

if __name__ == "__main__":
    res = scrape_boadilla()
    for e in res:
        print(f"Result: {e.title} at {e.venue.name} - {e.sessions[0].date} {e.sessions[0].time}")
