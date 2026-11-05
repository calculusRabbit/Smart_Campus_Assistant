import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MultiLabelBinarizer

DATA_PATH = Path("services/rag/data/all_events.json")
RANDOM_STATE = 42


def main():
    events = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    labeled = [
        event
        for event in events
        if isinstance(event, dict)
        and event.get("categories")
        and (event.get("title") or event.get("description"))
    ]

    texts = [
        f"{event.get('title') or ''} {event.get('description') or ''}".strip() for event in labeled
    ]
    labels = [event["categories"] for event in labeled]

    encoder = MultiLabelBinarizer()
    y = encoder.fit_transform(labels)

    print("Labeled events:", len(texts))
    print("Categories:", list(encoder.classes_))
    print("Category counts:", dict(zip(encoder.classes_, y.sum(axis=0).tolist(), strict=True)))

    # Keep recurring events with identical text in the same split.
    def normalize(value):
        return " ".join(str(value or "").lower().split())

    groups = [
        normalize(event.get("title")) + " || " + normalize(event.get("description"))
        for event in labeled
    ]

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.25,
        random_state=RANDOM_STATE,
    )
    train_idx, test_idx = next(splitter.split(texts, y, groups=groups))

    X_train = [texts[i] for i in train_idx]
    X_test = [texts[i] for i in test_idx]
    y_train = y[train_idx]
    y_test = y[test_idx]

    overlap = set(groups[i] for i in train_idx) & set(groups[i] for i in test_idx)
    if overlap:
        raise ValueError("Duplicate events crossed the split.")
    print("Overlapping event groups:", len(overlap))

    print("Training events:", len(X_train))
    print("Testing events:", len(X_test))

    train_counts = y_train.sum(axis=0)
    if any(count == 0 or count == len(y_train) for count in train_counts):
        print("Training labels do not have sufficient class variation.")
        return

    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
            (
                "classifier",
                OneVsRestClassifier(LogisticRegression(max_iter=1000, class_weight="balanced")),
            ),
        ]
    )

    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    print("\nEvaluation on held-out events:")
    print(
        classification_report(
            y_test,
            predictions,
            target_names=encoder.classes_,
            zero_division=0,
        )
    )
    print("Micro F1:", round(f1_score(y_test, predictions, average="micro", zero_division=0), 3))
    print("Macro F1:", round(f1_score(y_test, predictions, average="macro", zero_division=0), 3))

    # Retrain on all labeled events after evaluating on held-out data.
    model.fit(texts, y)

    import joblib

    output = Path("services/ml/models/event_classifier.joblib")
    output.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        {"model": model, "encoder": encoder},
        output,
    )

    print("\nFinal model trained on all labeled events.")
    print("Model saved to:", output)
    print("Model not deployed to chatbot.")


if __name__ == "__main__":
    main()
