import { useState } from "react"
import { login } from "../api"
import shockerImage from "../assets/images/wsu-shocker.png"
import styles from "./Auth.module.css"

export default function Login({ goTo }) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")

  async function handleSubmit(e) {
    e.preventDefault()

    try {
      await login(email, password)
      setError("")
      goTo("dashboard")
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <img className={styles.logo} src={shockerImage} alt="WSU Shocker" />
        <h2 className={styles.title}>Smart Campus</h2>
        <p className={styles.subtitle}>Log in to your account</p>

        {error && <p className={styles.error}>{error}</p>}

        <form onSubmit={handleSubmit}>
          <input
            className={styles.input}
            autoComplete="off"
            autoFocus
            placeholder="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            className={styles.input}
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit" className={styles.button}>
            Log In
          </button>
        </form>

        <p className={styles.switchText}>
          Don't have an account?{" "}
          <button onClick={() => goTo("signup")} className={styles.linkButton}>
            Register
          </button>
        </p>
      </div>
    </div>
  )
}
