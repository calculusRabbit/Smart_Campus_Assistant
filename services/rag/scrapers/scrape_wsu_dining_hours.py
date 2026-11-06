"""Extract officially published RSC dining hours from Wichita State University."""

import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

HOURS_URL = "https://www.wichita.edu/services/rsc/Operating_Hours/FoodCourtHours.php"

RESTAURANT_NAMES = {
    "Starbucks": "Starbucks",
    "Chick-fil-A": "Chick-fil-A",
    "Panda Express": "Panda Express",
    "Freddy's": "Freddy's Steakburgers",
    "Sushi Do": "Sushi-Do",
}

DAY_GROUPS = {
    "mon-thurs": [0, 1, 2, 3],
    "mon-thur": [0, 1, 2, 3],
    "mon-fri": [0, 1, 2, 3, 4],
    "fri": [4],
    "sat": [5],
    "sun": [6],
}

HOURS_PATTERN = re.compile(r"^\s*(.+?)\s*-\s*(.+?)\s*$")


def parse_clock(value: str) -> str:
    """Convert a published AM/PM time to 24-hour HH:MM format."""
    normalized = value.strip().lower().replace(".", "")
    normalized = re.sub(r"\s+", "", normalized)
    return datetime.strptime(normalized, "%I%p").strftime("%H:%M")


def parse_schedule_entry(day_line: str, time_line: str) -> dict:
    """Parse one published WSU day group and operating-hours range."""
    day_label = day_line.strip().removesuffix(":")
    days = DAY_GROUPS.get(day_label.lower())

    if days is None:
        raise ValueError(f"Unknown day label: {day_label}")

    match = HOURS_PATTERN.match(time_line.strip())
    if match is None:
        raise ValueError(f"Invalid hours: {time_line}")

    opening = parse_clock(match.group(1))
    closing = parse_clock(match.group(2))

    return {
        "days": days,
        "times": [[opening, closing]],
    }


def parse_hours(html: str) -> dict[str, list[dict]]:
    """Parse the official RSC restaurant schedules."""
    soup = BeautifulSoup(html, "html.parser")
    schedules = {}

    for heading in soup.select("h3"):
        published_name = heading.get_text(" ", strip=True)

        if published_name not in RESTAURANT_NAMES:
            continue

        paragraph = heading.find_next_sibling("p")
        if paragraph is None:
            raise ValueError(f"Missing hours for {published_name}")

        schedule = []

        lines = paragraph.get_text("\n", strip=True).splitlines()

        if len(lines) % 2 != 0:
            raise ValueError(f"Incomplete schedule for {published_name}")

        for index in range(0, len(lines), 2):
            schedule.append(parse_schedule_entry(lines[index], lines[index + 1]))

        if not schedule:
            raise ValueError(f"No operating hours found for {published_name}")

        schedules[RESTAURANT_NAMES[published_name]] = schedule

    if not schedules:
        raise ValueError("No official RSC dining hours found")

    return schedules


def fetch_hours() -> dict[str, list[dict]]:
    """Download current published RSC dining schedules."""
    response = requests.get(HOURS_URL, timeout=30)
    response.raise_for_status()
    return parse_hours(response.text)
