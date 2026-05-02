from bs4 import BeautifulSoup
import re
import os

def clean_text(text):
    if not text: return ""
    text = text.replace('\xa0', ' ')
    text = " ".join(text.split())
    return text.strip()

def test_parse():
    file_path = r'c:\Users\docto\OneDrive\Antigravity\madrid_dance\majadahonda_event.html'
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Restrict to detail view
    detail_view = soup.select_one('.detail-view')
    if not detail_view:
        print("Detail view not found")
        return

    # Title
    title_el = detail_view.select_one('span.title.h3')
    title_text = title_el.get_text().strip() if title_el else "Unknown"
    title = re.sub(r'^(?:Danza|Baile|Espect\u00e1culo|M\u00fasica y Danza)\s*[-:]\s*', '', title_text, flags=re.IGNORECASE)
    title = title.strip('"\'')
    print(f"Title: {title}")

    # Image
    img_el = detail_view.select_one('img.image')
    image_url = img_el.get('src') if img_el else ""
    print(f"Image: {image_url}")

    # Company & Price from .text
    company = ""
    price_range = "Consultar web"
    text_div = detail_view.select_one('.text')
    if text_div:
        for p in text_div.find_all('p'):
            p_text = p.get_text()
            if 'Cía' in p_text or 'Compañía' in p_text:
                company = p_text.split(':')[-1].strip()
            if 'Localidades' in p_text or 'Precio' in p_text:
                price_range = p_text.split(':')[-1].strip()

    print(f"Company: {company}")
    print(f"Price: {price_range}")

    # Sessions
    sessions = []
    start_date_el = detail_view.select_one('.start-date')
    start_time_el = detail_view.select_one('.start-time')
    
    if start_date_el and start_time_el:
        date_text = start_date_el.get_text().strip()
        time_text = start_time_el.get_text().strip()
        
        # Parse date: "sábado, 09 mayo 2026"
        months = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
        }
        
        match = re.search(r'(\d{1,2})\s+([a-z]+)\s+(\d{4})', date_text.lower())
        if match:
            day = match.group(1).zfill(2)
            month_str = match.group(2)
            month = months.get(month_str, '01')
            year = match.group(3)
            
            # Parse time: "20:00"
            time_match = re.search(r'(\d{2}):(\d{2})', time_text)
            if time_match:
                time = f"{time_match.group(1)}:{time_match.group(2)}"
                sessions.append({"date": f"{year}-{month}-{day}", "time": time})

    print(f"Sessions: {sessions}")

if __name__ == "__main__":
    test_parse()
