import json
import os

from services.rag.config import ALL_EVENTS_PATH, DATA_DIR, EVENTS_PATH, SHOCKERSYNC_EVENTS_PATH
from services.rag.scrapers.scraper import format_chunk

# this script puts the wsu calendar events and the shockersync events into one file (all_events.json)
# every event has the same fields, so the recommendation part does not care where it came from

# dont list every date if an event repeats more than this many times
MAX_LISTED_DATES = 5

# minilm cuts off at 256 tokens so only use the start of a long description
MAX_DESCRIPTION_WORDS = 120


def load_json(path):
    if not os.path.exists(path):
        print("file not found, skipping:", path)
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_eid(event):
    return event["eid"]


def make_date_text(dates):
    if len(dates) == 1:
        return dates[0]
    if len(dates) <= MAX_LISTED_DATES:
        return ", ".join(dates[:-1]) + " and " + dates[-1]
    return f"{len(dates)} dates between {dates[0]} and {dates[-1]}"


# the text that gets embedded, only what the event is about
# no date or place in it, those are for the rules later (like events that are soon get a boost)
def make_embed_text(event):
    text = event["title"] + "."

    if event["organization"]:
        text += " Hosted by " + event["organization"] + "."

    if event["categories"]:
        text += " Categories: " + ", ".join(event["categories"]) + "."

    if event["benefits"]:
        text += " Benefits: " + ", ".join(event["benefits"]) + "."

    if event["cost"]:
        text += " Cost: " + event["cost"] + "."

    # some descriptions are just the title again
    if event["description"] and event["description"].lower() != event["title"].lower():
        words = event["description"].split()
        text += " " + " ".join(words[:MAX_DESCRIPTION_WORDS])

    return text


# the calendar has a separate entry for each day of a repeating event
# if title, location, time and description match its the same event, so one record with all the dates
def group_calendar_events(events):
    groups = {}
    for e in events:
        key = (
            e.get("title", "").lower().strip(),
            e.get("location", "").lower().strip(),
            e.get("time", "").lower().strip(),
            e.get("description", "").lower().strip()
        )
        if key not in groups:
            groups[key] = []
        groups[key].append(e)

    return list(groups.values())


def make_calendar_event(group):
    # highest eID is the newest, use its details
    group.sort(key=get_eid)
    newest = group[-1]

    dates = []
    for e in group:
        if e["start_date"] not in dates:
            dates.append(e["start_date"])
    dates.sort()

    end_date = dates[-1]
    for e in group:
        if e.get("end_date") and e["end_date"] > end_date:
            end_date = e["end_date"]

    # a single entry already has its chunk_text, for a group make a new one with all the dates
    if len(group) == 1:
        chunk_text = newest["chunk_text"]
    else:
        with_dates = dict(newest)
        with_dates["start_date"] = make_date_text(dates)
        with_dates["end_date"] = ""
        chunk_text = format_chunk(with_dates)

    event = {
        "source": "wsu_calendar",
        "id": str(newest["eid"]),
        "title": newest.get("title", ""),
        "start_date": dates[0],
        "end_date": end_date,
        "dates": dates,
        "time": newest.get("time", ""),
        "location": newest.get("location", ""),
        "description": newest.get("description", ""),
        "categories": newest.get("categories", []),
        "url": newest.get("url", ""),
        "cost": newest.get("cost", ""),
        "organization": "",
        "benefits": [],
        "chunk_text": chunk_text
    }
    event["embed_text"] = make_embed_text(event)
    return event


def make_shockersync_event(e):
    event = {
        "source": "shockersync",
        "id": str(e.get("id", "")),
        "title": e.get("title", ""),
        "start_date": e.get("start_date", ""),
        "end_date": e.get("end_date", ""),
        "dates": [e.get("start_date", "")],
        "time": e.get("time", ""),
        "location": e.get("location", ""),
        "description": e.get("description", ""),
        "categories": e.get("categories", []),
        "url": e.get("url", ""),
        "cost": "",
        "organization": e.get("organization", ""),
        "benefits": e.get("benefits", []),
        "chunk_text": e.get("chunk_text", "")
    }
    event["embed_text"] = make_embed_text(event)
    return event


def main():
    calendar_list = load_json(EVENTS_PATH)
    shockersync_list = load_json(SHOCKERSYNC_EVENTS_PATH)

    all_events = []

    calendar_groups = group_calendar_events(calendar_list)
    for group in calendar_groups:
        all_events.append(make_calendar_event(group))

    for e in shockersync_list:
        all_events.append(make_shockersync_event(e))

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ALL_EVENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)

    print("done merging events")
    print("calendar events:", len(calendar_list), "-> after grouping repeats:", len(calendar_groups))
    print("shockersync events:", len(shockersync_list))
    print("total:", len(all_events))


if __name__ == "__main__":
    main()
