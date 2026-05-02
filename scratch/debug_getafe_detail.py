import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def debug_getafe_detail():
    url = "https://cultura.getafe.es/agenda-cultura/las-flamencas/"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        html = await page.content()
        with open("scratch/getafe_page_debug.html", "w", encoding="utf-8") as f:
            f.write(html)
        soup = BeautifulSoup(html, "html.parser")
        
        date_el = soup.select_one('.mec-single-date')
        date_text = date_el.get_text().strip() if date_el else "NOT FOUND"
        print(f"Date Text: '{date_text}'")
        
        # Check title
        title_el = soup.select_one('h1.mec-single-title')
        print(f"Title: {title_el.get_text().strip() if title_el else 'NOT FOUND'}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_getafe_detail())
