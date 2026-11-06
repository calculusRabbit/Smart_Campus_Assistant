"""Regression tests for hybrid recommendation eligibility."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from services.event_recommender import _score_matching_event

TODAY = date(2026, 11, 5)
NOW = datetime(2026, 11, 5, 12, 0, tzinfo=ZoneInfo("America/Chicago"))


def make_event(
    *,
    categories=None,
    event_date="2026-11-17",
    end_datetime="2026-11-17T20:00:00-06:00",
):
    return {
        "title": "Student Art Exhibition",
        "description": "Student paintings and creative artwork",
        "organization": "Student Art Club",
        "categories": categories if categories is not None else [],
        "dates": [event_date],
        "start_date": event_date,
        "end_date": event_date,
        "end_datetime": end_datetime,
    }


def score_event(event, similarity=0.44):
    return _score_matching_event(
        event,
        similarity,
        [],
        TODAY,
        NOW,
        "art",
    )


def test_eligible_art_event_passes_filters():
    result = score_event(make_event())
    assert result is not None


def test_closed_event_is_excluded():
    event = make_event(categories=["Student Organization Closed Event"])
    assert score_event(event) is None


def test_low_similarity_event_is_excluded():
    assert score_event(make_event(), similarity=0.29) is None


def test_expired_event_is_excluded():
    event = make_event(
        event_date="2026-11-03",
        end_datetime="2026-11-03T20:00:00-06:00",
    )
    assert score_event(event) is None


def test_out_of_window_event_is_excluded():
    event = make_event(
        event_date="2027-01-15",
        end_datetime="2027-01-15T20:00:00-06:00",
    )
    assert score_event(event) is None


def test_ml_bonus_does_not_change_eligibility():
    event = make_event(categories=["Student Organization Closed Event"])

    # Even if a classifier would award a positive bonus,
    # closed events must fail the existing eligibility checks.
    assert score_event(event) is None
