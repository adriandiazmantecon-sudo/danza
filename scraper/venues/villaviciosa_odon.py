from madrid_org_red_common import scrape_red_municipios

async def scrape():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/villaviciosa.html",
        venue_name="Coliseo de la Cultura (Auditorio Teresa Berganza)",
        municipality="Villaviciosa de Odón",
        venue_header_text="Coliseo de la Cultura (Auditorio Teresa Berganza)"
    )
