from madrid_org_red_common import scrape_red_municipios

async def scrape():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/villanuevapardillo.html",
        venue_name="Auditorio Municipal Sebastián Cestero",
        municipality="Villanueva del Pardillo",
        venue_header_text="Auditorio Municipal Sebastián Cestero"
    )
