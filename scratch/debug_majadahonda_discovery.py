import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def test_discovery():
    base_url = "https://cultura.majadahonda.org/espectaculos-culturales"
    # Try with a more complete URL
    list_url = f"{base_url}?p_p_id=CalendarSuite_INSTANCE_STa3SHI1sEeH&p_p_lifecycle=0&p_r_p_calendarPath=%2Fhtml%2Fsuite%2Fdisplays%2Flist.jsp&_CalendarSuite_INSTANCE_STa3SHI1sEeH_resetCur=false&_CalendarSuite_INSTANCE_STa3SHI1sEeH_delta=50"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"Navigating to: {list_url}")
        await page.goto(list_url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(5000)
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Save HTML for inspection
        with open("majadahonda_list_debug.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        candidate_links = soup.select('a.lfr-card-title-text, .lfr-card-title a, .lfr-card-content a')
        print(f"Found {len(candidate_links)} candidate links.")
        
        for a in candidate_links:
            href = a.get('href')
            text = a.get_text().strip()
            print(f"Link: {text} | Href: {href}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_discovery())
