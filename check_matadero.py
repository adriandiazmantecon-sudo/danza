from bs4 import BeautifulSoup

with open("scratch_matadero_event.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")
    for level in ['h1', 'h2', 'h3']:
        for h in soup.find_all(level):
            print(f"{level}: {h.text.strip()}")
