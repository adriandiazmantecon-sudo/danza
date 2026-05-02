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

async def scrape_majadahonda_details(page, url):
    """Scrapes a single event page from Majadahonda's cultural site."""
    print(f"Scraping Majadahonda event details: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(1000)
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Identify main content area
        content_area = soup.select_one('.portlet-body, #main-content, article')
        body_text = content_area.get_text(separator=" ") if content_area else soup.get_text(separator=" ")
        
        # Title extraction
        title_el = soup.select_one('span.title.h3, h1.title, .portlet-body h3')
        if not title_el:
            title_el = soup.select_one('h1')
            
        title_text = title_el.get_text().strip() if title_el else "Evento de Danza"
        title = re.sub(r'^(?:Danza|Baile|Espect\u00e1culo|M\u00fasica y Danza|M\u00fasica):\s*', '', title_text, flags=re.IGNORECASE)
        title = title.strip('"\' ')
        
        # Company name
        company = ""
        company_match = re.search(r'(?:Compa\u00f1\u00eda|C\u00eda\.?|Cia\.?):\s*(.*?)(?:\.|\n|$)', body_text, re.IGNORECASE)
        if company_match:
            company = clean_text(company_match.group(1))
        
        # Price
        price_range = "Consultar web"
        price_match = re.search(r'(?:Localidades|Precio|Entrada):\s*(.*?)(?:\.|\n|$)', body_text, re.IGNORECASE)
        if price_match:
            price_range = clean_text(price_match.group(1))
            if len(price_range) > 60: price_range = price_range[:57] + "..."

        # Image
        image_url = ""
        img_el = soup.select_one('.portlet-body img[src*="/image/"], .portlet-body img[src*="/documents/"]')
        if img_el:
            image_url = img_el.get('src')
        if image_url and not image_url.startswith('http'):
            image_url = "https://cultura.majadahonda.org" + image_url
            
        # Sessions
        sessions = []
        months = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
        }
        
        # Look for time
        time_match = re.search(r'Hora:\s*(\d{2}):(\d{2})', body_text, re.IGNORECASE)
        hour, minute = (time_match.group(1), time_match.group(2)) if time_match else ("20", "00")
        
        # NEW: Extract dates from sidebar (more reliable)
        sidebar_dates = soup.select('.calendar.detail-view .start-date, .calendar.detail-view .start')
        for sd in sidebar_dates:
            dt_text = sd.get_text().lower()
            # Match "09 mayo 2026" or "9 de mayo de 2026"
            m = re.search(r'(\d{1,2})(?:\s+de)?\s+([a-z]+)(?:\s+de)?\s+(\d{4})', dt_text)
            if m:
                day = m.group(1).zfill(2)
                month = months.get(m.group(2), '01')
                year = m.group(3)
                sessions.append(Session(date=f"{year}-{month}-{day}", time=f"{hour}:{minute}"))
        
        # Fallback to general body text search if sidebar failed
        if not sessions:
            # Format 1: 16 de mayo de 2026
            date_matches = re.finditer(r'(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})', body_text.lower())
            for m in date_matches:
                day = m.group(1).zfill(2)
                month = months.get(m.group(2), '01')
                year = m.group(3)
                sessions.append(Session(date=f"{year}-{month}-{day}", time=f"{hour}:{minute}"))
                
        if not sessions:
            # Format 2: abril 26 (monthly agendas - be careful)
            for month_name, month_num in months.items():
                pattern = rf'{month_name}\s+(\d{1,2})'
                m = re.search(pattern, body_text.lower())
                if m:
                    # Only accept if it's not clearly a PDF agenda link or if nothing else is found
                    if "agenda_" not in body_text.lower()[max(0, m.start()-10):m.end()]:
                        day = m.group(1).zfill(2)
                        sessions.append(Session(date=f"2026-{month_num}-{day}", time=f"{hour}:{minute}"))
                        break

        # Validation: Only keep future events
        today_str = datetime.now().strftime("%Y-%m-%d") # Use current actual date for better filtering
        valid_sessions = [s for s in sessions if s.date >= today_str]
        
        if not valid_sessions:
            all_dates = [s.date for s in sessions]
            print(f"  Skipping event with no future sessions: {title} (Found dates: {all_dates})")
            return None

        return Event(
            id=str(uuid.uuid4()),
            title=title,
            company=company or title,
            venue=Venue("Casa de la Cultura Carmen Conde", "Majadahonda"),
            type="Danza",
            price_range=price_range,
            is_free="gratis" in price_range.lower() or "gratuito" in price_range.lower(),
            image_url=image_url or "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=800&auto=format&fit=crop",
            url=url,
            sessions=valid_sessions
        )
    except Exception as e:
        print(f"  Error scraping Majadahonda event {url}: {e}")
        return None


async def scrape_majadahonda():
    """Main function to scrape Majadahonda dance events."""
    print("Starting Majadahonda Scraper...")
    events = []
    base_url = "https://cultura.majadahonda.org/espectaculos-culturales"
    # Use robust URL with full parameters and delta=100 to see all events
    list_url = f"{base_url}?p_p_id=CalendarSuite_INSTANCE_STa3SHI1sEeH&p_p_lifecycle=0&p_r_p_calendarPath=%2Fhtml%2Fsuite%2Fdisplays%2Flist.jsp&_CalendarSuite_INSTANCE_STa3SHI1sEeH_delta=100"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"Discovering events from: {list_url}")
        try:
            await page.goto(list_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)
            
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            # Find all event links in the list
            candidate_links = soup.select('a.lfr-card-title-text, .lfr-card-title a, .lfr-card-content a')
            
            urls = []
            for a in candidate_links:
                href = a.get('href')
                text = a.get_text().strip()
                # Filter for dance/baile in title
                if href and ('danza' in text.lower() or 'baile' in text.lower() or 'ballet' in text.lower()):
                    if not href.startswith('http'):
                        href = "https://cultura.majadahonda.org" + href
                    urls.append(href)
            
            urls = list(set(urls))
            print(f"Found {len(urls)} dance-related event URLs in Majadahonda.")
            
            for url in urls:
                event = await scrape_majadahonda_details(page, url)
                if event and event.sessions:
                    events.append(event)
                    
        except Exception as e:
            print(f"Error in Majadahonda discovery phase: {e}")
            
        await browser.close()
        
    print(f"Majadahonda Scraping finished. Total events found: {len(events)}")
    return events

if __name__ == "__main__":
    res = asyncio.run(scrape_majadahonda())
    for e in res:
        print(f"Result: {e.title} | Company: {e.company} | Sessions: {len(e.sessions)}")
