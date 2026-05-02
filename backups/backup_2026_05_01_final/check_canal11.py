import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({'User-Agent': 'Mozilla/5.0'})
        await page.goto("https://www.teatroscanal.com/entradas/danza-madrid/", timeout=60000)
        await page.wait_for_timeout(3000)
        
        # Get raw HTML
        html = await page.evaluate('document.body.innerHTML')
        with open("canal_html.txt", "w", encoding="utf-8") as f:
            f.write(html)
        print("Wrote html to canal_html.txt")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
