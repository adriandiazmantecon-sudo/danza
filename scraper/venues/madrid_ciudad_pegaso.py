from madrid_es_common import get_events_for_venue

def scrape_ciudad_pegaso():
    """
    Scrapes events for Centro Cultural Ciudad Pegaso (San Blas - Canillejas)
    """
    return get_events_for_venue(r"Ciudad Pegaso")
