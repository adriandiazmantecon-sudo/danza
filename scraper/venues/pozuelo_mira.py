from madrid_org_red_common import scrape_red_municipios

async def scrape():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/pozuelo.html",
        venue_name="MIRA Teatro",
        municipality="Pozuelo de Alarcón",
        venue_header_text="MIRA Teatro"
    )
