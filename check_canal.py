import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.teatroscanal.com/espectaculos/danza/")
        await page.wait_for_timeout(3000)
        
        # get all event titles
        titles = await page.evaluate('''() => {
            const elements = document.querySelectorAll('article.hentry .entry-title a, article.hentry h3 a, article.hentry h4 a, article.hentry .title a, article .entry-title a, article h3 a, article h4 a, article .title a');
            return Array.from(elements).map(el => el.innerText).filter(t => t.trim() !== '');
        }''')
        
        print("Initial titles:", len(titles))
        for t in titles: print("-", t)
        
        # Check if there is a 'load more' button
        load_more = await page.evaluate('''() => {
            const btn = document.querySelector('.load-more, #load-more, .cargar-mas, a.next, a.page-numbers');
            return btn ? btn.innerText : 'None';
        }''')
        print("Load more button?", load_more)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
