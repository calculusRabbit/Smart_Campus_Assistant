import { useEffect, useState } from "react";
import { getUser, getEvents, getCourses, getRecommendedEvents, sendChat } from "../api";
import NavBar from "../components/NavBar";
import styles from "./Dashboard.module.css";

function EventCard({event}) {
  return (
    <div className={styles.eventCard}>
      <p className={styles.eventCategory}>{event.event_category}</p>
      <h3 className={styles.eventName}>{event.event_name}</h3>
      <p>{event.event_date} at {event.event_time}</p>
      <p><strong>Location: </strong>{event.event_location}</p>
      <p>{event.event_description}</p>

      {/* backend does not send a score yet so only show it when there is one */}
      {event.score !== undefined &&
        <p style={{fontWeight: "bold", color: getScoreColor(event.score)}}>Match: {event.score}%</p>
      }

      <div className={styles.eventButtons}>
        <button className={styles.primaryButton}>View Details</button>
        <button className={styles.darkButton}>Save</button>
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


// turn the data that /chat sends back into simple lines of text
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
  const [schedules, resetSchedules] = useState([]);
  const [recommended, setRecommended] = useState(false);

  // get data from backend and update arr
  useEffect(() => {
    // if the student saved interests show recommended events, if not show all events
    getRecommendedEvents(user.id).then(recs => {
      if (recs.length > 0) {
        resetEvents(recs);
        setRecommended(true);
      }
      else {
        getEvents().then(all => resetEvents(all));
      }
    });

    // fetch schedue
    getCourses().then(courses => resetSchedules(courses));

  }, []);

  let eventCards = [];
  for (let i = 0; i < events.length; i++) {
    eventCards.push(<EventCard key={events[i].event_id} event={events[i]} />);
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
            <h2 className={styles.sectionTitle}>{recommended ? "Recommended For You" : "Upcoming Events"} ({events.length} events)</h2>
            {!recommended && <p className={styles.hint}>Add your interests in Profile to get recommendations.</p>}
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
