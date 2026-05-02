import asyncio
import re
import unicodedata
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def scrape_event_details(page, url):
    print(f"Scraping event details: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(1000)
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        content_area = soup.select_one('#block-comunidad-madrid-content, .c-main-content, main')
        
        # --- EXTRACT TITLE AND COMPANY (NEW LOGIC) ---
        h1_el = soup.select_one('h1.heading, h1.c-title, h1')
        h1_text = h1_el.get_text().strip() if h1_el else ""
        
        def normalize_text(text):
            if not text: return ""
            text = text.replace('\xa0', ' ')
            text = unicodedata.normalize('NFC', text)
            text = " ".join(text.split())
            text = text.strip('• \t\n\r\xa0*!-–—,.')
            return text

        def clean_title_str(text):
            if not text: return ""
            # Remove "DANZA:", "TEATRO:", etc.
            text = re.sub(r'^(?:DANZA|M\u00daSICA|TEATRO|ACTIVIDADES|PROGRAMACI\u00d3N|DANZA Y M\u00daSICA):\s*', '', text, flags=re.IGNORECASE)
            # Remove day of week patterns and dates (e.g. - sábado 9, - 16 de mayo)
            days_regex = r'\s+-\s+(?:lunes|martes|mi\u00e9rcoles|miercoles|jueves|viernes|s\u00e1bado|sabado|domingo)(?:\s+\d{1,2})?'
            text = re.split(days_regex, text, flags=re.IGNORECASE)[0]
            text = re.split(r':\s+(?:lunes|martes|mi\u00e9rcoles|miercoles|jueves|viernes|s\u00e1bado|sabado|domingo)', text, flags=re.IGNORECASE)[0]
            # Remove " - 20:00 h" or similar
            text = re.sub(r'\s+\d{1,2}:\d{2}\s*h?$', '', text, flags=re.IGNORECASE)
            # Remove trailing " - Paco Rabal"
            text = re.sub(r'\s+-\s+Paco Rabal.*$', '', text, flags=re.IGNORECASE)
            return normalize_text(text)

        base_title = clean_title_str(h1_text)
        title = base_title
        company = ""
        
        if content_area:
            body_divs = content_area.select('.field--name-body, .field--name-field-texto-explicativo')
            company_keywords = r'Compa\u00f1\u00eda|C\u00eda\.?|Conservatorio|Ballet|Grupo|Escuela|Centro|Creaci\u00f3n|Profesora?|Director|Coreograf\u00eda|Direcci\u00f3n|Autora?|Ensemble|Producc\u00f3n'
            skip_patterns = r'\d+\s*a\s*\d+\s*h|lunes|martes|mi\u00e9rcoles|miercoles|jueves|viernes|s\u00e1bado|sabado|domingo|horas|precio|entradas|M\u00fasica|Sinfon\u00eda|Pieza'
            institutional_names = r'Real Conservatorio Profesional de Danza Mariemma|Mariemma|Larreal|Tejido Conectivo|Antonio Gades|Rafaela Carrasco|Sara Baras'

            for body_el in body_divs:
                h3_elements = body_el.select('h3')
                for h3_el in h3_elements:
                    h3_text = h3_el.get_text(separator="\n").strip()
                    if not h3_text or len(h3_text) < 3: continue
                    if re.search(skip_patterns, h3_text, re.IGNORECASE): continue
                    
                    lines = [l.strip() for l in h3_text.split("\n") if l.strip()]
                    if len(lines) >= 2:
                        potential_title = clean_title_str(lines[0])
                        potential_company = normalize_text(lines[1])
                        if potential_title and potential_company:
                            title = potential_title
                            company = potential_company
                            break
                    elif len(lines) == 1:
                        line = lines[0]
                        if re.search(company_keywords, line, re.IGNORECASE) or re.search(institutional_names, line, re.IGNORECASE):
                            company = line
                            break
                
                if company: break

                first_elements = body_el.select('p, strong, b, h4')[:8]
                for el in first_elements:
                    text = el.get_text().strip()
                    if not text or len(text) < 3 or len(text) > 100: continue
                    if re.search(skip_patterns, text, re.IGNORECASE): continue
                    if re.search(company_keywords, text, re.IGNORECASE) or re.search(institutional_names, text, re.IGNORECASE):
                        company = text
                        break
                if company: break

        title = clean_title_str(title)
        company = normalize_text(company)
        company_prefix_regex = r'^(?:Compa\u00f1\u00eda|C\u00eda\.?|Cia\.?|Profesora?|Director|Coreograf\u00eda|Direcci\u00f3n|Autora?|Conservatorio|Grupo|Escuela|Producci\u00f3n)(?::\s*|\s+)'
        company = re.sub(company_prefix_regex, '', company, flags=re.IGNORECASE)
        
        if company and title:
            if company.lower() == title.lower():
                pass
            elif title.lower().startswith(company.lower()):
                title = re.sub(r'^' + re.escape(company) + r'[:\s-]*', '', title, flags=re.IGNORECASE)

        if not company or company == "":
            company = title
        if not title:
            title = base_title
        if not title:
            title = clean_title_str(h1_text)

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
