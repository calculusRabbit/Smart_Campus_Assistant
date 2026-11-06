from typing import Any

from services.ml.predictor import predict_event_categories


def enrich_event_recommendations(
    recommendations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Add optional ML predictions without changing existing recommendations."""
    enriched = []

    for event in recommendations:
        item = event.copy()

        title = str(item.get("event_name") or "")
        description = str(item.get("event_description") or "")

        if not title and not description:
            enriched.append(item)
            continue

        try:
            prediction = predict_event_categories(title, description)
        except Exception:
            # ML must never prevent the original recommendations from working.
            enriched.append(item)
            continue

        if prediction.get("status") == "ok" and prediction.get("categories"):
            item["ml_predicted_categories"] = prediction["categories"]

        enriched.append(item)

    return enriched
