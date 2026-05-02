import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({'User-Agent': 'Mozilla/5.0'})
        await page.goto("https://www.teatroscanal.com/entradas/actividades-madrid/", timeout=60000)
        await page.wait_for_timeout(3000)
        
        # Get body text
        titles = await page.evaluate('''() => {
            const elements = document.querySelectorAll('article .entry-title a, article h3 a, article h4 a, article .title a, .hentry .entry-title a');
            return Array.from(elements).map(el => el.innerText).filter(t => t.trim() !== '');
        }''')
        print("Actividades titles:")
        for t in titles: print("-", t)
        
        # also print the raw innerText of the body
        body = await page.evaluate('document.body.innerText')
        print("\\nBody snippets with danza:")
        for line in body.split('\\n'):
            if 'danza' in line.lower():
                print(line)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
