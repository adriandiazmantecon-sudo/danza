from madrid_org_red_common import scrape_red_municipios

async def scrape():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/sanmartinvega.html",
        venue_name="Centro Cívico Cultural",
        municipality="San Martín de la Vega",
        venue_header_text="Centro Cívico Cultural"
    )
