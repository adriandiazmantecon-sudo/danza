from madrid_es_common import get_events_for_venue

def scrape_maris_stella():
    """
    Scrapes events for Centro de Educación Ambiental y Cultural Maris Stella
    """
    return get_events_for_venue(r"Maris Stella")
