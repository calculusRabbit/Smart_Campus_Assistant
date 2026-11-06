"""Regression tests for WSU's published dining schedules."""

import pytest

from database import get_dining_hours_for_day
from services.rag.scrapers.scrape_wsu_dining_hours import (
    parse_hours,
    parse_schedule_entry,
)

# Schedule values transcribed from WSU's official Fall 2026 hours page.
WSU_HOURS_HTML = """
<h3>Starbucks</h3>
<p>
<strong>Mon-Thurs:</strong>7 a.m. - 9 p.m.<br/>
<strong>Fri:</strong>7 a.m. - 7 p.m.<br/>
<strong>Sat:</strong>9 a.m. - 4 p.m.<br/>
</p>
<h3>Chick-fil-A</h3>
<p>
<strong>Mon-Thurs:</strong>7 a.m. - 7 p.m.<br/>
<strong>Fri:</strong>7 a.m. - 5 p.m.<br/>
<strong>Sat:</strong>11 a.m. - 2 p.m.<br/>
</p>
<h3>Panda Express</h3>
<p>
<strong>Mon-Thurs:</strong>10 a.m. - 7 p.m.<br/>
<strong>Fri:</strong>10 a.m. - 5 p.m.<br/>
</p>
<h3>Freddy's</h3>
<p>
<strong>Mon-Thurs:</strong>10 a.m. - 7 p.m.<br/>
<strong>Fri:</strong>10 a.m. - 5 p.m.<br/>
</p>
<h3>Sushi Do</h3>
<p>
<strong>Mon-Thurs:</strong>10 a.m. - 7 p.m.<br/>
<strong>Fri:</strong>10 a.m. - 5 p.m.<br/>
</p>
"""


def test_parse_all_five_published_restaurants():
    schedules = parse_hours(WSU_HOURS_HTML)
    assert set(schedules) == {
        "Starbucks",
        "Chick-fil-A",
        "Panda Express",
        "Freddy's Steakburgers",
        "Sushi-Do",
    }


def test_starbucks_weekday_hours():
    schedule = parse_hours(WSU_HOURS_HTML)["Starbucks"]

    assert get_dining_hours_for_day(schedule, 0) == ("7:00 AM", "9:00 PM")
    assert get_dining_hours_for_day(schedule, 4) == ("7:00 AM", "7:00 PM")
    assert get_dining_hours_for_day(schedule, 5) == ("9:00 AM", "4:00 PM")


def test_chick_fil_a_saturday_hours():
    schedule = parse_hours(WSU_HOURS_HTML)["Chick-fil-A"]

    assert get_dining_hours_for_day(schedule, 5) == ("11:00 AM", "2:00 PM")


def test_unpublished_sunday_hours_remain_unknown():
    schedules = parse_hours(WSU_HOURS_HTML)

    for schedule in schedules.values():
        assert get_dining_hours_for_day(schedule, 6) == ("N/A", "N/A")


def test_unknown_day_label_rejected():
    with pytest.raises(ValueError, match="Unknown day label"):
        parse_schedule_entry("Unknown:", "7 a.m. - 9 p.m.")


def test_invalid_time_range_rejected():
    with pytest.raises(ValueError, match="Invalid hours"):
        parse_schedule_entry("Fri:", "not published")


def test_missing_schedule_rejected():
    with pytest.raises(ValueError, match="Missing hours"):
        parse_hours("<h3>Starbucks</h3>")


def test_empty_page_rejected():
    with pytest.raises(ValueError, match="No official RSC dining hours"):
        parse_hours("<html><body>No dining schedules</body></html>")
