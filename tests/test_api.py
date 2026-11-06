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
        json={"message": "What is the Japanese Culture Association?"},
    )

    data = response.json()

    assert response.status_code == 200
    assert data["intent"] == "rag"
    assert data["reply"] == ("The Japanese Culture Association is a WSU student organization.")
    assert "[1] Japanese Culture Association" in data["sources"]


def test_dining_endpoint(monkeypatch):
    sample_dining = [
        {
            "dining_id": 1,
            "dining_name": "Shocker Dining Hall",
            "dining_location": "Shocker Hall",
            "opening_time": "N/A",
            "closing_time": "N/A",
            "dining_status": "Unknown",
            "cuisine": [],
        }
    ]

    monkeypatch.setattr(
        "main.get_dining_from_database",
        lambda: sample_dining,
    )

    response = client.get("/dining")
    data = response.json()

    assert response.status_code == 200
    assert data["dining"] == sample_dining


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


def test_chat_finds_a_professor_by_name(monkeypatch):
    """Professor lookup should not depend on database seed names."""
    professor = {
        "professor_id": 999999,
        "professor_name": "Ada Exampleton",
        "professor_department": "School of Computing",
        "professor_email": "example@wichita.edu",
        "office_location": "TBA",
        "professor_rating": None,
    }

    monkeypatch.setattr(
        "main.get_professors_from_database",
        lambda: [professor],
    )

    data = client.post(
        "/chat",
        json={"message": "tell me about professor Ada Exampleton"},
    ).json()

    assert data["intent"] == "professors"
    assert data["data"]["professor_id"] == professor["professor_id"]
    assert data["data"]["professor_name"] == professor["professor_name"]


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


def test_chat_filters_professors_by_department(monkeypatch):
    """Department faculty questions should return only matching real records."""
    no_matches(monkeypatch)
    monkeypatch.setattr("main.RAG_ENABLED", False)

    professors = [
        {
            "professor_id": 101,
            "professor_name": "Rajeev Nair",
            "professor_department": "Mechanical Engineering",
            "professor_email": "rajeev.nair@wichita.edu",
        },
        {
            "professor_id": 102,
            "professor_name": "Rajiv Bagai",
            "professor_department": "School of Computing",
            "professor_email": "rajiv.bagai@wichita.edu",
        },
        {
            "professor_id": 103,
            "professor_name": "Test Instructor",
            "professor_department": "Test Department",
            "professor_email": "test@example.edu",
        },
    ]

    monkeypatch.setattr(
        "main.get_professors_from_database",
        lambda: professors,
    )

    response = client.post(
        "/chat",
        json={"message": "Who are the professors in Mechanical Engineering?"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "professors"
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 1
    assert data["data"][0]["professor_name"] == "Rajeev Nair"
    assert data["data"][0]["professor_department"] == "Mechanical Engineering"


def test_chat_engineering_events_use_shockersync(monkeypatch):
    """Engineering event questions should reach the live recommender."""
    no_matches(monkeypatch)

    class FakeRecommender:
        def recommend(self, message, top_k=5):
            assert "engineering" in message
            assert top_k == 5
            return [
                {
                    "event_id": "shockersync-test",
                    "event_name": "Engineering Workshop",
                }
            ]

    monkeypatch.setattr(
        "main.get_recommender",
        lambda: FakeRecommender(),
    )

    response = client.post(
        "/chat",
        json={"message": "Recommend engineering events"},
    )

    assert response.status_code == 200

    result = response.json()

    assert result["intent"] == "recommendations"
    assert len(result["data"]) == 1
    assert result["data"][0]["event_name"] == "Engineering Workshop"


def test_chat_general_events_use_shockersync(monkeypatch):
    """General event questions should list upcoming ShockerSync events."""
    no_matches(monkeypatch)

    class FakeRecommender:
        events = [
            {
                "id": "12345",
                "source": "shockersync",
                "title": "Campus Welcome Event",
                "dates": ["2026-11-10"],
                "start_date": "2026-11-10",
                "end_date": "2026-11-10",
                "end_datetime": "2026-11-10T18:00:00-06:00",
                "time": "4:00 PM",
                "location": "RSC",
                "description": "Welcome students",
                "categories": ["Campus Wide"],
                "url": "https://wichita.campuslabs.com/engage/event/12345",
            }
        ]

    monkeypatch.setattr(
        "main.get_recommender",
        lambda: FakeRecommender(),
    )

    def reject_database_events():
        raise AssertionError("General event chat must not use PostgreSQL test events")

    monkeypatch.setattr(
        "main.get_events_from_database",
        reject_database_events,
    )

    from datetime import date

    from services import event_recommender

    monkeypatch.setattr(
        event_recommender,
        "today_in_wichita",
        lambda: date(2026, 11, 3),
    )

    response = client.post(
        "/chat",
        json={"message": "What events are happening on campus?"},
    )

    assert response.status_code == 200

    result = response.json()

    assert result["intent"] == "events"
    assert len(result["data"]) == 1
    assert result["data"][0]["event_id"] == "shockersync-12345"
    assert result["data"][0]["event_name"] == "Campus Welcome Event"


def test_internships_do_not_match_internship_course(monkeypatch):
    """Plural career interests must not match a singular course title."""
    import main

    monkeypatch.setattr(
        main,
        "get_courses_from_database",
        lambda: [
            {
                "code": "ME 481N",
                "course_number": "",
                "name": "Internship",
            }
        ],
    )

    message = (
        "I'm interested in internships and career opportunities. What events do you recommend?"
    )

    assert main.find_course_by_message(message) is None
