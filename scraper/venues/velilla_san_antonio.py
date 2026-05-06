from madrid_org_red_common import scrape_red_municipios

async def scrape():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/velilla.html",
        venue_name="Centro Cultural Auditorio Mariana Pineda",
        municipality="Velilla de San Antonio",
        venue_header_text="Centro Cultural Auditorio Mariana Pineda"
    )
