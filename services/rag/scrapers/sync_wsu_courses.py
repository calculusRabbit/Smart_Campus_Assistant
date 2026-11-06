"""Validate and preview official WSU course catalog synchronization."""

from typing import Any

from database import get_connection
from services.rag.scrapers.scrape_wsu_courses import COURSE_URLS, fetch_courses

DEPARTMENT_NAMES = {
    "CS": "School of Computing",
    "ECE": "Electrical and Computer Engineering",
    "ME": "Mechanical Engineering",
    "AE": "Aerospace Engineering",
    "BME": "Biomedical Engineering",
}


def fetch_eligible_courses() -> list[dict[str, Any]]:
    """Retrieve schema-compatible courses from official catalog pages."""
    eligible = []

    for prefix in COURSE_URLS:
        courses = fetch_courses(prefix)
        eligible.extend(course for course in courses if course["eligible"])

    return eligible


def validate_courses(courses: list[dict[str, Any]]) -> None:
    """Validate catalog courses before database synchronization."""
    if not courses:
        raise ValueError("No courses supplied")

    seen = set()

    for course in courses:
        prefix = course["course_code"]
        number = course["course_number"]
        key = (prefix, number)

        if prefix not in DEPARTMENT_NAMES:
            raise ValueError(f"Unknown department prefix: {prefix}")

        if key in seen:
            raise ValueError(f"Duplicate catalog course: {prefix} {number}")

        seen.add(key)

        if not course["eligible"]:
            raise ValueError(f"Ineligible course: {prefix} {number}")

        if len(course["course_name"]) > 75:
            raise ValueError(f"Course name exceeds limit: {prefix} {number}")

        if len(course["course_description"]) > 500:
            raise ValueError(f"Description exceeds limit: {prefix} {number}")


def preview_sync(courses: list[dict[str, Any]]) -> dict[str, int]:
    """Compare catalog records with PostgreSQL without changing the database."""
    validate_courses(courses)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT department_id, department_name
                FROM departments
                WHERE department_name = ANY(%s)
            """,
                (list(DEPARTMENT_NAMES.values()),),
            )

            departments = {
                row["department_name"]: row["department_id"] for row in cursor.fetchall()
            }

            if len(departments) != len(DEPARTMENT_NAMES):
                raise ValueError("Not all required WSU departments exist")

            cursor.execute("""
                SELECT department_id, course_code, course_number
                FROM courses
            """)

            existing = {
                (
                    row["department_id"],
                    row["course_code"],
                    row["course_number"],
                )
                for row in cursor.fetchall()
            }

    new_count = 0
    existing_count = 0

    for course in courses:
        department_id = departments[DEPARTMENT_NAMES[course["course_code"]]]

        key = (
            department_id,
            course["course_code"],
            course["course_number"],
        )

        if key in existing:
            existing_count += 1
        else:
            new_count += 1

    return {
        "courses_total": len(courses),
        "would_insert": new_count,
        "already_existing": existing_count,
    }


def apply_sync(
    courses: list[dict[str, Any]],
    commit: bool = False,
) -> dict[str, int | bool]:
    """Synchronize eligible WSU courses with explicit commit control."""
    preview = preview_sync(courses)

    if not commit:
        return {
            "courses_total": preview["courses_total"],
            "inserted": preview["would_insert"],
            "already_existing": preview["already_existing"],
            "committed": False,
        }

    inserted = 0

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT department_id, department_name
                FROM departments
                WHERE department_name = ANY(%s)
            """,
                (list(DEPARTMENT_NAMES.values()),),
            )

            departments = {
                row["department_name"]: row["department_id"] for row in cursor.fetchall()
            }

            if len(departments) != len(DEPARTMENT_NAMES):
                raise ValueError("Required WSU departments are missing")

            cursor.execute("""
                SELECT last_value, is_called
                FROM public.courses_course_id_seq
            """)
            sequence_state = cursor.fetchone()
            next_id = (
                sequence_state["last_value"] + 1
                if sequence_state["is_called"]
                else sequence_state["last_value"]
            )

            cursor.execute("""
                SELECT COALESCE(MAX(course_id), 0) AS highest_id
                FROM courses
            """)
            highest_id = cursor.fetchone()["highest_id"]

            if next_id <= highest_id:
                raise ValueError("Course ID sequence is behind existing records")

            cursor.execute("""
                SELECT department_id, course_code, course_number
                FROM courses
            """)

            existing_keys = {
                (
                    row["department_id"],
                    row["course_code"],
                    row["course_number"],
                )
                for row in cursor.fetchall()
            }

            for course in courses:
                prefix = course["course_code"]
                number = course["course_number"]

                if not course["eligible"]:
                    raise ValueError(f"Ineligible course: {prefix} {number}")

                credits = course["course_credits"]

                if credits is None:
                    raise ValueError(f"Variable credits cannot be inserted: {prefix} {number}")

                department_id = departments[DEPARTMENT_NAMES[prefix]]

                course_key = (department_id, prefix, number)

                if course_key in existing_keys:
                    continue

                cursor.execute(
                    """
                    INSERT INTO courses (
                        course_id,
                        department_id,
                        course_code,
                        course_number,
                        course_name,
                        course_description,
                        course_credits
                    )
                    VALUES (
                        nextval('public.courses_course_id_seq'),
                        %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (
                        department_id,
                        course_code,
                        course_number
                    ) DO NOTHING
                    RETURNING course_id
                """,
                    (
                        department_id,
                        prefix,
                        number,
                        course["course_name"],
                        course["course_description"],
                        credits,
                    ),
                )

                if cursor.fetchone() is not None:
                    inserted += 1

        connection.commit()

    return {
        "courses_total": len(courses),
        "inserted": inserted,
        "already_existing": len(courses) - inserted,
        "committed": True,
    }
