from madrid_es_common import get_events_for_venue

def scrape_ivan_de_vargas():
    """
    Scrapes events for Biblioteca Pública Municipal Iván de Vargas
    """
    return get_events_for_venue(r"Iván de Vargas")
