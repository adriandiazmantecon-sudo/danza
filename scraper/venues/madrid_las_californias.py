from madrid_es_common import get_events_for_venue

def scrape_las_californias():
    """
    Scrapes events for Centro Cultural Las Californias (Retiro)
    """
    return get_events_for_venue(r"Las Californias")
