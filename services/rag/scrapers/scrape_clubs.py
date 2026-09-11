import requests
from bs4 import BeautifulSoup
import json
import re
import os

from config import CLUBS_PATH
api_url = "https://wichita.campuslabs.com/engage/api/discovery/search/organizations?top=300&skip=0"
output_file = CLUBS_PATH
headers = {"User-Agent": "Mozilla/5.0"}


def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()


def strip_html(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    return clean_text(soup.get_text())


def format_chunk(club):
    text = f"{club['title']} is a club at WSU. Status: {club['status']}."

    if club["categories"]:
        text += f" It is categorized as {', '.join(club['categories'])}."

    if club["description"]:
        text += f" {club['description']}."

    text += f" More info: {club['url']}"

    return text


def fetch_clubs():
    print("Fetching club from API")
    res = requests.get(api_url, headers=headers, timeout=10)
    print("http code:", res.status_code)
    return res.json().get("value", [])


def load_chunks():
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        print(f"Loaded {len(chunks)} existing chunks")
        return chunks
    return []


def get_existing_club_titles(chunks):
    existing = set()
    for c in chunks:
        if c.get("type") == "club":
            existing.add(c["title"])
    return existing


def parse_club(org):
    name = clean_text(org.get("Name", ""))
    if not name:
        return None

    raw_desc = org.get("Description") or org.get("Summary") or ""
    description = strip_html(raw_desc) if raw_desc else ""

    categories = org.get("CategoryNames") or []
    status = org.get("Status", "Unknown")

    website_key = org.get("WebsiteKey", "")
    url = f"https://wichita.campuslabs.com/engage/organization/{website_key}" if website_key else ""

    club = {
        "source": "club",
        "url": url,
        "title": name,
        "status": status,
        "categories": categories,
        "description": description
    }
    club["chunk_text"] = format_chunk(club)
    return club


def main():
    os.makedirs("data", exist_ok=True)

    organizations = fetch_clubs()
    print(f"Total clubs found: {len(organizations)}")

    chunks = load_chunks()
    existing_titles = get_existing_club_titles(chunks)

    total_added = 0
    for org in organizations:
        club = parse_club(org)
        if not club:
            continue

        if club["title"] in existing_titles:
            print(f"SKIPPED (already there): {club['title']}")
            continue

        chunks.append(club)
        total_added += 1
        print(f"ADDED: {club['title']}")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"\nDONE: added {total_added} clubs, total chunks now: {len(chunks)}")


if __name__ == "__main__":
    main()
