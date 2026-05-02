import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({'User-Agent': 'Mozilla/5.0'})
        
        # Go to home page
        await page.goto("https://www.teatroscanal.com/", timeout=60000)
        await page.wait_for_timeout(3000)
        
        # Scroll down
        for _ in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            
        titles = await page.evaluate('''() => {
            const elements = document.querySelectorAll('article.hentry .entry-title a, article.hentry h3 a, article.hentry h4 a, article.hentry .title a, article .entry-title a, article h3 a, article h4 a, article .title a');
            return Array.from(elements).map(el => el.innerText).filter(t => t.trim() !== '');
        }''')
        print("Home titles:")
        for t in titles: print("-", t)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
