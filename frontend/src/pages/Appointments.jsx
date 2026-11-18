import { useEffect, useState } from "react";
import { apiFetch } from "../api";
import NavBar from "../components/NavBar";
import styles from "./Appointments.module.css";

// Resource configuration is separate from authentication.
// Add other universities only after verifying their official URLs.
const universityResources = {
  wsu: {
    name: "Wichita State University",
    scheduling: {
      title: "WSU Navigate360",
      description:
        "Schedule supported academic advising, tutoring, and student support appointments through WSU.",
      url: "https://wichita.campus.eab.com/",
    },
    directory: {
      title: "WSU Faculty and Staff Directory",
      description:
        "Find a professor's official contact information and ask about office hours or individual appointment scheduling.",
      url: "https://www.wichita.edu/directories/",
    },
  },
};

export default function Appointments({ goTo }) {
  // WSU is the only configured university for this initial release.
  // University selection will be integrated separately after authentication
  // exposes a verified institution identifier.
  const university = universityResources.wsu;

  const [professors, setProfessors] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadProfessors() {
      try {
        const response = await apiFetch("/professors", {
          signal: controller.signal,
        });
        const data = await response.json();

        if (!Array.isArray(data.professors)) {
          throw new Error("Invalid professor response.");
        }

        const wsuProfessors = data.professors
          .filter((professor) => {
            const email = String(professor.professor_email || "")
              .trim()
              .toLowerCase();
            const name = String(professor.professor_name || "").toLowerCase();
            const department = String(
              professor.professor_department || "",
            ).toLowerCase();

            return (
              name.trim().length > 0 &&
              email.endsWith("@wichita.edu") &&
              email.includes("@") &&
              !name.includes("test") &&
              !department.includes("test")
            );
          })
          .sort((a, b) => a.professor_name.localeCompare(b.professor_name));

        if (!controller.signal.aborted) {
          setProfessors(wsuProfessors);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError("Could not load professors: " + err.message);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadProfessors();

    return () => controller.abort();
  }, []);

  const filteredProfessors = professors.filter((professor) => {
    const text = [professor.professor_name, professor.professor_department]
      .join(" ")
      .toLowerCase();

    return text.includes(search.trim().toLowerCase());
  });

  return (
    <div className={styles.page}>
      <NavBar goTo={goTo} />

      <main className={styles.container}>
        <button
          type="button"
          className={styles.backButton}
          onClick={() => goTo("dashboard")}
        >
          Back to Dashboard
        </button>

        <header className={styles.header}>
          <span className={styles.eyebrow}>
            Smart Campus Assistant / Resources
          </span>
          <h1>Appointment Resources</h1>
          <p>
            Find official university resources for scheduling appointments and
            contacting professors.
          </p>
        </header>

        <section className={styles.card}>
          <h2>{university.name}</h2>
          <p className={styles.subtitle}>
            Choose the official service that matches your appointment needs.
          </p>

          <h3>{university.scheduling.title}</h3>
          <p>{university.scheduling.description}</p>

          <a
            className={styles.submitButton}
            style={{ display: "inline-block", textDecoration: "none" }}
            href={university.scheduling.url}
            target="_blank"
            rel="noopener noreferrer"
          >
            Open WSU Navigate360
          </a>

          <hr style={{ margin: "28px 0", borderColor: "#e8e8ef" }} />

          <h3>{university.directory.title}</h3>
          <p>{university.directory.description}</p>

          <a
            href={university.directory.url}
            target="_blank"
            rel="noopener noreferrer"
          >
            Find a Professor in the WSU Directory
          </a>

          <section className={styles.professorSection}>
            <h3>Find a Professor</h3>
            <p>
              Search the currently configured WSU faculty records. Contact your
              professor to ask about office hours or their preferred scheduling
              method.
            </p>

            <label htmlFor="resource-professor-search">
              Search by professor name or department
            </label>
            <input
              id="resource-professor-search"
              className={styles.professorSearch}
              type="search"
              placeholder="Search WSU professors..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />

            {loading && <p role="status">Loading professors...</p>}

            {error && (
              <p className={styles.error} role="alert">
                {error}
              </p>
            )}

            {!loading && !error && filteredProfessors.length === 0 && (
              <p>No matching professors found.</p>
            )}

            {!loading && !error && (
              <div className={styles.professorList}>
                {filteredProfessors.map((professor) => (
                  <article
                    className={styles.professorCard}
                    key={professor.professor_id}
                  >
                    <div>
                      <h4>{professor.professor_name}</h4>
                      <p>{professor.professor_department}</p>
                    </div>

                    <a
                      href={
                        "mailto:" +
                        encodeURIComponent(professor.professor_email)
                      }
                      className={styles.contactLink}
                    >
                      Email Professor
                    </a>
                  </article>
                ))}
              </div>
            )}

            <p className={styles.notice}>
              Professor-specific booking links have not been verified. Email
              contact does not automatically schedule an appointment.
            </p>
          </section>

          <p className={styles.notice}>
            Smart Campus Assistant does not book or confirm appointments.
            Complete your scheduling directly through the university's official
            service. Individual professors may use different scheduling methods.
          </p>
        </section>
      </main>
    </div>
  );
}
