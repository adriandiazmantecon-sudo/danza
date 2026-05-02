from madrid_es_common import get_events_for_venue

def scrape_vallecas_teatro():
    """
    Scrapes events for Teatro Municipal de Vallecas
    """
    return get_events_for_venue(r"Teatro Municipal de Vallecas")
