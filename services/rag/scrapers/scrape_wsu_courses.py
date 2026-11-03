"""Read official Wichita State University course catalog pages."""

import re
from typing import Any

import requests
from bs4 import BeautifulSoup

COURSE_URLS = {
    "CS": "https://catalog.wichita.edu/undergraduate/courses/cs/",
    "ECE": "https://catalog.wichita.edu/undergraduate/courses/ece/",
    "ME": "https://catalog.wichita.edu/undergraduate/courses/me/",
    "AE": "https://catalog.wichita.edu/undergraduate/courses/ae/",
    "BME": "https://catalog.wichita.edu/undergraduate/courses/bme/",
}

COURSE_PATTERN = re.compile(r"^([A-Z]+)\s+([0-9]+[A-Z]*)\.\s+(.+?)\s+\(([^)]+)\)\.$")


def parse_courses(html: str, expected_prefix: str) -> list[dict[str, Any]]:
    """Parse official catalog records without changing their credit values."""
    soup = BeautifulSoup(html, "html.parser")
    courses = []

    for block in soup.select(".courseblock"):
        title = block.select_one(".courseblocktitle")
        description = block.select_one(".courseblockdesc")

        if title is None:
            raise ValueError("Course block is missing its title")

        match = COURSE_PATTERN.match(title.get_text(" ", strip=True))
        if match is None:
            raise ValueError("Unrecognized catalog course title")

        prefix, number, name, credit_text = match.groups()

        if prefix != expected_prefix:
            raise ValueError("Unexpected course prefix")

        description_text = description.get_text(" ", strip=True) if description else ""

        variable_credits = "-" in credit_text
        too_long = len(description_text) > 500

        courses.append(
            {
                "course_code": prefix,
                "course_number": number,
                "course_name": name,
                "course_description": description_text,
                "course_credits_text": credit_text,
                "course_credits": (None if variable_credits else float(credit_text)),
                "eligible": (not variable_credits and not too_long and len(name) <= 75),
                "source_url": COURSE_URLS[expected_prefix],
            }
        )

    if not courses:
        raise ValueError("No catalog courses found")

    return courses


def fetch_courses(prefix: str) -> list[dict[str, Any]]:
    """Download and parse one official WSU course catalog page."""
    if prefix not in COURSE_URLS:
        raise ValueError("Unknown course prefix")

    response = requests.get(COURSE_URLS[prefix], timeout=30)
    response.raise_for_status()

    return parse_courses(response.text, prefix)
