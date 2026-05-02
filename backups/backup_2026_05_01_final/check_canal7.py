import asyncio
from playwright.async_api import async_playwright
import time

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({'User-Agent': 'Mozilla/5.0'})
        await page.goto("https://www.teatroscanal.com/entradas/danza-madrid/", timeout=60000)
        await page.wait_for_timeout(3000)
        
        # Scroll down 5 times
        for _ in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
            # click load more if it exists
            await page.evaluate('''() => {
                const btn = document.querySelector('.load-more, #load-more, .cargar-mas, a.next, a.page-numbers');
                if (btn) btn.click();
            }''')
            await page.wait_for_timeout(2000)
            
        # Get body text
        body_text = await page.evaluate('document.body.innerText')
        print(body_text[:4000])
        print("---")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
