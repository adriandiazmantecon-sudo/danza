import re

def parse_spanish_date_sessions(date_time_str):
    months = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }
    
    sessions = []
    date_time_str = date_time_str.lower().replace('\n', ' ').strip()
    print(f"DEBUG: Processing string: '{date_time_str}'")
    
    date_match = re.search(r'(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})', date_time_str)
    if not date_match:
        print("DEBUG: No date match found.")
        return []
    
    day = date_match.group(1).zfill(2)
    month = months.get(date_match.group(2), '01')
    year = date_match.group(3)
    iso_date = f"{year}-{month}-{day}"
    print(f"DEBUG: Found date: {iso_date}")
    
    # Example: 'de 17.00 a 17.30 h' or 'a las 19.00 h'
    time_match = re.search(r'(?:de|las)\s+(\d{1,2})[\.:](\d{2})', date_time_str)
    if time_match:
        hour = time_match.group(1).zfill(2)
        minute = time_match.group(2)
        sessions.append({'date': iso_date, 'time': f"{hour}:{minute}"})
        print(f"DEBUG: Found time: {hour}:{minute}")
    else:
        print("DEBUG: No time match found.")
        sessions.append({'date': iso_date, 'time': "19:00"})
        
    return sessions

# Test with various strings
test_strings = [
    "Sábado, 16 de mayo de 2026, de 17.00 a 17.30 h.",
    "Domingo, 17 de mayo de 2026, a las 19.00 h.",
    "Viernes, 15 de mayo y sábado, 16 de mayo de 2026, de 17.00 a 17.30 h."
]

for s in test_strings:
    print(f"\nTesting: {s}")
    print(f"Result: {parse_spanish_date_sessions(s)}")
