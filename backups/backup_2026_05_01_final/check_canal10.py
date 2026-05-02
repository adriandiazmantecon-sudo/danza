import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({'User-Agent': 'Mozilla/5.0'})
        
        # Check all possible sections
        sections = [
            "https://www.teatroscanal.com/entradas/flamenco-madrid/",
            "https://www.teatroscanal.com/entradas/teatro-madrid/"
        ]
        
        for url in sections:
            print(f"Checking {url}")
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(2000)
            
            titles = await page.evaluate('''() => {
                const elements = document.querySelectorAll('article .entry-title a, article h3 a, article h4 a, article .title a, .hentry .entry-title a');
                return Array.from(elements).map(el => el.innerText).filter(t => t.trim() !== '');
            }''')
            print("Titles:", titles)
            print("="*40)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
