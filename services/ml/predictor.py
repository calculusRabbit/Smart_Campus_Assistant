from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib  # type: ignore[import-untyped]

MODEL_PATH = Path(__file__).resolve().parent / "models" / "event_classifier.joblib"


@lru_cache(maxsize=1)
def load_model() -> tuple[Any, Any]:
    """Load the locally trained, trusted ML classifier."""
    bundle = joblib.load(MODEL_PATH)
    return bundle["model"], bundle["encoder"]


def predict_event_categories(title: str, description: str = "") -> dict:
    """Predict ShockerSync event categories without affecting other services."""
    text = f"{title or ''} {description or ''}".strip()

    if not text:
        return {
            "status": "invalid_input",
            "categories": [],
            "probabilities": {},
        }

    try:
        model, encoder = load_model()
        probabilities = model.predict_proba([text])[0]

        scores = {
            str(category): round(float(probability), 3)
            for category, probability in zip(encoder.classes_, probabilities, strict=True)
        }

        predicted = [category for category, probability in scores.items() if probability >= 0.5]

        return {
            "status": "ok" if predicted else "uncertain",
            "categories": predicted,
            "probabilities": scores,
        }

    except (OSError, KeyError, ValueError, ImportError, AttributeError) as exc:
        return {
            "status": "model_unavailable",
            "categories": [],
            "probabilities": {},
            "error": type(exc).__name__,
        }
