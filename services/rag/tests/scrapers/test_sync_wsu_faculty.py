"""Integration tests for WSU faculty synchronization."""

import pytest

from services.rag.scrapers.sync_wsu_faculty import apply_sync, validate_faculty


def test_faculty_sync_rolls_back(monkeypatch):
    """Verify dry-run synchronization rolls back its transaction."""
    from unittest.mock import MagicMock

    faculty = [
        {
            "name": "Integration Test Professor",
            "email": "integration.test.professor@wichita.edu",
        }
    ]

    connection = MagicMock()
    connection.__enter__.return_value = connection

    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor

    cursor.fetchone.side_effect = [
        {"school_id": 1},
        {"department_id": 2},
        {"instructor_id": 3},
    ]

    monkeypatch.setattr(
        "services.rag.scrapers.sync_wsu_faculty.get_connection",
        lambda: connection,
    )

    result = apply_sync(faculty, commit=False)

    assert result["faculty_total"] == 1
    assert result["inserted"] == 1
    assert result["already_existing"] == 0
    assert result["committed"] is False
    connection.rollback.assert_called_once()


def test_duplicate_faculty_emails_rejected(monkeypatch):
    """Duplicate records must fail before opening a database connection."""
    faculty = [
        {
            "name": "Test Professor",
            "email": "test.professor@wichita.edu",
        }
    ]

    def unexpected_connection():
        raise AssertionError(
            "Database connection must not occur for duplicate faculty."
        )

    monkeypatch.setattr(
        "services.rag.scrapers.sync_wsu_faculty.get_connection",
        unexpected_connection,
    )

    with pytest.raises(ValueError, match="Duplicate faculty emails"):
        apply_sync(faculty + faculty, commit=False)


def test_invalid_faculty_name_rejected():
    faculty = [
        {"name": "SingleName", "email": "single.name@wichita.edu"}
    ]

    with pytest.raises(ValueError, match="Invalid faculty name"):
        validate_faculty(faculty)


def test_invalid_email_domain_rejected():
    faculty = [
        {"name": "Jane Smith", "email": "jane.smith@example.com"}
    ]

    with pytest.raises(ValueError, match="Invalid WSU faculty email"):
        validate_faculty(faculty)


def test_overlong_faculty_name_rejected():
    faculty = [
        {
            "name": "A" * 30 + " Smith",
            "email": "long.name@wichita.edu",
        }
    ]

    with pytest.raises(ValueError, match="exceeds database limits"):
        validate_faculty(faculty)
