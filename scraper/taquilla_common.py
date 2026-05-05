import asyncio
import re
import logging
from typing import List, Optional
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from models import Event, Venue, Session
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global cache to avoid redundant scraping when multiple venues are requested
_EVENTS_CACHE: Optional[List[Event]] = None

async def scrape_all_taquilla_events() -> List[Event]:
    """
    Scrapes all 'danza' events from taquilla.com using Playwright.
    """
    global _EVENTS_CACHE
    if _EVENTS_CACHE is not None:
        return _EVENTS_CACHE

    all_events = []
    url = "https://www.taquilla.com/espectaculos/danza/madrid"
    
    async with async_playwright() as p:
        logger.info("Launching browser for taquilla.com scraping...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        
        try:
            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_selector('.ent-result', timeout=30000)
            
            # Wait a bit for any dynamic content
            await asyncio.sleep(2)
            
            soup = BeautifulSoup(await page.content(), 'html.parser')
            event_blocks = soup.select('.ent-result')
            
            logger.info(f"Found {len(event_blocks)} event blocks on page.")
            
            for block in event_blocks:
                title_elem = block.select_one('.l-title-entity')
                venue_elem = block.select_one('.l-subtitle-entity')
                
                if not title_elem or not venue_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                venue_name_full = venue_elem.get_text(strip=True)
                # Venue name is usually "Venue Name, Municipality"
                venue_name = venue_name_full.split(',')[0].strip()
                municipality = "Madrid"
                if ',' in venue_name_full:
                    municipality = venue_name_full.split(',')[1].replace("Ver mapa", "").strip()
                
                sessions = []
                session_items = block.select('li[itemtype="https://schema.org/DanceEvent"]')
                
                # Default info from block
                event_url = ""
                price_range = ""
                
                for s_item in session_items:
                    date_meta = s_item.find('meta', itemprop='startDate')
                    url_meta = s_item.find('meta', itemprop='url')
                    price_meta = s_item.find('meta', itemprop='lowPrice')
                    
                    if date_meta:
                        date_val = date_meta['content'] # YYYY-MM-DD
                        # Find time in the list
                        time_span = s_item.select_one('.ent-results-list-hour-time span')
                        time_val = time_span.get_text(strip=True) if time_span else "20:00"
                        
                        sessions.append(Session(date=date_val, time=time_val))
                    
                    if url_meta and not event_url:
                        event_url = url_meta['content']
                        
                    if price_meta and not price_range:
                        price_val = price_meta['content']
                        price_range = f"{price_val}€"
                
                if not sessions:
                    continue
                
                # If event_url still empty, try to find any link in the block
                if not event_url:
                    first_link = block.select_one('a')
                    if first_link:
                        event_url = first_link['href']
                        if event_url.startswith('/'):
                            event_url = "https://www.taquilla.com" + event_url
                
                # Generic image for all these venues as requested
                image_url = "/images/generic_dance.png"
                
                event = Event(
                    id=str(uuid.uuid4()),
                    title=title,
                    company="", # Not necessary as per user request
                    venue=Venue(name=venue_name, municipality=municipality),
                    type="Danza",
                    price_range=price_range,
                    is_free=price_range.lower() in ["0€", "0.00€", "gratis", "gratuito"],
                    image_url=image_url,
                    url=event_url,
                    sessions=sessions
                )
                all_events.append(event)
                
        except Exception as e:
            logger.error(f"Error scraping taquilla.com: {e}")
        finally:
            await browser.close()
            
    _EVENTS_CACHE = all_events
    return all_events

async def get_events_for_venue(venue_name_pattern: str) -> List[Event]:
    """
    Returns events that match the given venue name pattern (substring).
    """
    all_events = await scrape_all_taquilla_events()
    filtered = []
    for event in all_events:
        if venue_name_pattern.lower() in event.venue.name.lower():
            filtered.append(event)
    return filtered
