import asyncio
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import uuid
import sys
import os

# Ensure the models are reachable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    
    chunks = list(re.finditer(r'(.*?)(?P<time>\d{1,2}(?::\d{2})?\s*[h])', time_str))
    
    parsed_rules = []
    if not chunks:
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
        range_match = re.search(r'(lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)\s+a\s+(lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)', chunk_text)
        if range_match:
            d1 = days_map[range_match.group(1)]
            d2 = days_map[range_match.group(2)]
            for d in range(d1, d2 + 1):
                active_days.add(d)
                
        for d_str, d_int in days_map.items():
            if re.search(r'\b' + d_str + r'\b', chunk_text):
                active_days.add(d_int)
                
        parsed_rules.append({'days': active_days, 'time': t_fmt})
        
    return parsed_rules

def parse_dates(date_str, time_str):
    date_str = date_str.lower().strip()
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
    
    # Range format: "7 al 9 de mayo de 2026"
    m_range = re.match(r'^(\d+)\s*(?:al|a|-)\s*(\d+)\s*de\s*([a-z]+)\s*de\s*(\d{4})$', date_str)
    if m_range:
        start_d = int(m_range.group(1))
        end_d = int(m_range.group(2))
        month = months.get(m_range.group(3))
        year = int(m_range.group(4))
        
        start_date = datetime(year, month, start_d)
        end_date = datetime(year, month, end_d)
        
        curr = start_date
        while curr <= end_date:
            t = get_time_for_day(curr.weekday())
            if t is not None:
                sessions.append(Session(date=curr.strftime("%Y-%m-%d"), time=t))
            curr += timedelta(days=1)
        return sessions

    # Range with diff months: "30 de mayo al 2 de junio de 2026"
    m_range2 = re.match(r'^(\d+)\s*de\s*([a-z]+)\s*(?:al|a|-)\s*(\d+)\s*de\s*([a-z]+)\s*de\s*(\d{4})$', date_str)
    if m_range2:
        sd, sm, ed, em, y = m_range2.groups()
        start_date = datetime(int(y), months[sm], int(sd))
        end_date = datetime(int(y), months[em], int(ed))
        curr = start_date
        while curr <= end_date:
            t = get_time_for_day(curr.weekday())
            if t is not None:
                sessions.append(Session(date=curr.strftime("%Y-%m-%d"), time=t))
            curr += timedelta(days=1)
        return sessions
    
    # Specific multiple dates: "26 y 27 de junio de 2026"
    m_y = re.match(r'^(\d+)\s*y\s*(\d+)\s*de\s*([a-z]+)\s*de\s*(\d{4})$', date_str)
    if m_y:
        d1, d2, m, y = m_y.groups()
        date1 = datetime(int(y), months[m], int(d1))
        date2 = datetime(int(y), months[m], int(d2))
        
        t1 = get_time_for_day(date1.weekday()) or "20:00"
        t2 = get_time_for_day(date2.weekday()) or "20:00"
        
        sessions.append(Session(date=date1.strftime("%Y-%m-%d"), time=t1))
        sessions.append(Session(date=date2.strftime("%Y-%m-%d"), time=t2))
        return sessions

    # Single date: "8 de mayo de 2026"
    m_single = re.match(r'^(\d+)\s*de\s*([a-z]+)\s*de\s*(\d{4})$', date_str)
    if m_single:
        d, m, y = m_single.groups()
        date1 = datetime(int(y), months[m], int(d))
        t1 = get_time_for_day(date1.weekday()) or "20:00"
        sessions.append(Session(date=date1.strftime("%Y-%m-%d"), time=t1))
        return sessions

    return sessions

async def scrape_matadero():
    events = []
    base_url = "https://www.centrodanzamatadero.es"
    prog_url = f"{base_url}/programacion"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        # Create context with longer default timeout
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        # Set a long timeout
        page.set_default_timeout(120000)
        
        print(f"Scraping Matadero catalog: {prog_url}")
        try:
            await page.goto(prog_url, wait_until="domcontentloaded", timeout=120000)
            await page.wait_for_timeout(5000)
            
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            links = set()
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/actividades/' in href or '/en/activities/' in href:
                    # Convert English URLs to Spanish to ensure consistent parsing
                    if '/en/activities/' in href:
                        href = href.replace('/en/activities/', '/actividades/')
                    
                    if not href.startswith('http'):
                        href = base_url + href
                    
                    # Deduplicate by ensuring we only take the base activity URL
                    # (remove query params if any)
                    href = href.split('?')[0]
                    links.add(href)
            
            print(f"Found {len(links)} links to process.")
            
            for link in links:
                print(f"Scraping Matadero event: {link}")
                try:
                    # Set a dedicated timeout for each event page
                    await page.goto(link, wait_until="domcontentloaded", timeout=90000)
                    await page.wait_for_timeout(3000)
                    event_html = await page.content()
                    esoup = BeautifulSoup(event_html, "html.parser")
                    
                    # Title and company
                    h1 = esoup.find('h1')
                    title_text = h1.text.strip() if h1 else "Unknown Title"
                    
                    # Check if it's "Centro Danza Matadero" and get the next one
                    headers1 = esoup.find_all('h1')
                    if len(headers1) > 1 and "Centro Danza" in title_text:
                        title_text = headers1[1].text.strip()
                    
                    company_text = title_text
                    subtitle_node = esoup.find(class_='field--name-field-subtitle')
                    show_title = subtitle_node.text.strip() if subtitle_node else title_text
                    
                    # It's usually "Company | Person". Let's just use the subtitle as title and H1 as company
                    if subtitle_node:
                        company_text = title_text
                        title_text = show_title
                    
                    # Image
                    img_url = ""
                    # Priority: 1. Main media image, 2. Standard image, 3. og:image meta tag
                    img_node = esoup.select_one('.field--name-field-media-image img') or esoup.select_one('.field--name-field-image img')
                    if img_node:
                        img_url = img_node.get('src', '')
                    
                    if not img_url:
                        og_img = esoup.find('meta', property='og:image')
                        if og_img:
                            img_url = og_img.get('content', '')

                    if img_url and not img_url.startswith('http'):
                        img_url = base_url + img_url
                            
                    # Dates and Time
                    date_tip = esoup.select_one('.group--info2 .field--name-field-schedule-tip') or esoup.select_one('.main-content--right .field--name-field-schedule-tip') or esoup.find(class_='field--name-field-schedule-tip')
                    date_str = date_tip.get_text(separator=' ', strip=True) if date_tip else ""
                    if date_str.lower().startswith("fecha"):
                        date_str = date_str[5:].strip()
                    
                    schedule_txt = esoup.select_one('.group--info2 .field--name-field-schedule-txt') or esoup.select_one('.main-content--right .field--name-field-schedule-txt') or esoup.find(class_='field--name-field-schedule-txt')
                    time_str = schedule_txt.get_text(separator=' ', strip=True) if schedule_txt else ""
                    # remove "Horario" if present
                    if time_str.lower().startswith("horario"):
                        time_str = time_str[7:].strip()
                    
                    sessions = parse_dates(date_str, time_str)
                    
                    if not sessions:
                        print(f"No sessions found for {title_text}, skipping.")
                        continue
                    
                    # Price
                    price_div = esoup.find(class_='field--name-field-price')
                    price_range = price_div.get_text(strip=True) if price_div else ""
                    if price_range.lower().startswith("precio"):
                        price_range = price_range[6:].strip()
                    
                    event = Event(
                        id=str(uuid.uuid4()),
                        title=title_text,
                        company=company_text,
                        venue=Venue(name="Matadero Madrid", municipality="Madrid"),
                        type="Danza",
                        price_range=price_range,
                        is_free="gratis" in price_range.lower(),
                        image_url=img_url,
                        url=link,
                        sessions=sessions
                    )
                    events.append(event)
                except Exception as e:
                    print(f"Error parsing event {link}: {e}")
        except Exception as e:
            print(f"Error loading catalog {prog_url}: {e}")
                
        await browser.close()
        return events

if __name__ == "__main__":
    evs = asyncio.run(scrape_matadero())
    for e in evs:
        print(f"{e.title} - {e.company}: {len(e.sessions)} sessions")
