import { useState } from "react";
import NavBar from "../components/NavBar";
import styles from "./MLClassifier.module.css";

export default function MLClassifier({ goTo }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handlePredict(event) {
    event.preventDefault();
    setResult(null);
    setError("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/ml/predict-event", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, description }),
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }

      setResult(await response.json());
    } catch {
      setError("Unable to connect to the ML prediction service.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <NavBar goTo={goTo} />

      <main className={styles.page}>
        <div className={styles.panel}>
          <h1 className={styles.title}>ML Event Classifier</h1>
          <p>
            Test our trained machine learning model using an event title and
            description.
          </p>

          <form onSubmit={handlePredict}>
            <label htmlFor="ml-title">Event title</label>
            <input
              id="ml-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              maxLength={500}
              placeholder="Example: Student Cultural Festival"
              className={styles.field}
            />

            <label htmlFor="ml-description">Event description</label>
            <textarea
              id="ml-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              maxLength={5000}
              rows={5}
              placeholder="Describe the event..."
              className={styles.field}
            />

            <button
              type="submit"
              className={styles.button}
              disabled={loading || (!title.trim() && !description.trim())}
            >
              {loading ? "Predicting..." : "Predict Categories"}
            </button>
          </form>

          {error && (
            <p role="alert" className={styles.error}>
              {error}
            </p>
          )}

          {result && (
            <section className={styles.results} aria-live="polite">
              <h2>ML Prediction Results</h2>
              <p>Status: {result.status}</p>

              {result.status === "model_unavailable" && (
                <p>The ML model is currently unavailable.</p>
              )}

              {result.status === "uncertain" && (
                <p>No category reached the prediction threshold.</p>
              )}

              <p>
                <strong>Predicted categories:</strong>{" "}
                {result.categories.length
                  ? result.categories.join(", ")
                  : "None"}
              </p>

              <h3>Category probabilities</h3>
              {Object.entries(result.probabilities)
                .sort((a, b) => b[1] - a[1])
                .map(([category, probability]) => (
                  <div key={category} className={styles.bar}>
                    <div>
                      {category}: {(probability * 100).toFixed(1)}%
                    </div>
                    <progress
                      value={probability}
                      max={1}
                      className={styles.progress}
                      aria-label={`${category} probability`}
                    />
                  </div>
                ))}

              <p className={styles.note}>
                Experimental model. These scores are model estimates, not
                guaranteed probabilities of an event's true category.
              </p>
            </section>
          )}
        </div>
      </main>
    </>
  );
}
