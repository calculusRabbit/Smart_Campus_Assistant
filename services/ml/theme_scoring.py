"""Optional ML theme evidence for personalized event recommendations."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib  # type: ignore[import-untyped]

MODEL_PATH = Path(__file__).resolve().parent / "models" / "event_theme_classifier.joblib"

THEME_BY_INTEREST = {
    "art": "Arts",
    "sports": "Athletics",
    "volunteering": "CommunityService",
    "culture": "Cultural",
}

ML_THEME_BOOST = 0.05


@lru_cache(maxsize=1)
def load_theme_model() -> Any:
    """Load the locally trained, trusted nine-theme classifier once."""
    return joblib.load(MODEL_PATH)


def get_theme_bonus(
    interests: str,
    title: str,
    description: str = "",
) -> float:
    """Give a small bonus when ML theme evidence matches an interest."""
    selected = {
        THEME_BY_INTEREST[word]
        for word in interests.casefold().replace(",", " ").split()
        if word in THEME_BY_INTEREST
    }

    if not selected or not (title or description):
        return 0.0

    try:
        model = load_theme_model()
        prediction = str(model.predict([f"{title}. {description}"])[0])
    except (OSError, ValueError, KeyError, ImportError, AttributeError):
        return 0.0

    return ML_THEME_BOOST if prediction in selected else 0.0
