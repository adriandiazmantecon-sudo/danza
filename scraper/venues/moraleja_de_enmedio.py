import asyncio
import sys
import os

# Ensure the models and common logic are reachable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from madrid_org_red_common import scrape_red_municipios

async def scrape_moraleja():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/moraleja.html",
        venue_name="Centro Cultural El Cerro",
        municipality="Moraleja de Enmedio"
    )

if __name__ == "__main__":
    res = asyncio.run(scrape_moraleja())
    for e in res:
        print(f"Result: {e.title} | Company: {e.company} | Sessions: {len(e.sessions)}")
