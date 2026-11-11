import styles from "./Auth.module.css";

// shown when the url does not match any page
export default function NotFound({ goTo }) {
  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h2 className={styles.title}>Page not found</h2>
        <p className={styles.subtitle}>There is nothing at this address.</p>
        <button onClick={() => goTo("dashboard")} className={styles.button}>
          Go to Dashboard
        </button>
      </div>
    </div>
  );
}
