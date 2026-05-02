from madrid_es_common import get_events_for_venue

def scrape_dulce_chacon():
    """
    Scrapes events for Espacio de Igualdad Dulce Chacón. Villaverde
    """
    return get_events_for_venue(r"Dulce\s*Chac")
