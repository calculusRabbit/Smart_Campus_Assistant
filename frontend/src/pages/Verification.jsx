import { useEffect, useRef, useState } from "react";
import { apiFetch, refreshUser } from "../api";

export default function Verification({ goTo }) {
  const [status, setStatus] = useState(null);
  const [step, setStep] = useState("sso");
  const [email, setEmail] = useState("");
  const [sentEmail, setSentEmail] = useState("");
  const [challengeId, setChallengeId] = useState(null);
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("");
  const [studidId, setStudidId] = useState(null);
  const [busy, setBusy] = useState(false);
  const [resendAt, setResendAt] = useState(0);
  const [helpAt, setHelpAt] = useState(0);
  const [now, setNow] = useState(Date.now());

  const alive = useRef(true);
  const inFlight = useRef(false);

  useEffect(() => {
    alive.current = true;

    const controller = new AbortController();
    const timer = window.setInterval(
      () => setNow(Date.now()),
      1000,
    );

    apiFetch("/verification", {
      signal: controller.signal,
    })
      .then((response) => response.json())
      .then((data) => {
        if (controller.signal.aborted) return;

        setStatus(data);

        const otp = data.otp;

        if (
          data.verification?.method === "manual" &&
          data.verification?.status === "pending"
        ) {
          setStep("manual");
        } else if (
          otp &&
          otp.school_id === data.school_id
        ) {
          const resend =
            Date.parse(otp.resend_available_at) || 0;

          setResendAt(
            Math.max(
              resend,
              Date.parse(otp.locked_until) || 0,
            ),
          );
          setHelpAt(resend);

          if (
            !otp.consumed &&
            otp.challenge_id &&
            Date.parse(otp.expires_at) > Date.now()
          ) {
            setEmail(otp.email);
            setSentEmail(otp.email);
            setChallengeId(otp.challenge_id);
            setStep("otp-code");
          }
        }

        if (data.studid_id) {
          setStudidId(data.studid_id);
        }
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          setMessage(err.message);
        }
      });

    return () => {
      alive.current = false;
      controller.abort();
      window.clearInterval(timer);
    };
  }, []);

  const resendWait = Math.max(
    0,
    Math.ceil((resendAt - now) / 1000),
  );

  const helpWait = Math.max(
    0,
    Math.ceil((helpAt - now) / 1000),
  );

  async function run(action) {
    if (inFlight.current) return;

    inFlight.current = true;
    setBusy(true);

    try {
      await action();
    } catch (err) {
      if (alive.current) {
        setMessage(err.message);

        if (err.retryAfter > 0) {
          setResendAt(
            Date.now() + err.retryAfter * 1000,
          );
        }
      }
    } finally {
      inFlight.current = false;

      if (alive.current) {
        setBusy(false);
      }
    }
  }

  async function post(path, body = {}) {
    const response = await apiFetch(path, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    return response.json();
  }

  async function apply(result) {
    if (!alive.current) return;

    setMessage(result.message || "");

    if (result.email_required) {
      setStep("otp-email");
    }

    if (result.manual_required) {
      setStep("manual");
    }

    if (result.approved) {
      await refreshUser();

      if (alive.current) {
        goTo("dashboard");
      }
    }
  }

  function startStudid() {
    if (inFlight.current) return;

    const popup = window.open(
      "about:blank",
      "_blank",
    );

    if (!popup) {
      setMessage(
        "Please allow the sign-in tab, or use email OTP.",
      );
      return;
    }

    popup.opener = null;

    void run(async () => {
      try {
        const result = await post(
          "/verification/studid",
        );

        if (!alive.current) {
          popup.close();
          return;
        }

        setStudidId(result.id);
        popup.location.replace(result.url);

        setMessage(
          "Sign in in the other tab, then return here.",
        );
      } catch (err) {
        popup.close();
        throw err;
      }
    });
  }

  function checkStudid() {
    void run(async () => {
      const result = await post(
        `/verification/studid/${studidId}`,
      );

      if (!alive.current) return;

      if (!result.pending) {
        setStudidId(null);
      }

      await apply(result);
    });
  }

  function switchToOtp() {
    void run(async () => {
      if (studidId) {
        await apiFetch(
          `/verification/studid/${studidId}`,
          { method: "DELETE" },
        );
      }

      if (!alive.current) return;

      setStudidId(null);
      setCode("");
      setStep("otp-email");
      setMessage("");
    });
  }

  async function sendTo(address) {
    const result = await post(
      "/verification/otp/send",
      { email: address },
    );

    if (!alive.current) return;

    if (result.resend_available_at) {
      const deadline = Date.parse(
        result.resend_available_at,
      );

      setResendAt(deadline);
      setHelpAt(deadline);
    }

    if (result.sent) {
      setEmail(result.email);
      setSentEmail(result.email);
      setChallengeId(result.challenge_id);
      setStudidId(null);
      setCode("");
      setStep("otp-code");
    }

    await apply(result);
  }

  function sendCode(event) {
    event.preventDefault();
    void run(() => sendTo(email));
  }

  function checkCode(event) {
    event.preventDefault();

    void run(async () => {
      const result = await post(
        "/verification/otp/check",
        {
          code,
          challenge_id: challengeId,
        },
      );

      if (
        alive.current &&
        result.otp_locked
      ) {
        setResendAt(
          Date.parse(result.locked_until),
        );
        setChallengeId(null);
      }

      await apply(result);
    });
  }

  function changeEmail() {
    void run(async () => {
      await apiFetch(
        "/verification/otp",
        { method: "DELETE" },
      );

      if (!alive.current) return;

      setEmail("");
      setSentEmail("");
      setChallengeId(null);
      setCode("");
      setStep("otp-email");
      setMessage("");
    });
  }

  function requestManual() {
    void run(async () => {
      if (studidId) {
        await apiFetch(
          `/verification/studid/${studidId}`,
          { method: "DELETE" },
        );
      }

      await apiFetch(
        "/verification/otp",
        { method: "DELETE" },
      );

      const result = await post(
        "/verification/manual",
      );

      if (alive.current) {
        setStudidId(null);
      }

      await apply(result);
    });
  }

  function upload(event) {
    event.preventDefault();

    const body = new FormData(
      event.currentTarget,
    );

    void run(async () => {
      const response = await apiFetch(
        "/verification/manual/document",
        {
          method: "POST",
          body,
        },
      );

      await apply(await response.json());
    });
  }

  return (
    <main
      style={{
        maxWidth: 650,
        margin: "2rem auto",
      }}
    >
      <h1>Student verification</h1>

      <p>
        Institution: {status?.school || "Loading..."}
      </p>
      <p>
        Status: {status?.account_status || "Loading..."}
      </p>

      {status?.verification?.admin_message && (
        <p>{status.verification.admin_message}</p>
      )}

      {message && (
        <p role="status">{message}</p>
      )}

      {step === "sso" && (
        <section>
          <h2>Institutional sign-in — preferred</h2>

          <p>
            Use your institution&apos;s sign-in through Studid.
            It opens in another tab; keep this application
            tab open. You&apos;ll then confirm your .edu email.
          </p>

          <button
            type="button"
            onClick={startStudid}
            disabled={
              busy ||
              !status ||
              Boolean(studidId)
            }
          >
            Continue with institutional SSO
          </button>

          {studidId && (
            <button
              type="button"
              onClick={checkStudid}
              disabled={busy}
            >
              {busy
                ? "Checking..."
                : "Check institutional login"}
            </button>
          )}

          <div>
            <button
              type="button"
              onClick={switchToOtp}
              disabled={busy || !status}
            >
              I don&apos;t want to use SSO, or I can&apos;t use SSO
            </button>
          </div>
        </section>
      )}

      {step === "otp-email" && (
        <section>
          <h2>Verify your .edu email</h2>

          <form onSubmit={sendCode}>
            <label>
              Institution .edu email
              <input
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
              />
            </label>

            <button
              type="submit"
              disabled={busy || resendWait > 0}
            >
              {resendWait > 0
                ? `Send code in ${resendWait}s`
                : "Send code"}
            </button>
          </form>

          <button
            type="button"
            onClick={requestManual}
            disabled={busy}
          >
            I can&apos;t access, or don&apos;t have, an .edu email
          </button>
        </section>
      )}

      {step === "otp-code" && (
        <section>
          <h2>Enter your verification code</h2>

          <p>
            Code sent to {sentEmail}.
            Codes expire in five minutes.
          </p>

          <form onSubmit={checkCode}>
            <label>
              Six-digit code
              <input
                inputMode="numeric"
                autoComplete="one-time-code"
                pattern="[0-9]{6}"
                maxLength={6}
                value={code}
                required
                onChange={(event) =>
                  setCode(event.target.value)
                }
              />
            </label>

            <button
              type="submit"
              disabled={busy || !challengeId}
            >
              Verify code
            </button>
          </form>

          <div>
            <button
              type="button"
              onClick={() =>
                void run(() => sendTo(sentEmail))
              }
              disabled={busy || resendWait > 0}
              style={{
                opacity:
                  busy || resendWait > 0 ? 0.5 : 1,
              }}
            >
              {resendWait > 0
                ? `Resend code in ${resendWait}s`
                : "Resend code"}
            </button>
          </div>

          <div>
            <button
              type="button"
              onClick={requestManual}
              disabled={busy || helpWait > 0}
              style={{
                opacity:
                  busy || helpWait > 0 ? 0.5 : 1,
              }}
            >
              I don&apos;t see the OTP email in my inbox
            </button>
          </div>

          <button
            type="button"
            onClick={changeEmail}
            disabled={busy}
          >
            Change email
          </button>
        </section>
      )}

      {step === "manual" && (
        <section>
          <h2>Manual enrollment document</h2>

          <p>
            Submit a current enrollment letter or schedule.
            Redact unrelated personal information.
            One PDF, maximum 5 MiB.
          </p>

          <form onSubmit={upload}>
            <input
              type="file"
              name="file"
              accept="application/pdf"
              required
            />

            <button
              type="submit"
              disabled={busy}
            >
              Submit document
            </button>
          </form>
        </section>
      )}

      <button
        type="button"
        onClick={() => goTo("dashboard")}
        disabled={busy}
      >
        Back to dashboard
      </button>
    </main>
  );
}