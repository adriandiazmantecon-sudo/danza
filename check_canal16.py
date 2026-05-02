import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({'User-Agent': 'Mozilla/5.0'})
        await page.goto("https://www.teatroscanal.com/entradas/danza-madrid/", timeout=60000)
        await page.wait_for_timeout(3000)
        
        events = await page.evaluate('''() => {
            let results = [];
            document.querySelectorAll('.div-show2').forEach(el => {
                let textContent = el.innerText;
                let lines = textContent.split('\\n').map(l => l.trim()).filter(l => l);
                let title = lines.length > 1 ? lines[1] : (lines.length > 0 ? lines[0] : "Unknown");
                let company = lines.length > 0 ? lines[0] : "Unknown";
                
                let a = el.querySelector('a');
                let url = a ? a.href : "";
                
                let img = el.querySelector('img');
                let imgUrl = img ? img.src : "";
                
                results.push({title, company, url, imgUrl});
            });
            return results;
        }''')
        
        print("Events extracted:")
        for e in events:
            print(e)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
