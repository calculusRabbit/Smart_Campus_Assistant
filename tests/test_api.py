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

def test_chat_uses_rag_for_unmatched_question(monkeypatch):
    from services.rag import pipeline

    monkeypatch.setattr("main.find_course_by_message", lambda message: None)
    monkeypatch.setattr("main.find_professor_by_message", lambda message: None)

    def fake_query_rag(user_input, history):
        assert user_input == "What is the Japanese Culture Association?"
        assert history == []

        return (
            "The Japanese Culture Association is a WSU student organization.",
            "[1] Japanese Culture Association",
        )

    monkeypatch.setattr(
        pipeline,
        "query_RAG",
        fake_query_rag,
    )

    response = client.post(
        "/chat",
        json={
            "message": "What is the Japanese Culture Association?"
        },
    )

    data = response.json()

    assert response.status_code == 200
    assert data["intent"] == "rag"
    assert data["reply"] == (
        "The Japanese Culture Association is a WSU student organization."
    )
    assert "[1] Japanese Culture Association" in data["sources"]