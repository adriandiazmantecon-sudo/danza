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
from venues.madrid_la_usina import scrape_la_usina
from venues.madrid_cuarta_pared import scrape_cuarta_pared
from venues.corral_usera import scrape_corral_usera
from venues.fuenlabrada_tomas_valiente import scrape_tomas_y_valiente
from venues.fuenlabrada_josep_carreras import scrape_josep_carreras
from venues.replika_teatro import scrape_replika_teatro
from venues.dt_espacio_escenico import scrape_dt_espacio_escenico
from venues.teatro_elias_ahuja import scrape_teatro_elias_ahuja
from venues.auditorio_placido_domingo import scrape_auditorio_placido_domingo
from venues.ciempozuelos import scrape_ciempozuelos
from venues.ajalvir import scrape_ajalvir
from venues.alcala import scrape_alcala
from venues.alcobendas import scrape_alcobendas
from venues.alcorcon_buero_vallejo import scrape_alcorcon_buero
from venues.alcorcon_vinagrande import scrape_alcorcon_vina
from venues.algete import scrape_algete
from venues.alpedrete import scrape_alpedrete
from venues.aranjuez import scrape_aranjuez
from venues.arganda import scrape_arganda
from venues.arroyomolinos import scrape_arroyomolinos
from venues.becerril import scrape_becerril
from venues.boadilla_teatro import scrape_boadilla_teatro
from venues.boadilla_auditorio import scrape_boadilla_auditorio
from venues.buitrago import scrape_buitrago
from venues.camarma import scrape_camarma
from venues.cenicientos import scrape_cenicientos
from venues.chapineria import scrape_chapineria
from venues.chinchon_lope import scrape_chinchon_lope
from venues.chinchon_plaza import scrape_chinchon_plaza
from venues.cobena import scrape_cobena
from venues.collado_mediano import scrape_collado_mediano
from venues.collado_villalba_teatro import scrape_collado_villalba_teatro
from venues.collado_villalba_jardines import scrape_collado_villalba_jardines
from venues.colmenar_arroyo import scrape_colmenar_arroyo
from venues.colmenar_oreja import scrape_colmenar_oreja
from venues.colmenar_viejo import scrape_colmenar_viejo
from venues.colmenarejo import scrape_colmenarejo
from venues.coslada import scrape_coslada
from venues.cubas_de_la_sagra import scrape_cubas
from venues.el_alamo import scrape_el_alamo
from venues.fuenlabrada_nuria_espert import scrape_nuria_espert
from venues.fuenlabrada_maribel_verdu import scrape_maribel_verdu
from venues.galapagar import scrape_galapagar
from venues.getafe_espacio_mercado import scrape_getafe_espacio_mercado
from venues.grinon import scrape_grinon
from venues.guadarrama import scrape_guadarrama
from venues.hoyo_de_manzanares import scrape_hoyo_manzanares
from venues.la_cabrera import scrape_la_cabrera
from venues.las_rozas_perez_de_la_riva import scrape_las_rozas_perez_riva
from venues.las_rozas_joaquin_rodrigo import scrape_las_rozas_joaquin_rodrigo
from venues.leganes_jose_monleon import scrape_leganes_monleon
from venues.madrid_pilar_miro import scrape_pilar_miro
from venues.manzanares_el_real import scrape_manzanares_real
from venues.majadahonda_red import scrape_majadahonda_red
from venues.meco import scrape_meco
from venues.mejorada_del_campo import scrape_mejorada
from venues.moraleja_de_enmedio import scrape_moraleja
from venues.moralzarzal import scrape_moralzarzal
from venues.morata_de_tajuna import scrape_morata
from venues.mostoles_el_soto import scrape_mostoles_el_soto
from venues.navalcarnero import scrape_navalcarnero
from venues.paracuellos_de_jarama import scrape_paracuellos
from venues.parla_jaime_salom import scrape_parla_jaime_salom
from venues.parla_dulce_chacon import scrape_parla_dulce_chacon
from venues.pedrezuela import scrape_pedrezuela
from venues.pinto import scrape_pinto
from venues.pozuelo_mira import scrape as scrape_pozuelo_mira
from venues.rivas_pilar_bardem import scrape as scrape_rivas_pilar_bardem
from venues.rivas_casa_grande import scrape as scrape_rivas_casa_grande
from venues.san_agustin_guadalix import scrape as scrape_san_agustin_guadalix
from venues.san_fernando_henares import scrape as scrape_san_fernando_henares
from venues.san_lorenzo_escorial import scrape as scrape_san_lorenzo_escorial
from venues.san_martin_vega import scrape as scrape_san_martin_vega
from venues.san_martin_valdeiglesias import scrape as scrape_san_martin_valdeiglesias
from venues.san_sebastian_reyes import scrape as scrape_san_sebastian_reyes
from venues.serranillos_del_valle import scrape as scrape_serranillos_del_valle
from venues.soto_del_real import scrape as scrape_soto_del_real
from venues.talamanca_jarama import scrape as scrape_talamanca_jarama
from venues.torrejon_rodero import scrape as scrape_torrejon_rodero
from venues.torrejon_calzada import scrape as scrape_torrejon_calzada
from venues.torrelaguna import scrape as scrape_torrelaguna
from venues.torrelodones import scrape as scrape_torrelodones
from venues.torres_alameda import scrape as scrape_torres_alameda
from venues.tres_cantos import scrape as scrape_tres_cantos
from venues.valdemorillo import scrape as scrape_valdemorillo
from venues.valdemoro import scrape as scrape_valdemoro
from venues.valdeolmos_alalpardo import scrape as scrape_valdeolmos_alalpardo
from venues.velilla_san_antonio import scrape as scrape_velilla_san_antonio
from venues.villa_del_prado import scrape as scrape_villa_del_prado
from venues.villanueva_canada import scrape as scrape_villanueva_canada
from venues.villanueva_pardillo import scrape as scrape_villanueva_pardillo
from venues.villaviciosa_odon import scrape as scrape_villaviciosa_odon

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
        'escalera_jacob': ('La Escalera de Jacob', scrape_escalera_jacob),
        'la_usina': ('Teatro La Usina', scrape_la_usina),
        'cuarta_pared': ('Sala Cuarta Pared', scrape_cuarta_pared),
        'corral_usera': ('El Corral de Usera', scrape_corral_usera),
        'fuenlabrada_tomas_valiente': ('Teatro Tomás y Valiente', scrape_tomas_y_valiente),
        'fuenlabrada_josep_carreras': ('Teatro Josep Carreras', scrape_josep_carreras),
        'replika': ('Réplika Teatro', scrape_replika_teatro),
        'dt_espacio': ('DT Espacio Escénico', scrape_dt_espacio_escenico),
        'ahuja': ('Teatro Elías Ahuja', scrape_teatro_elias_ahuja),
        'placido': ('Auditorio Plácido Domingo', scrape_auditorio_placido_domingo),
        'ciempozuelos': ('Sala Multifuncional de Ciempozuelos', scrape_ciempozuelos),
        'ajalvir': ('Ajalvir - Salón Municipal de Actos', scrape_ajalvir),
        'alcala': ('Alcalá de Henares - Teatro Salón Cervantes', scrape_alcala),
        'alcobendas': ('Alcobendas - Teatro Auditorio Ciudad de Alcobendas', scrape_alcobendas),
        'alcorcon_buero': ('Alcorcón - Teatro municipal Buero Vallejo', scrape_alcorcon_buero),
        'alcorcon_vina': ('Alcorcón - Centro Cultural Viñagrande', scrape_alcorcon_vina),
        'algete': ('Algete - Auditorio Joan Manuel Serrat', scrape_algete),
        'alpedrete': ('Alpedrete - Centro Cultural Alpedrete', scrape_alpedrete),
        'aranjuez': ('Aranjuez - Auditorio Joaquín Rodrigo', scrape_aranjuez),
        'arganda': ('Arganda del Rey - Auditorio Montserrat Caballé', scrape_arganda),
        'arroyomolinos': ('Arroyomolinos - Auditorium del centro de las artes', scrape_arroyomolinos),
        'becerril': ('Becerril de la Sierra - Sala Real', scrape_becerril),
        'boadilla_teatro': ('Boadilla del Monte - Teatro Municipal', scrape_boadilla_teatro),
        'boadilla_auditorio': ('Boadilla del Monte - Auditorio Municipal', scrape_boadilla_auditorio),
        'buitrago': ('Buitrago del Lozoya - Casa de la Cultura', scrape_buitrago),
        'camarma': ('Camarma de Esteruelas - Auditorio Municipal', scrape_camarma),
        'cenicientos': ('Cenicientos - CC Carmen de la Rocha', scrape_cenicientos),
        'chapineria': ('Chapinería - Auditorio Municipal', scrape_chapineria),
        'chinchon_lope': ('Chinchón - Teatro Lope de Vega', scrape_chinchon_lope),
        'chinchon_plaza': ('Chinchón - Plaza Mayor', scrape_chinchon_plaza),
        'cobena': ('Cobeña - Casa de la Cultura', scrape_cobena),
        'collado_mediano': ('Collado Mediano - Teatro Carlos Saura', scrape_collado_mediano),
        'collado_villalba_teatro': ('Collado Villalba - Teatro Casa de la Cultura', scrape_collado_villalba_teatro),
        'collado_villalba_jardines': ('Collado Villalba - Jardines de Peñalba', scrape_collado_villalba_jardines),
        'colmenar_arroyo': ('Colmenar de Arroyo - Centro El Corralizo', scrape_colmenar_arroyo),
        'colmenar_oreja': ('Colmenar de Oreja - Teatro Diéguez', scrape_colmenar_oreja),
        'colmenar_viejo': ('Colmenar Viejo - Auditorio Villa de Colmenar Viejo', scrape_colmenar_viejo),
        'colmenarejo': ('Colmenarejo - Teatro Municipal', scrape_colmenarejo),
        'coslada': ('Coslada - Teatro Municipal', scrape_coslada),
        'cubas': ('Cubas de la Sagra - CAE', scrape_cubas),
        'el_alamo': ('El Álamo - Centro Sociocultural', scrape_el_alamo),
        'fuenlabrada_nuria': ('Fuenlabrada - Teatro Nuria Espert', scrape_nuria_espert),
        'fuenlabrada_maribel': ('Fuenlabrada - Teatro Maribel Verdú', scrape_maribel_verdu),
        'galapagar': ('Galapagar - Centro Cultural La Pocilla', scrape_galapagar),
        'getafe_mercado': ('Getafe - Espacio Mercado', scrape_getafe_espacio_mercado),
        'grinon': ('Griñón - Centro Cultural', scrape_grinon),
        'guadarrama': ('Guadarrama - Centro Cultural La Torre', scrape_guadarrama),
        'hoyo': ('Hoyo de Manzanares - Teatro Las Cigüeñas', scrape_hoyo_manzanares),
        'la_cabrera': ('La Cabrera - CCH Sierra Norte', scrape_la_cabrera),
        'las_rozas_perez': ('Las Rozas - CC Pérez de la Riva', scrape_las_rozas_perez_riva),
        'las_rozas_joaquin': ('Las Rozas - Auditorio Joaquín Rodrigo', scrape_las_rozas_joaquin_rodrigo),
        'leganes_monleon': ('Leganés - Teatro José Monleón', scrape_leganes_monleon),
        'madrid_pilar': ('Madrid - CC Pilar Miró', scrape_pilar_miro),
        'manzanares_real': ('Manzanares el Real - Sala El Rodaje', scrape_manzanares_real),
        'majadahonda_red': ('Majadahonda - Casa de Cultura (Red)', scrape_majadahonda_red),
        'meco': ('Meco - CC Antonio Llorente', scrape_meco),
        'mejorada': ('Mejorada del Campo - Casa de Cultura', scrape_mejorada),
        'moraleja': ('Moraleja de Enmedio - CC El Cerro', scrape_moraleja),
        'moralzarzal': ('Moralzarzal - Teatro Municipal', scrape_moralzarzal),
        'morata': ('Morata de Tajuña - CC Francisco González', scrape_morata),
        'mostoles_soto': ('Móstoles - CSC El Soto', scrape_mostoles_el_soto),
        'navalcarnero': ('Navalcarnero - Teatro Municipal Centro', scrape_navalcarnero),
        'paracuellos': ('Paracuellos de Jarama - Centro Cultural', scrape_paracuellos),
        'parla_jaime': ('Parla - Teatro Jaime Salom', scrape_parla_jaime_salom),
        'parla_dulce': ('Parla - Teatro Dulce Chacón', scrape_parla_dulce_chacon),
        'pedrezuela': ('Pedrezuela - Auditorio Municipal', scrape_pedrezuela),
        'pinto': ('Pinto - Teatro Francisco Rabal', scrape_pinto),
        'pozuelo_mira': ('Pozuelo de Alarcón - MIRA Teatro', scrape_pozuelo_mira),
        'rivas_pilar_bardem': ('Rivas-Vaciamadrid - Auditorio Pilar Bardem', scrape_rivas_pilar_bardem),
        'rivas_casa_grande': ('Rivas-Vaciamadrid - La Casa + Grande', scrape_rivas_casa_grande),
        'san_agustin_guadalix': ('San Agustín de Guadalix - Casa de Cultura', scrape_san_agustin_guadalix),
        'san_fernando_henares': ('San Fernando de Henares - Teatro García Lorca', scrape_san_fernando_henares),
        'san_lorenzo_escorial': ('San Lorenzo de El Escorial - Casa de Cultura', scrape_san_lorenzo_escorial),
        'san_martin_vega': ('San Martín de la Vega - Centro Cívico Cultural', scrape_san_martin_vega),
        'san_martin_valdeiglesias': ('San Martín de Valdeiglesias - Teatro Municipal', scrape_san_martin_valdeiglesias),
        'san_sebastian_reyes': ('San Sebastián de los Reyes - Auditorio Adolfo Marsillach', scrape_san_sebastian_reyes),
        'serranillos': ('Serranillos del Valle - Centro Cultural', scrape_serranillos_del_valle),
        'soto_del_real': ('Soto del Real - Centro Cultural', scrape_soto_del_real),
        'talamanca': ('Talamanca de Jarama - Salón de Actos', scrape_talamanca_jarama),
        'torrejon_rodero': ('Torrejón de Ardoz - Teatro José María Rodero', scrape_torrejon_rodero),
        'torrejon_calzada': ('Torrejón de la Calzada - Casa de Cultura', scrape_torrejon_calzada),
        'torrelaguna': ('Torrelaguna - Casa de Cultura', scrape_torrelaguna),
        'torrelodones': ('Torrelodones - Teatro Bulevar', scrape_torrelodones),
        'torres_alameda': ('Torres de la Alameda - Auditorio Las Amapolas', scrape_torres_alameda),
        'tres_cantos': ('Tres Cantos - Teatro Municipal', scrape_tres_cantos),
        'valdemorillo': ('Valdemorillo - Casa de Cultura', scrape_valdemorillo),
        'valdemoro': ('Valdemoro - Teatro Juan Prado', scrape_valdemoro),
        'valdeolmos': ('Valdeolmos-Alalpardo - Casa de Cultura', scrape_valdeolmos_alalpardo),
        'velilla': ('Velilla de San Antonio - CC Mariana Pineda', scrape_velilla_san_antonio),
        'villa_del_prado': ('Villa del Prado - Centro de Artes', scrape_villa_del_prado),
        'villanueva_canada': ('Villanueva de la Cañada - CC La Despernada', scrape_villanueva_canada),
        'villanueva_pardillo': ('Villanueva del Pardillo - Auditorio Sebastián Cestero', scrape_villanueva_pardillo),
        'villaviciosa': ('Villaviciosa de Odón - Coliseo de la Cultura', scrape_villaviciosa_odon)
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
                    venue_name = e.get('venue', {}).get('name', '')
                    muni = e.get('venue', {}).get('municipality', '')
                    if url:
                        key = f"{url}_{venue_name}_{muni}"
                        master_dict[key] = e
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
                    venue_name = event_dict.get('venue', {}).get('name', '')
                    muni = event_dict.get('venue', {}).get('municipality', '')
                    
                    if url:
                        # Use a unique key combining URL and location to support the same event in multiple places
                        key = f"{url}_{venue_name}_{muni}"
                        master_dict[key] = event_dict
                
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

