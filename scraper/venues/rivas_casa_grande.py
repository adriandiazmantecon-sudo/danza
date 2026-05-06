from madrid_org_red_common import scrape_red_municipios

async def scrape():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/rivas.html",
        venue_name="Centro Juvenil La Casa + Grande",
        municipality="Rivas-Vaciamadrid",
        venue_header_text="Centro Juvenil La Casa + Grande"
    )
