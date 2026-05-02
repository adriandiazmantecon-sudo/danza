import asyncio
from playwright.async_api import async_playwright
import re

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # Add a user agent to maybe bypass some basic blocks
        await page.set_extra_http_headers({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        await page.goto("https://www.teatroscanal.com/espectaculos/danza/", timeout=60000)
        await page.wait_for_timeout(5000)
        
        # Get body text
        body_text = await page.evaluate('document.body.innerText')
        print(body_text[:2000])
        print("---")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
