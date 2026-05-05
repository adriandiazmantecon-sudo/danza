import asyncio
import sys
import os

# Ensure the models and common logic are reachable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from madrid_org_red_common import scrape_red_municipios

async def scrape_ciempozuelos():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/ciempozuelos.html",
        venue_name="Sala Multifuncional de Ciempozuelos",
        municipality="Ciempozuelos"
    )

if __name__ == "__main__":
    res = asyncio.run(scrape_ciempozuelos())
    for e in res:
        print(f"Result: {e.title} | Company: {e.company} | Sessions: {len(e.sessions)} | Date: {e.sessions[0].date} {e.sessions[0].time}")
