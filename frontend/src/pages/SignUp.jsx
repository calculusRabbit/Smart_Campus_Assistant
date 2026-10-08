import { useState } from "react"
import { signup } from "../api"
import shockerImage from "../assets/images/wsu-shocker.png"
import { interestOptions, MAX_TAG_WORDS } from "../interests"
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
  const [aboutText, setAboutText] = useState("")
  const [interests, setInterests] = useState([])
  const [error, setError] = useState("")

  function toggleInterest(name) {
    if (interests.includes(name)) {
      setInterests(interests.filter(i => i !== name))
    } else {
      setInterests([...interests, name])
    }
  }

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

    // the text is optional but a text with only a few words would be saved like a tag
    const text = aboutText.trim()
    if (text !== "" && text.split(" ").length <= MAX_TAG_WORDS) {
      setError("Write a bit more about what you like, a full sentence works best.")
      return
    }

    // the text goes first, then the tags (same as the profile page)
    let interestList = []
    if (text !== "") {
      interestList.push(text)
    }
    interestList = interestList.concat(interests)

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
        interests: interestList,
      })
      goTo("login")
    } catch (err) {
      setError(err.message)
    }
  }

  // each tag is a button that turns yellow when picked
  let interestButtons = []
  for (let i = 0; i < interestOptions.length; i++) {
    let name = interestOptions[i]
    let picked = interests.includes(name)
    interestButtons.push(
      <button
        key={name}
        type="button"
        onClick={() => toggleInterest(name)}
        className={picked ? styles.pill + " " + styles.pillPicked : styles.pill}
      >
        {name}
      </button>
    )
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

          <p className={styles.label}>What do you like to do, get involved in or explore?</p>
          <textarea
            className={styles.input + " " + styles.textarea}
            placeholder="I like going to concerts and hackathons, and I want to join a club about..."
            value={aboutText}
            onChange={(e) => setAboutText(e.target.value)}
          />

          <p className={styles.label}>Pick some tags too</p>
          <div className={styles.pills}>{interestButtons}</div>

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
