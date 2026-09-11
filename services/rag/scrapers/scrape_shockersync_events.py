import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime, timedelta, timezone
from config import SHOCKERSYNC_EVENTS_PATH

BASE_URL = "https://wichita.campuslabs.com/engage/api/discovery/event/search"
HEADERS = {"User-Agent": "Mozilla/5.0"}
PAGE_SIZE = 100


def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def strip_html(html: str) -> str:
    return clean_text(BeautifulSoup(html, "html.parser").get_text())


def get_start_date() -> str:
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    offset = "-05:00"
    local = seven_days_ago.strftime("%Y-%m-%dT00:00:00")
    return local + offset


def fetch_page(ends_after: str, skip: int) -> list:
    params = {
        "endsAfter": ends_after,
        "orderByField": "endsOn",
        "orderByDirection": "ascending",
        "take": PAGE_SIZE,
        "skip": skip
    }
    res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
    print(f"http code: {res.status_code} | skip={skip}")
    return res.json().get("value", [])


def format_chunk(event: dict) -> str:
    text = f"{event['title']} hosted by {event['organization']}"
    text += f" on {event['start_date']}"

    if event["end_date"] and event["end_date"] != event["start_date"]:
        text += f" to {event['end_date']}"

    if event["time"]:
        text += f" at {event['time']}"

    if event["location"]:
        text += f" in {event['location']}"

    text += "."

    if event["description"]:
        text += f" {event['description']}."

    if event["categories"]:
        text += f" Categories: {', '.join(event['categories'])}."

    if event["benefits"]:
        text += f" Benefits: {', '.join(event['benefits'])}."

    return text


def parse_event(raw: dict) -> dict:
    start = raw.get("startsOn", "")
    end = raw.get("endsOn", "")

    start_date = start[:10] if start else ""
    end_date = end[:10] if end else ""
    time_text = ""
    if start:
        try:
            dt = datetime.fromisoformat(start)
            time_text = dt.strftime("%-I:%M %p")
        except Exception:
            pass

    event_id = raw.get("id", "")
    url = f"https://wichita.campuslabs.com/engage/event/{event_id}" if event_id else ""

    event = {
        "url": url,
        "title": clean_text(raw.get("name", "")),
        "organization": clean_text(raw.get("organizationName", "")),
        "start_date": start_date,
        "end_date": end_date,
        "time": time_text,
        "location": clean_text(raw.get("location", "") or ""),
        "description": strip_html(raw.get("description", "") or ""),
        "categories": raw.get("categoryNames", []),
        "benefits": raw.get("benefitNames", []),
        "theme": raw.get("theme", "")
    }
    event["chunk_text"] = format_chunk(event)
    return event


def main():
    os.makedirs("data", exist_ok=True)
    ends_after = get_start_date()
    print(f"Fetching events from {ends_after}")

    events = []
    skip = 0
    while True:
        page = fetch_page(ends_after, skip)
        if not page:
            break
        for raw in page:
            events.append(parse_event(raw))
        print(f"Fetched {len(page)} events (total so far: {len(events)})")
        if len(page) < PAGE_SIZE:
            break
        skip += PAGE_SIZE

    with open(SHOCKERSYNC_EVENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)

    print(f"Done: {len(events)} events saved")


if __name__ == "__main__":
    main()
