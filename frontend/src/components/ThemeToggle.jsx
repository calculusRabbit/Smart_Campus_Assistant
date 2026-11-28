import { useState } from "react";
import { THEMES, getTheme, setTheme } from "../theme";
import styles from "./ThemeToggle.module.css";

// small switch to pick light, dark or color-blind mode (top bar and login pages)
export default function ThemeToggle() {
  const [theme, setThemeState] = useState(getTheme());

  function handleClick(id) {
    setTheme(id);
    setThemeState(id);
  }

  return (
    <div className={styles.wrap} role="group" aria-label="Theme">
      {THEMES.map((t) => (
        <button
          key={t.id}
          type="button"
          className={styles.option}
          aria-pressed={theme === t.id}
          onClick={() => handleClick(t.id)}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
