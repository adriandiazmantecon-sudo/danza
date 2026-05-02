import asyncio
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import uuid

from models import Event, Venue, Session

months = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}

def parse_schedule(time_str):
    time_str = time_str.lower()
    days_map = {
        'lunes': 0, 'martes': 1, 'miercoles': 2, 'miércoles': 2,
        'jueves': 3, 'viernes': 4, 'sabado': 5, 'sábado': 5, 'domingo': 6
    }
    
    # Extract chunks that end with a time (e.g. "Jueves y viernes: 20:00 h.")
    chunks = list(re.finditer(r'(.*?)(?P<time>\d{1,2}(?::\d{2})?\s*[h])', time_str))
    
    parsed_rules = []
    if not chunks:
        # Default time if no specific schedule is found
        parsed_rules.append({'days': set(), 'time': '20:00'})
        return parsed_rules

    last_end = 0
    for m in chunks:
        chunk_text = time_str[last_end:m.end()].strip()
        last_end = m.end()
        
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*h', m.group('time'))
        if time_match:
            h = int(time_match.group(1))
            min_match = time_match.group(2)
            mins = int(min_match) if min_match else 0
            t_fmt = f"{h:02d}:{mins:02d}"
        else:
            t_fmt = "20:00"
            
        active_days = set()
        # Look for ranges like "Lunes a Viernes"
        range_match = re.search(r'(lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)\s+a\s+(lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)', chunk_text)
        if range_match:
            d1 = days_map[range_match.group(1)]
            d2 = days_map[range_match.group(2)]
            for d in range(d1, d2 + 1):
                active_days.add(d)
                
        # Look for individual days like "Sábados y Domingos"
        for d_str, d_int in days_map.items():
            if re.search(r'\b' + d_str + r'\b', chunk_text):
                active_days.add(d_int)
                
        parsed_rules.append({'days': active_days, 'time': t_fmt})
        
    return parsed_rules

def parse_dates(date_str, time_str):
    date_str = date_str.lower().strip()
    # Remove "del" prefix if present
    if date_str.startswith("del "):
        date_str = date_str[4:].strip()
        
    time_str = time_str.lower().strip() if time_str else ""
    
    rules = parse_schedule(time_str)
    
    def get_time_for_day(day_index):
        for r in rules:
            if day_index in r['days']:
                return r['time']
        for r in rules:
            if not r['days']:
                return r['time']
        return None

    sessions = []
    
    # Range format: "7 al 31 de mayo de 2026"
    m_range = re.match(r'^(\d+)\s*(?:al|a|-)\s*(\d+)\s*de\s*([a-z]+)\s*de\s*(\d{4})$', date_str)
    if m_range:
        start_d = int(m_range.group(1))
        end_d = int(m_range.group(2))
        month = months.get(m_range.group(3))
        year = int(m_range.group(4))
        
        if month:
            start_date = datetime(year, month, start_d)
            end_date = datetime(year, month, end_d)
            
            curr = start_date
            while curr <= end_date:
                t = get_time_for_day(curr.weekday())
                if t is not None:
                    sessions.append(Session(date=curr.strftime("%Y-%m-%d"), time=t))
                curr += timedelta(days=1)
            return sessions

    # Range with different months: "30 de mayo al 2 de junio de 2026"
    m_range2 = re.match(r'^(\d+)\s*de\s*([a-z]+)\s*(?:al|a|-)\s*(\d+)\s*de\s*([a-z]+)\s*de\s*(\d{4})$', date_str)
    if m_range2:
        sd, sm, ed, em, y = m_range2.groups()
        if sm in months and em in months:
            start_date = datetime(int(y), months[sm], int(sd))
            end_date = datetime(int(y), months[em], int(ed))
            curr = start_date
            while curr <= end_date:
                t = get_time_for_day(curr.weekday())
                if t is not None:
                    sessions.append(Session(date=curr.strftime("%Y-%m-%d"), time=t))
                curr += timedelta(days=1)
            return sessions
    
    # Single date: "8 de mayo de 2026"
    m_single = re.match(r'^(\d+)\s*de\s*([a-z]+)\s*de\s*(\d{4})$', date_str)
    if m_single:
        d, m, y = m_single.groups()
        if m in months:
            date1 = datetime(int(y), months[m], int(d))
            t1 = get_time_for_day(date1.weekday()) or "20:00"
            sessions.append(Session(date=date1.strftime("%Y-%m-%d"), time=t1))
            return sessions

    return sessions

async def scrape_teatro_gran_via():
    events = []
    base_url = "https://gruposmedia.com"
    listing_url = f"{base_url}/danza/"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        print(f"Scraping Teatro Gran Via catalog: {listing_url}")
        await page.goto(listing_url)
        await page.wait_for_timeout(3000)
        
        # Smedia uses Essential Grid. We need to find the links.
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Selector identified: a.eg-invisiblebutton
        link_nodes = soup.select('a.eg-invisiblebutton')
        links = []
        for a in link_nodes:
            href = a.get('href', '')
            if href and href not in links:
                links.append(href)
        
        print(f"Found {len(links)} candidate links.")
        
        for link in links:
            print(f"Checking event: {link}")
            try:
                await page.goto(link)
                await page.wait_for_timeout(2000)
                event_html = await page.content()
                esoup = BeautifulSoup(event_html, "html.parser")
                
                # Check if it's Teatro Gran Via
                # Selector: .elementor-icon-list-item:has(a[href="#fichateatro"]) .elementor-icon-list-text
                # Since BeautifulSoup doesn't support :has(), we search manually
                venue_text = ""
                venue_items = esoup.select('.elementor-icon-list-item')
                for item in venue_items:
                    if item.find('a', href="#fichateatro") or item.find(class_='fa-map-marker-alt'):
                        venue_text = item.get_text(strip=True)
                        break
                
                if not venue_text or "GRAN VÍA" not in venue_text.upper():
                    print(f"Skipping event at another venue: {venue_text}")
                    continue
                
                # Title
                title_node = esoup.select_one('h1.elementor-heading-title')
                title_text = title_node.get_text(strip=True) if title_node else "Unknown Title"
                
                # Company (Try to extract from title "Artist - Show" or from description)
                company_text = title_text
                if " - " in title_text:
                    company_text = title_text.split(" - ")[0]
                elif " – " in title_text:
                    company_text = title_text.split(" – ")[0]
                
                # Image extraction - more robust
                img_url = ""
                
                # 1. Try og:image meta tag (usually very reliable and often allows hotlinking better than thumbnails)
                og_image = esoup.find('meta', property='og:image')
                if og_image and og_image.get('content'):
                    img_url = og_image['content']
                    print(f"Found og:image: {img_url}")

                # 2. Try to find a "cartel" (poster) link in "Descargas y enlaces" or main content
                if not img_url or "elementor/thumbs" in img_url:
                    cartel_link = esoup.find('a', href=re.compile(r'cartel.*\.jpg|png', re.I))
                    if cartel_link:
                        potential_url = cartel_link.get('href')
                        if potential_url:
                            if potential_url.startswith('/'):
                                potential_url = base_url + potential_url
                            img_url = potential_url
                            print(f"Found cartel link: {img_url}")

                # 3. Fallback to main images but avoid elementor thumbnails if possible
                if not img_url or "elementor/thumbs" in img_url:
                    main_node = esoup.select_one('main')
                    if main_node:
                        img_nodes = main_node.select('img')
                        for img in img_nodes:
                            src = img.get('src', '')
                            alt = img.get('alt', '').lower()
                            if src and "logo" not in src.lower() and "cyber-monday" not in src.lower() and "elementor/thumbs" not in src:
                                # If it's a poster (usually contains title or is vertical)
                                if title_text.lower() in alt or not img_url:
                                    img_url = src
                                    if title_text.lower() in alt:
                                        break
                
                # 4. Final fallback to any image if still empty
                if not img_url:
                    for img in esoup.select('img'):
                        src = img.get('src', '')
                        if src and "logo" not in src.lower() and "cyber-monday" not in src.lower() and "elementor/thumbs" not in src:
                            img_url = src
                            break

                # Dates
                date_text = ""
                venue_items = esoup.select('.elementor-icon-list-item')
                for item in venue_items:
                    if item.find(class_='fa-calendar-alt'):
                        date_text = item.get_text(strip=True)
                        break
                
                # Schedule
                schedule_text = ""
                for item in venue_items:
                    if item.find(class_='fa-clock'):
                        schedule_text = item.get_text(strip=True)
                        break
                
                sessions = parse_dates(date_text, schedule_text)
                
                # Filter past sessions
                now = datetime.now()
                sessions = [s for s in sessions if datetime.strptime(s.date, "%Y-%m-%d") >= now - timedelta(days=1)]
                
                if not sessions:
                    print(f"No future sessions found for {title_text}, skipping.")
                    continue
                
                # Price
                price_text = ""
                # Try specific text search first
                page_text = esoup.get_text()
                price_match = re.search(r'(?:Mejor\s+)?Precio\s*(?::\s*)?(\d+€)', page_text)
                if price_match:
                    price_text = price_match.group(0)
                else:
                    for item in venue_items:
                        text = item.get_text(strip=True)
                        if item.find(class_='fa-euro-sign') or "€" in text or "Precio" in text:
                            price_text = text
                            break
                
                event = Event(
                    id=str(uuid.uuid4()),
                    title=title_text,
                    company=company_text,
                    venue=Venue(name="Teatro Gran Vía", municipality="Madrid"),
                    type="Danza",
                    price_range=price_text,
                    is_free="gratis" in price_text.lower(),
                    image_url=img_url,
                    url=link,
                    sessions=sessions
                )
                events.append(event)
                print(f"Added event: {title_text}")
            except Exception as e:
                print(f"Error parsing event {link}: {e}")
                
        await browser.close()
        return events

if __name__ == "__main__":
    evs = asyncio.run(scrape_teatro_gran_via())
    for e in evs:
        print(f"{e.title}: {len(e.sessions)} sessions, Price: {e.price_range}")
