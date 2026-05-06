from madrid_org_red_common import scrape_red_municipios

async def scrape():
    return await scrape_red_municipios(
        url="https://www.madrid.org/clas_artes/red/torresalameda.html",
        venue_name="Auditorio Torres de la Alameda (Las Amapolas)",
        municipality="Torres de la Alameda",
        venue_header_text="AUDITORIO TORRES DE LA ALAMEDA (LAS AMAPOLAS)"
    )
