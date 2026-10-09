import json

from services.rag.config import CHUNKS_PATH, EVENTS_PATH, CLUBS_PATH, PAGES_CHUNKS_PATH, SHOCKERSYNC_EVENTS_PATH
from services.rag.scrapers.scraper import format_chunk

# dont list every date if an event repeats more than this many times
MAX_LISTED_DATES = 5

# this script combines events, clubs, and scraped pages into one file (chunks.json)
# that file is what gets embedded later and put into the FAISS index


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# make sure every record has the same fields no matter where it came from
def normalize(item, source):
    return {
        "source": source,
        "url": item.get("url", ""),
        "title": item.get("title", ""),
        "chunk_text": item.get("chunk_text", "")
    }


def get_eid(event):
    return event["eid"]


# the calendar has a separate entry for each day of a repeating event
# if title, location, time and description match its the same event, so one chunk with all the dates
def group_events(events):
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

    result = []
    for group in groups.values():
        # not repeating, leave it alone
        if len(group) == 1:
            result.append(group[0])
            continue

        # highest eID is the newest, use its details
        group.sort(key=get_eid)
        newest = dict(group[-1])

        dates = []
        for e in group:
            if e["start_date"] not in dates:
                dates.append(e["start_date"])
        dates.sort()

        if len(dates) == 1:
            date_text = dates[0]
        elif len(dates) <= MAX_LISTED_DATES:
            date_text = ", ".join(dates[:-1]) + " and " + dates[-1]
        else:
            date_text = f"{len(dates)} dates between {dates[0]} and {dates[-1]}"

        # format_chunk puts start_date after the title so all the dates go there
        newest["start_date"] = date_text
        newest["end_date"] = ""
        newest["chunk_text"] = format_chunk(newest)
        result.append(newest)

    return result


def main():
    chunks = []

    # wsu calendar events
    events_list = load_json(EVENTS_PATH)
    grouped_events = group_events(events_list)
    for e in grouped_events:
        chunks.append(normalize(e, "event"))

    # shockersync events
    shockersync_list = load_json(SHOCKERSYNC_EVENTS_PATH)
    for e in shockersync_list:
        chunks.append(normalize(e, "event"))

    # clubs
    clubs_list = load_json(CLUBS_PATH)
    for c in clubs_list:
        chunks.append(normalize(c, "club"))

    # pages are already normalized by chunker.py so just add them in as-is
    pages_list = load_json(PAGES_CHUNKS_PATH)
    for p in pages_list:
        chunks.append(p)

    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print("done merging chunks")
    print("events:", len(events_list), "-> after grouping repeats:", len(grouped_events))
    print("shockersync events:", len(shockersync_list))
    print("clubs:", len(clubs_list))
    print("pages:", len(pages_list))
    print("total:", len(chunks))


if __name__ == "__main__":
    main()
