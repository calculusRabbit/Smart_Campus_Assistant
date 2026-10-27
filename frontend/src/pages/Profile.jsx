import { useEffect, useState } from "react"
import { getUser, getInterests, saveInterests } from "../api"
import shockerImage from "../assets/images/wsu-shocker.png"
import { interestOptions, MAX_TAG_WORDS } from "../interests"
import styles from "./Auth.module.css"

export default function Profile({ goTo }) {
  const user = getUser()

  // major and year have no backend yet so keep them in the browser for now
  const [major, setMajor] = useState(localStorage.getItem("major") || "")
  const [year, setYear] = useState(localStorage.getItem("year") || "freshman")
  const [interests, setInterests] = useState([])
  const [aboutText, setAboutText] = useState("")
  const [message, setMessage] = useState("")

  // load saved stuff when the page opens
  // the text and the tags are saved in the same list so split them again here
  useEffect(() => {
    getInterests(user.id).then(saved => {
      let tags = []
      let texts = []
      for (let i = 0; i < saved.length; i++) {
        if (saved[i].split(" ").length > MAX_TAG_WORDS) {
          texts.push(saved[i])
        } else {
          tags.push(saved[i])
        }
      }
      setInterests(tags)
      setAboutText(texts.join(" "))
    })
  }, [])

  function toggleInterest(name) {
    if (interests.includes(name)) {
      setInterests(interests.filter(i => i !== name))
    } else {
      setInterests([...interests, name])
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()

    localStorage.setItem("major", major)
    localStorage.setItem("year", year)

    const text = aboutText.trim()

    // a text with only a few words would be saved like a tag
    if (text !== "" && text.split(" ").length <= MAX_TAG_WORDS) {
      setMessage("Write a bit more, a full sentence works best.")
      return
    }

    // the text goes first, then the tags
    let toSave = []
    if (text !== "") {
      toSave.push(text)
    }
    toSave = toSave.concat(interests)

    // backend says at least one interest is needed
    if (toSave.length === 0) {
      setMessage("Write something you like or pick at least one tag.")
      return
    }

    try {
      await saveInterests(user.id, toSave)
      setMessage("Saved!")
    } catch (err) {
      setMessage(err.message)
    }
  }

  // each interest is a button that turns yellow when picked
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
        <h2 className={styles.title}>Profile</h2>
        <p className={styles.subtitle}>Logged in as {user.email}</p>
        {message && <p className={styles.message}>{message}</p>}

        <form onSubmit={handleSubmit}>
          <p className={styles.label}>Major</p>
          <input
            className={styles.input}
            type="text"
            placeholder="Computer Science"
            value={major}
            onChange={(e) => setMajor(e.target.value)}
          />

          <p className={styles.label}>Year</p>
          <select className={styles.input} value={year} onChange={(e) => setYear(e.target.value)}>
            <option value="freshman">Freshman</option>
            <option value="sophomore">Sophomore</option>
            <option value="junior">Junior</option>
            <option value="senior">Senior</option>
          </select>

          <p className={styles.label}>What do you like to do, get involved in or explore?</p>
          <textarea
            className={styles.input + " " + styles.textarea}
            placeholder="I like going to concerts and hackathons, and I want to join a club about..."
            value={aboutText}
            onChange={(e) => setAboutText(e.target.value)}
          />

          <p className={styles.label}>Pick some tags too</p>
          <div className={styles.pills}>{interestButtons}</div>

          <button type="submit" className={styles.button}>
            Save
          </button>
        </form>

        <button onClick={() => goTo("dashboard")} className={styles.darkButton}>
          Back to Dashboard
        </button>
      </div>
    </div>
  )
}
