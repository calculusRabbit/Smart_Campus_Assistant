from datetime import date, datetime
from zoneinfo import ZoneInfo

import numpy as np

from services.event_recommender import EventRecommender, next_date

TODAY = date(2026, 10, 13)


def make_event(event_date):
    return {
        "id": "123",
        "source": "shockersync",
        "title": "Programming Workshop",
        "organization": "ACM",
        "description": "Learn Python programming",
        "categories": ["Technology"],
        "dates": [event_date],
        "end_date": event_date,
        "time": "2:00 PM",
        "location": "Jabara Hall",
        "url": "https://example.com/event/123",
    }


class FakeIndex:
    ntotal = 1

    def search(self, vector, count):
        return (
            np.array([[0.8]], dtype=np.float32),
            np.array([[0]], dtype=np.int64),
        )


def make_recommender(event_date):
    return EventRecommender(
        [make_event(event_date)],
        FakeIndex(),
        lambda text: np.zeros((1, 384), dtype=np.float32),
    )


def test_past_event_excluded():
    assert next_date(make_event("2026-10-12"), TODAY) is None


def test_upcoming_event_accepted():
    assert next_date(make_event("2026-10-20"), TODAY) == "2026-10-20"


def test_past_event_not_recommended():
    results = make_recommender("2026-10-12").recommend(
        "programming", today=TODAY
    )
    assert results == []


def test_upcoming_event_recommended():
    results = make_recommender("2026-10-20").recommend(
        "programming", today=TODAY
    )

    assert len(results) == 1
    assert results[0]["event_name"] == "Programming Workshop"
    assert results[0]["event_date"] == "2026-10-20"
    assert results[0]["event_id"] == "shockersync-123"
    assert results[0]["score"] == 80


def test_event_beyond_lookahead_excluded():
    results = make_recommender("2026-12-01").recommend(
        "programming", today=TODAY
    )
    assert results == []


def test_completed_event_excluded():
    recommender = make_recommender("2026-10-13")
    recommender.events[0]["end_datetime"] = "2026-10-13T14:00:00-05:00"

    now = datetime(2026, 10, 13, 15, 0, tzinfo=ZoneInfo("America/Chicago"))
    results = recommender.recommend("programming", today=TODAY, now=now)

    assert results == []


def test_ongoing_event_recommended():
    recommender = make_recommender("2026-10-13")
    recommender.events[0]["end_datetime"] = "2026-10-13T16:00:00-05:00"

    now = datetime(2026, 10, 13, 15, 0, tzinfo=ZoneInfo("America/Chicago"))
    results = recommender.recommend("programming", today=TODAY, now=now)

    assert len(results) == 1
    assert results[0]["event_name"] == "Programming Workshop"


def test_duplicate_event_recommended_once():
    class DuplicateIndex:
        ntotal = 2

        def search(self, vector, count):
            return (
                np.array([[0.9, 0.8]], dtype=np.float32),
                np.array([[0, 1]], dtype=np.int64),
            )

    event = make_event("2026-10-20")
    recommender = EventRecommender(
        [event, event.copy()],
        DuplicateIndex(),
        lambda text: np.zeros((1, 384), dtype=np.float32),
    )

    results = recommender.recommend("programming", today=TODAY)

    assert len(results) == 1
    assert results[0]["event_id"] == "shockersync-123"
    assert results[0]["score"] == 90
