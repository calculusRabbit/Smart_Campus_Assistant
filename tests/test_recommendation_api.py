class FakeRecommender:
    def __init__(self):
        self.asked = []

    def recommend(self, likes_text):
        self.asked.append(likes_text)
        return [{"event_id": "wsu_calendar-1", "event_name": "Hack Night", "score": 80}]


class BrokenRecommender:
    def recommend(self, likes_text):
        raise FileNotFoundError("all_events.json is missing")


def get_no_interests(student_id):
    return []


def get_coding_interests(student_id):
    return ["coding"]


def get_coding_and_music(student_id):
    return ["coding", "music"]


def get_broken_recommender():
    return BrokenRecommender()


def test_recommend_events_by_interest(client, monkeypatch, fake_events):
    def fake_get_events():
        return fake_events

    monkeypatch.setattr("main.get_events_from_database", fake_get_events)

    response = client.post("/recommendations/events", json={"interests": ["coding"]})
    data = response.json()

    assert response.status_code == 200
    assert data["interests"] == ["coding"]
    # only Hack Night has the coding category
    assert len(data["recommended_events"]) == 1
    assert data["recommended_events"][0]["event_name"] == "Hack Night"


def test_recommend_events_for_career_and_coding(client, monkeypatch, fake_events):
    def fake_get_events():
        return fake_events

    monkeypatch.setattr("main.get_events_from_database", fake_get_events)

    response = client.post("/recommendations/events", json={"interests": ["Career", " coding "]})
    names = []
    for event in response.json()["recommended_events"]:
        names.append(event["event_name"])

    assert names == ["Hack Night", "Job Fair"]


def test_recommend_events_with_an_interest_nobody_has(client, monkeypatch, fake_events):
    def fake_get_events():
        return fake_events

    monkeypatch.setattr("main.get_events_from_database", fake_get_events)

    response = client.post("/recommendations/events", json={"interests": ["knitting"]})

    assert response.json()["recommended_events"] == []


def test_recommend_events_needs_interests(client):
    response = client.post("/recommendations/events", json={})

    assert response.status_code == 422


def test_student_without_interests_gets_404(client, monkeypatch):
    monkeypatch.setattr("main.get_student_interests", get_no_interests)

    response = client.get("/students/1/recommendations/events")

    assert response.status_code == 404
    assert response.json()["detail"] == "No saved interests found for this student."


def test_student_recommendations_use_the_recommender(client, monkeypatch):
    fake = FakeRecommender()

    def get_fake_recommender():
        return fake

    monkeypatch.setattr("main.get_student_interests", get_coding_and_music)
    monkeypatch.setattr("main.get_recommender", get_fake_recommender)

    response = client.get("/students/1/recommendations/events")
    data = response.json()

    assert response.status_code == 200
    assert data["student_id"] == 1
    assert data["interests"] == ["coding", "music"]
    assert data["recommended_events"][0]["score"] == 80
    # the recommender gets one sentence made from the saved items
    assert fake.asked == ["I am interested in coding and music."]


def test_student_recommendations_fall_back_when_the_recommender_breaks(
    client, monkeypatch, fake_events
):
    monkeypatch.setattr("main.get_student_interests", get_coding_interests)
    monkeypatch.setattr("main.get_recommender", get_broken_recommender)
    def fake_get_events():
        return fake_events

    monkeypatch.setattr("main.get_events_from_database", fake_get_events)

    response = client.get("/students/1/recommendations/events")
    data = response.json()

    assert response.status_code == 200
    assert len(data["recommended_events"]) == 1
    assert data["recommended_events"][0]["event_name"] == "Hack Night"
