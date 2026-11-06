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


@pytest.mark.parametrize(
    ("original", "expected"),
    [
        ("Rajiv Bagai", ("Rajiv", "Bagai")),
        ("Dr. Rajeev Nair", ("Rajeev", "Nair")),
        ("Visvakumar Aravinthan, Ph.D.", ("Visvakumar", "Aravinthan")),
        ("Ali Gordon Ph.D., F. ASME", ("Ali", "Gordon")),
        ("Hyuck M. Kwon, Ph.D.", ("Hyuck", "M. Kwon")),
        ("Sergio Salinas Monroy", ("Sergio", "Salinas Monroy")),
        ("Dr. T.S. Ravi", ("T.S.", "Ravi")),
        ("A.V.M. Raza MS", ("A.V.M.", "Raza")),
        ("Chihdar (Charles) Yang, Ph.D.", ("Chihdar", "(Charles) Yang")),
    ],
)
def test_normalize_faculty_name(original, expected):
    from services.rag.scrapers.sync_wsu_faculty import normalize_faculty_name

    assert normalize_faculty_name(original) == expected


def test_apply_sync_uses_normalized_faculty_name(monkeypatch):
    """Verify academic titles are removed before database insertion."""
    from unittest.mock import MagicMock

    faculty = [
        {
            "name": "Dr. Rajeev Nair",
            "email": "rajeev.nair@wichita.edu",
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

    apply_sync(faculty, commit=False)

    insert_calls = [
        call
        for call in cursor.execute.call_args_list
        if "INSERT INTO instructors" in call.args[0]
    ]

    assert len(insert_calls) == 1
    parameters = insert_calls[0].args[1]

    assert parameters[0] == "Rajeev"
    assert parameters[1] == "Nair"
    connection.rollback.assert_called_once()


def test_apply_sync_uses_correct_department(monkeypatch):
    """Verify ECE faculty are assigned to the correct department."""
    from unittest.mock import MagicMock

    faculty = [
        {
            "name": "Visvakumar Aravinthan, Ph.D.",
            "email": "visvakumar.aravinthan@wichita.edu",
            "department": "Electrical and Computer Engineering",
        }
    ]

    connection = MagicMock()
    connection.__enter__.return_value = connection

    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchone.side_effect = [
        {"school_id": 1},
        {"department_id": 5},
        {"instructor_id": 10},
    ]

    monkeypatch.setattr(
        "services.rag.scrapers.sync_wsu_faculty.get_connection",
        lambda: connection,
    )

    apply_sync(faculty, commit=False)

    department_calls = [
        call
        for call in cursor.execute.call_args_list
        if "INSERT INTO departments" in call.args[0]
    ]

    assert len(department_calls) == 1

    parameters = department_calls[0].args[1]
    assert parameters[1] == "Electrical and Computer Engineering"
    assert parameters[2] == "ECE"

    connection.rollback.assert_called_once()


def test_apply_sync_supports_multiple_departments(monkeypatch):
    """Faculty from different departments must get correct department IDs."""
    from unittest.mock import MagicMock

    faculty = [
        {
            "name": "Rajiv Bagai",
            "email": "rajiv.bagai@wichita.edu",
            "department": "School of Computing",
        },
        {
            "name": "Visvakumar Aravinthan, Ph.D.",
            "email": "visvakumar.aravinthan@wichita.edu",
            "department": "Electrical and Computer Engineering",
        },
    ]

    connection = MagicMock()
    connection.__enter__.return_value = connection

    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchone.side_effect = [
        {"school_id": 1},
        {"department_id": 2},
        {"department_id": 3},
        {"instructor_id": 10},
        {"instructor_id": 11},
    ]

    monkeypatch.setattr(
        "services.rag.scrapers.sync_wsu_faculty.get_connection",
        lambda: connection,
    )

    result = apply_sync(faculty, commit=False)

    department_calls = [
        call
        for call in cursor.execute.call_args_list
        if "INSERT INTO departments" in call.args[0]
    ]

    instructor_calls = [
        call
        for call in cursor.execute.call_args_list
        if "INSERT INTO instructors" in call.args[0]
    ]

    assert len(department_calls) == 2
    assert len(instructor_calls) == 2

    department_parameters = {
        call.args[1][1]: call.args[1][2]
        for call in department_calls
    }
    assert department_parameters == {
        "School of Computing": "SOC",
        "Electrical and Computer Engineering": "ECE",
    }

    instructor_department_ids = {
        call.args[1][3]: call.args[1][2]
        for call in instructor_calls
    }
    assert instructor_department_ids == {
        "rajiv.bagai@wichita.edu": 2,
        "visvakumar.aravinthan@wichita.edu": 3,
    }

    assert result["faculty_total"] == 2
    assert result["inserted"] == 2
    assert result["committed"] is False
    connection.rollback.assert_called_once()
