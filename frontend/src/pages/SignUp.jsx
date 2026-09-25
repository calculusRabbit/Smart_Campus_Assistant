import { useState } from "react"
import { signup } from "../api"
import shockerImage from "../assets/images/wsu-shocker.png"
import styles from "./Auth.module.css"

export default function SignUp({ goTo }) {
  const [username, setUsername] = useState("")
  const [firstName, setFirstName] = useState("")
  const [lastName, setLastName] = useState("")
  const [email, setEmail] = useState("")
  const [dob, setDob] = useState("")
  const [zipcode, setZipcode] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [error, setError] = useState("")

  async function handleSubmit(e) {
    e.preventDefault()

    // GUYS!!! this is not enough btw, backend needs to check all this too
    // NEVER TRUST USER INPUTTTTTTTTT
    if (username.length < 5 || username.length > 30) {
      setError("Username must be between 5 and 30 characters.")
      return
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.")
      return
    }

    if (!/^\d{5}(-\d{4})?$/.test(zipcode)) {
      setError("Zipcode must be 5 digits (e.g. 67260).")
      return
    }

    // simple age check, just compares birth year to current year
    const birthYear = new Date(dob).getFullYear()
    const currentYear = new Date().getFullYear()
    const age = currentYear - birthYear

    if (age < 14) {
      setError("You must be at least 14 years old to sign up.")
      return
    }

    setError("")

    try {
      await signup({
        username: username,
        first_name: firstName,
        last_name: lastName,
        email: email,
        dob: dob,
        zipcode: zipcode,
        password: password,
      })
      goTo("login")
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <img className={styles.logo} src={shockerImage} alt="WSU Shocker" />
        <h2 className={styles.title}>Create account</h2>
        <p className={styles.subtitle}>Join Smart Campus</p>

        {error && <p className={styles.error}>{error}</p>}

        <form onSubmit={handleSubmit}>
          <input
            className={styles.input}
            type="text"
            name="username"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />

          <div className={styles.nameRow}>
            <input
              className={styles.input}
              type="text"
              name="first_name"
              placeholder="First name"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              required
            />
            <input
              className={styles.input}
              type="text"
              name="last_name"
              placeholder="Last name"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              required
            />
          </div>

          <input
            className={styles.input}
            type="email"
            name="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <p className={styles.label}>Date of birth</p>
          <input
            className={styles.input}
            type="date"
            name="dob"
            value={dob}
            onChange={(e) => setDob(e.target.value)}
            required
          />

          <input
            className={styles.input}
            type="text"
            name="zipcode"
            placeholder="Zipcode (67260)"
            value={zipcode}
            onChange={(e) => setZipcode(e.target.value)}
            required
          />

          <input
            className={styles.input}
            type="password"
            name="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <input
            className={styles.input}
            type="password"
            name="confirmPassword"
            placeholder="Confirm password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />

          <button type="submit" className={styles.button}>Create Account</button>
        </form>

        <p className={styles.switchText}>
          Already have an account?{" "}
          <button onClick={() => goTo("login")} className={styles.linkButton}>Sign in</button>
        </p>
      </div>
    </div>
  )
}
