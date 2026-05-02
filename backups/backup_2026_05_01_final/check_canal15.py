import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({'User-Agent': 'Mozilla/5.0'})
        await page.goto("https://www.teatroscanal.com/entradas/danza-madrid/", timeout=60000)
        await page.wait_for_timeout(3000)
        
        html = await page.evaluate('document.body.innerHTML')
        soup = BeautifulSoup(html, "html.parser")
        
        # Look for "Las hijas de Bernarda" to find the container
        for el in soup.find_all(string=lambda text: text and "Las hijas de Bernarda" in text):
            parent = el.parent
            for _ in range(5):
                if parent:
                    print(f"Parent tag: {parent.name}, classes: {parent.get('class')}")
                    parent = parent.parent
            print("="*40)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
