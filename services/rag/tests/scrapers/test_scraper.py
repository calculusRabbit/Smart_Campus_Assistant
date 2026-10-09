from datetime import date, timedelta
from scrapers.scraper import should_keep


def test_recent_event_is_kept():
    today = date.today().isoformat()
    assert should_keep(today, ["Student Life"]) is True


def test_old_event_is_dropped():
    old_date = (date.today() - timedelta(days=400)).isoformat()
    assert should_keep(old_date, ["Student Life"]) is False

from bs4 import BeautifulSoup
from scrapers.scraper import (
    clean_text,
    parse_description,
    format_chunk,
    find_existing,
)


def test_clean_text_removes_extra_whitespace():
    result = clean_text("  Japan   Festival \n at WSU  ")
    assert result == "Japan Festival at WSU"


def test_parse_description_extracts_html_text():
    html = """
    <article>
        <div itemprop="description">
            Join us for the Japan Festival.<br>
            Everyone is welcome.
        </div>
    </article>
    """
    soup = BeautifulSoup(html, "html.parser")

    result = parse_description(soup)

    assert result == "Join us for the Japan Festival. Everyone is welcome."


def test_parse_description_missing_element():
    soup = BeautifulSoup("<article><h1>Event</h1></article>", "html.parser")

    assert parse_description(soup) == ""


def test_invalid_date_is_kept():
    assert should_keep("invalid-date", ["Student Life"]) is True


def test_old_academic_event_is_dropped():
    old_date = (date.today() - timedelta(days=200)).isoformat()

    assert should_keep(old_date, ["Academic Calendar"]) is False


def test_format_chunk_includes_event_details():
    event = {
        "title": "Japan Festival",
        "start_date": "2026-10-20",
        "end_date": "2026-10-21",
        "time": "10:00 AM",
        "location": "Rhatigan Student Center",
        "description": "Celebrate Japanese culture",
        "categories": ["Student Life", "Culture"],
        "cost": "Free",
    }

    result = format_chunk(event)

    assert "Japan Festival on 2026-10-20 to 2026-10-21" in result
    assert "at 10:00 AM" in result
    assert "Rhatigan Student Center" in result
    assert "Celebrate Japanese culture" in result
    assert "Student Life, Culture" in result
    assert "It is Free" in result


def test_find_existing_returns_matching_event():
    events = [
        {"title": "Japan Festival", "eid": 1},
        {"title": "Career Fair", "eid": 2},
    ]

    assert find_existing(events, "Career Fair") == events[1]


def test_find_existing_returns_none_when_missing():
    events = [{"title": "Japan Festival", "eid": 1}]

    assert find_existing(events, "Unknown Event") is None

from unittest.mock import Mock
from scrapers import scraper


def test_scrape_event_extracts_event_information(monkeypatch):
    html = """
    <article class="wsu_calendar_event_display">
        <h1 itemprop="name">Japan Festival</h1>

        <add-to-calendar-button
            startdate="2026-10-20"
            enddate="2026-10-20">
        </add-to-calendar-button>

        <time itemprop="startDate">10:00 AM</time>

        <div id="event-details">
            <p>Cost: Free</p>
        </div>

        <a itemprop="location">Rhatigan Student Center</a>
        <a itemprop="eventType">Student Life</a>

        <div itemprop="description">
            Celebrate Japanese culture at WSU.
        </div>
    </article>
    """

    fake_response = Mock()
    fake_response.status_code = 200
    fake_response.text = html

    mock_get = Mock(return_value=fake_response)
    monkeypatch.setattr(scraper.requests, "get", mock_get)

    result = scraper.scrape_event(12345)

    assert result is not None
    assert result["eid"] == 12345
    assert result["title"] == "Japan Festival"
    assert result["start_date"] == "2026-10-20"
    assert result["end_date"] == "2026-10-20"
    assert result["time"] == "10:00 AM"
    assert result["cost"] == "Free"
    assert result["location"] == "Rhatigan Student Center"
    assert result["categories"] == ["Student Life"]
    assert result["description"] == "Celebrate Japanese culture at WSU."
    assert "Japan Festival" in result["chunk_text"]

    mock_get.assert_called_once_with(
        "https://www.wichita.edu/calendar/index.php?eID=12345",
        timeout=10,
    )

import requests


def test_scrape_event_handles_network_failure(monkeypatch):
    def fail_request(*args, **kwargs):
        raise requests.RequestException("Connection failed")

    monkeypatch.setattr(scraper.requests, "get", fail_request)

    assert scraper.scrape_event(12345) is None


def test_scrape_event_rejects_invalid_page(monkeypatch):
    fake_response = Mock(
        status_code=200,
        text="<html><body>No event found</body></html>",
    )

    monkeypatch.setattr(
        scraper.requests, "get",
        lambda *args, **kwargs: fake_response,
    )

    assert scraper.scrape_event(12345) is None


def test_scrape_event_rejects_missing_title(monkeypatch):
    html = """
    <article class="wsu_calendar_event_display">
        <add-to-calendar-button startdate="2026-10-20">
        </add-to-calendar-button>
    </article>
    """

    fake_response = Mock(status_code=200, text=html)

    monkeypatch.setattr(
        scraper.requests, "get",
        lambda *args, **kwargs: fake_response,
    )

    assert scraper.scrape_event(12345) is None


def test_scrape_event_filters_old_events(monkeypatch):
    html = """
    <article class="wsu_calendar_event_display">
        <h1 itemprop="name">Old Campus Event</h1>
        <add-to-calendar-button
            startdate="2020-01-01"
            enddate="2020-01-01">
        </add-to-calendar-button>
    </article>
    """

    fake_response = Mock(status_code=200, text=html)

    monkeypatch.setattr(
        scraper.requests, "get",
        lambda *args, **kwargs: fake_response,
    )

    assert scraper.scrape_event(12345) is None

def test_main_saves_and_merges_events(monkeypatch, tmp_path):
    from scrapers import scraper

    output_file = tmp_path / "events.json"
    monkeypatch.setattr(scraper, "OUTPUT_FILE", output_file)

    # Keep the test small instead of scraping thousands of event IDs.
    real_range = range

    def small_range(*args):
        if args == (33000, 19999, -1):
            return iter([33000, 32999])
        return real_range(*args)

    monkeypatch.setattr("builtins.range", small_range)
    monkeypatch.setattr(scraper.time, "sleep", lambda seconds: None)

    events = {
        33000: {
            "title": "Japan Festival",
            "start_date": "2026-10-20",
            "end_date": "2026-10-20",
        },
        32999: {
            "title": "Japan Festival",
            "start_date": "2026-10-21",
            "end_date": "2026-10-21",
        },
    }

    def fake_scrape_event(eid):
        event = events[eid].copy()
        event.update({
            "time": "10:00 AM",
            "location": "Rhatigan Student Center",
            "description": "Cultural celebration",
            "categories": ["Student Life"],
            "cost": "Free",
        })
        event["chunk_text"] = scraper.format_chunk(event)
        return event

    monkeypatch.setattr(scraper, "scrape_event", fake_scrape_event)

    scraper.main()

    import json

    saved = json.loads(output_file.read_text(encoding="utf-8"))

    assert len(saved) == 1
    assert saved[0]["title"] == "Japan Festival"
    assert saved[0]["start_date"] == "2026-10-20"
    assert saved[0]["end_date"] == "2026-10-21"

def test_scrape_event_extracts_real_wsu_location(monkeypatch):
    from scrapers import scraper

    html = """
    <article class="wsu_calendar_event_display">
        <h1 itemprop="name">Campus Event</h1>

        <div itemprop="location"
             itemscope
             itemtype="http://schema.org/Place">
            <h3 class="location heading5">Location:</h3>
            <p>
                <a href="/calendar/index.php?com=location&lID=38">
                    Wilner Auditorium
                </a>
            </p>
        </div>
    </article>
    """

    class FakeResponse:
        status_code = 200
        text = html

    monkeypatch.setattr(
        scraper.requests,
        "get",
        lambda *args, **kwargs: FakeResponse()
    )

    # Avoid relying on the actual date-filtering behavior.
    monkeypatch.setattr(
        scraper,
        "parse_description",
        lambda *args, **kwargs: "Campus event at Wilner Auditorium."
    )

    event = scraper.scrape_event(33000)

    assert event is not None
    assert event["location"] == "Wilner Auditorium"