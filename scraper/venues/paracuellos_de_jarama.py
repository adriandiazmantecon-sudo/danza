import asyncio
import sys
import os

# Ensure the models and common logic are reachable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from madrid_org_red_common import scrape_red_municipios

async def scrape_paracuellos():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/paracuellos.html",
        venue_name="Centro Cultural de Paracuellos",
        municipality="Paracuellos de Jarama"
    )

if __name__ == "__main__":
    res = asyncio.run(scrape_paracuellos())
    for e in res:
        print(f"Result: {e.title} | Company: {e.company} | Sessions: {len(e.sessions)}")
