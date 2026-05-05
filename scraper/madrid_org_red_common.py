import asyncio
import re
import uuid
import sys
import os
import unicodedata
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Ensure the models are reachable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
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
    # Match day and month
    match_date = re.search(r'(\d{1,2})\s+de\s+([a-z]+)', date_str)
    # Match time
    match_time = re.search(r'(\d{2}):(\d{2})', date_str)
    
    if match_date:
        day = match_date.group(1).zfill(2)
        month_name = match_date.group(2)
        month = months.get(month_name, '01')
        
        hour = "20"
        minute = "00"
        if match_time:
            hour = match_time.group(1)
            minute = match_time.group(2)
            
        year = datetime.now().year
        # If the month is significantly earlier than current month, it might be next year 
        # (e.g. if today is Dec and event is Jan).
        # But for historical records, we might want to be careful.
        # However, the user said "assume current year if missing".
        
        return f"{year}-{month}-{day}", f"{hour}:{minute}"
    return None, None

async def scrape_event_details(page, url, info, venue_name, municipality):
    """Scrapes a single event page for image and additional info."""
    print(f"Scraping event details: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(500)
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Image
        image_url = ""
        img_el = soup.select_one('.carousel-inner img, .item.active img, img[src*="/fotos/fichas/"]')
        if img_el:
            image_url = img_el.get('src')
        
        if image_url and not image_url.startswith('http'):
            image_url = "https://www.madrid.org/clas_artes/red/" + image_url
            
        if not image_url:
            og_img = soup.find('meta', property='og:image')
            if og_img:
                image_url = og_img.get('content', '')

        # Info from the list (discovery phase)
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
            title = normalize_text(lines[0])
            if any(k in lines[1].lower() for k in ["danza", "teatro", "música", "familiar", "circo"]):
                category = normalize_text(lines[1])
                company = "" # Might be merged with title or unknown
            else:
                company = normalize_text(lines[1])
            date_time_str = lines[2]

        date_iso, time_iso = parse_spanish_date(date_time_str)
        
        if not date_iso:
            # Try to find date in the page if not in the list text
            # Often it's in a <p> with a calendar icon or specific text
            date_p = soup.find(string=re.compile(r'\d{1,2}\s+de\s+[a-z]+', re.IGNORECASE))
            if date_p:
                date_iso, time_iso = parse_spanish_date(date_p)

        if not date_iso:
            print(f"  Warning: No date found for {url}")
            return None

        sessions = [Session(date=date_iso, time=time_iso)]

        # Category check
        is_dance = any(k in (category + title + (info['text'])).lower() for k in ["danza", "baile", "ballet", "flamenco"])
        if not is_dance:
            return None

        return Event(
            id=str(uuid.uuid4()),
            title=title or "Sin título",
            company=company or "Compañía desconocida",
            venue=Venue(venue_name, municipality),
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

async def scrape_red_municipios(url, venue_name, municipality, venue_header_text=None):
    print(f"Starting Scraper for {venue_name} ({municipality})...")
    events = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"Discovering events from: {url}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(1000)
            
            # Extract links and info
            # If venue_header_text is provided, we only take links under that header
            events_info = await page.evaluate('''(headerText) => {
                const links = Array.from(document.querySelectorAll('a'));
                let filteredLinks = links;
                
                if (headerText) {
                    const headers = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, strong, p'));
                    const targetHeader = headers.find(h => h.innerText.toUpperCase().includes(headerText.toUpperCase()));
                    if (targetHeader) {
                        // Find next headers to define a range
                        const allElements = Array.from(document.querySelectorAll('*'));
                        const startIndex = allElements.indexOf(targetHeader);
                        
                        // Find next sibling header or significant separator
                        let nextHeader = null;
                        for (let i = startIndex + 1; i < allElements.length; i++) {
                            const el = allElements[i];
                            if (['H1', 'H2', 'H3', 'H4', 'H5', 'H6'].includes(el.tagName) || 
                                (el.tagName === 'P' && el.innerText.toUpperCase() === el.innerText && el.innerText.length > 5)) {
                                // Potential next venue header
                                if (!el.innerText.includes(headerText)) {
                                    nextHeader = el;
                                    break;
                                }
                            }
                        }
                        
                        const endIndex = nextHeader ? allElements.indexOf(nextHeader) : allElements.length;
                        const rangeElements = allElements.slice(startIndex, endIndex);
                        filteredLinks = rangeElements.filter(el => el.tagName === 'A');
                    }
                }

                return filteredLinks
                    .map(a => ({
                        href: a.href,
                        text: a.innerText || ""
                    }))
                    .filter(a => {
                        const href = a.href.toLowerCase();
                        const isEvent = href.includes('.html') && 
                                        !href.includes('index.html') && 
                                        !href.includes('municipios.html') &&
                                        !href.includes('funcionamiento.html') &&
                                        !href.includes('teatro.html') &&
                                        !href.includes('danza.html') &&
                                        !href.includes('musica.html') &&
                                        !href.includes('familiar.html') &&
                                        !href.includes('circo.html') &&
                                        !href.includes('descargas.html') &&
                                        !href.includes(window.location.pathname.split('/').pop());
                        
                        if (!isEvent) return false;
                        
                        // Filter for Danza keywords
                        const text = a.text.toLowerCase();
                        return text.includes('danza') || text.includes('baile') || text.includes('ballet') || text.includes('flamenco');
                    });
            }''', venue_header_text)
            
            print(f"Found {len(events_info)} candidate dance events.")
            
            # Deduplicate by URL
            unique_links = {}
            for info in events_info:
                unique_links[info['href']] = info
            
            for href, info in unique_links.items():
                event = await scrape_event_details(page, href, info, venue_name, municipality)
                if event:
                    events.append(event)
                    
        except Exception as e:
            print(f"Error in discovery phase for {venue_name}: {e}")
            
        await browser.close()
        
    print(f"Scraping finished for {venue_name}. Total events: {len(events)}")
    return events
