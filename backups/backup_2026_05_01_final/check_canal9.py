import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({'User-Agent': 'Mozilla/5.0'})
        
        # Check all possible sections
        sections = [
            "https://www.teatroscanal.com/entradas/flamenco-madrid/",
            "https://www.teatroscanal.com/entradas/festivales-madrid/",
            "https://www.teatroscanal.com/entradas/performance-madrid/",
            "https://www.teatroscanal.com/entradas/teatro-madrid/"
        ]
        
        for url in sections:
            print(f"Checking {url}")
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(2000)
            body_text = await page.evaluate('document.body.innerText')
            
            # just print lines containing "COMPRAR" and the lines above it to see events
            lines = body_text.split('\\n')
            for i, line in enumerate(lines):
                if 'COMPRAR' in line:
                    start = max(0, i-5)
                    print(f"--- Event near line {i}:")
                    for j in range(start, i):
                        if lines[j].strip():
                            print("  ", lines[j])
            print("="*40)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
