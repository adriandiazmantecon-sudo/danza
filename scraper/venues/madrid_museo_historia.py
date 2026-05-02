from madrid_es_common import get_events_for_venue

def scrape_museo_historia():
    """
    Scrapes events for Museo de Historia de Madrid
    """
    return get_events_for_venue(r"Museo de Historia")
