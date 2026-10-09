import pytest
from fastapi.testclient import TestClient

from database import fetch_all, get_connection
from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def keep_interests():
    # the tests save interests for student 1, so put the old value back after
    rows = fetch_all("SELECT interests FROM students WHERE student_id = 1")
    old_interests = rows[0]["interests"]

    yield 1

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE students SET interests = %s WHERE student_id = 1",
        (old_interests,)
    )
    connection.commit()
    connection.close()


@pytest.fixture
def fake_events():
    # a few events so the recommendation tests dont depend on the seed data
    # the category is the first tag, the old matching only knows coding and career
    return [
        {"event_id": 1, "event_name": "Hack Night", "event_date": "2026-10-10",
         "event_time": "6:00 PM", "event_location": "Jabara Hall",
         "event_description": "build stuff", "event_category": "coding",
         "event_tags": ["coding"]},
        {"event_id": 2, "event_name": "Job Fair", "event_date": "2026-10-12",
         "event_time": "10:00 AM", "event_location": "RSC",
         "event_description": "meet employers", "event_category": "career",
         "event_tags": ["career"]},
        {"event_id": 3, "event_name": "Jazz Concert", "event_date": "2026-10-15",
         "event_time": "7:30 PM", "event_location": "Wiedemann Hall",
         "event_description": "live music", "event_category": "music",
         "event_tags": ["music"]},
    ]
