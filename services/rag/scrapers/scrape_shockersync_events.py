import requests
from bs4 import BeautifulSoup
import json
import os
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from services.rag.config import DATA_DIR, RETRIES, SHOCKERSYNC_EVENTS_PATH

BASE_URL = "https://wichita.campuslabs.com/engage/api/discovery/event/search"
HEADERS = {"User-Agent": "Mozilla/5.0"}
PAGE_SIZE = 100


def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def strip_html(html: str) -> str:
    return clean_text(BeautifulSoup(html, "html.parser").get_text())


def get_start_date() -> str:
    # today in wichita time, only events that end today or later
    now = datetime.now(ZoneInfo("America/Chicago"))
    return now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()


def fetch_page(ends_after: str, skip: int):
    # returns the events on this page, None if it keeps failing
    params = {
        "endsAfter": ends_after,
        "orderByField": "endsOn",
        "orderByDirection": "ascending",
        "take": PAGE_SIZE,
        "skip": skip
    }
    for attempt in range(RETRIES):
        try:
            res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
            print(f"http code: {res.status_code} | skip={skip}")
            if res.status_code == 200:
                return res.json().get("value", [])
        except (requests.RequestException, ValueError) as e:
            print(f"request error: {e}")

        time.sleep(2 * (attempt + 1))
    return None


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


def to_wichita_time(text: str):
    # api gives utc times, change to wichita time
    try:
        return datetime.fromisoformat(text).astimezone(ZoneInfo("America/Chicago"))
    except ValueError:
        return None


def parse_event(raw: dict) -> dict:
    start = raw.get("startsOn", "")
    end = raw.get("endsOn", "")

    start_dt = to_wichita_time(start) if start else None
    end_dt = to_wichita_time(end) if end else None

    # if the time cant be read use the first 10 characters like before
    start_date = start[:10] if start else ""
    end_date = end[:10] if end else ""
    time_text = ""
    if start_dt:
        start_date = start_dt.strftime("%Y-%m-%d")
        time_text = start_dt.strftime("%-I:%M %p")
    if end_dt:
        end_date = end_dt.strftime("%Y-%m-%d")

    event_id = raw.get("id", "")
    url = f"https://wichita.campuslabs.com/engage/event/{event_id}" if event_id else ""

    event = {
        "id": event_id,
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


def load_old_events():
    if os.path.exists(SHOCKERSYNC_EVENTS_PATH):
        with open(SHOCKERSYNC_EVENTS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_events(events):
    with open(SHOCKERSYNC_EVENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    ends_after = get_start_date()
    print(f"Fetching events from {ends_after}")

    old_events = load_old_events()

    # keyed by url so a duplicate event is only saved once
    new_events = {}
    skip = 0
    while True:
        page = fetch_page(ends_after, skip)
        if page is None:
            print("could not load a page, stopping. the old file is kept as it is")
            return
        for raw in page:
            event = parse_event(raw)
            new_events[event["url"]] = event
        print(f"Fetched {len(page)} events (total so far: {len(new_events)})")
        if len(page) < PAGE_SIZE:
            break
        skip += PAGE_SIZE

    if len(new_events) == 0 and len(old_events) > 0:
        print("got 0 events, something is probably wrong. the old file is kept as it is")
        return

    # compare with last time just to print what changed
    old_by_url = {}
    for e in old_events:
        old_by_url[e["url"]] = e

    added = 0
    changed = 0
    for url, event in new_events.items():
        if url not in old_by_url:
            added += 1
        elif old_by_url[url]["chunk_text"] != event["chunk_text"]:
            changed += 1

    removed = 0
    for url in old_by_url:
        if url not in new_events:
            removed += 1

    save_events(list(new_events.values()))
    print(f"Done: {added} new, {changed} changed, {removed} removed, {len(new_events)} total")


if __name__ == "__main__":
    main()
