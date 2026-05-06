from madrid_org_red_common import scrape_red_municipios

async def scrape():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/sanmartindevaldeiglesias.html",
        venue_name="Teatro Municipal Cine Teatro",
        municipality="San Martín de Valdeiglesias",
        venue_header_text="Teatro Municipal Cine Teatro"
    )
