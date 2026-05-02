import json
import os
import sys
import argparse

# Ensure the venues package is reachable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import EnhancedJSONEncoder
import asyncio
import inspect
from venues.teatro_real import scrape_teatro_real
from venues.teatros_del_canal import scrape_teatros_del_canal
from venues.matadero import scrape_matadero
from venues.zarzuela import scrape_zarzuela
from venues.teatro_gran_via import scrape_teatro_gran_via
from venues.real_coliseo import scrape_real_coliseo
from venues.paco_rabal import scrape_paco_rabal
from venues.majadahonda import scrape_majadahonda
from venues.getafe import scrape_getafe
from venues.mostoles import scrape_mostoles

def main():
    parser = argparse.ArgumentParser(description='Madrid Dance Events Scraper')
    parser.add_argument('--venue', help='Specific venue to scrape (comma separated for multiple: real,canal,matadero,...)')
    args = parser.parse_args()

    print("Starting Madrid Dance Events Scraper...")
    all_events = []
    
    # Map of keys to their display names and scraper functions
    venue_map = {
        'real': ('Teatro Real', scrape_teatro_real),
        'canal': ('Teatros del Canal', scrape_teatros_del_canal),
        'matadero': ('Centro Danza Matadero', scrape_matadero),
        'zarzuela': ('Teatro de la Zarzuela', scrape_zarzuela),
        'gran_via': ('Teatro Gran Vía', scrape_teatro_gran_via),
        'real_coliseo': ('Real Coliseo Carlos III', scrape_real_coliseo),
        'paco_rabal': ('Centro Cultural Paco Rabal', scrape_paco_rabal),
        'majadahonda': ('Casa de la Cultura Carmen Conde', scrape_majadahonda),
        'getafe': ('Teatro Federico García Lorca', scrape_getafe),
        'mostoles': ('Teatro del Bosque', scrape_mostoles)
    }

    venues_to_scrape = []
    if args.venue:
        requested_venues = [v.strip() for v in args.venue.split(',')]
        for rv in requested_venues:
            if rv in venue_map:
                venues_to_scrape.append(venue_map[rv])
            else:
                print(f"Warning: Venue '{rv}' not recognized. Available: {', '.join(venue_map.keys())}")
    else:
        venues_to_scrape = list(venue_map.values())

    # Output to the web app's data folder (now in public for easier updates)
    output_dir = os.path.join(os.path.dirname(__file__), "..", "web", "public", "data")
    output_path = os.path.join(output_dir, "events.json")
    
    existing_events = []
    if os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing_events = json.load(f)
        except:
            pass

    new_events_list = []
    for name, scraper_func in venues_to_scrape:
        try:
            if inspect.iscoroutinefunction(scraper_func):
                results = asyncio.run(scraper_func())
            else:
                results = scraper_func()
            new_events_list.extend(results)
        except Exception as e:
            print(f"Error scraping {name}: {e}")

    # Merge logic: preserve existing events (past events) while updating with new data
    # We use URL as the unique identifier for events
    new_events_dict = {e.url: e for e in new_events_list}
    
    # Start with existing events
    merged_dict = {}
    for e in existing_events:
        url = e.get('url')
        if url:
            merged_dict[url] = e

    # Update with new events (this replaces old data with fresh data for active events)
    for url, event in new_events_dict.items():
        merged_dict[url] = event.to_dict() if hasattr(event, "to_dict") else event

    all_events = list(merged_dict.values())

    # Output to the web app's data folder
    os.makedirs(output_dir, exist_ok=True)
    
    if all_events:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_events, f, cls=EnhancedJSONEncoder, ensure_ascii=False, indent=2)
        print(f"Successfully exported {len(all_events)} events to {output_path}")
    else:
        print("No events scraped. Kept the existing events.json.")

if __name__ == "__main__":
    main()
