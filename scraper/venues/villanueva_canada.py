from madrid_org_red_common import scrape_red_municipios

async def scrape():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/villanueva.html",
        venue_name="Centro Cultural La Despernada",
        municipality="Villanueva de la Cañada",
        venue_header_text="Centro Cultural La Despernada"
    )
