import re
from datetime import datetime

def parse_date(date_text):
    months = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
        'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
    }
    m = re.search(r'(\d{1,2})\s+([a-z]+)\s+(\d{4})', date_text.lower())
    if m:
        day = m.group(1).zfill(2)
        month_name = m.group(2)
        month_num = '01'
        for k, v in months.items():
            if k in month_name:
                month_num = v
                break
        year = m.group(3)
        return f"{year}-{month_num}-{day}"
    return None

date_text = "08 May 2026"
print(f"Input: {date_text} -> Output: {parse_date(date_text)}")
