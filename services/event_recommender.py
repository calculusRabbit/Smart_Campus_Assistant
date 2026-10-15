import json
from datetime import date, datetime
from zoneinfo import ZoneInfo

import numpy as np

from services.interest_expansion import expand_interests
from services.rag.config import ALL_EVENTS_PATH, EVENTS_EMBEDDING_MODEL, EVENTS_INDEX_PATH
from services.recommender_config import (
    LOOKAHEAD_DAYS,
    MAX_TAG_WORDS,
    MIN_SCORE,
    SEARCH_SIZE,
    SOON_BOOST,
    SOON_DAYS,
)

# recommends events from all_events.json by comparing the students text with the event texts
# (the vectors are in events_index.faiss, made by build_events_index.py)
# the numbers like the date window and the cutoff are in recommender_config.py


def today_in_wichita():
    return datetime.now(ZoneInfo("America/Chicago")).date()


def profile_to_text(interests):
    # tags are short items like "coding"
    # the text the student wrote is one long item (there is no text column yet)
    tags = []
    about = []
    for item in interests:
        if len(item.split()) > MAX_TAG_WORDS:
            about.append(item.strip())
        else:
            tags.append(item)

    text = " ".join(about)
    if len(tags) == 1:
        text += " I am interested in " + tags[0] + "."
    elif len(tags) > 1:
        text += " I am interested in " + ", ".join(tags[:-1]) + " and " + tags[-1] + "."
    return text.strip()


def next_date(event, today):
    # the first date of the event that is in the window, None if they are all too old
    oldest_text = today.isoformat()

    upcoming = []
    for d in event["dates"]:
        if d and d >= oldest_text:
            upcoming.append(d)
    if len(upcoming) > 0:
        return min(upcoming)

    # Do not invent occurrences within a multi-day event's date range.
    # The source may describe a recurring schedule without providing exact dates.
    return None


def mentions_dislike(event, dislikes):
    text = event["title"] + " " + " ".join(event["categories"]) + " " + event["organization"]
    text = text.lower()
    for word in dislikes:
        if word.lower().strip() in text:
            return True
    return False


class EventRecommender:
    def __init__(self, events, index, embed):
        # embed turns a text into a normalized vector
        if index.ntotal != len(events):
            raise ValueError("index and all_events.json do not match, build the index again")
        self.events = events
        self.index = index
        self.embed = embed

    @classmethod
    def load(cls):
        # imported here so importing this file is fast
        import faiss
        from sentence_transformers import SentenceTransformer

        with open(ALL_EVENTS_PATH, encoding="utf-8") as f:
            events = json.load(f)
        index = faiss.read_index(str(EVENTS_INDEX_PATH))
        model = SentenceTransformer(EVENTS_EMBEDDING_MODEL)

        def embed(text):
            vector = model.encode([text]).astype(np.float32)
            faiss.normalize_L2(vector)
            return vector

        return cls(events, index, embed)

    def recommend(self, likes_text, dislikes=None, top_k=10, today=None, now=None):
        if now is None:
            now = datetime.now(ZoneInfo("America/Chicago"))
        if dislikes is None:
            dislikes = []
        if today is None:
            today = today_in_wichita()
        if likes_text.strip() == "":
            return []

        scores, ids = self.index.search(self.embed(expand_interests(likes_text)), SEARCH_SIZE)

        results = []
        for score, i in zip(scores[0], ids[0], strict=True):
            if i == -1:
                continue

            event = self.events[i]
            scored = _score_upcoming_event(event, score, dislikes, today, now)
            if scored is None:
                continue

            when, final_score = scored

            categories = event["categories"]
            results.append({
                "event_id": event["source"] + "-" + event["id"],
                "event_name": event["title"],
                "event_date": when,
                "event_time": event["time"],
                "event_location": event["location"],
                "event_description": event["description"],
                "event_category": categories[0] if len(categories) > 0 else "general",
                "url": event["url"],
                "score": round(final_score * 100)
            })

        results.sort(key=get_score, reverse=True)

        unique_results = []
        seen_events = set()

        for result in results:
            event_key = (result["event_id"], result["event_date"])
            if event_key in seen_events:
                continue

            seen_events.add(event_key)
            unique_results.append(result)

        return unique_results[:top_k]


def _score_upcoming_event(event, score, dislikes, today, now):
    # Exclude events that have already ended, including earlier today.
    end_text = event.get("end_datetime")
    if end_text and datetime.fromisoformat(end_text) <= now:
        return None

    when = next_date(event, today)
    if mentions_dislike(event, dislikes):
        return None

    ongoing_range = False
    if when is None:
        start_date = event.get("start_date")
        if start_date is None:
            dates = event.get("dates") or []
            start_date = min(dates) if dates else None

        end_date = event.get("end_date")
        if (
            start_date
            and end_date
            and start_date < today.isoformat() <= end_date
        ):
            when = f"Ongoing through {end_date}"
            ongoing_range = True
        else:
            return None

    final_score = float(score)
    if final_score < MIN_SCORE:
        return None

    days = 0 if ongoing_range else (date.fromisoformat(when) - today).days
    if days > LOOKAHEAD_DAYS:
        return None

    if not ongoing_range and days < SOON_DAYS:
        final_score += SOON_BOOST

    return when, min(1.0, final_score)


def get_score(result):
    return result["score"]


# loading takes a few seconds so only do it the first time
_recommender = None


def get_recommender():
    global _recommender
    if _recommender is None:
        _recommender = EventRecommender.load()
    return _recommender
