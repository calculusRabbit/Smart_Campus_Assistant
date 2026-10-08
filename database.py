import os
from datetime import datetime
from zoneinfo import ZoneInfo

import psycopg
from psycopg.rows import dict_row

DATABASE_NAME = os.getenv("POSTGRES_DB", "smart_campus")

# the database keeps times in utc, we show them in wichita time
LOCAL_TIMEZONE = ZoneInfo("America/Chicago")

# day numbers in class_timings and open_hours, i am guessing 0 is monday
DAY_LETTERS = ["M", "T", "W", "R", "F", "Sa", "Su"]


def get_connection():
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


def fetch_all(query, params=None):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    connection.close()
    return rows


def format_clock(text):
    # "13:30" -> "1:30 PM"
    try:
        return datetime.strptime(text, "%H:%M").strftime("%-I:%M %p")
    except ValueError:
        return text


def get_first_times(schedule):
    # schedule looks like [{"days": [0, 2], "times": [["11:00", "12:15"]]}, {"days": [1, 3], "times": []}]
    # gives back the days and times of the first entry that has times
    for entry in schedule or []:
        if entry.get("times"):
            return entry.get("days", []), entry["times"][0]
    return [], None


def format_class_time(schedule):
    days, times = get_first_times(schedule)
    if times is None:
        return "TBA"

    letters = ""
    for day in days:
        letters += DAY_LETTERS[day]
    return f"{letters} {format_clock(times[0])} - {format_clock(times[1])}"


def format_place(row):
    parts = []
    for key in ("address_room", "address_street", "city"):
        if row.get(key):
            parts.append(row[key])
    if len(parts) == 0:
        return "TBA"
    return ", ".join(parts)


def get_events_from_database():
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
            time_text = start.strftime("%-I:%M %p")

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


def get_student_interests(student_id: int):
    rows = fetch_all(
        "SELECT interests FROM students WHERE student_id = %s",
        (student_id,)
    )
    if len(rows) == 0 or rows[0]["interests"] is None:
        return []
    return rows[0]["interests"]


def save_student_interests(student_id: int, interests: list[str]):
    cleaned = []
    for interest in interests:
        cleaned.append(interest.lower().strip())

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE students SET interests = %s WHERE student_id = %s",
        (cleaned, student_id)
    )
    # no row changed means there is no student with this id
    found = cursor.rowcount > 0
    connection.commit()
    connection.close()
    return found


def get_deadlines_from_database():
    rows = fetch_all("""
        SELECT deadline_id, deadline_action, deadline_datetime, deadline_description
        FROM deadlines
        ORDER BY deadline_datetime
    """)

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


def get_courses_from_database():
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


def get_professors_from_database():
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


def get_dining_from_database():
    rows = fetch_all("""
        SELECT dn.dining_id, dn.dining_name, dn.cuisine, dn.event_status,
               l.open_hours, l.address_room, l.address_street, l.city
        FROM dining dn
        LEFT JOIN locations l ON l.location_id = dn.location_id
        ORDER BY dn.dining_id
    """)

    dining = []
    for row in rows:
        days, times = get_first_times(row["open_hours"])
        opening = "N/A"
        closing = "N/A"
        if times is not None:
            opening = format_clock(times[0])
            closing = format_clock(times[1])

        # not sure what event_status means exactly, treating true as open
        status = "Unknown"
        if row["event_status"] is True:
            status = "Open"
        elif row["event_status"] is False:
            status = "Closed"

        dining.append({
            "dining_id": row["dining_id"],
            "dining_name": row["dining_name"],
            "dining_location": format_place(row),
            "opening_time": opening,
            "closing_time": closing,
            "dining_status": status,
            "cuisine": row["cuisine"] or []
        })

    return dining
