import { useEffect, useState } from "react";
import { apiFetch, refreshUser } from "../api";
import NavBar from "../components/NavBar";
import styles from "./Auth.module.css";

export default function Verification({ goTo }) {
  const [status, setStatus] = useState(null);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("");
  const [manual, setManual] = useState(false);
  const [studidId, setStudidId] = useState(null);
  const [checkingStudid, setCheckingStudid] = useState(false);

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
      await refreshUser();
      goTo("dashboard");
    }

    return result;
  }

  async function startStudid() {
    // open during the click so browser doesn't block the tab
    const popup = window.open("about:blank", "_blank");

    if (!popup) {
      setMessage(
        "Please allow Studid to open in a new tab for SSO verification",
      );
      return;
    }

    popup.opener = null;

    try {
      const data = await post("/verification/studid", {});
      setStudidId(data.id);
      popup.location.replace(data.url);
      setMessage("Sign in in the new tab, then return to this tab.");
    } catch (err) {
      popup.close();
      setMessage(
        `${err.message}. Email OTP and manual verification remain available.`,
      );
    }
  }

  async function checkStudid() {
    setCheckingStudid(true);

    try {
      for (let attempt = 0; attempt < 12; attempt++) {
        const data = await post(`/verification/studid/${studidId}`, {});

        if (!data.pending) {
          setStudidId(null);
          return;
        }

        if (attempt < 11) {
          await new Promise((resolve) => setTimeout(resolve, 5000));
        }
      }

      setMessage(
        "Login is still pending. Finish SSO and check again, or use email OTP.",
      );
    } catch (err) {
      setMessage(
        `${err.message}. You can use email OTP or manual verification instead.`,
      );
    } finally {
      setCheckingStudid(false);
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
    <>
      <NavBar goTo={goTo} />
      <div className={styles.pageInner}>
        <main className={styles.card + " " + styles.wide}>
          <h1>Student verification</h1>

          <p>Institution: {status?.school || "Loading..."}</p>
          <p>Status: {status?.account_status || "Loading..."}</p>

          {status?.verification?.admin_message && (
            <p>{status.verification.admin_message}</p>
          )}

          {message && <p role="status">{message}</p>}

          <h2>Institutional SSO via studid.io (optional)</h2>
          <p>
            Studid is a third-party service. It opens in a separate tab (please
            keep this tab open). Email OTP and manual verification are still
            available below.
          </p>

          <button type="button" onClick={startStudid} disabled={checkingStudid}>
            Continue with Studid
          </button>

          {studidId && (
            <button
              type="button"
              onClick={checkStudid}
              disabled={checkingStudid}
            >
              {checkingStudid ? "Checking..." : "Check institutional login"}
            </button>
          )}

          <h2>Verify institution email</h2>
          <p>
            Six digits, five-minute validity, three guesses total. Wait one
            minute before requesting another code.
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
            I can't access my .edu email / I didn't receive a code / I want to
            use manual verification
          </button>

          {manual && (
            <section>
              <h2>Manual enrollment document</h2>
              <p>
                Submit a current enrolment letter or schedule. Redact unrelated
                personal information. One PDF, maximum 5 MB.
              </p>

              <form onSubmit={upload}>
                <input
                  type="file"
                  name="file"
                  accept="application/pdf"
                  required
                />
                <button type="submit">Submit document</button>
              </form>
            </section>
          )}

          <button type="button" onClick={() => goTo("dashboard")}>
            Back to dashboard
          </button>
        </main>
      </div>
    </>
  );
}
