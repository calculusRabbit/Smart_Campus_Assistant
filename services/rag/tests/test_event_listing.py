from datetime import date, datetime
from zoneinfo import ZoneInfo


def test_list_upcoming_events_excludes_past_and_closed():
    from services.event_recommender import list_upcoming_events

    def event(event_id, event_date, category="Campus Wide", end_hour=18):
        return {
            "id": str(event_id),
            "source": "shockersync",
            "title": f"Event {event_id}",
            "dates": [event_date],
            "start_date": event_date,
            "end_date": event_date,
            "end_datetime": f"{event_date}T{end_hour:02d}:00:00-06:00",
            "time": "5:00 PM",
            "location": "RSC",
            "description": "Campus activity",
            "categories": [category],
            "url": f"https://wichita.campuslabs.com/engage/event/{event_id}",
        }

    events = [
        event(1, "2026-11-02"),
        event(2, "2026-11-04"),
        event(3, "2026-11-05", "Student Organization Closed Event"),
        event(4, "2026-12-15"),
        event(5, "2026-11-03", end_hour=9),
    ]

    now = datetime(
        2026,
        11,
        3,
        12,
        0,
        tzinfo=ZoneInfo("America/Chicago"),
    )

    results = list_upcoming_events(
        events,
        today=date(2026, 11, 3),
        now=now,
        limit=10,
    )

    assert len(results) == 1
    assert results[0]["event_id"] == "shockersync-2"
    assert results[0]["event_name"] == "Event 2"
    assert results[0]["event_date"] == "2026-11-04"


def test_recommendations_exclude_closed_events(monkeypatch):
    """Closed events must not enter personalized recommendation scoring."""
    from datetime import date, datetime
    from zoneinfo import ZoneInfo

    from services import event_recommender

    today = date(2026, 11, 3)
    now = datetime(2026, 11, 3, 10, 0, tzinfo=ZoneInfo("America/Chicago"))

    monkeypatch.setattr(
        event_recommender,
        "matches_event_topic",
        lambda event, query: True,
    )
    monkeypatch.setattr(
        event_recommender,
        "matches_requested_activity",
        lambda event, query: True,
    )
    monkeypatch.setattr(
        event_recommender,
        "_score_upcoming_event",
        lambda *args: ("2026-11-13", 0.8),
    )

    closed_event = {
        "categories": ["Student Organization Closed Event"],
    }
    public_event = {
        "categories": ["Campus Events"],
    }

    def score_event(event):
        return event_recommender._score_matching_event(event, 0.8, [], today, now, "career")

    assert score_event(closed_event) is None
    assert score_event(public_event) == ("2026-11-13", 0.8)
