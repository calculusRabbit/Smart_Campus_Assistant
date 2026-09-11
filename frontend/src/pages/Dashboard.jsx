// let events = [
//   {id: 1, title: "Dev Club Meeting", date: "2026-03-15", time: "5:00 PM", location: "Jabara Hall 167", score: 87, type: "club"},
//   {id: 2, title: "CS Career Fair", date: "2026-03-15", time: "5:00 PM", location: "RSC", score: 99, type: "academic"},
//   {id: 3, title: "Basketball Tournament", date: "2026-03-15", time: "5:00 PM", location: "Heskett Center", score: 36, type: "sports"},
//   {id: 4, title: "Study Group - Algorithms CS560", date: "2026-03-15", time: "5:00 PM", location: "Ablah Library 2nd Floor", score: 100, type: "academic"},
//   {id: 5, title: "Vietnamese Student Association Potluck", date: "2026-03-15", time: "5:00 PM", location: "RSC Room 6767", score: 67, type: "social"},
// ];

// let schedules = [
//   {id: 1, code: "CS 560", name: "Machine Learning", time: "TR 2:00-3:15 PM", room: "Jabara 210", professor: "Dr. Yang"},
//   {id: 2, code: "CS 797Y", name: "NLP", time: "TR 2:00-3:15 PM", room: "LinQuist 305", professor: "Mr. Bean"},
//   {id: 3, code: "CS 598", name: "Senior Project", time: "TR 2:00-3:15 PM", room: "Jabara 115", professor: "Dr. John Cena"},
// ];

// react stuff
import { useEffect, useState } from "react";

let user = {id: 1, name: "Vu", year: "senior", major: "CS", money: -67};

function EventCard({event}) {
  return (
    <div style={{border: "1px solid #ccc", backgroundColor: "white"}}>
      <p style={{color: "gray"}}>{event.event_tags}</p>
      <h3>{event.event_name}</h3>
      <p>{event.event_date} at {event.event_time}</p>
      <p><strong>Location: </strong>{event.event_location}</p>
      <p style={{fontWeight: "bold", color: getScoreColor(event.score)}}>Match: {event.score}%</p>

      <div style={{display: "flex"}}>
        <button>View Details</button>
        <button>Save</button>
      </div>
    </div>
  );
}


function ScheduleCard({course}) {
  return (
    <div style={{borderBottom: "1px solid gray"}}>
      <p style={{fontWeight: "bold"}}>{course.code} - {course.name}</p>
      <p style={{fontSize: "13px", color: "#555"}}>{course.time} | {course.room}</p>
      <p style={{fontSize: "12px", color: "#888"}}>{course.professor}</p>
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


export default function Dashboard() {

  const [events,resetEvents] = useState([]);
  const [schedules, resetSchedules] = useState([]);

  // get data from backend and update arr
  useEffect(() => {
    // fetch events from backend
    fetch("http://localhost:8000/events")
    .then(res => res.json()).then(data => resetEvents(data.events));

    // fetch schedue
    fetch("http://localhost:8000/courses")
    .then(res => res.json()).then(data => resetSchedules(data.courses));

  }, []);

  let eventCards = [];
  let eventScores = [50, 67, 87, 99, 100];
  for (let i = 0; i < events.length; i++) {
    events[i].score = eventScores[i % eventScores.length]; // assign score for testing
    eventCards.push(<EventCard key={events[i].event_id} event={events[i]} />);
  }

  let scheduleCards = [];
  for (let i = 0; i < schedules.length; i++) {
    scheduleCards.push(<ScheduleCard key={schedules[i].id} course={schedules[i]}/>);
  }


  
  return (
    <div style={{backgroundColor: "#f5f5f5"}}>

      <nav style={{backgroundColor: "#fff", display: "flex", justifyContent: "space-between"}}>
        <span style={{fontWeight: "bold", fontSize: "20px"}}>Smart Campus</span>
        <span style={{fontWeight: "bold"}}>Vu Nguyen</span>
      </nav>


      <div style={{margin: "0 auto", padding: "20px"}}>
        <h1>Hey, Vu</h1>
        <p style={{color: "#555"}}>Here is whats going on around campus today.</p>
        <div style={{display: "grid", gridTemplateColumns: "1fr 300px", gap: "20px"}}>

          <div>
            <h2>Recommended For You ({events.length} events)</h2>
            {eventCards}
          </div>



          <div>
            <div style={{backgroundColor: "#fff", border: "1px solid #ddd", padding: "16px"}}>
              <h3 style={{marginTop: 0}}>My Classes</h3>
              {scheduleCards}
            </div>


            <div style={{backgroundColor: "#fff", border: "1px solid #ddd", padding: "10px"}}>
              <h3 style={{marginTop: 0}}>Notifications</h3>
              <p>CS560 homework DUE in 2 days</p>
              <p>New club event matche your profile</p>
              <p>Career fair registration closes tomorrow</p>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}