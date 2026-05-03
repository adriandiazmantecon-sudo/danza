from playwright.sync_api import sync_playwright
import uuid
import sys
import os
import re
import time

# Ensure the models are reachable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Event, Venue, Session

def try_goto(page, url, timeout=90000, retries=3):
    for i in range(retries):
        try:
            print(f"  Navigating to {url} (Attempt {i+1})...")
            # Use a slightly more conservative wait
            page.goto(url, wait_until="load", timeout=timeout)
            return True
        except Exception as e:
            print(f"  Attempt {i+1} failed: {e}")
            if i == retries - 1:
                return False
            time.sleep(2 * (i + 1))
    return False

def parse_spanish_date(date_str):
    """Converts 'Jueves 28 de Mayo de 2026' to '2026-05-28' or handles '20 de mayo'"""
    months = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }
    # Clean up the string
    clean_str = date_str.lower().replace(',', ' ').replace('.', ' ').strip()
    parts = clean_str.split()
    
    # Format: [Weekday] [Day] de [Month] de [Year]
    # Example: ['jueves', '28', 'de', 'mayo', 'de', '2026']
    if len(parts) >= 6:
        day = parts[1].zfill(2)
        month = months.get(parts[3], '01')
        year = parts[5]
        return f"{year}-{month}-{day}"
    
    # Format: [Day] de [Month]
    # Example: ['20', 'de', 'mayo']
    if len(parts) >= 3 and parts[1] == 'de':
        day = parts[0].zfill(2)
        month = months.get(parts[2], '01')
        year = str(time.localtime().tm_year)
        # If the month has passed, assume next year
        current_month = time.localtime().tm_mon
        if int(month) < current_month:
            year = str(int(year) + 1)
        return f"{year}-{month}-{day}"
        
    return ""

def scrape_event_details(context, url):
    """Scrapes a single event page for price and booking URL."""
    print(f"Scraping event details: {url}")
    page = context.new_page()
    # Set a standard user agent
    page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})
    
    try:
        # Increase timeout to 90s and use retry
        if not try_goto(page, url):
            print(f"  Failed to load event page after retries: {url}")
            return None
        
        # Wait for some content to load
        page.wait_for_timeout(3000)
        
        # Extract Title
        title_el = page.query_selector('div.autor-show-show p, p[itemprop="performers"]')
        title = title_el.inner_text().strip() if title_el else ""
        
        # Extract Company
        company_el = page.query_selector('div.destacado-title h1, h1[itemprop="name"]')
        company = company_el.inner_text().strip() if company_el else "Teatros del Canal"
        
        if not title and company_el:
            title = company
            company = "Teatros del Canal"

        # Extract Image
        image_url = ""
        image_el = page.query_selector('.destacado-right img')
        if image_el:
            image_url = image_el.get_attribute('src')
        
        if not image_url:
            og_image = page.query_selector('meta[property="og:image"]')
            if og_image:
                image_url = og_image.get_attribute('content')
        
        # Extract Price Range
        price_range = "Consultar web"
        price_els = page.query_selector_all('p, div, span, a')
        for el in price_els:
            try:
                text = el.inner_text()
                match = re.search(r'Desde\s*(\d+)\s*€', text, re.IGNORECASE)
                if match:
                    price_range = f"Desde {match.group(1)}€"
                    break
            except:
                continue

        # Extract Booking URL
        booking_url = ""
        buy_btn = page.query_selector('a.boton-comprar-aside-single-event')
        if buy_btn:
            booking_url = buy_btn.get_attribute('href')
        
        sessions = []
        if booking_url:
            print(f"  Going to booking page: {booking_url}")
            if try_goto(page, booking_url):
                page.wait_for_timeout(5000) # Wait a bit longer
                
                # Extract sessions from .DetalleTabla
                rows = page.query_selector_all('.DetalleTabla')
                for row in rows:
                    date_el = row.query_selector('.ListaSesionesFecha')
                    hour_el = row.query_selector('.ListaSesionesHora a')
                    
                    if date_el and hour_el:
                        date_str = date_el.inner_text().strip()
                        time_str = hour_el.inner_text().strip()
                        
                        iso_date = parse_spanish_date(date_str)
                        if iso_date:
                            sessions.append(Session(date=iso_date, time=time_str))
        
        if not sessions:
            print("  Warning: No sessions found on booking page.")

        # Always return the event, even if sessions are empty (it will be filtered by the UI if needed)
        # But for the aggregator, we keep it.
        return Event(
            id=str(uuid.uuid4()),
            title=title or "Evento sin t\u00edtulo",
            company=company,
            venue=Venue("Teatros del Canal", "Madrid"),
            type="Danza",
            price_range=price_range,
            is_free=False,
            image_url=image_url or "https://images.unsplash.com/photo-1518834107812-67b0b7c58434?q=80&w=800&auto=format&fit=crop",
            url=url,
            sessions=sessions
        )
    except Exception as e:
        print(f"  Error scraping event details for {url}: {e}")
        return None
    finally:
        page.close()

def scrape_teatros_del_canal():
    print("Starting Teatros del Canal Scraper (Sync Mode)...")
    events = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Set a global user agent for the context
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Discovery phase
        listing_page = context.new_page()
        listing_url = "https://www.teatroscanal.com/entradas/danza-madrid/"
        print(f"Discovering events from: {listing_url}")
        
        try:
            if try_goto(listing_page, listing_url):
                # Wait for the selector instead of fixed time
                try:
                    listing_page.wait_for_selector('.div-show2', timeout=20000)
                except:
                    print("  Warning: Timeout waiting for .div-show2, proceeding anyway...")
                
                urls = []
                items = listing_page.query_selector_all('.div-show2')
                print(f"Found {len(items)} items in listing")
                for item in items:
                    # Look for links in various places
                    link_el = item.query_selector('a.btn-info') or item.query_selector('h2.show-home a')
                    if link_el:
                        href = link_el.get_attribute('href')
                        if href:
                            urls.append(href)
            
            listing_page.close()
            
            # Deduplicate
            urls = list(set(urls))
            # Filter out abonos
            urls = [u for u in urls if '/abono-' not in u]
            print(f"Total URLs to scrape: {len(urls)}")
            
            for url in urls:
                try:
                    event = scrape_event_details(context, url)
                    if event and "ABONO" not in event.title.upper():
                        events.append(event)
                except Exception as e:
                    print(f"Error scraping {url}: {e}")
                time.sleep(1)
                
        except Exception as e:
            print(f"Error in discovery phase: {e}")
            
        browser.close()
        
    print(f"Teatros del Canal Scraping finished. Total events: {len(events)}")
    return events

if __name__ == "__main__":
    res = scrape_teatros_del_canal()
    for e in res:
        print(f"Result: {e.title} - {len(e.sessions)} sessions")
