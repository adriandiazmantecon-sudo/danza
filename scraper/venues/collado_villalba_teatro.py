import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from madrid_org_red_common import scrape_red_municipios

async def scrape_collado_villalba_teatro():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/colladovillalba.html",
        venue_name="Teatro Casa de la Cultura",
        municipality="Collado Villalba",
        venue_header_text="TEATRO CASA DE LA CULTURA"
    )

if __name__ == "__main__":
    res = asyncio.run(scrape_collado_villalba_teatro())
    for e in res:
        print(f"Result: {e.title} | Company: {e.company} | Date: {e.sessions[0].date}")
