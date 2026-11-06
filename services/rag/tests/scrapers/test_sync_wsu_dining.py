"""Tests for WSU dining synchronization validation."""

import pytest

from services.rag.scrapers.scrape_wsu_dining import DINING_URL
from services.rag.scrapers.sync_wsu_dining import (
    location_marker,
    validate_dining,
)


def make_record(name="Starbucks", area="Rhatigan Student Center"):
    return {
        "dining_name": name,
        "dining_location": area,
        "source_url": DINING_URL,
        "verified": True,
        "cuisine": [],
    }


def test_valid_dining_records():
    records = [
        make_record("Starbucks", "Rhatigan Student Center"),
        make_record("Starbucks", "Innovation Campus"),
    ]
    validate_dining(records)


def test_duplicate_name_and_location_rejected():
    records = [make_record(), make_record()]

    with pytest.raises(ValueError, match="Duplicate dining record"):
        validate_dining(records)


def test_same_name_different_locations_allowed():
    validate_dining(
        [
            make_record("Starbucks", "Rhatigan Student Center"),
            make_record("Starbucks", "Innovation Campus"),
        ]
    )


def test_unverified_record_rejected():
    record = make_record()
    record["verified"] = False

    with pytest.raises(ValueError, match="Unverified dining record"):
        validate_dining([record])


def test_unexpected_source_rejected():
    record = make_record()
    record["source_url"] = "https://example.com"

    with pytest.raises(ValueError, match="Unexpected dining source"):
        validate_dining([record])


def test_dining_name_length_limit():
    with pytest.raises(ValueError, match="Invalid dining name"):
        validate_dining([make_record(name="A" * 76)])


def test_empty_records_rejected():
    with pytest.raises(ValueError, match="No dining records supplied"):
        validate_dining([])


def test_location_marker():
    assert location_marker("Shocker Hall") == ("Official WSU dining area: Shocker Hall")
