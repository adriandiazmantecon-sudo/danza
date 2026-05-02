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

async def scrape_getafe_details(page, url):
    """Scrapes a single event page from Getafe's cultural site."""
    print(f"Scraping Getafe event details: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        # Small delay for dynamic content
        await page.wait_for_timeout(1000)
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Title
        title_el = soup.select_one('h1.mec-single-title')
        title = title_el.get_text().strip() if title_el else "Evento de Danza"
        
        # Image
        image_url = ""
        img_el = soup.select_one('.mec-events-event-image img')
        if img_el:
            image_url = img_el.get('src')
        
        # Date & Time
        date_text = ""
        # The date is inside .mec-single-event-date
        date_el = soup.select_one('.mec-single-event-date .mec-start-date-label') or soup.select_one('.mec-single-event-date .mec-events-abbr')
        if date_el:
            date_text = date_el.get_text().strip()
            
        time_text = "20:00" # Default
        time_el = soup.select_one('.mec-single-event-time .mec-events-abbr')
        if time_el:
            time_text = time_el.get_text().strip()
            # If it contains PM/AM, we might need to handle it, but usually it's 24h or simple
            
        # Price
        price_range = "Consultar web"
        # Price is often in .mec-single-event-cost or within the content
        cost_el = soup.select_one('.mec-single-event-cost .mec-cost')
        if cost_el:
            price_range = cost_el.get_text().strip()
        else:
            body_text = soup.get_text()
            # Look for patterns like "8 €", "8€", "12,50 €"
            price_match = re.search(r'(\d+(?:[.,]\d+)?)\s*€', body_text)
            if price_match:
                price_range = f"{price_match.group(1)} €"
            
        # Venue is almost always Federico García Lorca for this list
        venue_name = "Teatro Federico García Lorca"
        venue_el = soup.select_one('.mec-single-venue-name')
        if venue_el:
            venue_name = venue_el.get_text().strip()
            
        # Parse Date
        # Format can be "12 mayo 2026" or "12 May 2026"
        months = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
            'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }
        
        sessions = []
        if date_text:
            m = re.search(r'(\d{1,2})\s+([a-z]+)\s+(\d{4})', date_text.lower())
            if m:
                day = m.group(1).zfill(2)
                month_name = m.group(2)
                month_num = '01'
                for k, v in months.items():
                    if k in month_name:
                        month_num = v
                        break
                year = m.group(3)
                sessions.append(Session(date=f"{year}-{month_num}-{day}", time=time_text))
        
        # Validation: Only keep future events
        today_str = datetime.now().strftime("%Y-%m-%d")
        valid_sessions = [s for s in sessions if s.date >= today_str]
        
        if not valid_sessions and sessions:
            print(f"  Skipping past event: {title} ({sessions[0].date})")
            return None
            
        if not sessions:
            print(f"  Warning: No sessions parsed for {title} (date_text was: '{date_text}')")
            return None

        print(f"  Successfully scraped: {title} - {valid_sessions[0].date if valid_sessions else 'No date'}")
        return Event(
            id=str(uuid.uuid4()),
            title=title,
            company=title, # Simplified as requested
            venue=Venue(venue_name, "Getafe"),
            type="Danza",
            price_range=price_range,
            is_free="gratis" in price_range.lower() or "gratuito" in price_range.lower() or re.search(r'\b0\s*€', price_range),
            image_url=image_url or "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=800&auto=format&fit=crop",
            url=url,
            sessions=valid_sessions
        )
    except Exception as e:
        print(f"  Error scraping Getafe event {url}: {e}")
        return None

async def scrape_getafe():
    """Main function to scrape Getafe dance events."""
    print("Starting Getafe Scraper (Teatro Federico García Lorca)...")
    events = []
    base_url = "https://cultura.getafe.es/teatro-federico-garcia-lorca/"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"Navigating to: {base_url}")
        try:
            await page.goto(base_url, wait_until="networkidle", timeout=60000)
            
            # Load more events if "Ver más" button exists
            while True:
                load_more = await page.query_selector('div.mec-load-more-button')
                if load_more and await load_more.is_visible():
                    print("Clicking 'Ver más'...")
                    await load_more.click()
                    await page.wait_for_timeout(2000) # Wait for AJAX
                else:
                    break
            
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            # Find all event articles
            articles = soup.select('article.mec-event-article')
            print(f"Found {len(articles)} total events in Getafe agenda.")
            
            urls = []
            keywords = ['danza', 'baile', 'ballet']
            
            for article in articles:
                text = article.get_text().lower()
                if any(k in text for k in keywords):
                    link_el = article.select_one('a.mec-color-hover, h3 a')
                    if link_el:
                        href = link_el.get('href')
                        if href:
                            urls.append(href)
            
            urls = list(set(urls))
            print(f"Found {len(urls)} dance-related events in Getafe.")
            
            for url in urls:
                event = await scrape_getafe_details(page, url)
                if event and event.sessions:
                    events.append(event)
                    
        except Exception as e:
            print(f"Error in Getafe discovery phase: {e}")
            
        await browser.close()
        
    print(f"Getafe Scraping finished. Total events found: {len(events)}")
    return events

if __name__ == "__main__":
    res = asyncio.run(scrape_getafe())
    for e in res:
        print(f"Result: {e.title} | Venue: {e.venue.name} | Sessions: {len(e.sessions)}")
