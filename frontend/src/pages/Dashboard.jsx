import { useEffect, useState } from "react";
import { getUser, getEvents, getCourses, getRecommendedEvents, sendChat } from "../api";
import NavBar from "../components/NavBar";
import styles from "./Dashboard.module.css";

function EventCard({event, saved, onToggleSave}) {
  return (
    <div className={styles.eventCard}>
      <p className={styles.eventCategory}>{event.event_category}</p>
      <h3 className={styles.eventName}>{event.event_name}</h3>
      <p>{event.event_date} at {event.event_time}</p>
      <p><strong>Location: </strong>{event.event_location}</p>
      <p>{event.event_description}</p>

      {/* no score from the backend yet */}
      {event.score !== undefined &&
        <p style={{fontWeight: "bold", color: getScoreColor(event.score)}}>Match: {event.score}%</p>
      }

      <div className={styles.eventButtons}>
        <button className={styles.primaryButton}>View Details</button>
        <button
          className={saved ? styles.savedButton : styles.darkButton}
          onClick={() => onToggleSave(event.event_id)}
        >
          {saved ? "Saved ✓" : "Save"}
        </button>
      </div>
    </div>
  );
}


function ScheduleCard({course}) {
  return (
    <div className={styles.scheduleItem}>
      <p className={styles.scheduleName}>{course.code} - {course.name}</p>
      <p className={styles.scheduleInfo}>{course.time} | {course.room}</p>
      <p className={styles.scheduleProfessor}>{course.professor}</p>
    </div>
  );
}


function getScoreColor(score) {
  if (score >= 50) {
    return "green";
  }
  else {
    return "orange";
  }
}


// make lines of text from the data /chat sends back
function chatDataToLines(result) {
  let lines = [];
  if (!result.data) {
    return lines;
  }

  let items = result.data;
  if (!Array.isArray(items)) {
    items = [items];
  }

  for (let i = 0; i < items.length; i++) {
    let item = items[i];

    if (result.intent === "events" || result.intent === "recommendations") {
      lines.push(item.event_name + " | " + item.event_date + " " + item.event_time + " | " + item.event_location);
    }
    else if (result.intent === "dining") {
      lines.push(item.dining_name + " | " + item.dining_location + " | " + item.opening_time + " - " + item.closing_time + " | " + item.dining_status);
    }
    else if (result.intent === "courses") {
      lines.push(item.code + " " + item.name + " | " + item.time + " | " + item.room + " | " + item.professor);
    }
    else if (result.intent === "professors") {
      lines.push(item.professor_name + " | " + item.professor_department + " | " + item.professor_email + " | rating " + item.professor_rating);
    }
    else if (result.intent === "deadlines") {
      lines.push(item.deadline_title + " | " + item.deadline_date + " | " + item.deadline_description);
    }
  }
  return lines;
}


function ChatPanel() {
  const [messages, setMessages] = useState([
    {from: "bot", text: "Hi! Ask me about events, dining, courses, professors or deadlines.", lines: []}
  ]);
  const [input, setInput] = useState("");

  async function handleSend(e) {
    e.preventDefault();
    const text = input.trim();
    if (text === "") {
      return;
    }

    // show what the user typed right away
    let newMessages = [...messages, {from: "user", text: text, lines: []}];
    setMessages(newMessages);
    setInput("");

    try {
      const result = await sendChat(text);
      // result.detail is the error message from fastapi
      const reply = result.reply || result.detail || "Something went wrong.";
      setMessages([...newMessages, {from: "bot", text: reply, lines: chatDataToLines(result)}]);
    } catch {
      setMessages([...newMessages, {from: "bot", text: "Cannot connect to the backend.", lines: []}]);
    }
  }

  let messageList = [];
  for (let i = 0; i < messages.length; i++) {
    let m = messages[i];
    let lineList = [];
    for (let j = 0; j < m.lines.length; j++) {
      lineList.push(<p key={j} className={styles.chatLine}>- {m.lines[j]}</p>);
    }

    let isUser = m.from === "user";
    messageList.push(
      <div key={i} className={isUser ? styles.message + " " + styles.messageUser : styles.message}>
        <span className={isUser ? styles.bubble + " " + styles.bubbleUser : styles.bubble}>
          {m.text}
          {lineList}
        </span>
      </div>
    );
  }

  return (
    <div className={styles.box + " " + styles.chat}>
      <h3 className={styles.boxTitle}>Campus Assistant</h3>
      <div className={styles.chatMessages}>
        {messageList}
      </div>
      <form onSubmit={handleSend} className={styles.chatForm}>
        <input
          className={styles.chatInput}
          placeholder="Ask something..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" className={styles.primaryButton}>Send</button>
      </form>
    </div>
  );
}


export default function Dashboard({ goTo }) {

  const user = getUser();

  const [events, resetEvents] = useState([]);
  const [allEvents, setAllEvents] = useState([]);
  const [schedules, resetSchedules] = useState([]);
  const [recEvents, setRecEvents] = useState([]);
  const [recLoaded, setRecLoaded] = useState(false);
  const [recLoading, setRecLoading] = useState(false);
  const [recMessage, setRecMessage] = useState("");
  const [tab, setTab] = useState("upcoming");

  // saved events are only in the browser for now
  const [savedIds, setSavedIds] = useState(JSON.parse(localStorage.getItem("savedEvents") || "[]"));

  function toggleSave(eventId) {
    let newIds = [];
    if (savedIds.includes(eventId)) {
      newIds = savedIds.filter(id => id !== eventId);
    } else {
      newIds = [...savedIds, eventId];
    }
    setSavedIds(newIds);
    localStorage.setItem("savedEvents", JSON.stringify(newIds));
  }

  // the backend compares the students interests with the events, the first time is slow
  async function loadRecommendations() {
    setRecLoading(true);
    setRecMessage("");

    let recs = [];
    try {
      recs = await getRecommendedEvents(user.id);
    } catch {
      setRecMessage("Could not reach the backend.");
    }

    setRecEvents(recs);
    setRecLoaded(true);
    setRecLoading(false);
    setTab("recommended");

    if (recs.length === 0) {
      setRecMessage("No matches yet. Write what you like in Profile and try again.");
    }
  }

  // get data from backend and update arr
  useEffect(() => {
    getEvents().then(all => {
      setAllEvents(all);
      resetEvents(all);
    });

    // fetch schedue
    getCourses().then(courses => resetSchedules(courses));

  }, []);

  // saved tab shows the saved ones from all events and from the recommended ones
  let savedEvents = [];
  let everyEvent = allEvents.concat(recEvents);
  for (let i = 0; i < everyEvent.length; i++) {
    if (savedIds.includes(everyEvent[i].event_id)) {
      savedEvents.push(everyEvent[i]);
    }
  }

  let shownEvents = events;
  if (tab === "saved") {
    shownEvents = savedEvents;
  } else if (tab === "recommended") {
    shownEvents = recEvents;
  }

  let eventCards = [];
  for (let i = 0; i < shownEvents.length; i++) {
    eventCards.push(
      <EventCard
        key={shownEvents[i].event_id}
        event={shownEvents[i]}
        saved={savedIds.includes(shownEvents[i].event_id)}
        onToggleSave={toggleSave}
      />
    );
  }

  let scheduleCards = [];
  for (let i = 0; i < schedules.length; i++) {
    scheduleCards.push(<ScheduleCard key={schedules[i].id} course={schedules[i]}/>);
  }


  return (
    <div className={styles.page}>

      <NavBar goTo={goTo} />

      <div className={styles.banner}>
        <h1 className={styles.bannerTitle}>Hey, {user.name}</h1>
        <p className={styles.bannerText}>Here is whats going on around campus today.</p>
      </div>

      <div className={styles.content}>
        <div className={styles.layout}>

          <div>
            <div className={styles.tabs}>
              <button
                className={tab === "upcoming" ? styles.tabActive : styles.tab}
                onClick={() => setTab("upcoming")}
              >
                Upcoming ({events.length})
              </button>
              {recLoaded &&
                <button
                  className={tab === "recommended" ? styles.tabActive : styles.tab}
                  onClick={() => setTab("recommended")}
                >
                  Recommended ({recEvents.length})
                </button>
              }
              <button
                className={tab === "saved" ? styles.tabActive : styles.tab}
                onClick={() => setTab("saved")}
              >
                Saved ({savedEvents.length})
              </button>
            </div>

            <button className={styles.primaryButton} onClick={loadRecommendations} disabled={recLoading}>
              {recLoading ? "Finding events..." : "Get recommendations"}
            </button>
            <p className={styles.hint}>Compares what you wrote in Profile with the events.</p>

            {tab === "recommended" && recMessage !== "" && <p className={styles.hint}>{recMessage}</p>}
            {tab === "saved" && savedEvents.length === 0 && <p className={styles.hint}>No saved events yet, click Save on an event.</p>}
            {eventCards}
          </div>


          <div>
            <div className={styles.box}>
              <h3 className={styles.boxTitle}>My Classes</h3>
              {scheduleCards}
            </div>

            <ChatPanel />
          </div>
        </div>
      </div>
    </div>
  );
}
