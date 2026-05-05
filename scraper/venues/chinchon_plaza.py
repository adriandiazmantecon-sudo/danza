import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from madrid_org_red_common import scrape_red_municipios

async def scrape_chinchon_plaza():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/chinchon.html",
        venue_name="Plaza Mayor",
        municipality="Chinchón",
        venue_header_text="PLAZA MAYOR"
    )

if __name__ == "__main__":
    res = asyncio.run(scrape_chinchon_plaza())
    for e in res:
        print(f"Result: {e.title} | Company: {e.company} | Date: {e.sessions[0].date}")
