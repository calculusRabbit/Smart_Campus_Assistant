"""Integration tests for ML-enhanced recommendation ranking."""

from datetime import date, datetime
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

import numpy as np

from services.event_recommender import EventRecommender

TODAY = date(2026, 11, 5)
NOW = datetime(2026, 11, 5, 12, 0, tzinfo=ZoneInfo("America/Chicago"))


def make_event(event_id, title, *, closed=False, expired=False):
    event_date = "2026-11-03" if expired else "2026-11-17"

    return {
        "id": str(event_id),
        "source": "shockersync",
        "title": title,
        "description": "Student art exhibition and creative artwork",
        "organization": "Student Art Club",
        "categories": (["Student Organization Closed Event"] if closed else []),
        "dates": [event_date],
        "start_date": event_date,
        "end_date": event_date,
        "end_datetime": f"{event_date}T20:00:00-06:00",
        "time": "6:00 PM",
        "location": "Campus",
        "url": f"https://example.com/events/{event_id}",
    }


def test_ml_bonus_changes_ranking_without_bypassing_filters():
    events = [
        make_event(1, "Student Art Exhibition A"),
        make_event(2, "Student Art Exhibition B"),
        make_event(3, "Student Art Exhibition Closed", closed=True),
        make_event(4, "Student Art Exhibition Expired", expired=True),
        make_event(5, "Student Art Exhibition Low Similarity"),
    ]

    index = Mock()
    index.ntotal = len(events)
    index.search.return_value = (
        np.array([[0.44, 0.42, 0.50, 0.48, 0.29]], dtype=np.float32),
        np.array([[0, 1, 2, 3, 4]], dtype=np.int64),
    )

    recommender = EventRecommender(
        events=events,
        index=index,
        embed=lambda text: np.zeros((1, 2), dtype=np.float32),
    )

    def fake_bonus(interest, title, description):
        return 0.05 if title == "Student Art Exhibition B" else 0.0

    with (
        patch(
            "services.event_recommender.get_theme_bonus",
            side_effect=fake_bonus,
        ),
        patch(
            "services.event_recommender.enrich_event_recommendations",
            side_effect=lambda results: results,
        ),
    ):
        results = recommender.recommend(
            "art",
            top_k=10,
            today=TODAY,
            now=NOW,
        )

    assert len(results) == 2

    assert results[0]["event_name"] == "Student Art Exhibition B"
    assert results[0]["score"] == 47

    assert results[1]["event_name"] == "Student Art Exhibition A"
    assert results[1]["score"] == 44

    assert all(
        "Closed" not in event["event_name"]
        and "Expired" not in event["event_name"]
        and "Low Similarity" not in event["event_name"]
        for event in results
    )
