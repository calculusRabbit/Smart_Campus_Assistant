import json
from collections.abc import Callable
from datetime import date, datetime
from typing import Any
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


def today_in_wichita() -> date:
    return datetime.now(ZoneInfo("America/Chicago")).date()


def profile_to_text(interests: list[str]) -> str:
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


def next_date(event: dict[str, Any], today: date) -> str | None:
    # The first upcoming event date, or None if none is available.
    oldest_text = today.isoformat()

    upcoming: list[str] = []

    for d in event["dates"]:
        if isinstance(d, str) and d >= oldest_text:
            upcoming.append(d)

    if upcoming:
        return min(upcoming)

    # Do not invent occurrences within a multi-day event's date range.
    return None


def mentions_dislike(event: dict[str, Any], dislikes: list[str]) -> bool:
    text = event["title"] + " " + " ".join(event["categories"]) + " " + event["organization"]
    text = text.lower()
    for word in dislikes:
        if word.lower().strip() in text:
            return True
    return False


TOPIC_KEYWORDS = {
    "programming": (
        "programming",
        "coding",
        "software development",
        "python",
        "github",
        "hackathon",
        "computer science",
        "developer",
    ),
    "career": (
        "career",
        "internship",
        "job fair",
        "employment",
        "employer",
        "recruiting",
        "resume",
        "professional development",
        "professional networking",
    ),
    "soccer": ("soccer", "football", "futbol"),
    "artificial intelligence": (
        "ai club",
        "artificial intelligence",
        "machine learning",
        "ai workshop",
        "ai 101",
    ),
    "music": (
        "music",
        "musical",
        "concert",
        "songfest",
        "singing",
        "choir",
        "orchestra",
        "live performance",
    ),
    "cybersecurity": (
        "cybersecurity",
        "cyber security",
        "information security",
        "infosec",
        "wicys",
        "cyber defense",
    ),
}

TOPIC_QUERY_ALIASES = {
    "programming": (
        "programming",
        "coding",
        "software development",
        "python",
        "computer science",
    ),
    "career": (
        "career",
        "careers",
        "internship",
        "internships",
        "jobs",
        "job fair",
        "networking",
    ),
    "soccer": ("soccer", "futbol"),
    "artificial intelligence": (
        "artificial intelligence",
        "machine learning",
        "ai",
        "ai club",
    ),
    "music": (
        "music",
        "musical",
        "concert",
        "concerts",
        "singing",
    ),
    "cybersecurity": (
        "cybersecurity",
        "cyber security",
        "information security",
        "infosec",
    ),
}


def matches_event_topic(event: dict[str, Any], interests: str) -> bool:
    """Require topic evidence for recognized student interests."""
    import re

    query = interests.casefold()

    def contains_phrase(text: str, phrase: str) -> bool:
        pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
        return re.search(pattern, text) is not None

    selected_topics = [
        topic
        for topic, aliases in TOPIC_QUERY_ALIASES.items()
        if any(contains_phrase(query, alias) for alias in aliases)
    ]

    if not selected_topics:
        return True

    text = " ".join(
        [
            str(event.get("title", "")),
            str(event.get("description", "")),
            str(event.get("organization", "")),
            " ".join(event.get("categories", [])),
        ]
    ).casefold()

    return any(
        contains_phrase(text, keyword)
        for topic in selected_topics
        for keyword in TOPIC_KEYWORDS[topic]
    )


class EventRecommender:
    def __init__(
        self,
        events: list[dict[str, Any]],
        index: Any,
        embed: Callable[[str], np.ndarray],
    ) -> None:
        # embed turns a text into a normalized vector
        if index.ntotal != len(events):
            raise ValueError("index and all_events.json do not match, build the index again")
        self.events = events
        self.index = index
        self.embed = embed

    @classmethod
    def load(cls) -> "EventRecommender":
        # imported here so importing this file is fast
        import faiss
        from sentence_transformers import SentenceTransformer

        with open(ALL_EVENTS_PATH, encoding="utf-8") as f:
            events = json.load(f)
        index = faiss.read_index(str(EVENTS_INDEX_PATH))
        model = SentenceTransformer(EVENTS_EMBEDDING_MODEL)

        def embed(text: str) -> np.ndarray:
            vector = model.encode([text]).astype(np.float32)
            faiss.normalize_L2(vector)
            return vector

        return cls(events, index, embed)

    def recommend(
        self,
        likes_text: str,
        dislikes: list[str] | None = None,
        top_k: int = 10,
        today: date | None = None,
        now: datetime | None = None,
    ) -> list[dict[str, Any]]:
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
            scored = _score_matching_event(event, score, dislikes, today, now, likes_text)
            if scored is None:
                continue

            when, final_score = scored

            categories = event["categories"]
            results.append(
                {
                    "event_id": event["source"] + "-" + event["id"],
                    "event_name": event["title"],
                    "event_date": when,
                    "event_time": event["time"],
                    "event_location": event["location"],
                    "event_description": event["description"],
                    "event_category": categories[0] if len(categories) > 0 else "general",
                    "url": event["url"],
                    "score": round(final_score * 100),
                }
            )

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


def matches_requested_activity(event: dict[str, Any], query: str) -> bool:
    """Filter explicit activity requests without restricting broad interests."""
    import re

    query = query.casefold()

    title = str(event.get("title", "")).casefold()
    description = str(event.get("description", "")).casefold()
    organization = str(event.get("organization", "")).casefold()

    def contains(text: str, terms: tuple[str, ...]) -> bool:
        return any(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text) for term in terms)

    if contains(query, ("soccer", "futbol")):
        return (
            contains(title, ("soccer", "football", "futbol", "practice", "match", "game"))
            or (
                contains(organization, ("soccer",))
                and contains(title + " " + description, ("practice", "match", "game", "tournament"))
            )
        ) and not contains(title + " " + description, ("rave", "edm party", "dance party"))

    if contains(query, ("concert", "concerts", "performances", "performance")):
        performance_terms = (
            "concert",
            "songfest",
            "recital",
            "showcase",
            "live performance",
            "live music",
            "lip sync",
            "singing competition",
        )
        if contains(query, ("music", "musical", "concert", "concerts")):
            return contains(title + " " + description, performance_terms)

    if contains(query, ("workshop", "workshops")):
        return contains(
            title + " " + description,
            ("workshop", "workshops", "training", "hands-on"),
        )

    return True


def _score_matching_event(
    event: dict[str, Any],
    score: Any,
    dislikes: list[str],
    today: date,
    now: datetime,
    likes_text: str,
) -> tuple[str, float] | None:
    if not matches_event_topic(event, likes_text):
        return None
    if not matches_requested_activity(event, likes_text):
        return None
    return _score_upcoming_event(event, score, dislikes, today, now)


def get_event_display_date(event: dict[str, Any], today: date) -> tuple[str, bool] | None:
    """Return an upcoming date or an ongoing-event label."""
    when = next_date(event, today)

    if when is not None:
        return when, False

    start_date = event.get("start_date")
    if start_date is None:
        dates = event.get("dates") or []
        start_date = min(dates) if dates else None

    end_date = event.get("end_date")

    if start_date and end_date and start_date < today.isoformat() <= end_date:
        return f"Ongoing through {end_date}", True

    return None


def _score_upcoming_event(
    event: dict[str, Any],
    score: Any,
    dislikes: list[str],
    today: date,
    now: datetime,
) -> tuple[str, float] | None:
    # Exclude events that have already ended.
    end_text = event.get("end_datetime")
    if end_text and datetime.fromisoformat(end_text) <= now:
        return None

    if mentions_dislike(event, dislikes):
        return None

    display_date = get_event_display_date(event, today)
    if display_date is None:
        return None

    when, ongoing_range = display_date

    final_score = float(score)
    if final_score < MIN_SCORE:
        return None

    days = 0 if ongoing_range else (date.fromisoformat(when) - today).days
    if days > LOOKAHEAD_DAYS:
        return None

    if not ongoing_range and days < SOON_DAYS:
        final_score += SOON_BOOST

    return when, min(1.0, final_score)


def get_score(result: dict[str, Any]) -> float:
    return float(result["score"])


# loading takes a few seconds so only do it the first time
_recommender = None


def get_recommender() -> EventRecommender:
    global _recommender
    if _recommender is None:
        _recommender = EventRecommender.load()
    return _recommender
