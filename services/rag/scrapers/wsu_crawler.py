import requests
from bs4 import BeautifulSoup
import json
import re
import time
import os

from config import RAW_DATA_PATH

def scrape_page(url):
    try:
        res = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )

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
    with open("data/all_urls.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            urls.append(json.loads(line)["url"])
    
    print("total urls:", len(urls))

    output_file = RAW_DATA_PATH

    documents = []
    for i, url in enumerate(urls):
        print(f"scraping {i+1}/{len(urls)}: {url}")
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
        if i % 100 == 0 and i > 0:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(documents, f, ensure_ascii=False, indent=2)

        time.sleep(0.3)

    # final save
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    print("done! total documents:", len(documents))


if __name__ == "__main__":
    main()

