"""Read-only scraper for Wichita State University School of Computing faculty."""

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

FACULTY_URL = "https://www.wichita.edu/academics/engineering/SoC/faculty-staff.php"


def extract_faculty_card(card) -> dict | None:
    """Extract faculty details from one profile card."""
    name_element = card.select_one(".profile-name")
    title_element = card.select_one(".profile-display-profile_title")
    email_element = card.select_one(".profile-display-email a")
    phone_element = card.select_one(".profile-display-phone")
    profile_element = card.select_one(".profile-name-link")

    name = name_element.get_text(" ", strip=True) if name_element else ""
    title = title_element.get_text(" ", strip=True) if title_element else ""
    email = (
        email_element.get("href", "").removeprefix("mailto:").strip().lower()
        if email_element
        else ""
    )
    phone = phone_element.get_text(" ", strip=True) if phone_element else ""
    profile_url = urljoin(FACULTY_URL, profile_element.get("href", "")) if profile_element else ""

    if not name or not email.endswith("@wichita.edu"):
        return None

    return {
        "name": name,
        "title": title,
        "department": "School of Computing",
        "email": email,
        "phone": phone,
        "profile_url": profile_url,
        "source_url": FACULTY_URL,
    }


def parse_faculty(html: str) -> list[dict]:
    """Extract unique faculty profiles from the School of Computing page."""
    soup = BeautifulSoup(html, "html.parser")

    faculty_heading = soup.find(
        "h2",
        string=lambda text: text and text.strip() == "Faculty",
    )

    if faculty_heading is None:
        raise ValueError("Faculty section not found")

    collection = faculty_heading.find_next(
        "div",
        class_="collection__items",
    )

    if collection is None or "profiles" not in collection.get("class", []):
        raise ValueError("Faculty profile collection not found")

    professors = []
    seen_emails = set()

    for card in collection.select("div.teaser.collection__item.profile"):
        professor = extract_faculty_card(card)

        if professor is None:
            continue

        email = professor["email"]
        if email in seen_emails:
            continue

        seen_emails.add(email)
        professors.append(professor)

    return professors


def fetch_faculty() -> list[dict]:
    response = requests.get(
        FACULTY_URL,
        timeout=30,
        headers={"User-Agent": "SmartCampusAssistant/1.0"},
    )
    response.raise_for_status()
    return parse_faculty(response.text)


if __name__ == "__main__":
    import json

    faculty = fetch_faculty()

    print(f"Faculty records extracted: {len(faculty)}")
    print(json.dumps(faculty, indent=2, ensure_ascii=False))
