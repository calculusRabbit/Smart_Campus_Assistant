import { useEffect, useState } from "react";
import { createAppointment, getStudentAppointments, getUser } from "../api";
import NavBar from "../components/NavBar";
import styles from "./Appointments.module.css";

export default function Appointments({ goTo }) {
  const user = getUser();

  const [professors, setProfessors] = useState([]);
  const [professorId, setProfessorId] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [reason, setReason] = useState("");

  const [loading, setLoading] = useState(false);
  const [loadingProfessors, setLoadingProfessors] = useState(true);
  const [error, setError] = useState("");
  const [confirmation, setConfirmation] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState("");

  // Local date avoids UTC date differences near midnight.
  function todayString() {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, "0");
    const day = String(today.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  useEffect(() => {
    async function loadProfessors() {
      try {
        const response = await fetch("http://localhost:8000/professors");

        if (!response.ok) {
          throw new Error("Could not load professors.");
        }

        const data = await response.json();
        setProfessors(data.professors || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoadingProfessors(false);
      }
    }

    loadProfessors();
  }, []);

  useEffect(() => {
    if (!user?.id) {
      setHistoryLoading(false);
      return;
    }

    let active = true;

    getStudentAppointments(user.id)
      .then((items) => {
        if (active) setAppointments(items);
      })
      .catch(() => {
        if (active) {
          setHistoryError("Could not load appointment history.");
        }
      })
      .finally(() => {
        if (active) setHistoryLoading(false);
      });

    return () => {
      active = false;
    };
  }, [user?.id]);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setConfirmation(null);

    if (!user) {
      setError("Please log in to request an appointment.");
      return;
    }

    if (!professorId || !date || !time || !reason.trim()) {
      setError("Please complete all appointment fields.");
      return;
    }

    if (new Date(`${date}T${time}:00`) <= new Date()) {
      setError("Please choose a future date and time.");
      return;
    }

    if (reason.trim().length > 300) {
      setError("The reason must be 300 characters or fewer.");
      return;
    }

    setLoading(true);

    try {
      const result = await createAppointment({
        student_id: user.id,
        instructor_id: Number(professorId),
        appointment_date: date,
        appointment_time: time,
        reason: reason.trim(),
      });

      const professor = professors.find(
        (item) => item.professor_id === Number(professorId),
      );

      setConfirmation({
        ...result,
        professor_name: professor?.professor_name || "Professor",
      });

      setHistoryError("");
      try {
        const updated = await getStudentAppointments(user.id);
        setAppointments(updated);
      } catch {
        setHistoryError("Request saved, but appointment history could not refresh.");
      }

      setProfessorId("");
      setDate("");
      setTime("");
      setReason("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.page}>
      <NavBar goTo={goTo} />

      <main className={styles.container}>
        <button
          type="button"
          className={styles.backButton}
          onClick={() => goTo("dashboard")}
        >
          ? Back to Dashboard
        </button>

        <header className={styles.header}>
          <span className={styles.eyebrow}>Smart Campus Assistant</span>
          <h1>Professor Appointments</h1>
          <p>
            Request a meeting with a professor to discuss coursework,
            academic questions, or other university matters.
          </p>
        </header>

        <section className={styles.card}>
          <h2>Request an Appointment</h2>
          <p className={styles.subtitle}>
            Select your preferred meeting date and time.
            All requests are subject to professor approval.
          </p>

          {error && (
            <div className={styles.error} role="alert">
              {error}
            </div>
          )}

          {confirmation && (
            <div className={styles.success} role="status">
              <h3>Appointment Request Submitted!</h3>
              <p>
                Your request to meet with{" "}
                <strong>{confirmation.professor_name}</strong> was saved.
              </p>
              <p>
                <strong>Date:</strong> {confirmation.appointment_date}
              </p>
              <p>
                <strong>Time:</strong> {confirmation.appointment_time}
              </p>
              <p>
                <strong>Request ID:</strong> {confirmation.appointment_id}
              </p>
              <span className={styles.pending}>Pending Approval</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className={styles.form}>
            <label htmlFor="appointment-professor">
              Select Professor
            </label>
            <select
              id="appointment-professor"
              value={professorId}
              onChange={(event) => setProfessorId(event.target.value)}
              disabled={loading || loadingProfessors}
              required
            >
              <option value="">
                {loadingProfessors
                  ? "Loading professors..."
                  : "Choose a professor"}
              </option>

              {professors.map((professor) => (
                <option
                  key={professor.professor_id}
                  value={professor.professor_id}
                >
                  {professor.professor_name}
                  {professor.professor_department
                    ? ` ? ${professor.professor_department}`
                    : ""}
                </option>
              ))}
            </select>

            <div className={styles.dateTimeRow}>
              <div className={styles.field}>
                <label htmlFor="appointment-date">Appointment Date</label>
                <input
                  id="appointment-date"
                  type="date"
                  min={todayString()}
                  value={date}
                  onChange={(event) => setDate(event.target.value)}
                  required
                  disabled={loading}
                />
              </div>

              <div className={styles.field}>
                <label htmlFor="appointment-time">Preferred Time</label>
                <input
                  id="appointment-time"
                  type="time"
                  value={time}
                  onChange={(event) => setTime(event.target.value)}
                  required
                  disabled={loading}
                />
              </div>
            </div>

            <label htmlFor="appointment-reason">
              Reason for Appointment
            </label>
            <textarea
              id="appointment-reason"
              rows="5"
              maxLength={300}
              placeholder="Example: I would like to discuss my course schedule and academic progress."
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              required
              disabled={loading}
            />

            <p className={styles.characterCount}>
              {reason.length}/300 characters
            </p>

            <button
              className={styles.submitButton}
              type="submit"
              disabled={loading || loadingProfessors || professors.length === 0}
            >
              {loading ? "Submitting..." : "Submit Appointment Request"}
            </button>
          </form>

          <p className={styles.notice}>
            This form submits an appointment request only. It does not
            automatically reserve a professor's time or send a notification.
          </p>
        </section>

        <section className={styles.card} style={{ marginTop: "28px" }}>
          <h2>My Appointments</h2>
          <p className={styles.subtitle}>
            Review your submitted appointment requests and their current status.
          </p>

          {historyLoading && <p>Loading your appointments...</p>}

          {historyError && (
            <p className={styles.error} role="alert">{historyError}</p>
          )}

          {!historyLoading && appointments.length === 0 && (
            <p className={styles.subtitle}>
              You have not submitted any appointment requests yet.
            </p>
          )}

          {!historyLoading && appointments.map((appointment) => (
            <article
              key={appointment.appointment_id}
              className={styles.historyCard}
            >
              <div className={styles.historyHeading}>
                <h3>{appointment.professor_name}</h3>
                <span className={styles.pending}>
                  {appointment.status === "pending"
                    ? "Pending Approval"
                    : appointment.status}
                </span>
              </div>

              <p>
                <strong>Date:</strong> {appointment.appointment_date}
              </p>
              <p>
                <strong>Time:</strong>{" "}
                {appointment.appointment_time.slice(0, 5)}
              </p>
              <p>
                <strong>Reason:</strong> {appointment.reason}
              </p>
              <p className={styles.historyId}>
                Request #{appointment.appointment_id}
              </p>
            </article>
          ))}
        </section>
      </main>
    </div>
  );
}
