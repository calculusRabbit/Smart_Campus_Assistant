"""Read dining information from Wichita State University's official website."""

from typing import Any

import requests
from bs4 import BeautifulSoup

DINING_URL = "https://www.wichita.edu/student_life/dining.php"

DINING_SECTIONS = {
    "Rhatigan Student Center Food Court": {
        "location": "Rhatigan Student Center",
        "names": (
            "Starbucks",
            "Chick-fil-A",
            "Freddy's Steakburgers",
            "Panda Express",
            "Sushi-Do",
            "Shocker Sports Grill and Lanes",
        ),
    },
    "Shocker Hall Dining": {
        "location": "Shocker Hall",
        "names": ("Shocker Dining Hall", "GroundHouse"),
        "aliases": {"Shocker Dining Hall": "400-seat dining hall"},
    },
    "Food trucks provide endless variety": {
        "location": "Innovation Campus Food Truck Plaza",
        "names": ("Food Truck Plaza",),
    },
    "Innovation Campus": {
        "location": "Innovation Campus",
        "names": (
            "Starbucks",
            "Fuzzy's Taco Shop",
            "Jersey Mike's",
            "Pizza Shuttle",
            "Social Tap Drinkery",
            "Sungrano Pizza",
            "Wheatly's Burgers",
            "Mega-Bytes",
            "Cargill Cafe",
            "Cafe at NetApp Wichita",
        ),
    },
}


def normalize_dining_name(text: str) -> str:
    """Normalize punctuation and whitespace for restaurant name matching."""
    replacements = str.maketrans(
        {
            "\u2010": "-",
            "\u2011": "-",
            "\u2012": "-",
            "\u2013": "-",
            "\u2014": "-",
            "\u2018": "'",
            "\u2019": "'",
        }
    )
    return " ".join(text.translate(replacements).casefold().split())


def parse_dining(html: str) -> list[dict[str, Any]]:
    """Extract officially documented dining names and campus areas."""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    found_sections = set()

    for teaser in soup.select("div.teaser"):
        heading = teaser.select_one("h1, h2, h3, h4")
        editorial = teaser.select_one(".teaser__editorial")

        if heading is None or editorial is None:
            continue

        section = " ".join(heading.get_text(" ", strip=True).split())
        if section not in DINING_SECTIONS:
            continue

        description = editorial.get_text(" ", strip=True)
        config = DINING_SECTIONS[section]
        found_sections.add(section)

        for name in config["names"]:
            alias = config.get("aliases", {}).get(name, name)

            if normalize_dining_name(alias) not in normalize_dining_name(description):
                if name == "Food Truck Plaza" and "Food Truck Plaza" in section:
                    pass
                else:
                    continue

            results.append(
                {
                    "dining_name": name,
                    "dining_location": config["location"],
                    "opening_time": None,
                    "closing_time": None,
                    "cuisine": [],
                    "source_url": DINING_URL,
                    "verified": True,
                }
            )

    if not found_sections:
        raise ValueError("No recognized WSU dining sections found")

    if not results:
        raise ValueError("No dining locations found")

    return results


def fetch_dining() -> list[dict[str, Any]]:
    """Download and parse WSU's official campus dining page."""
    response = requests.get(DINING_URL, timeout=30)
    response.raise_for_status()
    return parse_dining(response.text)
