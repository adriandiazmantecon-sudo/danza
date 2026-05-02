import json
import os

path = os.path.join('web', 'src', 'data', 'events.json')
with open(path, 'r', encoding='utf-8') as f:
    events = json.load(f)

paco_events = [e for e in events if 'Paco Rabal' in e['venue']['name']]
for e in paco_events:
    print(f"URL: {e['url']}")
    print(f"Title: {e['title']}")
    print(f"Company: {e['company']}")
    print("-" * 20)
