from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def no_course(message):
    return None


def no_professor(message):
    return None


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

    # the env on my laptop has rag turned off, so turn it on here
    monkeypatch.setattr("main.RAG_ENABLED", True)
    monkeypatch.setattr("main.find_course_by_message", no_course)
    monkeypatch.setattr("main.find_professor_by_message", no_professor)

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

def test_dining_endpoint():
    response = client.get("/dining")
    data = response.json()

    assert response.status_code == 200
    assert isinstance(data["dining"], list)
    assert len(data["dining"]) > 0


def test_professors_endpoint():
    response = client.get("/professors")
    data = response.json()

    assert response.status_code == 200
    assert len(data["professors"]) > 0
    assert "professor_name" in data["professors"][0]


def test_deadlines_endpoint():
    response = client.get("/deadlines")
    data = response.json()

    assert response.status_code == 200
    assert isinstance(data["deadlines"], list)


def test_courses_filter_by_code():
    all_courses = client.get("/courses").json()["courses"]
    first_code = all_courses[0]["code"]

    response = client.get("/courses", params={"code": first_code.lower()})
    courses = response.json()["courses"]

    assert response.status_code == 200
    assert len(courses) > 0
    for course in courses:
        assert first_code.lower() in course["code"].lower()


def test_courses_filter_by_professor():
    all_courses = client.get("/courses").json()["courses"]
    name = all_courses[0]["professor"]

    courses = client.get("/courses", params={"professor": name}).json()["courses"]

    assert len(courses) > 0
    for course in courses:
        assert name.lower() in course["professor"].lower()


def test_courses_filter_with_no_match():
    response = client.get("/courses", params={"code": "zzzzz"})

    assert response.status_code == 200
    assert response.json()["courses"] == []


# chat, the finders are turned off in most of these so the answer doesnt depend on the seed data


def no_matches(monkeypatch):
    monkeypatch.setattr("main.find_course_by_message", no_course)
    monkeypatch.setattr("main.find_professor_by_message", no_professor)


def test_chat_empty_message_is_rejected():
    response = client.post("/chat", json={"message": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "Message cannot be empty."


def test_chat_without_a_message_is_422():
    response = client.post("/chat", json={})

    assert response.status_code == 422


def test_chat_events(monkeypatch):
    no_matches(monkeypatch)
    response = client.post("/chat", json={"message": "what events are happening"})
    data = response.json()

    assert data["intent"] == "events"
    assert isinstance(data["data"], list)


def test_chat_dining(monkeypatch):
    no_matches(monkeypatch)
    data = client.post("/chat", json={"message": "I am hungry"}).json()

    assert data["intent"] == "dining"
    assert isinstance(data["data"], list)


def test_chat_courses(monkeypatch):
    no_matches(monkeypatch)
    data = client.post("/chat", json={"message": "show me the classes"}).json()

    assert data["intent"] == "courses"
    assert len(data["data"]) > 0


def test_chat_professors(monkeypatch):
    no_matches(monkeypatch)
    data = client.post("/chat", json={"message": "who is my instructor"}).json()

    assert data["intent"] == "professors"


def test_chat_deadlines(monkeypatch):
    no_matches(monkeypatch)
    data = client.post("/chat", json={"message": "when is the add/drop deadline"}).json()

    assert data["intent"] == "deadlines"


def test_chat_finds_a_course_by_its_name():
    course = client.get("/courses").json()["courses"][0]

    data = client.post("/chat", json={"message": "tell me about " + course["name"]}).json()

    assert data["intent"] == "courses"
    assert "name" in data["data"]


def test_chat_finds_a_course_by_its_code():
    course = client.get("/courses").json()["courses"][0]

    data = client.post("/chat", json={"message": "what is " + course["code"] + "?"}).json()

    assert data["intent"] == "courses"


def test_chat_finds_a_professor_by_name():
    # courses and professors are checked first, so use a name that is not a course name
    professor = client.get("/professors").json()["professors"][0]

    data = client.post("/chat", json={"message": professor["professor_name"].lower()}).json()

    assert data["intent"] in ("professors", "courses")
    assert data["data"] is not None


def test_chat_recommendation_for_coding(monkeypatch, fake_events):
    no_matches(monkeypatch)
    def fake_get_events():
        return fake_events

    monkeypatch.setattr("main.get_events_from_database", fake_get_events)

    data = client.post("/chat", json={"message": "recommend something about coding"}).json()

    assert data["intent"] == "recommendations"
    assert data["interests"] == ["coding"]
    names = []
    for event in data["data"]:
        names.append(event["event_name"])
    assert names == ["Hack Night"]


def test_chat_unknown_when_rag_is_off(monkeypatch):
    no_matches(monkeypatch)
    monkeypatch.setattr("main.RAG_ENABLED", False)

    data = client.post("/chat", json={"message": "blah blah blah"}).json()

    assert data["intent"] == "unknown"
    assert "could not understand" in data["reply"]


def test_contains_keyword_only_matches_whole_words():
    from main import contains_keyword

    assert contains_keyword("what events are there", "events") is True
    assert contains_keyword("seventeen", "event") is False
    assert contains_keyword("who is dr. yang", "dr.") is True


def test_find_course_and_professor_return_none_for_other_text():
    from main import find_course_by_message, find_professor_by_message

    assert find_course_by_message("qwertyuiop") is None
    assert find_professor_by_message("qwertyuiop") is None
