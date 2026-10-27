def test_save_then_get_interests(client, keep_interests):
    response = client.post(
        "/students/1/interests",
        json={"interests": ["Coding", "music"]},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["student_id"] == 1
    assert data["message"] == "Student interests saved successfully."

    saved = client.get("/students/1/interests").json()

    assert saved["student_id"] == 1
    assert saved["interests"] == ["coding", "music"]


def test_saving_again_replaces_the_old_interests(client, keep_interests):
    client.post("/students/1/interests", json={"interests": ["coding", "art"]})
    client.post("/students/1/interests", json={"interests": ["sports"]})

    saved = client.get("/students/1/interests").json()

    assert saved["interests"] == ["sports"]


def test_the_text_a_student_wrote_is_saved_as_one_item(client, keep_interests):
    text = "I like building apps and going to hackathons"
    client.post("/students/1/interests", json={"interests": [text, "coding"]})

    saved = client.get("/students/1/interests").json()

    assert saved["interests"] == [text.lower(), "coding"]


def test_empty_interests_are_rejected(client):
    response = client.post("/students/1/interests", json={"interests": []})

    assert response.status_code == 400
    assert response.json()["detail"] == "At least one student interest is required."


def test_unknown_student_is_404(client):
    response = client.post("/students/999999/interests", json={"interests": ["coding"]})

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found."


def test_get_interests_of_unknown_student_is_empty(client):
    response = client.get("/students/999999/interests")

    assert response.status_code == 200
    assert response.json()["interests"] == []


def test_missing_interests_is_422(client):
    response = client.post("/students/1/interests", json={})

    assert response.status_code == 422


def test_interests_have_to_be_a_list(client):
    response = client.post("/students/1/interests", json={"interests": "coding"})

    assert response.status_code == 422


def test_student_id_has_to_be_a_number(client):
    response = client.get("/students/abc/interests")

    assert response.status_code == 422
