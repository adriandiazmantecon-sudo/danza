from playwright.sync_api import sync_playwright
import uuid
import sys
import os
import re
import time

# Ensure the models are reachable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Event, Venue, Session

def parse_spanish_date(date_str):
    """Converts '07 mayo 2026' or '07 MAYO 2026' to '2026-05-07'"""
    months = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }
    # Clean up the string (remove commas, etc.)
    clean_str = date_str.lower().replace(',', ' ').replace('.', ' ')
    parts = clean_str.split()
    if len(parts) >= 3:
        day = parts[0].zfill(2)
        month = months.get(parts[1], '01')
        year = parts[2]
        if len(year) == 2:
            year = "20" + year
        return f"{year}-{month}-{day}"
    return ""

def scrape_event_details(browser, url):
    """Scrapes a single event page for all sessions and metadata using a fresh page."""
    print(f"Scraping event details: {url}")
    page = browser.new_page()
    try:
        # Increase timeout for slow site
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Extract Title
        title_el = page.query_selector('h1')
        title = title_el.inner_text().strip() if title_el else "Unknown Title"
        print(f"  Title: {title}")
        
        # Extract Company
        company_el = page.query_selector('h3.subt')
        company = company_el.inner_text().strip() if company_el else ""
        
        # Extract Image
        image_el = page.query_selector('.field--name-field-imagen img')
        image_url = ""
        if image_el:
            image_url = image_el.get_attribute('src')
            if image_url and not image_url.startswith('http'):
                image_url = "https://www.teatroreal.es" + image_url
                
        # Extract Price Range
        price_range = "Desde 15€" # Fallback
        price_els = page.query_selector_all('.field--name-field-precio, .field--name-field-precios, a[href*="tickets.teatroreal.es"]')
        for el in price_els:
            text = el.inner_text()
            match = re.search(r'Desde\s+(\d+)\s+euros', text, re.IGNORECASE)
            if match:
                price_range = f"Desde {match.group(1)}€"
                break

        # Extract Sessions
        sessions = []
        rows = page.query_selector_all('.functions-show__block--item')
        print(f"  Found {len(rows)} session rows")
        for row in rows:
            date_el = row.query_selector('.functions-show__block--item-date p')
            hour_el = row.query_selector('.functions-show__block--item-hour p')
            
            if date_el and hour_el:
                date_str = date_el.inner_text().strip()
                time_str = hour_el.inner_text().strip()
                
                iso_date = parse_spanish_date(date_str)
                if iso_date:
                    sessions.append(Session(date=iso_date, time=time_str))
        
        print(f"  Extracted {len(sessions)} valid sessions")
                    
        return Event(
            id=str(uuid.uuid4()),
            title=title,
            company=company,
            venue=Venue("Teatro Real", "Madrid"),
            type="Ballet" if "BALLET" in title.upper() or "BALLET" in company.upper() else "Danza",
            price_range=price_range,
            is_free=False,
            image_url=image_url,
            url=url,
            sessions=sessions
        )
    finally:
        page.close()

def scrape_teatro_real():
    print("Starting Teatro Real Scraper...")
    events = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # Discovery phase
        discovery_urls = [
            "https://www.teatroreal.es/es/temporada-actual/danza",
            "https://www.teatroreal.es/es/temporada/proxima-temporada/danza#toContent"
        ]
        
        urls = []
        for listing_url in discovery_urls:
            print(f"Discovering events from: {listing_url}")
            listing_page = browser.new_page()
            try:
                listing_page.goto(listing_url, wait_until="domcontentloaded", timeout=60000)
                # Use the robust selector found in inspection
                items = listing_page.query_selector_all('.page-thumb-artist__block.danza')
                print(f"  Found {len(items)} dance items in {listing_url}")
                for item in items:
                    link_el = item.query_selector('a')
                    if link_el:
                        href = link_el.get_attribute('href')
                        if href:
                            href = href.strip()
                            if not href.startswith('http'):
                                href = "https://www.teatroreal.es" + href
                            urls.append(href)
            except Exception as e:
                print(f"  Error on {listing_url}: {e}")
            finally:
                listing_page.close()
        
        # Add known URLs if they weren't discovered
        known_urls = [
            "https://www.teatroreal.es/es/espectaculo/real-ballet-suecia",
            "https://www.teatroreal.es/es/espectaculo/alvin-ailey-american-dance-theater",
            "https://www.teatroreal.es/es/espectaculo/tanztheater-wuppertal-pina-bausch"
        ]
        for url in known_urls:
            if url not in urls:
                urls.append(url)
        
        # Deduplicate
        urls = list(set(urls))
        print(f"Total URLs to scrape: {len(urls)}")
        
        for url in urls:
            try:
                event = scrape_event_details(browser, url)
                if event and event.sessions:
                    events.append(event)
            except Exception as e:
                print(f"Error scraping {url}: {e}")
            # Be nice to the server
            time.sleep(2)
                
        browser.close()
        
    print(f"Teatro Real Scraping finished. Total events: {len(events)}")
    return events

if __name__ == "__main__":
    res = scrape_teatro_real()
    for e in res:
        print(f"Result: {e.title} - {len(e.sessions)} sessions")
