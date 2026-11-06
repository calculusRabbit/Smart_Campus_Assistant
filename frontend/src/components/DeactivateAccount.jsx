import { useState } from "react";
import { deleteAccount } from "../api";
import Captcha from "./Captcha";

export default function DeactivateAccount({ goTo }) {
  const [message, setMessage] = useState("");
  const [captchaKey, setCaptchaKey] = useState(0);

  async function handleSubmit(event) {
    event.preventDefault();

    if (
      !window.confirm(
        "Deactivate your account? Your data is retained, and logging in restores it.",
      )
    ) {
      return;
    }

    const form = new FormData(event.currentTarget);

        try {
      await deleteAccount(
        form.get("password"),
        form.get("captcha"),
      );

      goTo("login");
    } catch (err) {
      setMessage(err.message);
      setCaptchaKey((value) => value + 1);
    }
  }

  return (
    <section>
      <h2>Deactivate account</h2>
      <p>
        Your data is retained. Log in with your password to restore the account.
      </p>

      {message && <p role="alert">{message}</p>}

      <form onSubmit={handleSubmit}>
        <label>
          Confirm password
          <input
            type="password"
            name="password"
            autoComplete="current-password"
            maxLength={128}
            required
          />
        </label>

        <Captcha key={captchaKey} action="deactivate" />

        <button type="submit">Deactivate account</button>
      </form>
    </section>
  );
}
