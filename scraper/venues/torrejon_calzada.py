from madrid_org_red_common import scrape_red_municipios

async def scrape():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/torrejondelacalzada.html",
        venue_name="Casa de Cultura",
        municipality="Torrejón de la Calzada",
        venue_header_text="Casa de Cultura"
    )
