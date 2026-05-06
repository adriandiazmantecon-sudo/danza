import asyncio
import sys
import os

# Ensure the models and common logic are reachable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from madrid_org_red_common import scrape_red_municipios

async def scrape_parla_dulce_chacon():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/parla.html",
        venue_name="Teatro Dulce Chacón",
        municipality="Parla",
        venue_header_text="Teatro Dulce Chacón"
    )

if __name__ == "__main__":
    res = asyncio.run(scrape_parla_dulce_chacon())
    for e in res:
        print(f"Result: {e.title} | Company: {e.company} | Sessions: {len(e.sessions)}")
