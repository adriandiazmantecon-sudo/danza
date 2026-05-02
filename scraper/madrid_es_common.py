import re
import logging
from typing import List, Optional
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from models import Event, Venue, Session
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global cache to avoid redundant scraping when multiple venues are requested
_EVENTS_CACHE: Optional[List[Event]] = None

SPANISH_MONTHS = {
    'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
    'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
    'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
}

def parse_iso_date(iso_str: str) -> Optional[tuple]:
    """
    Parses '2026-05-02T20:00:00+0200' to ('2026-05-02', '20:00')
    """
    try:
        dt = datetime.fromisoformat(iso_str.replace(' ', ''))
        return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
    except Exception:
        return None

def parse_spanish_date(date_str: str) -> List[str]:
    """
    Fallback date parser for Spanish text.
    """
    date_str = date_str.lower().strip()
    date_pattern = r'(\d{1,2})\s+([a-z]+)\s+(\d{4})'
    matches = re.findall(date_pattern, date_str)
    
    results = []
    for day, month_name, year in matches:
        month = SPANISH_MONTHS.get(month_name)
        if month:
            results.append(f"{year}-{month}-{int(day):02d}")
            
    if not results:
        short_pattern = r'(\d{1,2})\s+(?:de\s+)?([a-z]+)'
        matches = re.findall(short_pattern, date_str)
        current_year = datetime.now().year
        for day, month_name in matches:
            month = SPANISH_MONTHS.get(month_name)
            if month:
                year = current_year
                if int(month) < datetime.now().month:
                    year += 1
                results.append(f"{year}-{month}-{int(day):02d}")
                
    return sorted(list(set(results)))

def scrape_all_madrid_es_events() -> List[Event]:
    """
    Scrapes all 'danza y baile' events from madrid.es using Playwright.
    """
    global _EVENTS_CACHE
    if _EVENTS_CACHE is not None:
        return _EVENTS_CACHE

    all_events = []
    
    with sync_playwright() as p:
        logger.info("Launching browser for madrid.es scraping...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        
        base_search_url = "https://www.madrid.es/sites/v/index.jsp?vgnextoid=ca9671ee4a9eb410VgnVCM100000171f5a0aRCRD&vgnextchannel=ca9671ee4a9eb410VgnVCM100000171f5a0aRCRD&idioma=es&newSearch=true&tema=&fechaIni=&texto=&tipoInstalacion=Danza+y+baile&tipo=3310c5e290e06310VgnVCM100000171f5a0aTAXC&cuando=cuandoCualquiera&fechaAccesible=&distrito=-1&lugar=&usuario=-1&enviar=buscar"
        
        current_actual = 1
        total_results = None
        
        while True:
            url = base_search_url
            if current_actual > 1:
                url = f"https://www.madrid.es/sites/v/index.jsp?vgnextoid=ca9671ee4a9eb410VgnVCM100000171f5a0aRCRD&vgnextchannel=ca9671ee4a9eb410VgnVCM100000171f5a0aRCRD&idioma=es&newSearch=false&total={total_results or 100}&actual={current_actual}&tipoInstalacion=Danza+y+baile&tipo=3310c5e290e06310VgnVCM100000171f5a0aTAXC&cuando=cuandoCualquiera&distrito=-1&usuario=-1"
            
            logger.info(f"Navigating to actual={current_actual}: {url}")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_selector('ul.events-results', timeout=30000)
            except Exception as e:
                logger.error(f"Error loading page with actual={current_actual}: {e}")
                break
                
            soup = BeautifulSoup(page.content(), 'html.parser')
            
            if total_results is None:
                total_elem = soup.select_one('li.results-total')
                if total_elem:
                    text = total_elem.get_text()
                    match = re.search(r'(\d+)', text)
                    if match:
                        total_results = int(match.group(1))
                        logger.info(f"Total results to scrape: {total_results}")
            
            items = soup.select('ul.events-results > li')
            if not items:
                logger.info("No items found on this page.")
                break
                
            logger.info(f"Found {len(items)} items on current page.")
            
            for item in items:
                title_elem = item.select_one('a.event-link')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                event_url = "https://www.madrid.es" + title_elem['href']
                
                sessions = []
                date_span = item.select_one('p.event-date span')
                if date_span and date_span.get('title'):
                    iso_info = parse_iso_date(date_span['title'])
                    if iso_info:
                        sessions.append(Session(date=iso_info[0], time=iso_info[1]))
                
                date_elem = item.select_one('p.event-date')
                date_str = date_elem.get_text(strip=True) if date_elem else ""
                if not sessions:
                    dates = parse_spanish_date(date_str)
                    sessions = [Session(date=d, time="20:00") for d in dates]
                
                venue_elem = item.select_one('a.event-location')
                venue_name = "Madrid"
                if venue_elem:
                    venue_name = venue_elem.get('data-name') or venue_elem.get_text(strip=True)
                
                img_elem = item.select_one('div.event-image img')
                image_url = ""
                if img_elem:
                    image_url = "https://www.madrid.es" + img_elem['src']
                
                venue_obj = Venue(name=venue_name, municipality="Madrid")
                
                event = Event(
                    id=re.sub(r'[^a-z0-9]', '', (title + venue_name).lower()),
                    title=title,
                    company="",
                    venue=venue_obj,
                    type="Danza",
                    price_range="",
                    is_free="gratis" in date_str.lower() or "entrada libre" in date_str.lower(),
                    image_url=image_url,
                    url=event_url,
                    sessions=sessions
                )
                all_events.append(event)
            
            current_actual += 25
            if total_results and current_actual > total_results:
                break
            if len(items) < 25:
                break
                
        browser.close()
        
    _EVENTS_CACHE = all_events
    return all_events

def get_events_for_venue(venue_pattern: str) -> List[Event]:
    """
    Returns events that match the given venue pattern (regex).
    """
    all_events = scrape_all_madrid_es_events()
    filtered = []
    for event in all_events:
        # Check if venue name matches pattern
        if re.search(venue_pattern, event.venue.name, re.IGNORECASE):
            filtered.append(event)
        else:
            # Try cleaning name
            clean_name = re.sub(r'\s*\(.*\)', '', event.venue.name)
            # Handle common variations like "Conde Duque" vs "CondeDuque"
            clean_name = clean_name.replace("CondeDuque", "Conde Duque")
            if re.search(venue_pattern, clean_name, re.IGNORECASE):
                filtered.append(event)
                
    return filtered
