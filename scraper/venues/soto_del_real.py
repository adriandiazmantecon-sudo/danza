from madrid_org_red_common import scrape_red_municipios

async def scrape():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/sotoreal.html",
        venue_name="Centro Cultural",
        municipality="Soto del Real",
        venue_header_text="Centro Cultural"
    )
