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

GIGLON_GROUP_URL = "https://www.giglon.com/grupo?nameId=eventos-ayuntamiento-de-fuenlabrada"

# AJAX URL for pagination (discovered from page source)
GIGLON_AJAX_URL = (
    "https://www.giglon.com/grupo"
    "?p_p_id=groupuser_WAR_giglonportlet_INSTANCE_LdxvazwVlt34"
    "&p_p_lifecycle=0"
    "&p_p_state=exclusive"
    "&p_p_mode=view"
    "&p_p_col_id=column-1"
    "&p_p_col_count=1"
    "&_groupuser_WAR_giglonportlet_INSTANCE_LdxvazwVlt34_objType=9"
    "&_groupuser_WAR_giglonportlet_INSTANCE_LdxvazwVlt34_objId=54993969"
    "&_groupuser_WAR_giglonportlet_INSTANCE_LdxvazwVlt34_nameId=eventos-ayuntamiento-de-fuenlabrada"
    "&_groupuser_WAR_giglonportlet_INSTANCE_LdxvazwVlt34_jspPage=%2Fhtml%2Futil%2FeventListAux.jsp"
)

VENUE_NAME = "Teatro Josep Carreras"
VENUE_KEYWORDS = ["josep carreras"]
MUNICIPALITY = "Fuenlabrada"


def parse_giglon_date(fecha_str):
    """Parse date strings like '15/05/2026 20:00' -> ('2026-05-15', '20:00')"""
    m = re.match(r'(\d{2})/(\d{2})/(\d{4})\s+(\d{2}:\d{2})', fecha_str.strip())
    if m:
        day, month, year, time = m.groups()
        return f"{year}-{month}-{day}", time
    # Try date-only
    m2 = re.match(r'(\d{2})/(\d{2})/(\d{4})', fecha_str.strip())
    if m2:
        day, month, year = m2.groups()
        return f"{year}-{month}-{day}", "20:00"
    return None, None


def clean_text(text):
    if not text:
        return ""
    return " ".join(text.split()).strip()


GIGLON_BASE = "https://www.giglon.com"


async def get_all_event_urls_for_venue(page, venue_keywords):
    """
    Navigate all pages of the Giglon Fuenlabrada group listing and
    collect event URLs where tipo == 'Danza' and venue matches our target.
    Pre-sets cookies to bypass the consent wall.
    """
    urls = []

    # Pre-set Giglon cookies so the consent overlay doesn't wipe the page content
    await page.context.add_cookies([
        {"name": "aviso-giglon", "value": "1", "domain": "www.giglon.com", "path": "/"},
        {"name": "giglon-cookies1", "value": "true", "domain": "www.giglon.com", "path": "/"},
        {"name": "giglon-cookies3", "value": "true", "domain": "www.giglon.com", "path": "/"},
    ])

    # Load first page and wait for event rows to appear
    await page.goto(GIGLON_GROUP_URL, wait_until="domcontentloaded", timeout=60000)
    try:
        await page.wait_for_selector("[onclick*=\"window.location='/evento/\"]", timeout=15000)
    except Exception:
        print("  Warning: event rows did not appear within timeout on page 1.")

    # Determine number of pages from pagination
    total_pages = 1
    try:
        pag_text = await page.inner_text(".list-pagination")
        m = re.search(r'Página \d+ de (\d+)', pag_text)
        if m:
            total_pages = int(m.group(1))
    except Exception:
        pass

    print(f"  Giglon Fuenlabrada: {total_pages} page(s) to process.")

    for page_num in range(1, total_pages + 1):
        if page_num > 1:
            # Navigate subsequent pages via AJAX URL with page parameter
            ajax_url = GIGLON_AJAX_URL + f"&page={page_num}"
            await page.goto(ajax_url, wait_until="domcontentloaded", timeout=60000)
            try:
                await page.wait_for_selector("[onclick*=\"window.location='/evento/\"]", timeout=10000)
            except Exception:
                print(f"  Warning: event rows did not appear on page {page_num}.")

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Each event row has onclick="window.location='/evento/...'"
        rows = soup.find_all(attrs={"onclick": re.compile(r"window\.location='/evento/")})
        print(f"  Page {page_num}: {len(rows)} event row(s) found in HTML.")
        for row in rows:
            # Extract columns: [img][title][date][venue][municipality][tipo][price][btn]
            cells = row.find_all("div", class_="cell")
            if len(cells) < 6:
                continue

            tipo = clean_text(cells[5].get_text()) if len(cells) > 5 else ""
            venue_cell = clean_text(cells[3].get_text()) if len(cells) > 3 else ""

            # Filter: must be Danza type AND at our specific venue
            if tipo.lower() != "danza":
                continue
            if not any(kw in venue_cell.lower() for kw in venue_keywords):
                continue

            # Extract URL
            onclick = row.get("onclick", "")
            url_match = re.search(r"'/evento/([^']+)'", onclick)
            if url_match:
                event_url = f"{GIGLON_BASE}/evento/{url_match.group(1)}"
                if event_url not in urls:
                    urls.append(event_url)

    print(f"  Found {len(urls)} Danza event(s) at {VENUE_NAME}.")
    return urls



async def scrape_event_detail(page, url):
    """Scrape a single Giglon event detail page."""
    print(f"  Scraping detail: {url}")
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(1500)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Title
        h1 = soup.find("h1")
        title = clean_text(h1.get_text()) if h1 else "Evento de Danza"

        # Extract structured fields using label elements
        def get_label_value(label_text):
            for lbl in soup.find_all("label", class_="lformulario"):
                if clean_text(lbl.get_text()) == label_text:
                    parent = lbl.parent
                    if parent:
                        span = parent.find("span")
                        if span:
                            return clean_text(span.get_text())
            return ""

        fecha_raw = get_label_value("Fecha")
        recinto = get_label_value("Recinto")
        artistas_raw = get_label_value("Artistas")

        # Parse date and time
        event_date, event_time = parse_giglon_date(fecha_raw)
        if not event_date:
            print(f"    Could not parse date from '{fecha_raw}' — skipping.")
            return None

        # Validate future event
        today_str = datetime.now().strftime("%Y-%m-%d")
        if event_date < today_str:
            print(f"    Skipping past event: {title} ({event_date})")
            return None

        # Company: first artist listed (or title as fallback)
        company = ""
        if artistas_raw:
            lines = [l.strip() for l in artistas_raw.split("\n") if l.strip()]
            company = lines[0] if lines else artistas_raw
        if not company:
            company = title

        # Price
        price_raw = ""
        price_match = re.search(r'desde\s+([\d,\.]+\s*€)', soup.get_text(), re.IGNORECASE)
        if price_match:
            price_raw = price_match.group(1).replace(",", ".").strip()
        if not price_raw:
            price_raw = "Consultar web"

        is_free = ("gratis" in price_raw.lower()
                   or "gratuito" in price_raw.lower()
                   or re.search(r'\b0[,.]?00\s*€', price_raw) is not None)

        # Image – prefer high-res, strip duplicate imageThumbnail params
        img_url = ""
        img_el = soup.find("img", src=re.compile(r"/documents/"))
        if img_el:
            src = img_el.get("src", "")
            # Clean up doubled query params like ?imageThumbnail=2?imageThumbnail=3
            src = re.sub(r'\?imageThumbnail=\d+', '', src)
            src = src.rstrip("?")
            if src.startswith("http"):
                img_url = src
            else:
                img_url = "https://www.giglon.com" + src

        if not img_url:
            img_url = "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=800&auto=format&fit=crop"

        print(f"    OK: {title} | {event_date} {event_time} | {price_raw}")
        return Event(
            id=str(uuid.uuid4()),
            title=title,
            company=company,
            venue=Venue(VENUE_NAME, MUNICIPALITY),
            type="Danza",
            price_range=price_raw,
            is_free=is_free,
            image_url=img_url,
            url=url,
            sessions=[Session(date=event_date, time=event_time)]
        )

    except Exception as e:
        print(f"    Error scraping {url}: {e}")
        return None


async def scrape_josep_carreras():
    """Main scraper function for Teatro Josep Carreras (Fuenlabrada)."""
    print(f"Starting scraper: {VENUE_NAME} ({MUNICIPALITY})...")
    events = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        try:
            urls = await get_all_event_urls_for_venue(page, VENUE_KEYWORDS)
            for url in urls:
                event = await scrape_event_detail(page, url)
                if event:
                    events.append(event)
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Error in {VENUE_NAME} scraper: {e}")
        finally:
            await browser.close()

    print(f"Finished {VENUE_NAME}. Total dance events: {len(events)}")
    return events


if __name__ == "__main__":
    res = asyncio.run(scrape_josep_carreras())
    for e in res:
        print(f"  {e.title} | {e.venue.name} | {e.sessions[0].date} {e.sessions[0].time} | {e.price_range}")
