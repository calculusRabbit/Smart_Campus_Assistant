import json

from config import CHUNKS_PATH, EVENTS_PATH, CLUBS_PATH, PAGES_CHUNKS_PATH, SHOCKERSYNC_EVENTS_PATH

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


def main():
    chunks = []

    # wsu calendar events
    events_list = load_json(EVENTS_PATH)
    for e in events_list:
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
    print("events:", len(events_list))
    print("shockersync events:", len(shockersync_list))
    print("clubs:", len(clubs_list))
    print("pages:", len(pages_list))
    print("total:", len(chunks))


if __name__ == "__main__":
    main()
