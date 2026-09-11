from datetime import date, timedelta
from scrapers.scraper import should_keep


def test_recent_event_is_kept():
    today = date.today().isoformat()
    assert should_keep(today, ["Student Life"]) is True


def test_old_event_is_dropped():
    old_date = (date.today() - timedelta(days=400)).isoformat()
    assert should_keep(old_date, ["Student Life"]) is False
