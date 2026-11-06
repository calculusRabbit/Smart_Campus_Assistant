"""Tests for the official WSU course catalog scraper."""

import pytest

from services.rag.scrapers.scrape_wsu_courses import parse_courses


def make_html(title: str, description: str = "Course description.") -> str:
    return (
        '<div class="courseblock">'
        f'<p class="courseblocktitle">{title}</p>'
        f'<p class="courseblockdesc">{description}</p>'
        "</div>"
    )


def test_parse_regular_course():
    courses = parse_courses(
        make_html("CS 211. Introduction to Programming (4)."),
        "CS",
    )

    assert len(courses) == 1
    assert courses[0]["course_number"] == "211"
    assert courses[0]["course_name"] == "Introduction to Programming"
    assert courses[0]["course_credits"] == 4.0
    assert courses[0]["eligible"] is True


def test_variable_credits_are_not_guessed():
    courses = parse_courses(
        make_html("CS 281I. Noncredit Internship (1-3)."),
        "CS",
    )

    assert courses[0]["course_number"] == "281I"
    assert courses[0]["course_credits_text"] == "1-3"
    assert courses[0]["course_credits"] is None
    assert courses[0]["eligible"] is False


def test_long_description_is_preserved():
    description = "A" * 501

    courses = parse_courses(
        make_html("ME 250. Materials Engineering (3).", description),
        "ME",
    )

    assert courses[0]["course_description"] == description
    assert courses[0]["eligible"] is False


def test_fractional_credits():
    courses = parse_courses(
        make_html("AE 500. Special Topics (0.75)."),
        "AE",
    )

    assert courses[0]["course_credits"] == 0.75
    assert courses[0]["eligible"] is True


def test_wrong_department_is_rejected():
    with pytest.raises(ValueError, match="Unexpected course prefix"):
        parse_courses(
            make_html("CS 211. Introduction to Programming (4)."),
            "ECE",
        )


def test_invalid_title_is_rejected():
    with pytest.raises(ValueError, match="Unrecognized catalog course title"):
        parse_courses(
            make_html("Not a valid course title"),
            "CS",
        )
