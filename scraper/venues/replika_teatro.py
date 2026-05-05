from models import Event
from typing import List
from taquilla_common import get_events_for_venue

async def scrape_replika_teatro() -> List[Event]:
    return await get_events_for_venue("Replika")
