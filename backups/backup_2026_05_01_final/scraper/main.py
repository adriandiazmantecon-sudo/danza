import json
import os
import sys
import argparse

# Ensure the venues package is reachable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import EnhancedJSONEncoder
from venues.teatro_real import scrape_teatro_real
from venues.teatros_del_canal import scrape_teatros_del_canal

def main():
    parser = argparse.ArgumentParser(description='Madrid Dance Events Scraper')
    parser.add_argument('--venue', choices=['real', 'canal'], help='Specific venue to scrape')
    args = parser.parse_args()

    print("Starting Madrid Dance Events Scraper...")
    all_events = []
    
    # If a specific venue is requested, only scrape that one
    # Otherwise, scrape all
    venues_to_scrape = []
    if args.venue == 'real':
        venues_to_scrape = [('Teatro Real', scrape_teatro_real)]
    elif args.venue == 'canal':
        venues_to_scrape = [('Teatros del Canal', scrape_teatros_del_canal)]
    else:
        venues_to_scrape = [
            ('Teatro Real', scrape_teatro_real),
            ('Teatros del Canal', scrape_teatros_del_canal)
        ]

    # Load existing events to merge if scraping selectively
    output_dir = os.path.join(os.path.dirname(__file__), "..", "web", "src", "data")
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
