import asyncio
from playwright.async_api import async_playwright

async def check_encoding():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = "https://www.comunidad.madrid/actividades/2026/danza-aurunca-sabado-9"
        response = await page.goto(url)
        content = await page.content()
        print(f"Content contains 'Compa': {'Compa' in content}")
        # Search for the string that should be 'Compañía'
        import re
        match = re.search(r'Compa.{1,3}a', content)
        if match:
            found = match.group(0)
            print(f"Found string: {found}")
            print(f"Hex: {found.encode('utf-8', 'replace').hex()}")
            for char in found:
                print(f"Char: {char} | Code: {ord(char)}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_encoding())
