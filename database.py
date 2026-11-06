import os
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import psycopg
from psycopg.abc import Params
from psycopg.rows import dict_row

DATABASE_NAME = os.getenv("POSTGRES_DB", "smart_campus")

# the database keeps times in utc, we show them in wichita time
LOCAL_TIMEZONE = ZoneInfo("America/Chicago")

# day numbers in class_timings and open_hours, i am guessing 0 is monday
DAY_LETTERS = ["M", "T", "W", "R", "F", "Sa", "Su"]


def get_connection() -> psycopg.Connection[dict[str, Any]]:
    postgres_host = os.getenv("POSTGRES_HOST")

    # Docker / environment-based connection
    if postgres_host:
        return psycopg.connect(
            dbname=DATABASE_NAME,
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=postgres_host,
            port=os.getenv("POSTGRES_PORT", "5432"),
            row_factory=dict_row
        )

    # Existing local PostgreSQL connection
    return psycopg.connect(
        dbname=DATABASE_NAME,
        row_factory=dict_row
    )


def fetch_all(
    query: str,
    params: Params | None = None,
) -> list[dict[str, Any]]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


def format_clock(text: str) -> str:
    # "13:30" -> "1:30 PM"
    try:
        return datetime.strptime(text, "%H:%M").strftime("%I:%M %p").lstrip("0")
    except ValueError:
        return text


def get_first_times(schedule: Any) -> tuple[list[int], Any | None]:
    # gives back the days and times of the first entry that has times
    for entry in schedule or []:
        if entry.get("times"):
            return entry.get("days", []), entry["times"][0]
    return [], None


def format_class_time(schedule: Any) -> str:
    days, times = get_first_times(schedule)
    if times is None:
        return "TBA"

    letters = ""
    for day in days:
        letters += DAY_LETTERS[day]
    return f"{letters} {format_clock(times[0])} - {format_clock(times[1])}"


def format_place(row: dict[str, Any]) -> str:
    parts = []
    for key in ("address_room", "address_street", "city"):
        if row.get(key):
            parts.append(row[key])
    if len(parts) == 0:
        return "TBA"
    return ", ".join(parts)


def get_events_from_database() -> list[dict[str, Any]]:
    rows = fetch_all("""
        SELECT e.event_id, e.event_name, e.event_time, e.event_description, e.event_tags,
               l.address_room, l.address_street, l.city
        FROM events e
        LEFT JOIN locations l ON l.location_id = e.event_location
        ORDER BY lower(e.event_time) NULLS LAST, e.event_id
    """)

    events = []
    for row in rows:
        event_date = ""
        time_text = "Recurring"

        # event_time is a list of time ranges, we only show the first one
        if row["event_time"]:
            ranges = list(row["event_time"])
            start = ranges[0].lower.astimezone(LOCAL_TIMEZONE)
            event_date = start.strftime("%Y-%m-%d")
            time_text = start.strftime("%I:%M %p").lstrip("0")
        tags = row["event_tags"] or []
        category = "general"
        if len(tags) > 0:
            category = tags[0]

        events.append({
            "event_id": row["event_id"],
            "event_name": row["event_name"],
            "event_date": event_date,
            "event_time": time_text,
            "event_location": format_place(row),
            "event_description": row["event_description"] or "",
            "event_category": category,
            "event_tags": tags
        })

    return events


def get_student_interests(student_id: int) -> list[str]:
    rows = fetch_all(
        "SELECT interests FROM students "
        "WHERE student_id = %s AND deleted_timestamp IS NULL AND account_status <> 'closed'",
        (student_id,)
    )
    if len(rows) == 0 or rows[0]["interests"] is None:
        return []
    return list(rows[0]["interests"])


def save_student_interests(student_id: int, interests: list[str]) -> bool:
    cleaned = [interest.lower().strip() for interest in interests]

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE students
            SET interests = %s
            WHERE student_id = %s
              AND deleted_timestamp IS NULL
              AND account_status <> 'closed'
            """,
            (cleaned, student_id)
        )
        return cursor.rowcount > 0 #were any rows changed?


def get_deadlines_from_database(student_id: int) -> list[dict[str, Any]]:
    rows = fetch_all("""SELECT deadline_id, deadline_action, deadline_datetime, deadline_description
        FROM deadlines
        WHERE student_id = %s
        ORDER BY deadline_datetime
        """,(student_id,)
    )

    deadlines = []
    for row in rows:
        due = row["deadline_datetime"].astimezone(LOCAL_TIMEZONE)
        deadlines.append({
            "deadline_id": row["deadline_id"],
            "deadline_title": row["deadline_action"],
            "deadline_date": due.strftime("%Y-%m-%d"),
            "deadline_description": row["deadline_description"] or ""
        })

    return deadlines


def get_courses_from_database() -> list[dict[str, Any]]:
    # time, room and teacher are on the offering (one class section), not on the course
    rows = fetch_all("""
        SELECT c.course_id, o.offering_id, c.course_code, c.course_number, c.course_name,
               c.course_description, c.course_credits, d.department_name, o.class_timings,
               l.address_room, l.address_street, l.city,
               i.instructor_fname, i.instructor_lnames
        FROM courses c
        LEFT JOIN departments d ON d.department_id = c.department_id
        LEFT JOIN offerings o ON o.course_id = c.course_id
        LEFT JOIN locations l ON l.location_id = o.location_id
        LEFT JOIN instructors i ON i.instructor_id = o.primary_instructor
        ORDER BY c.course_id, o.offering_id
    """)

    courses = []
    for row in rows:
        professor = "TBA"
        if row["instructor_fname"]:
            professor = row["instructor_fname"] + " " + row["instructor_lnames"]

        # a course with no offering has no offering_id, so use a negative id to keep ids different
        course_id = row["offering_id"] or -row["course_id"]

        courses.append({
            "id": course_id,
            "course_id": row["course_id"],
            "code": row["course_code"] + " " + row["course_number"],
            "name": row["course_name"],
            "time": format_class_time(row["class_timings"]),
            "room": format_place(row),
            "professor": professor,
            "department": row["department_name"] or "",
            "description": row["course_description"] or "",
            "credits": row["course_credits"]
        })

    return courses


def get_professors_from_database() -> list[dict[str, Any]]:
    rows = fetch_all("""
        SELECT i.instructor_id, i.instructor_fname, i.instructor_lnames, i.instructor_email,
               d.department_name, l.address_room, l.address_street, l.city
        FROM instructors i
        LEFT JOIN departments d ON d.department_id = i.instructor_department
        LEFT JOIN locations l ON l.location_id = i.instructor_office
        ORDER BY i.instructor_id
    """)

    professors = []
    for row in rows:
        professors.append({
            "professor_id": row["instructor_id"],
            "professor_name": row["instructor_fname"] + " " + row["instructor_lnames"],
            "professor_department": row["department_name"] or "",
            "professor_email": row["instructor_email"],
            "office_location": format_place(row),
            "professor_rating": None
        })

    return professors


def get_dining_hours_for_day(
    schedule: Any,
    weekday: int | None = None,
) -> tuple[str, str]:
    """Return verified dining hours for one Wichita-local weekday."""
    from zoneinfo import ZoneInfo

    if weekday is None:
        weekday = datetime.now(ZoneInfo("America/Chicago")).weekday()

    for entry in schedule or []:
        if weekday in entry.get("days", []) and entry.get("times"):
            opening, closing = entry["times"][0]
            return format_clock(opening), format_clock(closing)

    return "N/A", "N/A"


def get_dining_from_database() -> list[dict[str, Any]]:
    rows = fetch_all("""
        SELECT dn.dining_id, dn.dining_name, dn.cuisine, dn.event_status,
               l.open_hours, l.location_notes
        FROM dining dn
        JOIN locations l ON l.location_id = dn.location_id
        WHERE l.location_notes LIKE 'Official WSU dining area: %'
        ORDER BY l.location_notes, dn.dining_name
    """)

    dining = []
    for row in rows:
        opening, closing = get_dining_hours_for_day(row["open_hours"])

        # not sure what event_status means exactly, treating true as open
        status = "Unknown"
        if row["event_status"] is True:
            status = "Open"
        elif row["event_status"] is False:
            status = "Closed"

        dining.append({
            "dining_id": row["dining_id"],
            "dining_name": row["dining_name"],
            "dining_location": row["location_notes"].removeprefix(
                "Official WSU dining area: "
            ).split(" | Restaurant:", 1)[0],
            "opening_time": opening,
            "closing_time": closing,
            "dining_status": status,
            "cuisine": row["cuisine"] or []
        })

    return dining


def get_course_details(
    course_code: str, course_number: str
) -> list[dict[str, Any]]:
    """Retrieve course details and offerings from PostgreSQL."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    c.course_id,
                    c.course_code,
                    c.course_number,
                    c.course_name,
                    c.course_description,
                    c.course_credits,
                    o.offering_id,
                    o.course_crn,
                    o.class_timings,
                    s.session_name,
                    s.academic_year,
                    i.instructor_fname,
                    i.instructor_lnames
                FROM courses AS c
                LEFT JOIN offerings AS o
                    ON o.course_id = c.course_id
                LEFT JOIN sessions AS s
                    ON s.session_id = o.offering_session
                LEFT JOIN instructors AS i
                    ON i.instructor_id = o.primary_instructor
                WHERE LOWER(c.course_code) = LOWER(%s)
                  AND LOWER(c.course_number) = LOWER(%s)
                ORDER BY s.academic_year DESC NULLS LAST,
                         o.offering_id
                """,
                (course_code, course_number),
            )
            return cursor.fetchall()

def get_courses_by_professor(professor: str) -> list[dict[str, Any]]:
    """Find courses by primary or secondary instructor name."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT c.*
                FROM courses AS c
                JOIN offerings AS o ON o.course_id = c.course_id
                LEFT JOIN instructors AS i
                    ON i.instructor_id = o.primary_instructor
                LEFT JOIN instructors AS i2
                    ON i2.instructor_id = o.secondary_instructor
                WHERE CONCAT_WS(' ', i.instructor_fname, i.instructor_lnames)
                        ILIKE %s
                   OR CONCAT_WS(' ', i2.instructor_fname, i2.instructor_lnames)
                        ILIKE %s
                """,
                (f"%{professor}%", f"%{professor}%"),
            )
            return cursor.fetchall()
