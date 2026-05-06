import asyncio
import sys
import os

# Ensure the models and common logic are reachable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from madrid_org_red_common import scrape_red_municipios

async def scrape_las_rozas_perez_riva():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/lasrozas.html",
        venue_name="Teatro Centro Cultural Pérez de la Riva",
        municipality="Las Rozas de Madrid",
        venue_header_text="Teatro Centro Cultural Pérez de la Riva"
    )

if __name__ == "__main__":
    res = asyncio.run(scrape_las_rozas_perez_riva())
    for e in res:
        print(f"Result: {e.title} | Company: {e.company} | Sessions: {len(e.sessions)}")
