from unittest.mock import patch

from services.ml.recommendation_enrichment import enrich_event_recommendations


def sample_events():
    return [
        {
            "event_id": "shockersync-100",
            "event_name": "Student Cultural Festival",
            "event_description": "International cultural celebration.",
            "event_category": "Campus Wide",
            "score": 85,
        },
        {
            "event_id": "shockersync-200",
            "event_name": "Student Workshop",
            "event_description": "A student learning workshop.",
            "event_category": "general",
            "score": 72,
        },
    ]


def test_successful_ml_enrichment():
    prediction = {
        "status": "ok",
        "categories": ["Cultural Event"],
        "probabilities": {"Cultural Event": 0.8},
    }

    with patch(
        "services.ml.recommendation_enrichment.predict_event_categories",
        return_value=prediction,
    ):
        results = enrich_event_recommendations(sample_events())

    assert len(results) == 2
    assert results[0]["ml_predicted_categories"] == ["Cultural Event"]
    assert results[1]["ml_predicted_categories"] == ["Cultural Event"]


def test_uncertain_ml_prediction_preserves_events():
    prediction = {
        "status": "uncertain",
        "categories": [],
        "probabilities": {},
    }

    original = sample_events()

    with patch(
        "services.ml.recommendation_enrichment.predict_event_categories",
        return_value=prediction,
    ):
        results = enrich_event_recommendations(original)

    assert results == original


def test_ml_failure_preserves_recommendations():
    original = sample_events()

    with patch(
        "services.ml.recommendation_enrichment.predict_event_categories",
        side_effect=RuntimeError("Model unavailable"),
    ):
        results = enrich_event_recommendations(original)

    assert results == original


def test_enrichment_preserves_ranking_and_official_categories():
    original = sample_events()

    with patch(
        "services.ml.recommendation_enrichment.predict_event_categories",
        return_value={
            "status": "ok",
            "categories": ["Workshop"],
        },
    ):
        results = enrich_event_recommendations(original)

    assert [event["event_id"] for event in results] == [
        "shockersync-100",
        "shockersync-200",
    ]
    assert [event["score"] for event in results] == [85, 72]
    assert [event["event_category"] for event in results] == [
        "Campus Wide",
        "general",
    ]
    assert "ml_predicted_categories" not in original[0]
