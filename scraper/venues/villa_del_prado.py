from madrid_org_red_common import scrape_red_municipios

async def scrape():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/villadelprado.html",
        venue_name="Centro de Artes de Villa del Prado",
        municipality="Villa del Prado",
        venue_header_text="Centro de Artes de Villa del Prado"
    )
