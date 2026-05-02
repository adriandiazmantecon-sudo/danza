from madrid_es_common import get_events_for_venue

def scrape_el_pozo():
    """
    Scrapes events for Centro Cultural El Pozo del tío Raimundo
    """
    return get_events_for_venue(r"El Pozo")
