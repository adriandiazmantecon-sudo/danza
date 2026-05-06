from madrid_org_red_common import scrape_red_municipios

async def scrape():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/torrelodones.html",
        venue_name="Teatro Bulevar",
        municipality="Torrelodones",
        venue_header_text="Teatro Bulevar"
    )
