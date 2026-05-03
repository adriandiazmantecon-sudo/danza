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

def parse_spanish_dates(date_text):
    """
    Parses dates like '29 y 30 de mayo 2026' or '16, 17 y 18 de octubre 2025'
    Returns a list of date strings (YYYY-MM-DD).
    """
    months = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }
    
    date_text = date_text.lower()
    
    # Extract year (4 digits)
    year_match = re.search(r'\b(20\d{2})\b', date_text)
    if not year_match:
        return []
    year = year_match.group(1)
    
    # Find the month
    month_val = None
    for m_name, m_val in months.items():
        if m_name in date_text:
            month_val = m_val
            break
    
    if not month_val:
        return []
    
    # Extract days
    # We look for numbers before the month name
    # e.g. "5 y 6", "16, 17 y 18"
    days_part = date_text.split(m_name)[0]
    days = re.findall(r'\b(\d{1,2})\b', days_part)
    
    result = []
    for d in days:
        day_str = d.zfill(2)
        result.append(f"{year}-{month_val}-{day_str}")
        
    return result

def scrape_event_details(context, url, title, company):
    """Scrapes the event project page for a featured image."""
    print(f"    Scraping project details: {url}")
    page = context.new_page()
    image_url = ""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # The featured image is often in a .post_featured_img or similar
        # In Cuarta Pared, it seems to be in a .wp-post-image or .jgrid-lazy-load
        img_el = page.query_selector('.wp-post-image') or \
                 page.query_selector('.jgrid-lazy-load') or \
                 page.query_selector('.post_item img') or \
                 page.query_selector('.wpb_wrapper img')
                 
        if img_el:
            # Check for data-src first due to lazy loading
            image_url = img_el.get_attribute('data-src') or \
                        img_el.get_attribute('data-lazy-src') or \
                        img_el.get_attribute('src')
            
            # If it's a data: image (placeholder) or a logo, it's not useful
            if not image_url or image_url.startswith('data:') or 'logo' in image_url.lower():
                # Try to find another image in the content area
                content_selectors = ['.post_item', '.wpb_wrapper', '.vc_tta-panel-body']
                for sel in content_selectors:
                    content_el = page.query_selector(sel)
                    if content_el:
                        all_imgs = content_el.query_selector_all('img')
                        for img in all_imgs:
                            src = img.get_attribute('data-src') or img.get_attribute('src')
                            if src and not src.startswith('data:') and 'logo' not in src.lower():
                                image_url = src
                                break
                    if image_url and not image_url.startswith('data:'):
                        break
        
        # Final fallback: any non-logo image on the page
        if not image_url or image_url.startswith('data:'):
            all_imgs = page.query_selector_all('img')
            for img in all_imgs:
                src = img.get_attribute('data-src') or img.get_attribute('src')
                if src and not src.startswith('data:') and 'logo' not in src.lower():
                    image_url = src
                    break
    except Exception as e:
        print(f"    Error scraping project details for {title}: {e}")
    finally:
        page.close()
    return image_url

def scrape_cuarta_pared():
    print("Starting Sala Cuarta Pared (Mover Madrid) Scraper...")
    events = []
    
    url = "https://www.cuartapared.es/movermadrid/"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        try:
            print(f"Navigating to: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)
            
            # Find all panels in the "Programación" section
            panels = page.query_selector_all('.vc_tta-panel')
            print(f"Found {len(panels)} potential event panels.")
            
            for panel in panels:
                try:
                    # Title and Company from h4
                    h4 = panel.query_selector('.vc_tta-panel-body h4')
                    if not h4:
                        continue
                        
                    h4_text = h4.inner_text().strip()
                    # Pattern: "Title – Company" or "Title - Company"
                    # Note: sometimes it uses a long dash or short dash
                    if " – " in h4_text:
                        parts = h4_text.split(" – ", 1)
                    elif " - " in h4_text:
                        parts = h4_text.split(" - ", 1)
                    else:
                        parts = [h4_text, "Compañía desconocida"]
                    
                    title = parts[0].strip()
                    company = parts[1].strip() if len(parts) > 1 else "Compañía desconocida"
                    
                    # URL from a in h4
                    link_el = h4.query_selector('a')
                    project_url = link_el.get_attribute('href') if link_el else url
                    
                    # Date, Time, Price from h5
                    h5 = panel.query_selector('.vc_tta-panel-body h5')
                    if not h5:
                        continue
                    
                    h5_text = h5.inner_text().strip()
                    # FECHAS: 29 y 30 de mayo 2026 | HORARIO: 20h30 | ... | PRECIO: 14€
                    
                    # Extract dates
                    dates_match = re.search(r'FECHAS:\s*([^|]+)', h5_text)
                    dates_text = dates_match.group(1).strip() if dates_match else ""
                    parsed_dates = parse_spanish_dates(dates_text)
                    
                    # Extract time
                    time_match = re.search(r'HORARIO:\s*([^|]+)', h5_text)
                    time_text = time_match.group(1).strip() if time_match else "20:30"
                    # Convert 20h30 to 20:30
                    time_text = time_text.replace('h', ':')
                    if ':' not in time_text and len(time_text) == 2:
                        time_text += ":00"
                    
                    # Extract price
                    price_match = re.search(r'PRECIO:\s*([^|]+)', h5_text)
                    price_range = price_match.group(1).strip() if price_match else "14€"
                    
                    # Get image from project page
                    image_url = ""
                    if project_url != url:
                        image_url = scrape_event_details(context, project_url, title, company)
                    
                    # Create sessions
                    sessions = [Session(date=d, time=time_text) for d in parsed_dates]
                    
                    if title and parsed_dates:
                        events.append(Event(
                            id=str(uuid.uuid4()),
                            title=title,
                            company=company,
                            venue=Venue("Sala Cuarta Pared", "Madrid"),
                            type="Danza",
                            price_range=price_range,
                            is_free=False,
                            image_url=image_url,
                            url=project_url,
                            sessions=sessions
                        ))
                        print(f"  Added event: {title} ({len(sessions)} sessions)")
                
                except Exception as panel_e:
                    print(f"  Error processing panel: {panel_e}")
                    
        except Exception as e:
            print(f"Error in discovery phase: {e}")
        finally:
            browser.close()
            
    print(f"Sala Cuarta Pared finished. Total events: {len(events)}")
    return events

if __name__ == "__main__":
    results = scrape_cuarta_pared()
    for e in results:
        print(f"Event: {e.title} by {e.company} - {len(e.sessions)} sessions, Price: {e.price_range}")
        for s in e.sessions:
            print(f"  Session: {s.date} at {s.time}")
