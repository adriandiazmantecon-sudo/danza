import asyncio
import sys
import os

# Ensure the models and common logic are reachable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from madrid_org_red_common import scrape_red_municipios

async def scrape_el_alamo():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/elalamo.html",
        venue_name="Centro Sociocultural El Álamo",
        municipality="El Álamo"
    )

if __name__ == "__main__":
    res = asyncio.run(scrape_el_alamo())
    for e in res:
        print(f"Result: {e.title} | Company: {e.company} | Sessions: {len(e.sessions)}")
