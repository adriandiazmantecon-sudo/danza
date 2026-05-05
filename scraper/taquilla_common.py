import asyncio
import re
import logging
from typing import List, Optional, Dict
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

    all_events_map: Dict[str, Event] = {}
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
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Wait for any of the event list items
            await page.wait_for_selector('li[itemtype="https://schema.org/DanceEvent"]', timeout=30000)
            
            # Scroll to load more if lazy loaded
            for _ in range(5):
                await page.mouse.wheel(0, 2000)
                await asyncio.sleep(0.5)
            
            soup = BeautifulSoup(await page.content(), 'html.parser')
            session_items = soup.select('li[itemtype="https://schema.org/DanceEvent"]')
            
            logger.info(f"Found {len(session_items)} session items on page.")
            
            for s_item in session_items:
                # Extract basic info from metadata
                name_meta = s_item.find('meta', itemprop='name')
                date_meta = s_item.find('meta', itemprop='startDate')
                url_meta = s_item.find('meta', itemprop='url')
                price_meta = s_item.find('meta', itemprop='lowPrice')
                
                # Venue info usually in a nested div/span with itemprop="location"
                location_elem = s_item.select_one('[itemprop="location"]')
                venue_name = "Madrid"
                if location_elem:
                    venue_name_elem = location_elem.find('meta', itemprop='name') or location_elem.select_one('[itemprop="name"]')
                    if venue_name_elem:
                        venue_name = venue_name_elem.get('content') if venue_name_elem.name == 'meta' else venue_name_elem.get_text(strip=True)

                if not name_meta or not date_meta:
                    continue
                
                title = name_meta['content'].strip()
                date_full = date_meta['content'] # e.g. "2026-05-08T21:00:00+02:00"
                date_val = date_full.split('T')[0]
                time_val = "20:00"
                if 'T' in date_full:
                    time_val = date_full.split('T')[1][:5]
                
                event_url = url_meta['content'] if url_meta else ""
                price_val = price_meta['content'] if price_meta else ""
                price_range = f"{price_val}€" if price_val else ""
                
                # Clean up venue name (sometimes it has city appended)
                venue_name = venue_name.split(',')[0].strip()
                
                # Use (title, venue) as key to group sessions
                key = f"{title}|{venue_name}"
                
                if key not in all_events_map:
                    all_events_map[key] = Event(
                        id=str(uuid.uuid4()),
                        title=title,
                        company="",
                        venue=Venue(name=venue_name, municipality="Madrid"),
                        type="Danza",
                        price_range=price_range,
                        is_free=price_range.lower() in ["0€", "0.00€", "gratis", "gratuito"],
                        image_url="/images/generic_dance.png",
                        url=event_url,
                        sessions=[]
                    )
                
                # Add session if not already added
                session = Session(date=date_val, time=time_val)
                if not any(s.date == session.date and s.time == session.time for s in all_events_map[key].sessions):
                    all_events_map[key].sessions.append(session)
                
                # Update price range if this session is cheaper
                if price_val and (not all_events_map[key].price_range or price_val < all_events_map[key].price_range.replace('€', '')):
                    all_events_map[key].price_range = f"{price_val}€"

            logger.info(f"Grouped into {len(all_events_map)} unique events.")
                
        except Exception as e:
            logger.error(f"Error scraping taquilla.com: {e}")
        finally:
            await browser.close()
            
    _EVENTS_CACHE = list(all_events_map.values())
    return _EVENTS_CACHE

import unicodedata

def normalize_string(s: str) -> str:
    """Removes accents and converts to lowercase."""
    if not s:
        return ""
    s = unicodedata.normalize('NFD', s)
    return "".join([c for c in s if unicodedata.category(c) != 'Mn']).lower()

async def get_events_for_venue(venue_name_pattern: str) -> List[Event]:
    """
    Returns events that match the given venue name pattern (substring).
    """
    all_events = await scrape_all_taquilla_events()
    normalized_pattern = normalize_string(venue_name_pattern)
    filtered = []
    for event in all_events:
        if normalized_pattern in normalize_string(event.venue.name):
            filtered.append(event)
    return filtered
