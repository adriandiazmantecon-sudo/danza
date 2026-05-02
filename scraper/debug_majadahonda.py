import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def debug_majadahonda():
    base_url = "https://cultura.majadahonda.org/espectaculos-culturales"
    list_url = f"{base_url}?_CalendarSuite_INSTANCE_STa3SHI1sEeH_delta=200"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"Loading: {list_url}")
        await page.goto(list_url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(5000)
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Look for all links that could be events
        links = soup.select('a')
        print(f"Total links found: {len(links)}")
        
        for a in links:
            href = a.get('href')
            text = a.get_text().strip()
            if href and ('danza' in text.lower() or 'baile' in text.lower() or 'ballet' in text.lower()):
                print(f"Found match: {text} -> {href}")
        
        # Save HTML for inspection
        with open("majadahonda_list.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_majadahonda())
