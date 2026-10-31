import json
import os
import re
import time
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from config import EVENTS_PATH

BASE_URL = "https://www.wichita.edu/calendar/index.php"
OUTPUT_FILE = EVENTS_PATH


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def parse_description(soup):
    desc_el = soup.select_one('[itemprop="description"]')
    if not desc_el:
        return ""
    for br in desc_el.find_all("br"):
        br.replace_with(" ")
    return clean_text(desc_el.get_text())


def should_keep(start_date_str, categories):
    try:
        event_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    except ValueError:
        print(f"could not parse date: '{start_date_str}' => keeping it")
        return True

    today = datetime.now()

    if "Academic Calendar" in categories:
        cutoff = today - timedelta(
            days=180
        )  # i feel like no need calendar like withdraw date in last semester 6 months
    else:
        cutoff = today - timedelta(days=(365))  # dont keep event older than 1 year

    return event_date >= cutoff


def format_chunk(data):
    text = f"{data['title']} on {data['start_date']}"

    if data["end_date"] and data["end_date"] != data["start_date"]:
        text += f" to {data['end_date']}"

    if data["time"]:
        text += f" at {data['time']}"

    if data["location"]:
        text += f" in {data['location']}"

    text += "."

    if data["description"] and data["description"].lower() != data["title"].lower():
        text += " " + data["description"] + "."

    if data["categories"]:
        text += " This event is about " + ", ".join(data["categories"]) + "."

    if data["cost"]:
        text += " It is " + data["cost"] + "."

    return text


def extract_event_cost(article):
    """Extract the event cost from its details section."""
    event_details = article.find("div", id="event-details")

    if event_details is None:
        return ""

    for paragraph in event_details.find_all("p"):
        text = paragraph.get_text()
        if "Cost:" in text:
            return clean_text(text.replace("Cost:", "").strip())

    return ""


def extract_event_location(article):
    """Extract the location listed on the WSU event page."""
    location_container = article.find(attrs={"itemprop": "location"})

    if location_container is None:
        return ""

    if location_container.name == "a":
        return clean_text(location_container.get_text())

    location_link = location_container.find("a")

    if location_link is not None:
        return clean_text(location_link.get_text())

    return ""


def scrape_event(eid):
    url_link = BASE_URL + "?eID=" + str(eid)

    # fetch page
    try:
        res = requests.get(url_link, timeout=10)
        print("http code: ", res.status_code)
    except requests.RequestException as e:
        print(f"request error: {e}")
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    # check if valid event page
    article = soup.find("article", class_="wsu_calendar_event_display")
    if not article:
        print("no article tag found, not a valid event page")
        return None

    # get title
    title = article.find("h1", itemprop="name")
    if title:
        title = clean_text(title.get_text())
    if not title:
        print("article found but no title, skipping")
        return None
    print("TITLE: ", title)

    # get dates
    calendar = article.find("add-to-calendar-button")
    if calendar:
        start_date = calendar.get("startdate", "")
        end_date = calendar.get("enddate", "")
        print(f"START DATE: {start_date} | END DATE: {end_date}")
    else:
        start_date = end_date = ""

    # get time start and end event
    time_element = article.find("time", itemprop="startDate")

    if time_element:
        time_text = clean_text(time_element.get_text())
    else:
        time_text = ""

    print(f"TIME: {time_text}")

    # Get event cost.
    cost = extract_event_cost(article)
    print("COST(MONEY):", cost)

    # Get event location.
    location = extract_event_location(article)
    print("LOCATION:", location)

    # get categories
    categories = []
    for a in article.find_all("a", itemprop="eventType"):
        categories.append(clean_text(a.get_text()))
    print("CATEGORIES: ", categories)

    # GET DESCRIPTION IMPRTANÈšT FOR RAG
    description = parse_description(article)
    print("DESCRIPTION:\n", description)

    # apply date filter, ONLY keep events within last 6 or 7 months
    if not should_keep(start_date, categories):
        print(f"FILTERED OUT: date {start_date} is too old")
        return None

    data = {
        "source": "event",
        "eid": eid,
        "url": url_link,
        "title": title,
        "start_date": start_date,
        "end_date": end_date,
        "time": time_text,
        "cost": cost,
        "location": location,
        "categories": categories,
        "description": description,
    }
    data["chunk_text"] = format_chunk(data)
    return data


def find_existing(chunks, title):
    for c in chunks:
        if c["title"] == title:
            return c
    return None


def add_or_merge_event(chunks, event, eid):
    """Add a new event or merge its dates with an existing event."""
    existing = find_existing(chunks, event["title"])

    if existing:
        if event["start_date"] < existing["start_date"]:
            existing["start_date"] = event["start_date"]

        if event["start_date"] > existing["end_date"]:
            existing["end_date"] = event["start_date"]

        existing["chunk_text"] = format_chunk(existing)
        print(
            f"MERGED: {event['title']} "
            f"(range now {existing['start_date']} to {existing['end_date']})"
        )
        return False

    chunks.append(event)
    print(f"SAVED EID {eid}: {event['title']}")
    print("CHUNK TEXT:", event["chunk_text"])
    return True


def save_events(chunks):
    """Save collected events to the configured JSON file."""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(chunks, file, indent=2, ensure_ascii=False)


def main():
    EID_end = 20000
    EID_start = 33000
    delay_time = 0.3

    os.makedirs("data", exist_ok=True)

    chunks = []
    total_saved = 0

    for i, eid in enumerate(range(EID_start, EID_end - 1, -1)):
        print("Scraping...")

        event = scrape_event(eid)

        if event:
            if add_or_merge_event(chunks, event, eid):
                total_saved += 1
        else:
            print(f"eID {eid} skipped")

        if i > 0 and i % 100 == 0:
            save_events(chunks)
            print(f"saved - {total_saved} events so far")

        time.sleep(delay_time)

    save_events(chunks)
    print("DONE", {total_saved})


if __name__ == "__main__":
    main()
