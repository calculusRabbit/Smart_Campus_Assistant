import { getUser, logout } from "../api";
import shockerImage from "../assets/images/wsu-shocker.png";
import styles from "./NavBar.module.css";

// top bar shown on every page after login
export default function NavBar({ goTo }) {
  const user = getUser();

  function handleLogout() {
    logout();
    goTo("login");
  }

  return (
    <nav className={styles.nav}>
      <span className={styles.brand} onClick={() => goTo("dashboard")}>
        <img className={styles.logo} src={shockerImage} alt="WSU Shocker" />
        Smart <span className={styles.brandAccent}>Campus</span>
      </span>
      <span>
        <span className={styles.userName}>{user.name}</span>
        <button className={styles.navButton} onClick={() => goTo("dashboard")}>Dashboard</button>
        <button className={styles.navButton} onClick={() => goTo("reviews")}>Reviews</button>
        <button className={styles.navButton} onClick={() => goTo("profile")}>Profile</button>
        <button className={styles.navButton} onClick={handleLogout}>Log out</button>
      </span>
    </nav>
  );
}
