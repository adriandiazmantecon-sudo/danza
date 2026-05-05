import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from madrid_org_red_common import scrape_red_municipios

async def scrape_boadilla_auditorio():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/boadilla.html",
        venue_name="Auditorio Municipal",
        municipality="Boadilla del Monte",
        venue_header_text="AUDITORIO MUNICIPAL"
    )

if __name__ == "__main__":
    res = asyncio.run(scrape_boadilla_auditorio())
    for e in res:
        print(f"Result: {e.title} | Company: {e.company} | Date: {e.sessions[0].date}")
