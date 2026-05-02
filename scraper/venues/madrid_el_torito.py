from madrid_es_common import get_events_for_venue

def scrape_el_torito():
    """
    Scrapes events for Centro Cultural el Torito (Moratalaz)
    """
    return get_events_for_venue(r"Torito")
