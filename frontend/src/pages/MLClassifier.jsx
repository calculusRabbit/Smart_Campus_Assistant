import { useState } from "react";
import NavBar from "../components/NavBar";

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

      <main style={{ maxWidth: 760, margin: "40px auto", padding: 24 }}>
        <h1
          style={{
            fontSize: "clamp(28px, 4vw, 42px)",
            lineHeight: 1.2,
            letterSpacing: "-0.5px",
            margin: "0 0 20px",
            overflowWrap: "break-word",
          }}
        >
          ShockerSync ML Event Classifier
        </h1>
        <p>
          Test our trained machine learning model using an event title
          and description.
        </p>

        <form onSubmit={handlePredict}>
          <label htmlFor="ml-title">Event title</label>
          <input
            id="ml-title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            maxLength={500}
            placeholder="Example: Student Cultural Festival"
            style={{ display: "block", width: "100%", margin: "8px 0 20px", padding: 12 }}
          />

          <label htmlFor="ml-description">Event description</label>
          <textarea
            id="ml-description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            maxLength={5000}
            rows={5}
            placeholder="Describe the event..."
            style={{ display: "block", width: "100%", margin: "8px 0 20px", padding: 12 }}
          />

          <button type="submit" disabled={loading || (!title.trim() && !description.trim())}>
            {loading ? "Predicting..." : "Predict Categories"}
          </button>
        </form>

        {error && <p role="alert">{error}</p>}

        {result && (
          <section style={{ marginTop: 32 }} aria-live="polite">
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
                <div key={category} style={{ marginBottom: 16 }}>
                  <div>
                    {category}: {(probability * 100).toFixed(1)}%
                  </div>
                  <progress
                    value={probability}
                    max={1}
                    style={{ width: "100%" }}
                    aria-label={`${category} probability`}
                  />
                </div>
              ))}

            <p style={{ fontSize: 13, opacity: 0.75 }}>
              Experimental model. These scores are model estimates,
              not guaranteed probabilities of an event's true category.
            </p>
          </section>
        )}
      </main>
    </>
  );
}
