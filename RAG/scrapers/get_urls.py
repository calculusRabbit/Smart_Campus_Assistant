import requests
from bs4 import BeautifulSoup
import json
from config import ALL_URLS_PATH

site_map = "https://www.wichita.edu/sitemap.xml"

def get_all_urls() -> list:
    print("fetching sitemap...")
    response = requests.get(site_map)

    soup = BeautifulSoup(response.text, "xml")

    list_url = []
    for tag in soup.find_all("loc"):
        url = tag.text
        list_url.append(url)
    
    return list_url


def filter_urls(urls):
    allowed_years = {"2025", "2026"}

    filtered = []
    for url in urls:
        # check if any 20xx year appears in URL
        has_old_year = False

        for year in ["2018", "2019", "2020", "2021", "2022", "2023", "2024"]:
            if year in url:
                has_old_year = True
                break

        # keep only if no old year found
        if not has_old_year:
            filtered.append(url)

    return filtered


def main():
    list_url = get_all_urls()
    # TODO: filter_urls() is defined above but never called here, so old/irrelevant
    # pages (2018-2024) are NOT being dropped right now. Uncomment the line below
    # to actually enable the filter before the next full scrape.
    # list_url = filter_urls(list_url)

    with open(ALL_URLS_PATH, "w", encoding="utf-8") as f:
        for url in list_url:
            f.write(json.dumps({"url": url}) + "\n")


if __name__ == "__main__":
    main()
    
