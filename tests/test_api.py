from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_home_page():
    response = client.get("/")

    assert response.status_code == 200


def test_events_endpoint():
    response = client.get("/events")
    data = response.json()

    assert response.status_code == 200
    assert "events" in data
    assert isinstance(data["events"], list)
    assert len(data["events"]) > 0


def test_courses_endpoint():
    response = client.get("/courses")
    data = response.json()

    assert response.status_code == 200
    assert "courses" in data
    assert isinstance(data["courses"], list)
    assert len(data["courses"]) > 0