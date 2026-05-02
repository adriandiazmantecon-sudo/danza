import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def debug_majadahonda_event(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"Loading event: {url}")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(5000)
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Save HTML for inspection
        with open("majadahonda_event.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        print("Title:", soup.select_one('h1, h2, h3, .title'))
        print("Text preview:", soup.get_text(separator=" ")[:1000])
        
        await browser.close()

if __name__ == "__main__":
    url = "https://cultura.majadahonda.org/espectaculos-culturales?p_p_id=CalendarSuite_INSTANCE_STa3SHI1sEeH&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&p_r_p_calendarBookingId=2968086&p_r_p_calendarPath=%2Fhtml%2Fsuite%2Fdisplays%2Fdetail.jsp"
    asyncio.run(debug_majadahonda_event(url))
