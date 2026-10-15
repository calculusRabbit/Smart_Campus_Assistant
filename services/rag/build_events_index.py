import json
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import faiss
import numpy as np
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

from services.rag.config import (
    ALL_EVENTS_PATH,
    EVENTS_EMBEDDING_MODEL,
    EVENTS_INDEX_PATH,
)

API_URL = "https://wichita.campuslabs.com/engage/api/discovery/event/search"
WICHITA_TZ = ZoneInfo("America/Chicago")
PAGE_SIZE = 100


def local_datetime(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(WICHITA_TZ)


def fetch_events():
    events = []
    skip = 0
    cutoff = datetime.now(UTC).isoformat()

    while True:
        response = requests.get(
            API_URL,
            params={
                "endsAfter": cutoff,
                "orderByField": "endsOn",
                "orderByDirection": "ascending",
                "take": PAGE_SIZE,
                "skip": skip,
            },
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30,
        )
        response.raise_for_status()
        page = response.json().get("value", [])
        events.extend(page)
        print(f"Fetched {len(events)} events")

        if len(page) < PAGE_SIZE:
            break
        skip += PAGE_SIZE

    return events


def transform_event(raw):
    start = local_datetime(raw.get("startsOn"))
    end = local_datetime(raw.get("endsOn"))
    if not start:
        return None

    event_id = str(raw.get("id", ""))
    if not event_id:
        return None

    description = BeautifulSoup(
        raw.get("description") or "", "html.parser"
    ).get_text(" ", strip=True)

    categories = raw.get("categoryNames") or []
    organization = raw.get("organizationName") or ""
    title = raw.get("name") or ""

    # Preserve the event's date range without inventing daily occurrences.
    last = end.date() if end else start.date()
    dates = [start.date().isoformat()]

    text = (
        f"{title}. Hosted by {organization}. "
        f"Categories: {', '.join(categories)}. "
        f"Description: {description}. "
        f"Location: {raw.get('location') or ''}."
    )

    return {
        "id": event_id,
        "source": "shockersync",
        "title": title,
        "organization": organization,
        "description": description,
        "categories": categories,
        "dates": dates,
        "start_date": start.date().isoformat(),
        "end_date": last.isoformat(),
        "end_datetime": end.isoformat() if end else None,
        "time": start.strftime("%I:%M %p").lstrip("0"),
        "location": raw.get("location") or "",
        "url": f"https://wichita.campuslabs.com/engage/event/{event_id}",
        "chunk_text": text,
    }


def main():
    raw_events = fetch_events()
    events = [event for raw in raw_events if (event := transform_event(raw))]
    if not events:
        raise RuntimeError("No events retrieved; existing index was not changed.")

    model = SentenceTransformer(EVENTS_EMBEDDING_MODEL)
    vectors = model.encode(
        [event["chunk_text"] for event in events],
        batch_size=32,
        show_progress_bar=True,
    ).astype(np.float32)

    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    ALL_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ALL_EVENTS_PATH, "w", encoding="utf-8") as file:
        json.dump(events, file, indent=2, ensure_ascii=False)

    faiss.write_index(index, str(EVENTS_INDEX_PATH))
    print(f"Saved {len(events)} events and {index.ntotal} vectors")


if __name__ == "__main__":
    main()
