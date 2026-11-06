import { useState } from "react";
import { getUser, logout } from "../api";
import shockerImage from "../assets/images/wsu-shocker.png";
import styles from "./NavBar.module.css";

// top bar shown on every page after login
export default function NavBar({ goTo }) {
  const user = getUser();
  // is the dropdown menu open
  const [open, setOpen] = useState(false);

  function handleLogout() {
    logout();
    goTo("login");
  }

  // go to a page and close the menu
  function handleGo(page) {
    setOpen(false);
    goTo(page);
  }

  return (
    <nav className={styles.nav}>
      <span className={styles.brand} onClick={() => goTo("dashboard")}>
        <img className={styles.logo} src={shockerImage} alt="WSU Shocker" />
        Smart <span className={styles.brandAccent}>Campus</span>
      </span>
      <span className={styles.menuWrap}>
        <button
          className={styles.navButton}
          aria-expanded={open}
          onClick={() => setOpen(!open)}
        >
          {user.name} ▾
        </button>
        {open && (
          <div className={styles.menu}>
            <button
              className={styles.menuItem}
              onClick={() => handleGo("dashboard")}
            >
              Dashboard
            </button>
            <button
              className={styles.menuItem}
              onClick={() => handleGo("ml-classifier")}
            >
              ML Classifier
            </button>
            <button
              className={styles.menuItem}
              onClick={() => handleGo("reviews")}
            >
              Reviews
            </button>
            <button
              className={styles.menuItem}
              onClick={() => handleGo("appointments")}
            >
              Appointments
            </button>
            <button
              className={styles.menuItem}
              onClick={() => handleGo("profile")}
            >
              Profile
            </button>
            <button className={styles.menuItem} onClick={handleLogout}>
              Log out
            </button>
          </div>
        )}
      </span>
    </nav>
  );
}
