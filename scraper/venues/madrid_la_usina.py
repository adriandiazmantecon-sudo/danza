from playwright.sync_api import sync_playwright
import uuid
import sys
import os
import re
import time
import json
from datetime import datetime

# Ensure the models are reachable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Event, Venue, Session

def scrape_event_details(context, url):
    """Scrapes a single event page for details and sessions."""
    print(f"  Scraping event: {url}")
    page = context.new_page()
    try:
        # User agent to avoid detection
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        
        # Extract basic info
        title_el = page.query_selector('h1')
        title = title_el.inner_text().strip() if title_el else "Evento sin título"
        
        # Image
        image_url = ""
        img_el = page.query_selector('meta[property="og:image"]')
        if img_el:
            image_url = img_el.get_attribute('content')
            
        # Extract company from subtitle or description if possible
        company = "Compañía desconocida"
        subtitle_el = page.query_selector('.subtitle') or page.query_selector('.event-subtitle')
        if subtitle_el:
            company = subtitle_el.inner_text().strip()
        
        if company == "Compañía desconocida":
            # Try multiple potential description selectors
            selectors = ['.description', '.event-description', '#description', '.js-description']
            for sel in selectors:
                desc_el = page.query_selector(sel)
                if desc_el:
                    desc_text = desc_el.inner_text()
                    match = re.search(r'Compañía:\s*([^\n\.]+)', desc_text)
                    if match:
                        company = match.group(1).strip()
                        break
            
            # Final fallback: search in whole body text
            if company == "Compañía desconocida":
                body_text = page.evaluate('() => document.body.innerText')
                match = re.search(r'Compañía:\s*([^\n\.]+)', body_text)
                if match:
                    company = match.group(1).strip()
        
        # Sessions from __NEXT_DATA__
        sessions = []
        prices = []
        
        next_data_script = page.query_selector('script#__NEXT_DATA__')
        if next_data_script:
            try:
                data = json.loads(next_data_script.inner_text())
                # Navigate through the JSON structure
                # This structure was identified during research
                page_props = data.get('props', {}).get('pageProps', {})
                sessions_data = page_props.get('sessions', {})
                days = sessions_data.get('days', [])
                
                for day_obj in days:
                    date_info = day_obj.get('day', {})
                    year = date_info.get('year')
                    month = date_info.get('month')
                    day = date_info.get('day')
                    
                    if not (year and month and day):
                        continue
                        
                    date_iso = f"{year}-{month}-{day}"
                        
                    day_sessions = day_obj.get('sessions', [])
                    for s in day_sessions:
                        time_info = s.get('date', {})
                        hour = time_info.get('hour')
                        minutes = time_info.get('minutes')
                        
                        if hour and minutes:
                            time_str = f"{hour}:{minutes}"
                            sessions.append(Session(date=date_iso, time=time_str))
                        
                        # Use bestReducedPrice if available, otherwise bestPrice
                        price = s.get('bestReducedPrice') or s.get('bestPrice')
                        if price is not None:
                            prices.append(float(price))
            except Exception as e:
                print(f"    Error parsing __NEXT_DATA__: {e}")
        
        # Fallback for price range if no sessions found in JSON (unlikely for Atrapalo but good to have)
        price_range = "Consultar web"
        if prices:
            min_p = min(prices)
            max_p = max(prices)
            if min_p == max_p:
                price_range = f"{int(min_p)}€" if min_p.is_integer() else f"{min_p}€"
            else:
                p1 = f"{int(min_p)}€" if min_p.is_integer() else f"{min_p}€"
                p2 = f"{int(max_p)}€" if max_p.is_integer() else f"{max_p}€"
                price_range = f"{p1} - {p2}"

        return Event(
            id=str(uuid.uuid4()),
            title=title,
            company=company,
            venue=Venue("Teatro La Usina", "Madrid"),
            type="Danza",
            price_range=price_range,
            is_free=False,
            image_url=image_url,
            url=url,
            sessions=sessions
        )
    except Exception as e:
        print(f"  Error scraping {url}: {e}")
        return None
    finally:
        page.close()

def scrape_la_usina():
    print("Starting La Usina (Atrapalo) Scraper...")
    events = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use a real browser context
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        listing_url = "https://www.atrapalo.com/entradas/madrid/teatro-y-danza/danza/"
        page = context.new_page()
        print(f"Discovering events from: {listing_url}")
        
        try:
            # Atrapalo might have some anti-bot, so we wait and scroll
            page.goto(listing_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000) # Wait for cards to render
            
            # Scroll to load all events if needed
            # For now, let's just extract what's on the page
            
            # Identify "La Usina" events
            # Structure: .js-event.event contains venue name in .locality
            
            cards = page.query_selector_all('.js-event.event')
            print(f"Found {len(cards)} total event cards.")
            
            urls = []
            for card in cards:
                venue_el = card.query_selector('.locality')
                venue_text = venue_el.inner_text().lower() if venue_el else ""
                
                if "usina" in venue_text:
                    link_el = card.query_selector('.product-name')
                    if link_el:
                        href = link_el.get_attribute('href')
                        if href:
                            if not href.startswith('http'):
                                href = "https://www.atrapalo.com" + href
                            urls.append(href)
            
            # Deduplicate
            urls = list(set(urls))
            print(f"Found {len(urls)} unique events for La Usina.")
            
            for url in urls:
                event = scrape_event_details(context, url)
                if event:
                    events.append(event)
                time.sleep(2) # Be extra nice to Atrapalo
                
        except Exception as e:
            print(f"Error in discovery phase: {e}")
        finally:
            browser.close()
            
    print(f"La Usina finished. Total events: {len(events)}")
    return events

if __name__ == "__main__":
    results = scrape_la_usina()
    for e in results:
        print(f"Event: {e.title} at {e.venue.name} - {len(e.sessions)} sessions, Price: {e.price_range}")
