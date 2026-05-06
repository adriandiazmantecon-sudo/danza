from madrid_org_red_common import scrape_red_municipios

async def scrape():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/sansebastian.html",
        venue_name="Teatro Municipal Adolfo Marsillach",
        municipality="San Sebastián de los Reyes",
        venue_header_text="Teatro Municipal Adolfo Marsillach"
    )
