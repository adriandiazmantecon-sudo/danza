import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from madrid_org_red_common import scrape_red_municipios

async def scrape_collado_mediano():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/colladomediano.html",
        venue_name="Teatro Municipal Carlos Saura",
        municipality="Collado Mediano"
    )

if __name__ == "__main__":
    res = asyncio.run(scrape_collado_mediano())
    for e in res:
        print(f"Result: {e.title} | Company: {e.company} | Date: {e.sessions[0].date}")
