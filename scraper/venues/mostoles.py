import asyncio
import re
import uuid
import sys
import os
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Ensure the models are reachable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Event, Venue, Session

def clean_text(text):
    if not text: return ""
    text = text.replace('\xa0', ' ')
    text = " ".join(text.split())
    return text.strip()

def parse_mostoles_sessions(date_text, time_text):
    """
    Parses dates like 'MAYO 30 Y 31, 20:00' or 'JUNIO 18, 19:00'
    Returns a list of Session objects.
    """
    sessions = []
    try:
        # Month mapping
        months_map = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
        }
        
        # Extract month
        month_match = re.search(r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)', date_text.lower())
        if not month_match:
            return []
        
        month_num = months_map[month_match.group(1)]
        year = "2026" # Default to 2026 as per user context
        
        # Extract days
        # Handles "30 Y 31" or just "18"
        # We look for numbers but ignore them if they are part of a time (HH:MM)
        # or if they are 00 (which sometimes happens in parsing errors)
        raw_days = re.findall(r'\b(\d{1,2})\b', date_text)
        days = []
        for d in raw_days:
            # Simple check: if it's 0 or 00, it's not a valid day
            if d in ['0', '00']:
                continue
            # If the number is followed by :XX, it's probably a time, not a day
            if f"{d}:" in date_text:
                continue
            days.append(d)
        
        # Extract time from time_text or end of date_text
        final_time = "20:00"
        time_match = re.search(r'(\d{1,2}:\d{2})', f"{date_text} {time_text}")
        if time_match:
            final_time = time_match.group(1)
            
        for day in days:
            date_str = f"{year}-{month_num}-{day.zfill(2)}"
            sessions.append(Session(date=date_str, time=final_time))
            
    except Exception as e:
        print(f"  Error parsing sessions from '{date_text}': {e}")
        
    return sessions

async def scrape_mostoles_details(page, url):
    """Scrapes a single event page from Teatro del Bosque."""
    print(f"Scraping Móstoles event details: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(1500)
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Title
        title_el = soup.select_one('h1.elementor-heading-title')
        title = title_el.get_text().strip() if title_el else "Evento de Danza"
        
        # Image
        image_url = ""
        img_el = soup.select_one('.elementor-widget-image img')
        if img_el:
            image_url = img_el.get('src')
        else:
            # Try background-image in header
            wrap_el = soup.select_one('.image-wrap')
            if wrap_el and wrap_el.get('style'):
                m = re.search(r"url\(['\"]?(.+?)['\"]?\)", wrap_el.get('style'))
                if m:
                    image_url = m.group(1)
            
        # Date & Time from meta
        # The site uses specific elementor-pbmeta or containers
        date_text = ""
        meta_el = soup.select_one('.elementor-widget-elementor-pbmeta')
        if meta_el:
            date_text = meta_el.get_text().strip()
        
        # Price - Look for container with "PRECIOS"
        price_range = "Consultar web"
        all_meta_containers = soup.select('.meta-container')
        for container in all_meta_containers:
            title_part = container.select_one('.title')
            if title_part and "PRECIOS" in title_part.get_text().upper():
                meta_part = container.select_one('.meta')
                if meta_part:
                    price_range = meta_part.get_text().strip()
                    break
        
        # Parse Sessions
        sessions = parse_mostoles_sessions(date_text, "")
        
        # Validation: Only keep future events
        today_str = datetime.now().strftime("%Y-%m-%d")
        valid_sessions = [s for s in sessions if s.date >= today_str]
        
        if not valid_sessions and sessions:
            print(f"  Skipping past event: {title} ({sessions[0].date})")
            return None
            
        if not sessions:
            print(f"  Warning: No sessions parsed for {title} (date_text was: '{date_text}')")
            return None

        print(f"  Successfully scraped: {title} - {len(valid_sessions)} sessions")
        return Event(
            id=str(uuid.uuid4()),
            title=title,
            company=title,
            venue=Venue("Teatro del Bosque", "Móstoles"),
            type="Danza",
            price_range=price_range,
            is_free="gratis" in price_range.lower() or "gratuito" in price_range.lower() or re.search(r'\b0\s*€', price_range),
            image_url=image_url or "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=800&auto=format&fit=crop",
            url=url,
            sessions=valid_sessions
        )
    except Exception as e:
        print(f"  Error scraping Móstoles event {url}: {e}")
        return None

async def scrape_mostoles():
    """Main function to scrape Móstoles dance events."""
    print("Starting Móstoles Scraper (Teatro del Bosque)...")
    events = []
    base_url = "https://escenamostoles.com/teatro-del-bosque/"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"Navigating to: {base_url}")
        try:
            await page.goto(base_url, wait_until="networkidle", timeout=60000)
            
            # Pagination: Click "VER MÁS" until gone
            # Selector from research: .load_more button
            for _ in range(5): # Limit clicks to avoid infinite loops
                load_more = await page.query_selector('.load_more button')
                if load_more and await load_more.is_visible():
                    print("Clicking 'VER MÁS'...")
                    await load_more.click()
                    await page.wait_for_timeout(2500)
                else:
                    break
            
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            # Find all event cards
            articles = soup.select('div.article')
            print(f"Found {len(articles)} total events in Móstoles.")
            
            urls = []
            for article in articles:
                badge = article.select_one('.etiqueta p a')
                if badge and "DANZA" in badge.get_text().upper():
                    link_el = article.select_one('h2.title a') or article.select_one('a')
                    if link_el:
                        href = link_el.get('href')
                        if href:
                            urls.append(href)
            
            urls = list(set(urls))
            print(f"Found {len(urls)} dance-related events in Móstoles.")
            
            for url in urls:
                event = await scrape_mostoles_details(page, url)
                if event:
                    events.append(event)
                    
        except Exception as e:
            print(f"Error in Móstoles discovery phase: {e}")
            
        await browser.close()
        
    print(f"Móstoles Scraping finished. Total events found: {len(events)}")
    return events

if __name__ == "__main__":
    res = asyncio.run(scrape_mostoles())
    for e in res:
        print(f"Result: {e.title} | Venue: {e.venue.name} | Sessions: {len(e.sessions)}")
