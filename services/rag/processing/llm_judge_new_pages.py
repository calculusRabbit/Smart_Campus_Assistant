import json
import os
import torch
from transformers import pipeline
from services.rag.config import JUDGE_MODEL, RAW_DATA_PATH, FILTERED_DIR
from services.rag.processing.llm_judge import get_score, load_pages, threshold

# judges only the pages we never judged before and adds them to the kept / dropped files
# llm_judge.py is for judging everything from zero (4 gpus), this one is for the nightly run

clean_file = os.path.join(FILTERED_DIR, "wsu_pages_clean.json")
dropped_file = os.path.join(FILTERED_DIR, "wsu_pages_dropped.json")


def load_if_exists(path):
    if os.path.exists(path):
        return load_pages(path)
    return []


def save_files(kept, dropped):
    with open(clean_file, "w", encoding="utf-8") as f:
        json.dump(kept, f, indent=2, ensure_ascii=False)
    with open(dropped_file, "w", encoding="utf-8") as f:
        json.dump(dropped, f, indent=2, ensure_ascii=False)


def main():
    raw_pages = load_pages(RAW_DATA_PATH)
    kept = load_if_exists(clean_file)
    dropped = load_if_exists(dropped_file)
    print("raw pages:", len(raw_pages), "| kept:", len(kept), "| dropped:", len(dropped))

    # a dropped page was judged too, so it should not be judged again
    judged = set()
    for page in kept:
        judged.add(page["url"])
    for page in dropped:
        judged.add(page["url"])

    todo = []
    for page in raw_pages:
        if page["url"] not in judged:
            todo.append(page)
    print("pages to judge:", len(todo))

    # dont load the model if there is nothing to do
    if len(todo) == 0:
        print("nothing new to judge")
        return

    device = 0 if torch.cuda.is_available() else -1
    pipe = pipeline("text-generation", model=JUDGE_MODEL, device=device)

    for i, page in enumerate(todo):
        score, reason = get_score(page["text"], pipe)
        page["score"] = score
        page["reason"] = reason

        if score >= threshold:
            kept.append(page)
            print(f"[{i+1}/{len(todo)}] {score:.2f} KEPT: {page['title']}")
        else:
            dropped.append(page)
            print(f"[{i+1}/{len(todo)}] {score:.2f} DROPPED: {page['title']}")

        # save every 50 pages so a long run is not lost if it stops
        if i % 50 == 0 and i > 0:
            save_files(kept, dropped)

    save_files(kept, dropped)
    print(f"done! kept {len(kept)}, dropped {len(dropped)} total")


if __name__ == "__main__":
    main()
