import requests
from bs4 import BeautifulSoup
import json
import re
import time
import os

from services.rag.config import ALL_URLS_PATH, RAW_DATA_PATH

def scrape_page(url):
    try:
        res = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        # not a normal page, dont save it
        if res.status_code != 200:
            return None, None

        soup = BeautifulSoup(res.text, "html.parser")

        # remove noise
        noise = ["nav", "footer", "header", "script", "style", "aside", "noscript", "iframe"]
        for tag in soup.find_all(noise):
            tag.decompose()

        title_element = soup.find("h1")

        if title_element is not None:
            title = title_element.get_text(strip=True)
        else:
            title = ""

        if title == "":
            title_element = soup.find("title")

            if title_element is not None:
                title = title_element.get_text(strip=True)
            else:
                title = url

        main = (
            soup.find("main") or
            soup.find("div", {"id": "main"}) or
            soup.find("div", {"class": "main-content"}) or
            soup.body
        )
        if main is None:
            return None, None

        text = main.get_text(separator=" ", strip=True)
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) < 100: # not usefull information i think
            return None, None
        text = title + " - " + text

        return title, text

    except requests.Timeout:
        return None, None
    except requests.ConnectionError:
        return None, None
    except Exception as e:
        return None, None


def main():
    urls = []
    with open(ALL_URLS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            urls.append(json.loads(line)["url"])
    
    print("total urls:", len(urls))

    output_file = RAW_DATA_PATH

    # pages we already scraped
    documents = []
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            documents = json.load(f)
    old_count = len(documents)
    print("pages we already have:", old_count)

    scraped = set()
    for doc in documents:
        scraped.add(doc["url"])

    # only the urls we dont have yet, failed ones are not saved so they get tried again
    todo = []
    for url in urls:
        if url not in scraped:
            todo.append(url)
            scraped.add(url)
    print("urls to scrape:", len(todo))

    for i, url in enumerate(todo):
        print(f"scraping {i+1}/{len(todo)}: {url}")
        title, text = scrape_page(url)

        if title and text:
            documents.append({
                "url": url,
                "title": title,
                "text": text
            })
        else:
            print("failed to scrape:", url)
        
        #save every 100 documents
        if i % 100 == 0 and i > 0 and len(documents) > old_count:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(documents, f, ensure_ascii=False, indent=2)

        time.sleep(0.3)

    # save at the end if there is something new
    if len(documents) > old_count:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)
    
    print(f"done! {len(documents) - old_count} new pages, {len(documents)} total")


if __name__ == "__main__":
    main()

