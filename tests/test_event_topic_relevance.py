import pytest

from services.event_recommender import matches_event_topic
from services.interest_expansion import extract_event_interests


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Are there any soccer activities this week?", "soccer"),
        ("What programming workshops are coming up?", "programming"),
        ("Are there any career networking events?", "career"),
        ("Are there any Python workshops?", "python"),
        ("Are there any software development events?", "programming"),
    ],
)
def test_extract_event_interests(question, expected):
    assert extract_event_interests(question) == expected


@pytest.mark.parametrize(
    ("title", "interest", "expected"),
    [
        ("Python Programming Workshop", "programming", True),
        ("IFC Tailgate", "programming", False),
        ("Career Networking Night", "career", True),
        ("Off-Campus Housing Fair", "career", False),
        ("Soccer Practice!", "soccer", True),
        ("SAC Arts and Culture Committee Meetings", "soccer", False),
    ],
)
def test_event_topic_relevance(title, interest, expected):
    event = {
        "title": title,
        "description": "",
        "organization": "",
        "categories": [],
    }
    assert matches_event_topic(event, interest) is expected
