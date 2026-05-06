from madrid_org_red_common import scrape_red_municipios

async def scrape():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/talamanca-de-jarama.html",
        venue_name="Salón de Actos",
        municipality="Talamanca de Jarama",
        venue_header_text="Salón de Actos"
    )
