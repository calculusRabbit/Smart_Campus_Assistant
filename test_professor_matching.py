"""Tests for professor name matching in the chatbot."""

from unittest.mock import patch

from main import find_professor_by_message

PROFESSORS = [
    {"professor_name": "Rajiv Bagai"},
    {"professor_name": "Kaushik Sinha"},
    {"professor_name": "Rong Li"},
    {"professor_name": "Alex Smith"},
    {"professor_name": "Jordan Smith"},
]


def find_match(message):
    with patch("main.get_professors_from_database", return_value=PROFESSORS):
        return find_professor_by_message(message)


def test_professor_full_name():
    result = find_match("Tell me about Rajiv Bagai")
    assert result["professor_name"] == "Rajiv Bagai"


def test_professor_surname():
    result = find_match("Who is Professor Sinha?")
    assert result["professor_name"] == "Kaushik Sinha"


def test_short_surname_does_not_match_inside_word():
    result = find_match("Where is the library?")
    assert result is None


def test_ambiguous_surname_returns_none():
    result = find_match("Tell me about Professor Smith")
    assert result is None


def test_full_name_resolves_ambiguous_surname():
    result = find_match("Tell me about Alex Smith")
    assert result["professor_name"] == "Alex Smith"


def test_unknown_professor_returns_none():
    result = find_match("Tell me about Professor Unknown")
    assert result is None
