import asyncio
import re
import uuid
import sys
import os
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import unicodedata

# Force UTF-8 output for Windows
if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'UTF-8':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except Exception:
        pass 

# Ensure the models are reachable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Event, Venue, Session

def normalize_text(text):
    if not text: return ""
    text = text.replace('\xa0', ' ')
    text = unicodedata.normalize('NFC', text)
    text = " ".join(text.split())
    text = text.strip('• \t\n\r\xa0*!-–—,.')
    return text

def parse_spanish_date(date_str):
    """
    Parses '7 de marzo - 19:00 h.' to (date, time)
    """
    months = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }
    
    date_str = date_str.lower()
    match = re.search(r'(\d{1,2})\s+de\s+([a-z]+).*?(\d{2}):(\d{2})', date_str)
    if match:
        day = match.group(1).zfill(2)
        month_name = match.group(2)
        hour = match.group(3)
        minute = match.group(4)
        
        month = months.get(month_name, '01')
        year = datetime.now().year
        # If the month is already passed in current year, assume next year
        if int(month) < datetime.now().month:
            year += 1
            
        return f"{year}-{month}-{day}", f"{hour}:{minute}"
    return None, None

async def scrape_event_details(page, url, info):
    """Scrapes a single event page for image and additional info."""
    print(f"Scraping event details: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(1000)
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Image
        image_url = ""
        # Common image location in these pages
        img_el = soup.select_one('.carousel-inner img, .item.active img, img[src*="/fotos/fichas/"]')
        if img_el:
            image_url = img_el.get('src')
        
        if image_url and not image_url.startswith('http'):
            image_url = "https://www.madrid.org/clas_artes/red/" + image_url
            
        # Fallback to OG image
        if not image_url:
            og_img = soup.find('meta', property='og:image')
            if og_img:
                image_url = og_img.get('content', '')

        # Extraction from the info object passed from the list
        lines = [l.strip() for l in info['text'].split('\n') if l.strip()]
        
        title = ""
        company = ""
        category = ""
        date_time_str = ""
        
        if len(lines) >= 4:
            title = normalize_text(lines[0])
            company = normalize_text(lines[1])
            category = normalize_text(lines[2])
            date_time_str = lines[3]
        elif len(lines) == 3:
            # Maybe missing company or category
            title = normalize_text(lines[0])
            if "Danza" in lines[1] or "Teatro" in lines[1]:
                category = normalize_text(lines[1])
                company = title
            else:
                company = normalize_text(lines[1])
            date_time_str = lines[2]

        date_iso, time_iso = parse_spanish_date(date_time_str)
        
        if not date_iso:
            print(f"  Warning: No date found for {url}")
            return None

        sessions = [Session(date=date_iso, time=time_iso)]

        return Event(
            id=str(uuid.uuid4()),
            title=title or "Sin título",
            company=company or title or "Compañía desconocida",
            venue=Venue("Sala Multifuncional de Ciempozuelos", "Ciempozuelos"),
            type="Danza",
            price_range="Consultar web",
            is_free=False,
            image_url=image_url or "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=800&auto=format&fit=crop",
            url=url,
            sessions=sessions
        )
    except Exception as e:
        print(f"  Error scraping event details {url}: {e}")
        return None

async def scrape_ciempozuelos():
    print("Starting Sala Multifuncional de Ciempozuelos Scraper...")
    events = []
    main_url = "https://www.madrid.org/clas_artes/red/ciempozuelos.html"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"Discovering events from: {main_url}")
        try:
            await page.goto(main_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(2000)
            
            # Extract links and info using the logic discovered in browser
            events_info = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a'))
                    .map(a => ({
                        href: a.href,
                        text: a.innerText || ""
                    }))
                    .filter(a => {
                        const href = a.href.toLowerCase();
                        const isEvent = href.includes('.html') && 
                                        !href.includes('index.html') && 
                                        !href.includes('ciempozuelos.html') &&
                                        !href.includes('municipios.html') &&
                                        !href.includes('funcionamiento.html') &&
                                        !href.includes('teatro.html') &&
                                        !href.includes('danza.html') &&
                                        !href.includes('musica.html') &&
                                        !href.includes('familiar.html') &&
                                        !href.includes('circo.html') &&
                                        !href.includes('descargas.html');
                        
                        if (!isEvent) return false;
                        
                        // Filter for Danza, baile, ballet
                        const text = a.text.toLowerCase();
                        return text.includes('danza') || text.includes('baile') || text.includes('ballet');
                    });
            }''')
            
            print(f"Found {len(events_info)} candidate dance events.")
            
            for info in events_info:
                event = await scrape_event_details(page, info['href'], info)
                if event:
                    events.append(event)
                    
        except Exception as e:
            print(f"Error in discovery phase: {e}")
            
        await browser.close()
        
    print(f"Ciempozuelos Scraping finished. Total events: {len(events)}")
    return events

if __name__ == "__main__":
    res = asyncio.run(scrape_ciempozuelos())
    for e in res:
        print(f"Result: {e.title} | Company: {e.company} | Sessions: {len(e.sessions)} | Date: {e.sessions[0].date} {e.sessions[0].time}")
