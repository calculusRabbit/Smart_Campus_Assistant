import { useState } from "react"

export default function SignUp() {
  const [username, setUsername] = useState("")
  const [firstName, setFirstName] = useState("")
  const [lastName, setLastName] = useState("")
  const [email, setEmail] = useState("")
  const [dob, setDob] = useState("")
  const [zipcode, setZipcode] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [error, setError] = useState("")

  function handleSubmit(e) {
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
    // TODO: connect to backend once a /signup endpoint exists
    console.log({ username, firstName, lastName, email, dob, zipcode, password })
  }

  return (
    <div>
      <h1>Create account</h1>
      {error && <p style={{ color: "red" }}>{error}</p>}

      <form onSubmit={handleSubmit}>
        <center>
          <table>
            <tbody>
              <tr>
                <td><label>Username</label></td>
                <td>
                  <input
                    type="text"
                    name="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                  />
                </td>
              </tr>

              <tr>
                <td><label>First Name</label></td>
                <td>
                  <input
                    type="text"
                    name="first_name"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    required
                  />
                </td>
              </tr>

              <tr>
                <td><label>Last Name</label></td>
                <td>
                  <input
                    type="text"
                    name="last_name"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    required
                  />
                </td>
              </tr>

              <tr>
                <td><label>Email</label></td>
                <td>
                  <input
                    type="email"
                    name="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </td>
              </tr>

              <tr>
                <td><label>Date of Birth</label></td>
                <td>
                  <input
                    type="date"
                    name="dob"
                    value={dob}
                    onChange={(e) => setDob(e.target.value)}
                    required
                  />
                </td>
              </tr>

              <tr>
                <td><label>Zipcode</label></td>
                <td>
                  <input
                    type="text"
                    name="zipcode"
                    placeholder="67260"
                    value={zipcode}
                    onChange={(e) => setZipcode(e.target.value)}
                    required
                  />
                </td>
              </tr>

              <tr>
                <td><label>Password</label></td>
                <td>
                  <input
                    type="password"
                    name="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </td>
              </tr>

              <tr>
                <td><label>Confirm Password</label></td>
                <td>
                  <input
                    type="password"
                    name="confirmPassword"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />
                </td>
              </tr>

              <tr>
                <td></td>
                <td><button type="submit">Create Account</button></td>
              </tr>
            </tbody>
          </table>
        </center>
      </form>

      <p>already have a account? <a href="/login">sign in</a></p>
    </div>
  )
}
