import asyncio
from playwright.async_api import async_playwright

async def test_discovery():
    base_url = "https://cultura.pozuelodealarcon.org/agenda"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print(f"Navigating to {base_url}...")
        await page.goto(base_url, wait_until="networkidle")
        
        # Wait a bit for potential JS loading
        await asyncio.sleep(2)
        
        # Save HTML for analysis
        html = await page.content()
        with open("pozuelo_list_debug.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        # Try to find event links
        # Looking at the original scraper, it expects: a.card__link
        links = await page.query_selector_all("a.card__link")
        print(f"Found {len(links)} candidate links using 'a.card__link'.")
        for link in links:
            href = await link.get_attribute("href")
            text = await link.inner_text()
            print(f"Link: {text.strip()} | Href: {href}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_discovery())
