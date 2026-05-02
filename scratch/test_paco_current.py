
import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import sys
import os

# Add scraper to path
sys.path.append(os.path.join(os.getcwd(), 'scraper'))
from venues.paco_rabal import scrape_event_details

async def test():
    urls = [
        "https://www.comunidad.madrid/actividades/2026/danza-aurunca-sabado-9",
        "https://www.comunidad.madrid/actividades/2026/danza-tejido-conectivo-escena",
        "https://www.comunidad.madrid/actividades/2026/danza-musica-bazamat-sabado-2-domingo-3",
        "https://www.comunidad.madrid/actividades/2026/danza-gala-danza-larreal",
        "https://www.comunidad.madrid/actividades/2026/danza-180pro-escena"
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for url in urls:
            print(f"\n--- Testing URL: {url} ---")
            event = await scrape_event_details(page, url)
            if event:
                print(f"Title:   '{event.title}'")
                print(f"Company: '{event.company}'")
                print(f"Sessions: {len(event.sessions)}")
            else:
                print("Failed to scrape event.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())
