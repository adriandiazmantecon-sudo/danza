import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('https://www.centrodanzamatadero.es/actividades/staatsballett-hannover-goyo-montero')
        await page.wait_for_timeout(3000)
        html = await page.content()
        with open('scratch_matadero_event.html', 'w', encoding='utf-8') as f:
            f.write(html)
        await browser.close()

asyncio.run(main())
