// turns the backend data into events for the week calendar

// letters used in the class times: M T W R F S U (R is thursday, U is sunday)
const DAY_NUMBERS = { U: 0, M: 1, T: 2, W: 3, R: 4, F: 5, S: 6 };

// 11 + "PM" -> 23, 12 + "AM" -> 0
function to24Hour(hour, ampm) {
  let h = Number(hour) % 12;
  if (ampm.toUpperCase() === "PM") {
    h = h + 12;
  }
  return h;
}

function pad(n) {
  return String(n).padStart(2, "0");
}

// "11:00" + "PM" -> "23:00"
function timeTo24(time, ampm) {
  const pieces = time.split(":");
  return pad(to24Hour(pieces[0], ampm)) + ":" + pieces[1];
}

// "WF 11:00 AM - 12:15 PM" -> { days: [3, 5], start: "11:00", end: "12:15" }
// returns null if the text looks different
export function parseClassTime(text) {
  if (!text) {
    return null;
  }

  // ["WF", "11:00", "AM", "-", "12:15", "PM"]
  const parts = text.split(" ");
  if (parts.length < 6) {
    return null;
  }

  let days = [];
  for (let i = 0; i < parts[0].length; i++) {
    const day = DAY_NUMBERS[parts[0][i].toUpperCase()];
    if (day === undefined) {
      return null;
    }
    days.push(day);
  }

  return {
    days: days,
    start: timeTo24(parts[1], parts[2]),
    end: timeTo24(parts[4], parts[5]),
  };
}

// classes repeat every week, events are on one date (they go in the all day row)
export function makeCalendarEvents(courses, events) {
  let result = [];

  for (let i = 0; i < courses.length; i++) {
    const time = parseClassTime(courses[i].time);
    if (time === null) {
      continue;
    }
    result.push({
      id: "course-" + courses[i].id,
      title: courses[i].code,
      fullName: courses[i].code + " " + courses[i].name,
      daysOfWeek: time.days,
      startTime: time.start,
      endTime: time.end,
      backgroundColor: "var(--primary)",
      borderColor: "var(--primary)",
      textColor: "var(--on-primary)",
    });
  }

  for (let i = 0; i < events.length; i++) {
    result.push({
      id: "event-" + events[i].event_id,
      title: events[i].event_name,
      fullName: events[i].event_time + " " + events[i].event_name,
      start: events[i].event_date,
      allDay: true,
      backgroundColor: "var(--warning-soft)",
      borderColor: "var(--warning-text)",
      textColor: "var(--warning-text)",
    });
  }

  return result;
}
