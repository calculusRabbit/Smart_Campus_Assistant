from pathlib import Path
from unittest.mock import patch

from services.ml import predictor


def test_predictor_returns_probabilities():
    result = predictor.predict_event_categories(
        "Student Cultural Festival",
        "A celebration featuring cultural performances and food.",
    )

    assert result["status"] in {"ok", "uncertain"}
    assert len(result["probabilities"]) == 5
    assert all(0 <= value <= 1 for value in result["probabilities"].values())


def test_predictor_rejects_empty_input():
    result = predictor.predict_event_categories("", "")

    assert result["status"] == "invalid_input"
    assert result["categories"] == []
    assert result["probabilities"] == {}


def test_predictor_handles_missing_model():
    predictor.load_model.cache_clear()

    with patch.object(
        predictor,
        "MODEL_PATH",
        Path("services/ml/models/nonexistent_model.joblib"),
    ):
        result = predictor.predict_event_categories(
            "Python Workshop",
            "Learn programming skills.",
        )

    assert result["status"] == "model_unavailable"
    assert result["categories"] == []
    predictor.load_model.cache_clear()


def test_predicted_categories_are_valid():
    result = predictor.predict_event_categories(
        "Student Fundraising Event",
        "A fundraising event supporting student organizations.",
    )

    valid_categories = {
        "Campus Wide",
        "Cultural Event",
        "Fundraiser",
        "Student Organization Closed Event",
        "Workshop",
    }

    assert result["status"] in {"ok", "uncertain"}
    assert set(result["categories"]).issubset(valid_categories)
