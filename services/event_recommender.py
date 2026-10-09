import json
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from services.rag.config import ALL_EVENTS_PATH, EVENTS_EMBEDDING_MODEL, EVENTS_INDEX_PATH
from services.recommender_config import (
    LOOKAHEAD_DAYS,
    LOOKBACK_DAYS,
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
    today_text = today.isoformat()
    oldest_text = (today - timedelta(days=LOOKBACK_DAYS)).isoformat()

    upcoming = []
    for d in event["dates"]:
        if d and d >= oldest_text:
            upcoming.append(d)
    if len(upcoming) > 0:
        return min(upcoming)

    # an event over many days that is still going on
    if event["end_date"] and event["end_date"] >= today_text:
        return today_text

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

    def recommend(self, likes_text, dislikes=None, top_k=10, today=None):
        if dislikes is None:
            dislikes = []
        if today is None:
            today = today_in_wichita()
        if likes_text.strip() == "":
            return []

        scores, ids = self.index.search(self.embed(likes_text), SEARCH_SIZE)

        results = []
        for score, i in zip(scores[0], ids[0], strict=True):
            if i == -1:
                continue
            event = self.events[i]

            # old events and events the student said they dont like
            when = next_date(event, today)
            if when is None or mentions_dislike(event, dislikes):
                continue

            # the cutoff is for how well the event matches, the rules below only change the order
            final_score = float(score)
            if final_score < MIN_SCORE:
                continue

            # too far away
            days = (date.fromisoformat(when) - today).days
            if days > LOOKAHEAD_DAYS:
                continue

            if days < SOON_DAYS:
                final_score += SOON_BOOST
            final_score = min(1.0, final_score)

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
        return results[:top_k]


def get_score(result):
    return result["score"]


# loading takes a few seconds so only do it the first time
_recommender = None


def get_recommender():
    global _recommender
    if _recommender is None:
        _recommender = EventRecommender.load()
    return _recommender
