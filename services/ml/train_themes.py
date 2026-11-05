import json
import re
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline

DATA_PATH = Path("services/ml/shockersync_theme_training.json")
MODEL_PATH = Path("services/ml/models/event_theme_classifier.joblib")


def clean_text(value: str) -> str:
    text = BeautifulSoup(str(value or ""), "html.parser").get_text(" ")
    return re.sub(r"\s+", " ", text).strip()


def load_training_data():
    events = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    unique = {}

    for event in events:
        title = clean_text(event.get("title", ""))
        description = clean_text(event.get("description", ""))
        theme = str(event.get("theme") or "").strip()

        if not theme or not (title or description):
            continue

        key = (title.casefold(), description.casefold())

        if key in unique and unique[key][1] != theme:
            raise ValueError(f"Conflicting labels for event: {title}")

        unique[key] = (f"{title}. {description}", theme)

    texts = [item[0] for item in unique.values()]
    labels = [item[1] for item in unique.values()]
    return texts, labels


def create_pipeline():
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=10000,
            sublinear_tf=True,
        )),
        ("classifier", LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=42,
        )),
    ])


def main():
    texts, labels = load_training_data()

    print("Unique training examples:", len(texts))
    print("Theme distribution:", dict(Counter(labels)))

    minimum_count = min(Counter(labels).values())
    folds = min(2, minimum_count)

    if folds < 2:
        raise ValueError("Not enough examples for stratified evaluation.")

    cv = StratifiedKFold(
        n_splits=folds,
        shuffle=True,
        random_state=42,
    )

    predictions = cross_val_predict(
        create_pipeline(),
        texts,
        labels,
        cv=cv,
    )

    print("\nCross-validation accuracy:",
          round(accuracy_score(labels, predictions), 4))
    print("Cross-validation macro F1:",
          round(f1_score(labels, predictions, average="macro"), 4))
    print("Cross-validation weighted F1:",
          round(f1_score(labels, predictions, average="weighted"), 4))

    print("\nPer-theme results:")
    print(classification_report(labels, predictions, zero_division=0))

    model = create_pipeline()
    model.fit(texts, labels)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print("\nSaved separate theme model:", MODEL_PATH)
    print("Existing category model and FAISS index unchanged.")


if __name__ == "__main__":
    main()
