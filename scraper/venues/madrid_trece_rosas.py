from madrid_es_common import get_events_for_venue

def scrape_trece_rosas():
    """
    Scrapes events for Auditorio Municipal Las Trece Rosas
    """
    return get_events_for_venue(r"Trece Rosas")
