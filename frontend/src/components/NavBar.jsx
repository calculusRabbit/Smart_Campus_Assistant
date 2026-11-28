import { useState } from "react";
import { logout } from "../api";
import ThemeToggle from "./ThemeToggle";
import { BRAND_START, BRAND_END, NAV_LINKS } from "../config";
import styles from "./NavBar.module.css";

// top bar shown on every page after login
export default function NavBar({ goTo }) {
  // is the dropdown menu open
  const [open, setOpen] = useState(false);

  async function handleLogout() {
    try {
      await logout();
    } catch (error) {
      window.alert(
        `Local login cleared, but server logout was not confirmed: ${error.message}`,
      );
    } finally {
      goTo("login");
    }
  }

  // go to a page and close the menu
  function handleGo(page) {
    setOpen(false);
    goTo(page);
  }

  let menuItems = [];
  for (let i = 0; i < NAV_LINKS.length; i++) {
    let link = NAV_LINKS[i];
    menuItems.push(
      <button
        key={link.page}
        className={styles.menuItem}
        onClick={() => handleGo(link.page)}
      >
        {link.label}
      </button>,
    );
  }

  return (
    <nav className={styles.nav}>
      <button className={styles.brand} onClick={() => goTo("dashboard")}>
        {BRAND_START} <span className={styles.brandAccent}>{BRAND_END}</span>
      </button>
      <div className={styles.right}>
        <ThemeToggle />
        <span className={styles.menuWrap}>
          <button
            className={styles.navButton}
            aria-expanded={open}
            onClick={() => setOpen(!open)}
          >
            Menu ▾
          </button>
          {open && (
            <div className={styles.menu}>
              {menuItems}
              <button className={styles.menuItem} onClick={handleLogout}>
                Log out
              </button>
            </div>
          )}
        </span>
      </div>
    </nav>
  );
}
