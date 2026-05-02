from madrid_es_common import get_events_for_venue

def scrape_conde_duque():
    """
    Scrapes events for Centro de Cultura Contemporánea CondeDuque
    """
    return get_events_for_venue(r"Conde\s*Duque")
