import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time

from services.rag.config import CLUBS_PATH, DATA_DIR, RETRIES
api_url = "https://wichita.campuslabs.com/engage/api/discovery/search/organizations"
output_file = CLUBS_PATH
headers = {"User-Agent": "Mozilla/5.0"}

# ask for way more than there are so we get all the clubs in one request
TOP = 1000


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
    # returns (clubs, total), or None if it keeps failing
    print("Fetching club from API")
    params = {"top": TOP, "skip": 0, "orderBy": "Name"}
    for attempt in range(RETRIES):
        try:
            res = requests.get(api_url, params=params, headers=headers, timeout=20)
            print("http code:", res.status_code)
            if res.status_code == 200:
                data = res.json()
                return data.get("value", []), data.get("@odata.count")
        except (requests.RequestException, ValueError) as e:
            print(f"request error: {e}")

        time.sleep(2 * (attempt + 1))
    return None


def load_old_clubs():
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_clubs(clubs):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(clubs, f, indent=2, ensure_ascii=False)


def parse_club(org):
    name = clean_text(org.get("Name", ""))
    club_id = org.get("Id")
    if not name or not club_id:
        return None

    raw_desc = org.get("Description") or org.get("Summary") or ""
    description = strip_html(raw_desc) if raw_desc else ""

    categories = org.get("CategoryNames") or []
    status = org.get("Status", "Unknown")

    website_key = org.get("WebsiteKey", "")
    url = f"https://wichita.campuslabs.com/engage/organization/{website_key}" if website_key else ""

    club = {
        "source": "club",
        "id": club_id,
        "url": url,
        "title": name,
        "status": status,
        "categories": categories,
        "description": description
    }
    club["chunk_text"] = format_chunk(club)
    return club


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    result = fetch_clubs()
    if result is None:
        print("could not load clubs, stopping. the old file is kept as it is")
        return
    organizations, total = result
    print(f"Total clubs found: {len(organizations)}")

    # if we got less than the api says, the list got cut off
    if total is not None and len(organizations) != total:
        print(f"got {len(organizations)} clubs but the api says {total}, stopping. the old file is kept as it is")
        return

    # keyed by id so a club is only saved once
    clubs = {}
    for org in organizations:
        club = parse_club(org)
        if club:
            clubs[club["id"]] = club

    old_clubs = load_old_clubs()
    if len(clubs) == 0 and len(old_clubs) > 0:
        print("got 0 clubs, something is probably wrong. the old file is kept as it is")
        return

    # compare with last time just to print what changed
    # (old records have no id so the first run says everything is new)
    old_by_id = {}
    for c in old_clubs:
        if "id" in c:
            old_by_id[c["id"]] = c

    added = 0
    changed = 0
    for club_id, club in clubs.items():
        if club_id not in old_by_id:
            added += 1
        elif old_by_id[club_id]["chunk_text"] != club["chunk_text"]:
            changed += 1

    removed = 0
    for club_id in old_by_id:
        if club_id not in clubs:
            removed += 1

    save_clubs(list(clubs.values()))
    print(f"\nDONE: {added} new, {changed} changed, {removed} removed, {len(clubs)} total")


if __name__ == "__main__":
    main()
