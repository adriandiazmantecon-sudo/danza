from dataclasses import dataclass, field
from typing import List, Optional
import json
from datetime import datetime

@dataclass
class Venue:
    name: str
    municipality: str

@dataclass
class Session:
    date: str  # YYYY-MM-DD
    time: str  # HH:MM

@dataclass
class Event:
    id: str
    title: str
    company: str
    venue: Venue
    type: str
    price_range: str
    is_free: bool
    image_url: str
    url: str
    sessions: List[Session] = field(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "venue": {
                "name": self.venue.name,
                "municipality": self.venue.municipality
            },
            "type": self.type,
            "price_range": self.price_range,
            "is_free": self.is_free,
            "image_url": self.image_url,
            "url": self.url,
            "sessions": [{"date": s.date, "time": s.time} for s in self.sessions]
        }

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, "to_dict"):
            return o.to_dict()
        return super().default(o)
