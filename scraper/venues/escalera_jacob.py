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

def parse_jacob_date(date_str):
    """
    Parses dates like 'mié., 3 jun.' or 'sáb., 20 jun.'
    Returns YYYY-MM-DD
    """
    months = {
        'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04',
        'may': '05', 'jun': '06', 'jul': '07', 'ago': '08',
        'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12'
    }
    
    try:
        # Remove day of week and clean
        # 'mié., 3 jun.' -> '3 jun.'
        clean_str = re.sub(r'^[a-záéíóú]+\.,\s*', '', date_str.lower()).strip()
        parts = clean_str.split()
        if len(parts) >= 2:
            day = parts[0].zfill(2)
            month_abbr = parts[1].replace('.', '')
            month = months.get(month_abbr, '01')
            year = str(datetime.now().year)
            
            # If month has passed, assume next year
            current_month = datetime.now().month
            if int(month) < current_month:
                year = str(int(year) + 1)
                
            return f"{year}-{month}-{day}"
    except Exception as e:
        print(f"Error parsing date {date_str}: {e}")
    return ""

def scrape_event_details(context, url):
    """Scrapes a single event page for details and sessions."""
    print(f"  Scraping event: {url}")
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Extract basic info
        title_el = page.query_selector('h1')
        title = title_el.inner_text().strip() if title_el else "Evento sin título"
        
        # Company
        company = ""
        company_label = page.query_selector('h4:has-text("Compañía:")')
        if company_label:
            # The company is usually the next sibling or text node
            company_text = page.evaluate('(el) => el.nextSibling.textContent', company_label)
            if company_text:
                company = company_text.strip()
        
        # Image
        image_url = ""
        # Check Open Graph first
        og_image = page.query_selector('meta[property="og:image"]')
        if og_image:
            image_url = og_image.get_attribute('content')
            
        if not image_url:
            img_el = page.query_selector('img[alt="' + title + '"]') or page.query_selector('.cartelera-detalle img')
            if img_el:
                image_url = img_el.get_attribute('src')
        
        if image_url and not image_url.startswith('http'):
            image_url = "https://www.laescaleradejacob.es" + image_url

        # Sessions from iframe
        sessions = []
        price_range = "Consultar web"
        
        iframe_el = page.query_selector('iframe[src*="dinaticket"]')
        if iframe_el:
            iframe_src = iframe_el.get_attribute('src')
            print(f"    Found dinaticket iframe: {iframe_src}")
            
            iframe_page = context.new_page()
            try:
                iframe_page.goto(iframe_src, wait_until="load", timeout=90000)
                # Wait a bit for content to render just in case
                iframe_page.wait_for_timeout(2000)
                
                # Each session block seems to have text like 'mié., 3 jun. Sala Teatro 20:00 h 10€'
                # Let's try to find elements that contain the price or time
                
                # Based on the snapshot, sessions are listed sequentially
                # We can look for patterns or specific classes if we knew them, 
                # but text content works well for this structure.
                
                # Let's extract all text and parse it
                all_text = iframe_page.evaluate('() => document.body.innerText')
                
                # Split by "gastos gestión" or similar markers
                blocks = all_text.split("gastos gestión")
                prices = []
                
                for block in blocks:
                    # Look for date: mié., 3 jun.
                    date_match = re.search(r'([a-záéíóú]+\.,\s*\d+\s*[a-z]+\.?)', block.lower())
                    # Look for time: 20:00 h
                    time_match = re.search(r'(\d{1,2}:\d{2})\s*h', block.lower())
                    # Look for price: 10€
                    price_match = re.search(r'(\d+)\s*€', block)
                    
                    if date_match and time_match:
                        date_str = date_match.group(1)
                        time_str = time_match.group(1)
                        iso_date = parse_jacob_date(date_str)
                        if iso_date:
                            sessions.append(Session(date=iso_date, time=time_str))
                    
                    if price_match:
                        prices.append(int(price_match.group(1)))
                
                if prices:
                    min_p = min(prices)
                    max_p = max(prices)
                    if min_p == max_p:
                        price_range = f"{min_p}€"
                    else:
                        price_range = f"{min_p}€ - {max_p}€"
                        
            except Exception as e:
                print(f"    Error scraping iframe: {e}")
            finally:
                iframe_page.close()

        return Event(
            id=str(uuid.uuid4()),
            title=title,
            company=company or "La Escalera de Jacob",
            venue=Venue("La Escalera de Jacob", "Madrid"),
            type="Danza",
            price_range=price_range,
            is_free=False,
            image_url=image_url or "https://www.laescaleradejacob.es/img/logo.png",
            url=url,
            sessions=sessions
        )
    except Exception as e:
        print(f"  Error scraping {url}: {e}")
        return None
    finally:
        page.close()

def scrape_escalera_jacob():
    print("Starting La Escalera de Jacob Scraper...")
    events = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        listing_url = "https://www.laescaleradejacob.es/cartelera/buscador/danza/"
        page = context.new_page()
        print(f"Discovering events from: {listing_url}")
        
        try:
            page.goto(listing_url, wait_until="domcontentloaded", timeout=60000)
            
            # Extract links to events
            # Based on snapshot: uid=1_138 StaticText "Danza" is inside a link
            links = page.query_selector_all('a:has-text("Danza")')
            urls = []
            for link in links:
                href = link.get_attribute('href')
                if href and '/cartelera/' in href and href != 'https://www.laescaleradejacob.es/cartelera/':
                    # Normalize URL
                    if href.startswith('/'):
                        href = "https://www.laescaleradejacob.es" + href
                    elif not href.startswith('http'):
                        href = "https://www.laescaleradejacob.es/cartelera/" + href
                    
                    if href != "https://www.laescaleradejacob.es/cartelera/buscador/":
                        urls.append(href)
            
            # Deduplicate
            urls = list(set(urls))
            print(f"Found {len(urls)} unique event URLs.")
            
            for url in urls:
                event = scrape_event_details(context, url)
                if event:
                    events.append(event)
                time.sleep(1) # Be nice
                
        except Exception as e:
            print(f"Error in discovery phase: {e}")
        finally:
            browser.close()
            
    print(f"La Escalera de Jacob finished. Total events: {len(events)}")
    return events

if __name__ == "__main__":
    results = scrape_escalera_jacob()
    for e in results:
        print(f"Event: {e.title} at {e.venue.name} - {len(e.sessions)} sessions, Price: {e.price_range}")
