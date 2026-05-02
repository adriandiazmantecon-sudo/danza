import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({'User-Agent': 'Mozilla/5.0'})
        await page.goto("https://www.teatroscanal.com/", timeout=60000)
        await page.wait_for_timeout(3000)
        
        # Get all links
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => a.href).filter(h => h.includes('danza'));
        }''')
        print("Danza links:", set(links))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
