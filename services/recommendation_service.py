"""Recommendation logic for the Smart Campus Assistant."""

from typing import Final

INTEREST_GROUPS: Final[dict[str, list[str]]] = {
    "coding": [
        "coding",
        "programming",
        "computer science",
        "technology",
        "software",
    ],
    "career": [
        "career",
        "job",
        "jobs",
        "internship",
        "internships",
        "employment",
    ],
}


class RecommendationService:
    """Handle student interest detection and event recommendation matching."""

    def __init__(self, interest_groups: dict[str, list[str]] | None = None) -> None:
        self._interest_groups = interest_groups or INTEREST_GROUPS

    def extract_interests(self, message: str) -> list[str]:
        """Return matching interest categories found in a user message."""
        normalized_message = message.lower()
        detected_interests: list[str] = []

        for category, related_interests in self._interest_groups.items():
            if any(interest in normalized_message for interest in related_interests):
                detected_interests.append(category)

        return detected_interests

    def related_interests(self, category: str) -> list[str]:
        """Return configured keywords for an interest category."""
        return self._interest_groups.get(category, [category])
