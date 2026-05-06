from madrid_org_red_common import scrape_red_municipios

async def scrape():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/serranillos.html",
        venue_name="Centro Cultural",
        municipality="Serranillos del Valle",
        venue_header_text="Centro Cultural"
    )
