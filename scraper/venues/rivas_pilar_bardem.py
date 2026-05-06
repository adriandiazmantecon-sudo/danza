from madrid_org_red_common import scrape_red_municipios

async def scrape():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/rivas.html",
        venue_name="Auditorio Municipal Pilar Bardem",
        municipality="Rivas-Vaciamadrid",
        venue_header_text="Auditorio Municipal Pilar Bardem"
    )
