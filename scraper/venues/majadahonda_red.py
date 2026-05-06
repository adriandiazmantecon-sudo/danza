import asyncio
import sys
import os

# Ensure the models and common logic are reachable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from madrid_org_red_common import scrape_red_municipios

async def scrape_majadahonda_red():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/majadahonda.html",
        venue_name="Casa de Cultura Carmen Conde",
        municipality="Majadahonda"
    )

if __name__ == "__main__":
    res = asyncio.run(scrape_majadahonda_red())
    for e in res:
        print(f"Result: {e.title} | Company: {e.company} | Sessions: {len(e.sessions)}")
