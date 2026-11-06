"""Tests for optional nine-theme ML recommendation scoring."""

from unittest.mock import Mock, patch

import pytest

from services.ml.theme_scoring import get_theme_bonus


@pytest.mark.parametrize(
    ("interest", "prediction"),
    [
        ("art", "Arts"),
        ("sports", "Athletics"),
        ("volunteering", "CommunityService"),
        ("culture", "Cultural"),
    ],
)
def test_matching_theme_receives_bonus(interest, prediction):
    model = Mock()
    model.predict.return_value = [prediction]

    with patch("services.ml.theme_scoring.load_theme_model", return_value=model):
        bonus = get_theme_bonus(interest, "Relevant event", "Event description")

    assert bonus == pytest.approx(0.05)


def test_nonmatching_theme_receives_no_bonus():
    model = Mock()
    model.predict.return_value = ["Social"]

    with patch("services.ml.theme_scoring.load_theme_model", return_value=model):
        bonus = get_theme_bonus("art", "Committee meeting")

    assert bonus == 0.0


@pytest.mark.parametrize(
    "interest",
    ["coding", "career", "business", "science", "health"],
)
def test_unmapped_interest_receives_no_bonus(interest):
    with patch("services.ml.theme_scoring.load_theme_model") as loader:
        bonus = get_theme_bonus(interest, "Student event")

    assert bonus == 0.0
    loader.assert_not_called()


def test_missing_model_fails_safely():
    with patch(
        "services.ml.theme_scoring.load_theme_model",
        side_effect=OSError("Model unavailable"),
    ):
        bonus = get_theme_bonus("sports", "Volleyball tournament")

    assert bonus == 0.0


def test_empty_event_receives_no_bonus():
    with patch("services.ml.theme_scoring.load_theme_model") as loader:
        bonus = get_theme_bonus("art", "", "")

    assert bonus == 0.0
    loader.assert_not_called()
