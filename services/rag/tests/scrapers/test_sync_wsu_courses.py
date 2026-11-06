"""Tests for WSU course synchronization validation."""

import pytest

from services.rag.scrapers.sync_wsu_courses import validate_courses


def sample_course(**overrides):
    course = {
        "course_code": "CS",
        "course_number": "211",
        "course_name": "Introduction to Programming",
        "course_description": "Introduction to computer programming.",
        "course_credits": 4.0,
        "eligible": True,
    }
    course.update(overrides)
    return course


def test_valid_course():
    validate_courses([sample_course()])


def test_empty_course_list():
    with pytest.raises(ValueError, match="No courses supplied"):
        validate_courses([])


def test_duplicate_courses():
    with pytest.raises(ValueError, match="Duplicate catalog course"):
        validate_courses([sample_course(), sample_course()])


def test_unknown_department():
    with pytest.raises(ValueError, match="Unknown department prefix"):
        validate_courses([sample_course(course_code="UNKNOWN")])


def test_ineligible_course():
    with pytest.raises(ValueError, match="Ineligible course"):
        validate_courses([sample_course(eligible=False)])


def test_long_course_name():
    with pytest.raises(ValueError, match="Course name exceeds limit"):
        validate_courses([sample_course(course_name="A" * 76)])


def test_long_course_description():
    with pytest.raises(ValueError, match="Description exceeds limit"):
        validate_courses([sample_course(course_description="A" * 501)])


def test_apply_sync_dry_run_never_writes(monkeypatch):
    """Dry-run mode must not open a connection or advance sequences."""
    from services.rag.scrapers import sync_wsu_courses

    course = sample_course()

    def fake_preview(courses):
        assert courses == [course]
        return {
            "courses_total": 1,
            "would_insert": 1,
            "already_existing": 0,
        }

    def forbidden_connection():
        raise AssertionError("Dry-run mode must not open a database connection here")

    monkeypatch.setattr(
        sync_wsu_courses,
        "preview_sync",
        fake_preview,
    )
    monkeypatch.setattr(
        sync_wsu_courses,
        "get_connection",
        forbidden_connection,
    )

    result = sync_wsu_courses.apply_sync([course], commit=False)

    assert result == {
        "courses_total": 1,
        "inserted": 1,
        "already_existing": 0,
        "committed": False,
    }


class FakeSyncCursor:
    """Simulate PostgreSQL queries for course synchronization tests."""

    def __init__(self, existing=False, fail_insert=False):
        self.existing = existing
        self.fail_insert = fail_insert
        self.rows = []
        self.queries = []
        self.insert_attempted = False

    def execute(self, query, params=None):
        from services.rag.scrapers.sync_wsu_courses import DEPARTMENT_NAMES

        sql = " ".join(query.split())
        self.queries.append(sql)

        if "SELECT department_id, department_name" in sql:
            self.rows = [
                {"department_id": index, "department_name": name}
                for index, name in enumerate(DEPARTMENT_NAMES.values(), start=1)
            ]
        elif "FROM public.courses_course_id_seq" in sql:
            self.rows = [{"last_value": 10, "is_called": True}]
        elif "SELECT COALESCE(MAX(course_id)" in sql:
            self.rows = [{"highest_id": 10}]
        elif "SELECT department_id, course_code, course_number" in sql:
            self.rows = (
                [{"department_id": 1, "course_code": "CS", "course_number": "211"}]
                if self.existing
                else []
            )
        elif "INSERT INTO courses" in sql:
            self.insert_attempted = True
            if self.fail_insert:
                raise RuntimeError("Simulated database insertion failure")
            self.rows = [{"course_id": 11}]
        else:
            raise AssertionError(f"Unexpected SQL: {sql}")

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class FakeSyncConnection:
    """Track commit and rollback behavior."""

    def __init__(self, existing=False, fail_insert=False):
        self.test_cursor = FakeSyncCursor(existing, fail_insert)
        self.commit_called = False
        self.rollback_called = False

    def cursor(self):
        return self.test_cursor

    def commit(self):
        self.commit_called = True

    def rollback(self):
        self.rollback_called = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self.rollback()
        return False


def mock_sync_database(monkeypatch, connection, existing=0):
    """Replace database dependencies with predictable test doubles."""
    from services.rag.scrapers import sync_wsu_courses

    monkeypatch.setattr(
        sync_wsu_courses,
        "preview_sync",
        lambda courses: {
            "courses_total": len(courses),
            "would_insert": len(courses) - existing,
            "already_existing": existing,
        },
    )
    monkeypatch.setattr(
        sync_wsu_courses,
        "get_connection",
        lambda: connection,
    )


def test_apply_sync_skips_existing_course(monkeypatch):
    """Existing courses must not trigger an INSERT or nextval."""
    from services.rag.scrapers import sync_wsu_courses

    connection = FakeSyncConnection(existing=True)
    mock_sync_database(monkeypatch, connection, existing=1)

    result = sync_wsu_courses.apply_sync(
        [sample_course()],
        commit=True,
    )

    assert result == {
        "courses_total": 1,
        "inserted": 0,
        "already_existing": 1,
        "committed": True,
    }
    assert not connection.test_cursor.insert_attempted
    assert not any("INSERT INTO courses" in sql for sql in connection.test_cursor.queries)
    assert connection.commit_called
    assert not connection.rollback_called


def test_apply_sync_rolls_back_on_insert_failure(monkeypatch):
    """An insertion failure must propagate without committing."""
    from services.rag.scrapers import sync_wsu_courses

    connection = FakeSyncConnection(fail_insert=True)
    mock_sync_database(monkeypatch, connection)

    with pytest.raises(
        RuntimeError,
        match="Simulated database insertion failure",
    ):
        sync_wsu_courses.apply_sync([sample_course()], commit=True)

    assert connection.test_cursor.insert_attempted
    assert connection.rollback_called
    assert not connection.commit_called
