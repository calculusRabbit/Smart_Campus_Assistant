import FullCalendar from "@fullcalendar/react";
import timeGridPlugin from "@fullcalendar/timegrid";
import { makeCalendarEvents } from "../schedule";
import styles from "./WeekSchedule.module.css";

// small week view for the sidebar, classes are blue blocks and events are in the top row
export default function WeekSchedule({ courses, events }) {
  return (
    <div className={styles.box}>
      <h3 className={styles.title}>This week</h3>
      <FullCalendar
        plugins={[timeGridPlugin]}
        initialView="timeGridWeek"
        firstDay={1}
        height="auto"
        slotDuration="01:00:00"
        slotMinTime="08:00:00"
        slotMaxTime="18:00:00"
        allDayText="Events"
        displayEventTime={false}
        dayHeaderFormat={{ weekday: "short" }}
        titleFormat={{ month: "short", day: "numeric" }}
        buttonIcons={false}
        buttonText={{ prev: "Prev", next: "Next" }}
        headerToolbar={{ left: "title", center: "", right: "prev,next" }}
        events={makeCalendarEvents(courses, events)}
        // the full name shows when you hover, the block only has room for the code
        eventDidMount={(info) => {
          info.el.title = info.event.extendedProps.fullName;
        }}
      />
    </div>
  );
}
