import asyncio
from venues.matadero import scrape_matadero

async def test():
    events = await scrape_matadero()
    for e in events:
        print(f"Title: {e.title}")
        print(f"Image: {e.image_url}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test())
