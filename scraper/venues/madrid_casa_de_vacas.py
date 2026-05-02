from madrid_es_common import get_events_for_venue

def scrape_casa_de_vacas():
    """
    Scrapes events for Centro Cultural Casa de Vacas (Retiro)
    """
    return get_events_for_venue(r"Casa de Vacas")
