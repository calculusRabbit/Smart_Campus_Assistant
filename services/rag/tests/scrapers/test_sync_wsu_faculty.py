"""Integration tests for WSU faculty synchronization."""

import pytest

from database import get_connection
from services.rag.scrapers.sync_wsu_faculty import apply_sync, validate_faculty


def test_faculty_sync_rolls_back():
    faculty = [
        {
            "name": "Integration Test Professor",
            "email": "integration.test.professor@wichita.edu",
        }
    ]

    result = apply_sync(faculty, commit=False)

    assert result["faculty_total"] == 1
    assert result["committed"] is False

    with get_connection() as connection:
        with connection.cursor() as cursor:
            emails = [person["email"] for person in faculty]

            cursor.execute(
                """
                SELECT COUNT(*) AS count
                FROM instructors
                WHERE instructor_email = ANY(%s)
                """,
                (emails,),
            )

            assert cursor.fetchone()["count"] == result["already_existing"]


def test_duplicate_faculty_emails_rejected():
    faculty = [
        {
            "name": "Test Professor",
            "email": "test.professor@wichita.edu",
        }
    ]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS count FROM instructors")
            before = cursor.fetchone()["count"]

    try:
        apply_sync(faculty + faculty, commit=False)
    except ValueError as error:
        assert "Duplicate faculty emails" in str(error)
    else:
        raise AssertionError("Expected duplicate faculty validation error")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS count FROM instructors")
            after = cursor.fetchone()["count"]

    assert before == after


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
