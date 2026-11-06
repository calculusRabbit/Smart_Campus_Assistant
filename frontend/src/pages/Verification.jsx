import { useEffect, useState } from "react";
import { apiFetch } from "../api";

export default function Verification({ goTo }) {
  const [status, setStatus] = useState(null);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("");
  const [manual, setManual] = useState(false);

  useEffect(() => {
    let active = true;

    apiFetch("/verification")
      .then((response) => response.json())
      .then((data) => {
        if (!active) return;

        setStatus(data);
        setManual(
          data.verification?.method === "manual" &&
            data.verification?.status === "pending",
        );
      })
      .catch((err) => {
        if (active) setMessage(err.message);
      });

    return () => {
      active = false;
    };
  }, []);

  async function post(path, body) {
    const response = await apiFetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const result = await response.json();
    setMessage(result.message || "");

    if (result.manual_required) setManual(true);

    if (result.approved) {
      // Current getUser() is in-memory; logging in again refreshes it.
      setMessage("Verified. Log out and log in again to refresh access.");
    }
  }

  async function sendCode(event) {
    event.preventDefault();

    try {
      await post("/verification/otp/send", { email });
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function checkCode(event) {
    event.preventDefault();

    try {
      await post("/verification/otp/check", { code });
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function requestManual() {
    try {
      await post("/verification/manual", {});
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function upload(event) {
    event.preventDefault();

    try {
      const response = await apiFetch("/verification/manual/document", {
        method: "POST",
        body: new FormData(event.currentTarget),
      });
      const result = await response.json();
      setMessage(result.message);
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <main style={{ maxWidth: 650, margin: "2rem auto" }}>
      <h1>Student verification</h1>

      <p>Institution: {status?.school || "Loading..."}</p>
      <p>Status: {status?.account_status || "Loading..."}</p>

      {status?.verification?.admin_message && (
        <p>{status.verification.admin_message}</p>
      )}

      {message && <p role="status">{message}</p>}

      <h2>Verify institution email</h2>
      <p>
        Six digits, five-minute validity, three guesses total. Wait one minute
        before requesting another code.
      </p>

      <form onSubmit={sendCode}>
        <label>
          Institution .edu email
          <input
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        <button type="submit">Send code</button>
      </form>

      <form onSubmit={checkCode}>
        <label>
          Code
          <input
            inputMode="numeric"
            autoComplete="one-time-code"
            pattern="[0-9]{6}"
            maxLength={6}
            value={code}
            required
            onChange={(event) => setCode(event.target.value)}
          />
        </label>
        <button type="submit">Verify code</button>
      </form>

      <button type="button" onClick={requestManual}>
        Cannot access email / no code received / use manual verification
      </button>

      {manual && (
        <section>
          <h2>Manual enrollment document</h2>
          <p>
            Submit a current enrollment letter or schedule. Redact unrelated
            personal information. One PDF, maximum 5 MiB.
          </p>

          <form onSubmit={upload}>
            <input type="file" name="file" accept="application/pdf" required />
            <button type="submit">Submit document</button>
          </form>
        </section>
      )}

      <button type="button" onClick={() => goTo("dashboard")}>
        Back to dashboard
      </button>
    </main>
  );
}
