import { useState } from "react"

export default function Login() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")

  function handleSubmit(e) {
    e.preventDefault()
    // TODO: connect to backend
    console.log(email, password)
  }

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto" }}>
      <div style={{ backgroundColor: "white", padding: "20px", border: "1px solid gray", textAlign: "center" }}>
        <h1>Log In</h1>
        {error && <p>{error}</p>}
        <form onSubmit={handleSubmit}>
          <input
            autoComplete="off"
            autoFocus
            placeholder="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <br /><br />
          <input
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <br /><br />
          <button type="submit" style={{ backgroundColor: "cornflowerblue", padding: "10px 25px" }}>
            Log In
          </button>
        </form>
        <br />
        <a href="/register" style={{ marginRight: "20px" }}>Register</a>
        <a href="/">Back to Home</a>
      </div>
    </div>
  )
}