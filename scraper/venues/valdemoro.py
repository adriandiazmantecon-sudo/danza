from madrid_org_red_common import scrape_red_municipios

async def scrape():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/valdemoro.html",
        venue_name="Teatro Municipal Juan Prado",
        municipality="Valdemoro",
        venue_header_text="Teatro Municipal Juan Prado"
    )
