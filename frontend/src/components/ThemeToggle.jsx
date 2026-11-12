import { useState } from "react";
import { ACCENTS, getAccent, getTheme, setAccent, setTheme } from "../theme";
import styles from "./ThemeToggle.module.css";

// dark mode button + little color dots, used in the top bar and on the login pages
export default function ThemeToggle() {
  const [theme, setThemeState] = useState(getTheme());
  const [accent, setAccentState] = useState(getAccent());

  function handleTheme() {
    let next = "dark";
    if (theme === "dark") {
      next = "light";
    }
    setTheme(next);
    setThemeState(next);
  }

  function handleAccent(name) {
    setAccent(name);
    setAccentState(name);
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.dots} role="group" aria-label="Color">
        {ACCENTS.map((name) => (
          <button
            key={name}
            type="button"
            className={`${styles.dot} ${styles[name]}`}
            aria-label={`${name} color`}
            aria-pressed={accent === name}
            onClick={() => handleAccent(name)}
          />
        ))}
      </div>
      <button
        type="button"
        className={styles.modeButton}
        aria-pressed={theme === "dark"}
        onClick={handleTheme}
      >
        {theme === "dark" ? "Light mode" : "Dark mode"}
      </button>
    </div>
  );
}
