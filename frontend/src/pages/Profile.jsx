import { useEffect, useState } from "react";
import {
  getUser,
  getInterests,
  saveInterests,
  deleteAccount,
  logout,
} from "../api";
import shockerImage from "../assets/images/babyboo-pokko.gif";
import { interestOptions, MAX_TAG_WORDS } from "../interests";
import styles from "./Auth.module.css";

// reasons in the delete account popup
const deleteReasons = [
  "Not useful for me",
  "The events or info were wrong",
  "Privacy concerns",
  "Too many notifications",
  "Using something else",
  "Other",
];

export default function Profile({ goTo }) {
  const user = getUser();

  // major and year have no backend yet so keep them in the browser for now
  const [major, setMajor] = useState(localStorage.getItem("major") || "");
  const [year, setYear] = useState(localStorage.getItem("year") || "freshman");
  const [interests, setInterests] = useState([]);
  const [aboutText, setAboutText] = useState("");
  const [message, setMessage] = useState("");

  // delete account popup
  const [showDelete, setShowDelete] = useState(false);
  const [reason, setReason] = useState("");
  const [comment, setComment] = useState("");
  const [deletePassword, setDeletePassword] = useState("");
  const [deleteError, setDeleteError] = useState("");
  const [deleting, setDeleting] = useState(false);

  // load saved stuff when the page opens
  // the text and the tags are saved in the same list so split them again here
  useEffect(() => {
    getInterests(user.id).then((saved) => {
      let tags = [];
      let texts = [];
      for (let i = 0; i < saved.length; i++) {
        if (saved[i].split(" ").length > MAX_TAG_WORDS) {
          texts.push(saved[i]);
        } else {
          tags.push(saved[i]);
        }
      }
      setInterests(tags);
      setAboutText(texts.join(" "));
    });
  }, [user.id]);

  function toggleInterest(name) {
    if (interests.includes(name)) {
      setInterests(interests.filter((i) => i !== name));
    } else {
      setInterests([...interests, name]);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();

    localStorage.setItem("major", major);
    localStorage.setItem("year", year);

    const text = aboutText.trim();

    // a text with only a few words would be saved like a tag
    if (text !== "" && text.split(" ").length <= MAX_TAG_WORDS) {
      setMessage("Write a bit more, a full sentence works best.");
      return;
    }

    // the text goes first, then the tags
    let toSave = [];
    if (text !== "") {
      toSave.push(text);
    }
    toSave = toSave.concat(interests);

    // backend says at least one interest is needed
    if (toSave.length === 0) {
      setMessage("Write something you like or pick at least one tag.");
      return;
    }

    try {
      await saveInterests(user.id, toSave);
      setMessage("Saved!");
    } catch (err) {
      setMessage(err.message);
    }
  }

  // close the popup and clear what was typed
  function closeDelete() {
    setShowDelete(false);
    setReason("");
    setComment("");
    setDeletePassword("");
    setDeleteError("");
  }

  async function handleDelete(e) {
    e.preventDefault();
    setDeleting(true);

    try {
      await deleteAccount(user.id, deletePassword, reason, comment);
      localStorage.setItem(
        "loginNotice",
        "Your account is scheduled for deletion. Log in within 30 days to restore it.",
      );
      // log out last, the page needs the user until it changes
      logout();
      goTo("login");
    } catch (err) {
      setDeleteError(err.message);
      setDeleting(false);
    }
  }

  let reasonOptions = [];
  for (let i = 0; i < deleteReasons.length; i++) {
    reasonOptions.push(
      <option key={deleteReasons[i]} value={deleteReasons[i]}>
        {deleteReasons[i]}
      </option>,
    );
  }

  // each interest is a button that turns yellow when picked
  let interestButtons = [];
  for (let i = 0; i < interestOptions.length; i++) {
    let name = interestOptions[i];
    let picked = interests.includes(name);
    interestButtons.push(
      <button
        key={name}
        type="button"
        onClick={() => toggleInterest(name)}
        className={picked ? styles.pill + " " + styles.pillPicked : styles.pill}
      >
        {name}
      </button>,
    );
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
          <select
            className={styles.input}
            value={year}
            onChange={(e) => setYear(e.target.value)}
          >
            <option value="freshman">Freshman</option>
            <option value="sophomore">Sophomore</option>
            <option value="junior">Junior</option>
            <option value="senior">Senior</option>
          </select>

          <p className={styles.label}>
            What do you like to do, get involved in or explore?
          </p>
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

        <hr className={styles.line} />
        <button
          onClick={() => setShowDelete(true)}
          className={styles.dangerButton}
        >
          Delete account
        </button>
      </div>

      {showDelete && (
        <div className={styles.overlay} onClick={closeDelete}>
          <form
            className={styles.modal}
            onClick={(e) => e.stopPropagation()}
            onSubmit={handleDelete}
          >
            <h3 className={styles.title}>Delete your account?</h3>
            <p className={styles.subtitle}>
              You can get your account back by logging in within 30 days. After
              that it is deleted for good.
            </p>

            <p className={styles.label}>Why are you leaving? (optional)</p>
            <select
              className={styles.input}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            >
              <option value="">Choose a reason</option>
              {reasonOptions}
            </select>
            <textarea
              className={styles.input + " " + styles.textarea}
              placeholder="Anything else you want to tell us? (optional)"
              maxLength={200}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />

            <p className={styles.label}>Enter your password to confirm</p>
            <input
              className={styles.input}
              type="password"
              value={deletePassword}
              onChange={(e) => setDeletePassword(e.target.value)}
            />
            {deleteError && <p className={styles.error}>{deleteError}</p>}

            <div className={styles.modalButtons}>
              <button
                type="button"
                onClick={closeDelete}
                className={styles.darkButton}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={deletePassword === "" || deleting}
                className={styles.dangerButton}
              >
                {deleting ? "Deleting..." : "Delete"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
