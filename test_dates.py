import re
from datetime import datetime, timedelta

months = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}

def parse_dates(date_str, time_str):
    date_str = date_str.lower()
    time_str = time_str.lower()
    
    # Extract time. "jueves a sábado / 20h", "20:30h"
    t_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*[h\s]', time_str)
    if t_match:
        h = int(t_match.group(1))
        m = int(t_match.group(2)) if t_match.group(2) else 0
        time_formatted = f"{h:02d}:{m:02d}"
    else:
        time_formatted = "20:00"

    sessions = []
    
    # Range format: "7 al 9 de mayo de 2026"
    m_range = re.search(r'(\d+)\s*(?:al|a|-)\s*(\d+)\s*de\s*([a-z]+)\s*de\s*(\d{4})', date_str)
    if m_range:
        start_d = int(m_range.group(1))
        end_d = int(m_range.group(2))
        month = months.get(m_range.group(3))
        year = int(m_range.group(4))
        
        start_date = datetime(year, month, start_d)
        end_date = datetime(year, month, end_d)
        
        curr = start_date
        while curr <= end_date:
            sessions.append({"date": curr.strftime("%Y-%m-%d"), "time": time_formatted})
            curr += timedelta(days=1)
        return sessions

    # Range with diff months: "30 de mayo al 2 de junio de 2026"
    m_range2 = re.search(r'(\d+)\s*de\s*([a-z]+)\s*(?:al|a|-)\s*(\d+)\s*de\s*([a-z]+)\s*de\s*(\d{4})', date_str)
    if m_range2:
        sd, sm, ed, em, y = m_range2.groups()
        start_date = datetime(int(y), months[sm], int(sd))
        end_date = datetime(int(y), months[em], int(ed))
        curr = start_date
        while curr <= end_date:
            sessions.append({"date": curr.strftime("%Y-%m-%d"), "time": time_formatted})
            curr += timedelta(days=1)
        return sessions
    
    # Single date: "8 de mayo de 2026"
    m_single = re.search(r'(\d+)\s*de\s*([a-z]+)\s*de\s*(\d{4})', date_str)
    if m_single:
        d, m, y = m_single.groups()
        sessions.append({"date": f"{y}-{months[m]:02d}-{int(d):02d}", "time": time_formatted})
        return sessions

    # Specific multiple dates: "26 y 27 de junio de 2026"
    m_y = re.search(r'(\d+)\s*y\s*(\d+)\s*de\s*([a-z]+)\s*de\s*(\d{4})', date_str)
    if m_y:
        d1, d2, m, y = m_y.groups()
        sessions.append({"date": f"{y}-{months[m]:02d}-{int(d1):02d}", "time": time_formatted})
        sessions.append({"date": f"{y}-{months[m]:02d}-{int(d2):02d}", "time": time_formatted})
        return sessions

    return []

print(parse_dates("7 al 9 de mayo de 2026", "Jueves a sábado / 20h"))
print(parse_dates("8 de mayo de 2026", "Jueves a sábado / 20h"))
print(parse_dates("26 y 27 de junio de 2026", "20:30 h"))
print(parse_dates("30 de mayo al 2 de junio de 2026", "Jueves a sábado / 20h"))
