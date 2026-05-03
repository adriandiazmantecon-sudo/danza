from playwright.sync_api import sync_playwright
import uuid
import sys
import os
import re
import time
import json
from datetime import datetime

# Force UTF-8 encoding for Windows consoles
if sys.platform == "win32":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# Ensure the models are reachable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Event, Venue, Session

def scrape_corral_usera():
    print("Starting El Corral de Usera Scraper...", flush=True)
    events = []
    base_url = "https://www.eventim-light.com"
    iframe_url = "https://www.eventim-light.com/es/a/674759731557ff1148d8ca20/iframe/"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )
        page = context.new_page()
        
        try:
            print(f"Navigating to: {iframe_url}", flush=True)
            page.goto(iframe_url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for content
            print("Waiting for event cards...", flush=True)
            page.wait_for_selector('[data-cy="eventCard"]', timeout=30000)
            print("Content loaded successfully.", flush=True)
            
            # 1. Apply Filter
            print("Applying 'Danza' filter...", flush=True)
            filter_btn = page.locator('button:has(.v-icon:text("tune")), .v-chip:has-text("Filter"), button:has-text("Filter")')
            
            if filter_btn.count() > 0:
                filter_btn.first.click()
                page.wait_for_timeout(2000)
                
                # Expand Category
                category_header = page.locator('div.v-list-group:has-text("Category"), div.v-list-group:has-text("Categoría")')
                if category_header.count() > 0:
                    category_header.first.click()
                    page.wait_for_timeout(1000)
                
                # Select 'Danza'
                danza_checkbox = page.locator('div.v-list-item:has-text("Danza")')
                if danza_checkbox.count() > 0:
                    danza_checkbox.first.click()
                    page.wait_for_timeout(1000)
                
                # Apply filter
                apply_btn = page.locator('button:has-text("Apply filter"), button:has-text("Aplicar filtro")')
                if apply_btn.count() > 0:
                    apply_btn.first.click()
                    page.wait_for_timeout(3000)
            
            # 2. Extract Event Cards
            event_cards_locators = page.locator('[data-cy="eventCard"]').all()
            print(f"Found {len(event_cards_locators)} events after filtering.", flush=True)
            
            discovered_events = []
            for card in event_cards_locators:
                try:
                    title = card.locator('[data-cy="card_title"]').inner_text().strip()
                    
                    img_el = card.locator('.v-img img')
                    image_url = img_el.get_attribute('src') if img_el.count() > 0 else ""
                    
                    link_el = card.locator('[data-cy="Card_button"]')
                    relative_link = link_el.get_attribute('href') if link_el.count() > 0 else ""
                    full_link = f"{base_url}{relative_link}" if relative_link.startswith('/') else relative_link
                    
                    if full_link:
                        discovered_events.append({
                            'title': title,
                            'image_url': image_url,
                            'url': full_link
                        })
                except Exception as e:
                    print(f"  Error parsing card: {e}", flush=True)

            # 3. Scrape Details for each event
            for dev in discovered_events:
                print(f"  Scraping details for: {dev['title']}", flush=True)
                detail_page = context.new_page()
                try:
                    detail_page.goto(dev['url'], wait_until="domcontentloaded", timeout=30000)
                    detail_page.wait_for_timeout(3000) # Wait for cards to render
                    
                    session_cards = detail_page.query_selector_all('.v-card.mx-auto')
                    if not session_cards:
                        session_cards = detail_page.query_selector_all('[data-cy="eventCard"]')

                    sessions = []
                    price_range = ""
                    
                    for s_card in session_cards:
                        date_el = s_card.query_selector('.event__date')
                        time_el = s_card.query_selector('.event__time')
                        
                        if date_el and time_el:
                            raw_date = date_el.inner_text().strip()
                            date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', raw_date)
                            if date_match:
                                day, month, year = date_match.groups()
                                formatted_date = f"{year}-{month}-{day}"
                            else:
                                formatted_date = raw_date
                                
                            raw_time = time_el.inner_text().strip()
                            formatted_time = raw_time
                            
                            sessions.append(Session(date=formatted_date, time=formatted_time))
                            
                            if not price_range:
                                price_btn = s_card.query_selector('[data-cy="Card_button"]')
                                if price_btn:
                                    price_text = price_btn.inner_text().strip()
                                    price_range = price_text

                    if sessions:
                        events.append(Event(
                            id=str(uuid.uuid4()),
                            title=dev['title'],
                            company="Varios",
                            venue=Venue("El Corral de Usera", "Madrid"),
                            type="Danza",
                            price_range=price_range or "Ver web",
                            is_free=False,
                            image_url=dev['image_url'],
                            url=dev['url'],
                            sessions=sessions
                        ))
                        print(f"    Added {len(sessions)} sessions.", flush=True)
                    
                except Exception as de:
                    print(f"    Error scraping {dev['url']}: {de}", flush=True)
                finally:
                    detail_page.close()
                    
        except Exception as e:
            print(f"Error in discovery phase: {e}", flush=True)
        finally:
            browser.close()
            
    print(f"El Corral de Usera finished. Total events: {len(events)}", flush=True)
    return events

if __name__ == "__main__":
    results = scrape_corral_usera()
    for e in results:
        print(f"Event: {e.title} - {len(e.sessions)} sessions, Price: {e.price_range}")
        for s in e.sessions:
            print(f"  Session: {s.date} at {s.time}")
