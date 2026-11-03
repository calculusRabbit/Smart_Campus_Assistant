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
