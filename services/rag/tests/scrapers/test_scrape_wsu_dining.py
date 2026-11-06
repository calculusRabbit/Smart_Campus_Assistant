"""Tests for official WSU dining page extraction."""

import pytest

from services.rag.scrapers.scrape_wsu_dining import (
    normalize_dining_name,
    parse_dining,
)


def make_teaser(title, description):
    return (
        '<div class="teaser">'
        f"<h2>{title}</h2>"
        f'<div class="teaser__editorial">{description}</div>'
        "</div>"
    )


def test_unicode_punctuation():
    assert normalize_dining_name("Chick\u2011fil\u2011A") == "chick-fil-a"
    assert normalize_dining_name("Freddy\u2019s Steakburgers") == ("freddy's steakburgers")


def test_rsc_restaurants():
    html = make_teaser(
        "Rhatigan Student Center Food Court",
        "Starbucks, Chick\u2011fil\u2011A, Freddy\u2019s Steakburgers, "
        "Panda Express, Sushi-Do, Shocker Sports Grill and Lanes",
    )
    records = parse_dining(html)

    assert len(records) == 6
    assert all(r["dining_location"] == "Rhatigan Student Center" for r in records)


def test_shocker_hall_nonbreaking_space():
    html = make_teaser(
        "Shocker Hall&nbsp;Dining",
        "Shocker Hall is home to a 400-seat dining hall. Next door is the GroundHouse.",
    )
    names = {r["dining_name"] for r in parse_dining(html)}

    assert names == {"Shocker Dining Hall", "GroundHouse"}


def test_food_truck_plaza():
    html = make_teaser(
        "Food trucks provide endless variety",
        "Food Truck Plaza features rotating food trucks.",
    )
    records = parse_dining(html)

    assert len(records) == 1
    assert records[0]["dining_name"] == "Food Truck Plaza"


def test_missing_dining_sections():
    with pytest.raises(ValueError, match="No recognized WSU dining sections"):
        parse_dining("<html><body><h1>Other page</h1></body></html>")


def test_no_unverified_restaurants():
    html = make_teaser(
        "Rhatigan Student Center Food Court",
        "Information about dining is temporarily unavailable.",
    )

    with pytest.raises(ValueError, match="No dining locations found"):
        parse_dining(html)
