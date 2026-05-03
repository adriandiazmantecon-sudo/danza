import json
import os
import sys
import argparse
import io

# Force UTF-8 encoding for Windows consoles
if sys.platform == "win32":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

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
from venues.boadilla import scrape_boadilla
from venues.madrid_conde_duque import scrape_conde_duque
from venues.madrid_el_pozo import scrape_el_pozo
from venues.madrid_maris_stella import scrape_maris_stella
from venues.madrid_el_torito import scrape_el_torito
from venues.madrid_casa_de_vacas import scrape_casa_de_vacas
from venues.madrid_ciudad_pegaso import scrape_ciudad_pegaso
from venues.madrid_vallecas_teatro import scrape_vallecas_teatro
from venues.madrid_las_californias import scrape_las_californias
from venues.madrid_trece_rosas import scrape_trece_rosas
from venues.madrid_museo_historia import scrape_museo_historia
from venues.madrid_ivan_de_vargas import scrape_ivan_de_vargas
from venues.madrid_dulce_chacon import scrape_dulce_chacon
from venues.escalera_jacob import scrape_escalera_jacob

def save_json(path, data):
    """Saves JSON data atomically using a temporary file."""
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, cls=EnhancedJSONEncoder, ensure_ascii=False, indent=2)
    if os.path.exists(path):
        os.remove(path)
    os.rename(tmp_path, path)

def main():
    parser = argparse.ArgumentParser(description='Madrid Dance Events Scraper')
    parser.add_argument('--venue', help='Specific venue to scrape (comma separated for multiple: real,canal,matadero,...)')
    args = parser.parse_args()

    print("Starting Madrid Dance Events Scraper...")
    
    # Map of keys to their display names and scraper functions
    venue_map = {
        'real': ('Teatro Real', scrape_teatro_real),
        'canal': ('Teatros del Canal', scrape_teatros_del_canal),
        'matadero': ('Centro Danza Matadero', scrape_matadero),
        'zarzuela': ('Teatro de la Zarzuela', scrape_zarzuela),
        'gran_via': ('Teatro Gran Vía', scrape_teatro_gran_via),
        'real_coliseo': ('Real Coliseo Carlos III', scrape_real_coliseo),
        'paco_rabal': ('Centro Cultural Paco Rabal', scrape_paco_rabal),
        'majadahonda': ('Casa de la Culture Carmen Conde', scrape_majadahonda),
        'getafe': ('Teatro Federico García Lorca', scrape_getafe),
        'mostoles': ('Teatro del Bosque', scrape_mostoles),
        'boadilla': ('Boadilla del Monte', scrape_boadilla),
        'conde_duque': ('Centro de Cultura Contemporánea CondeDuque', scrape_conde_duque),
        'el_pozo': ('CC El Pozo del Tío Raimundo', scrape_el_pozo),
        'maris_stella': ('CEAC Maris Stella', scrape_maris_stella),
        'el_torito': ('CC El Torito', scrape_el_torito),
        'casa_de_vacas': ('CC Casa de Vacas', scrape_casa_de_vacas),
        'ciudad_pegaso': ('CC Ciudad Pegaso', scrape_ciudad_pegaso),
        'vallecas_teatro': ('Teatro Municipal de Vallecas', scrape_vallecas_teatro),
        'las_californias': ('CC Las Californias', scrape_las_californias),
        'trece_rosas': ('Auditorio Las Trece Rosas', scrape_trece_rosas),
        'museo_historia': ('Museo de Historia', scrape_museo_historia),
        'ivan_de_vargas': ('Biblioteca Iván de Vargas', scrape_ivan_de_vargas),
        'dulce_chacon': ('Espacio Igualdad Dulce Chacón', scrape_dulce_chacon),
        'escalera_jacob': ('La Escalera de Jacob', scrape_escalera_jacob)
    }

    venues_to_scrape = []
    if args.venue:
        requested_venues = [v.strip() for v in args.venue.split(',')]
        for rv in requested_venues:
            if rv in venue_map:
                venues_to_scrape.append((rv, venue_map[rv]))
            else:
                print(f"Warning: Venue '{rv}' not recognized. Available: {', '.join(venue_map.keys())}")
    else:
        for vid, info in venue_map.items():
            venues_to_scrape.append((vid, info))

    # Output directories
    base_data_dir = os.path.join(os.path.dirname(__file__), "..", "web", "public", "data")
    venues_dir = os.path.join(base_data_dir, "venues")
    os.makedirs(venues_dir, exist_ok=True)
    
    output_path = os.path.join(base_data_dir, "events.json")
    
    # 1. Load existing master database robustly
    master_dict = {}
    if os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing_events = json.load(f)
                for e in existing_events:
                    url = e.get('url')
                    if url:
                        master_dict[url] = e
            print(f"Loaded {len(master_dict)} existing events from master database.")
        except Exception as e:
            print(f"CRITICAL ERROR: Could not load master database at {output_path}: {e}")
            print("Aborting to prevent data loss. Please check the file.")
            return

    # 2. Run scrapers and save individual venue files
    for venue_id, (venue_name, scraper_func) in venues_to_scrape:
        print(f"\nScraping {venue_name}...")
        try:
            if inspect.iscoroutinefunction(scraper_func):
                results = asyncio.run(scraper_func())
            else:
                results = scraper_func()
            
            if results is not None: # Even if empty list, we save it (it means the venue has 0 CURRENT events)
                venue_output_path = os.path.join(venues_dir, f"{venue_id}.json")
                results_dicts = [e.to_dict() if hasattr(e, "to_dict") else e for e in results]
                save_json(venue_output_path, results_dicts)
                print(f"Saved {len(results)} current events to venues/{venue_id}.json")
                
                # Update master dict (Never Delete Policy)
                for event_dict in results_dicts:
                    url = event_dict.get('url')
                    if url:
                        # Overwrite with newer data if URL matches
                        master_dict[url] = event_dict
                
                # Save master after each successful scrape to ensure progress is kept
                save_json(output_path, list(master_dict.values()))
                print(f"Master database updated. Total events: {len(master_dict)}")
            else:
                print(f"Warning: Scraper for {venue_name} returned None. Skipping update for this venue.")
                
        except Exception as e:
            print(f"Error scraping {venue_name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\nScraping cycle completed. Total events in database: {len(master_dict)}")

if __name__ == "__main__":
    main()

