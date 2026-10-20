from services.rag.build_events_index import transform_event


def test_multi_day_event_does_not_invent_daily_occurrences():
    raw = {
        "id": 12589950,
        "name": "Soccer Practice!",
        "description": "<p>Every Monday and Wednesday from 7-9pm.</p>",
        "startsOn": "2026-08-25T00:00:00+00:00",
        "endsOn": "2026-10-25T02:00:00+00:00",
        "organizationName": "Women's Club Soccer",
        "categoryNames": [],
        "location": "Metroplex",
    }

    event = transform_event(raw)

    assert event["start_date"] == "2026-08-24"
    assert event["end_date"] == "2026-10-24"
    assert event["dates"] == ["2026-08-24"]
