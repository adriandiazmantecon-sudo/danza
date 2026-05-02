import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Searching all entries for dance keywords...")
        await page.goto('https://www.teatroscanal.com/entradas/', timeout=60000)
        await page.wait_for_timeout(4000)
        
        events = await page.evaluate('''() => {
            let results = [];
            document.querySelectorAll('.div-show2').forEach(el => {
                results.push({
                    text: el.innerText,
                    url: el.querySelector('a') ? el.querySelector('a').href : ''
                });
            });
            return results;
        }''')
        
        found = 0
        for e in events:
            text = e['text'].lower()
            if any(k in text for k in ['danza', 'baile', 'ballet', 'flamenco']):
                found += 1
                print(f"MATCH: {e['text'].strip().replace('\\n', ' | ')}")
        
        print(f"Total entries checked: {len(events)}")
        print(f"Dance-related matches found: {found}")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
