
import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import re

async def debug_paco_rabal():
    url = "https://www.comunidad.madrid/actividades/2026/danza-aurunca-sabado-9"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print(f"Navigating to {url}")
        await page.goto(url, wait_until="domcontentloaded")
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        body_el = soup.select_one('.field--name-body, .field--name-field-texto-explicativo')
        if not body_el:
            print("Body element not found by classes. Searching for all div classes...")
            for div in soup.find_all('div', class_=True):
                if 'field--name-body' in div['class']:
                    print(f"Found div with field--name-body: {div}")
                    body_el = div
                    break
        
        if body_el:
            print("Body element found.")
            h3_el = body_el.select_one('h3')
            if h3_el:
                print("H3 found in body:")
                print(h3_el)
                h3_text = h3_el.get_text(separator="\n").strip()
                print(f"H3 text with separator: {repr(h3_text)}")
                lines = [line.strip() for line in h3_text.split("\n") if line.strip()]
                print(f"Lines: {lines}")
                
                if len(lines) >= 1:
                    print(f"Found Title Candidate: {lines[0]}")
                if len(lines) >= 2:
                    print(f"Found Company Candidate: {lines[1]}")
                else:
                    print("Less than 2 lines found.")
                    strong_tags = h3_el.find_all('strong')
                    print(f"Strong tags: {[s.get_text().strip() for s in strong_tags]}")
                    if len(strong_tags) >= 2:
                        print(f"Found Company via Strong tags: {strong_tags[1].get_text().strip()}")
            else:
                print("H3 NOT found in body.")
                # Print all children of body to see what's there
                print("Children of body:")
                for child in body_el.children:
                    if child.name:
                        print(f"Tag: {child.name}, Text: {child.get_text().strip()[:50]}...")
        else:
            print("Body element STILL not found.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_paco_rabal())
