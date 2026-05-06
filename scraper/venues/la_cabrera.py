import asyncio
import sys
import os

# Ensure the models and common logic are reachable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from madrid_org_red_common import scrape_red_municipios

async def scrape_la_cabrera():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/lacabrera.html",
        venue_name="Centro Cultural de Humanidades Sierra Norte",
        municipality="La Cabrera"
    )

if __name__ == "__main__":
    res = asyncio.run(scrape_la_cabrera())
    for e in res:
        print(f"Result: {e.title} | Company: {e.company} | Sessions: {len(e.sessions)}")
