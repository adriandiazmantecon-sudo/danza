import asyncio
import re
import unicodedata
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

class Session:
    def __init__(self, date, time):
        self.date = date
        self.time = time

class Venue:
    def __init__(self, name, city):
        self.name = name
        self.city = city

class Event:
    def __init__(self, id, title, company, venue, type, price_range, is_free, image_url, url, sessions):
        self.id = id
        self.title = title
        self.company = company
        self.venue = venue
        self.type = type
        self.price_range = price_range
        self.is_free = is_free
        self.image_url = image_url
        self.url = url
        self.sessions = sessions

def parse_sessions(soup, content_area):
    sessions = []
    if not content_area:
        return sessions
    time_tags = content_area.select('time[datetime]')
    for tag in time_tags:
        dt_str = tag.get('datetime')
        if not dt_str:
            continue
        try:
            parts = dt_str.split('T')
            if len(parts) >= 2:
                date_part = parts[0]
                time_part = parts[1][:5]
                if not any(s.date == date_part and s.time == time_part for s in sessions):
                    sessions.append(Session(date=date_part, time=time_part))
        except Exception as e:
            print(f"Error parsing datetime {dt_str}: {e}")
    return sessions

async def scrape_event_details(page, url):
    print(f"Scraping event details: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(1000)
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        content_area = soup.select_one('#block-comunidad-madrid-content, .c-main-content, main')
        h1_el = soup.select_one('h1.heading, h1.c-title, h1')
        h1_text = h1_el.get_text().strip() if h1_el else ""
        base_title = h1_text
        
        # --- ORIGINAL LOGIC ---
        title = base_title
        company = ""
        if content_area:
            body_divs = content_area.select('.field--name-body, .field--name-field-texto-explicativo')
            company_keywords = r'Compa\u00f1\u00eda|C\u00eda\.?|Conservatorio|Ballet|Grupo|Escuela|Centro|Creaci\u00f3n|Profesora?|Director|Coreograf\u00eda|Direcci\u00f3n|Autora?|Ensemble'
            skip_patterns = r'\d+\s*a\s*\d+\s*h|lunes|martes|mi\u00e9rcoles|miercoles|jueves|viernes|s\u00e1bado|sabado|domingo|horas|precio|entradas|Coreograf\u00eda|M\u00fasica|Sinfon\u00eda|Pieza'
            for body_el in body_divs:
                institutional_names = r'Real Conservatorio Profesional de Danza Mariemma|Mariemma|Larreal|Tejido Conectivo'
                first_paragraphs = body_el.select('p, h3, strong')
                for p_el in first_paragraphs[:5]:
                    p_text = p_el.get_text().strip()
                    if re.search(institutional_names, p_text, re.IGNORECASE) and len(p_text) < 100:
                        company = p_text
                        break
                if company: break
                h3_elements = body_el.select('h3')
                for h3_el in h3_elements:
                    h3_text = h3_el.get_text(separator="\n").strip()
                    if not h3_text or len(h3_text) < 3: continue
                    if re.search(skip_patterns, h3_text, re.IGNORECASE): continue
                    lines = [l.strip() for l in h3_text.split("\n") if l.strip()]
                    if len(lines) >= 2:
                        title = re.sub(r'^(?:DANZA|MÚSICA|TEATRO):\s*', '', lines[0], flags=re.IGNORECASE)
                        company = lines[1]
                        break
                    elif len(lines) == 1:
                        line = lines[0]
                        is_company_like = re.search(company_keywords, line, re.IGNORECASE)
                        if (not title or title == base_title) and not is_company_like:
                            title = re.sub(r'^(?:DANZA|MÚSICA|TEATRO):\s*', '', line, flags=re.IGNORECASE)
                        next_el = h3_el.find_next_sibling(['p', 'div', 'strong', 'em'])
                        if next_el:
                            next_text = next_el.get_text().strip()
                            if next_text and len(next_text) > 3 and not re.search(skip_patterns, next_text, re.IGNORECASE):
                                if re.search(company_keywords, next_text, re.IGNORECASE) or next_el.name in ['strong', 'em'] or next_el.find(['strong', 'em']):
                                    company = next_text
                                    break
                        if is_company_like:
                            company = line
                            break
                if title and company: break

        def normalize_text(text):
            if not text: return ""
            text = text.replace('\xa0', ' ')
            text = unicodedata.normalize('NFC', text)
            text = " ".join(text.split())
            text = text.strip('• \t\n\r\xa0*!-–—,.')
            return text

        title = normalize_text(title)
        company = normalize_text(company)
        company_prefix_regex = r'^(?:Compa\u00f1\u00eda|C\u00eda\.?|Cia\.?|Profesora?|Director|Coreograf\u00eda|Direcci\u00f3n|Autora?|Conservatorio|Grupo|Escuela)(?::\s*|\s+)'
        company = re.sub(company_prefix_regex, '', company, flags=re.IGNORECASE)

        if title:
            title = re.sub(r'^(?:DANZA|M\u00daSICA|TEATRO|ACTIVIDADES|PROGRAMACI\u00d3N):\s*', '', title, flags=re.IGNORECASE)
            days_regex = r'\s+-\s+(?:lunes|martes|mi\u00e9rcoles|miercoles|jueves|viernes|s\u00e1bado|sabado|domingo)'
            title = re.split(days_regex, title, flags=re.IGNORECASE)[0]
            title = re.split(r':\s+(?:lunes|martes|mi\u00e9rcoles|miercoles|jueves|viernes|s\u00e1bado|sabado|domingo)', title, flags=re.IGNORECASE)[0]
            title = re.sub(r'\s+\d{1,2}:\d{2}\s*h?$', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s+-\s+Paco Rabal.*$', '', title, flags=re.IGNORECASE)
            if company and title.lower().startswith(company.lower()):
                title = re.sub(r'^' + re.escape(company) + r'[:\s-]*', '', title, flags=re.IGNORECASE)
            title = title.strip('• \t\n\r\xa0*!-–—,.')

        return {"title": title, "company": company, "base_h1": h1_text}
    except Exception as e:
        print(f"Error: {e}")
        return None

async def main():
    urls = [
        "https://www.comunidad.madrid/actividades/2026/danza-tejido-conectivo-escena",
        "https://www.comunidad.madrid/actividades/2026/danza-aurunca-sabado-9"
    ]
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        for url in urls:
            res = await scrape_event_details(page, url)
            print(f"URL: {url}")
            print(f"  Base H1: {res['base_h1']}")
            print(f"  Extracted Title: {res['title']}")
            print(f"  Extracted Company: {res['company']}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
