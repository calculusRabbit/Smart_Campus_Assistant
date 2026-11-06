from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_ml_endpoint_returns_prediction():
    response = client.post(
        "/ml/predict-event",
        json={
            "title": "Student Cultural Festival",
            "description": "A celebration of food and music.",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["status"] in {"ok", "uncertain"}
    assert isinstance(result["categories"], list)
    assert len(result["probabilities"]) == 5


def test_ml_endpoint_handles_empty_input():
    response = client.post(
        "/ml/predict-event",
        json={"title": "", "description": ""},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "invalid_input"


def test_ml_endpoint_handles_missing_model():
    with patch(
        "services.ml.router.predict_event_categories",
        return_value={
            "status": "model_unavailable",
            "categories": [],
            "probabilities": {},
        },
    ):
        response = client.post(
            "/ml/predict-event",
            json={"title": "Python Workshop"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "model_unavailable"


def test_ml_endpoint_rejects_excessively_long_input():
    response = client.post(
        "/ml/predict-event",
        json={"title": "A" * 501},
    )

    assert response.status_code == 422
