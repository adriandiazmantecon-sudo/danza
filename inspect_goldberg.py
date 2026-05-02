import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def inspect_goldberg():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://www.centrodanzamatadero.es/actividades/staatsballett-hannover-goyo-montero")
        await page.wait_for_timeout(3000)
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        date_tip = soup.find_all(class_='field--name-field-schedule-tip')
        for dt in date_tip:
            print("Date tip:", dt.get_text(strip=True))
            
        schedule = soup.find_all(class_='field--name-field-schedule-txt')
        for sc in schedule:
            print("Schedule:", sc.get_text(strip=True))
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_goldberg())
