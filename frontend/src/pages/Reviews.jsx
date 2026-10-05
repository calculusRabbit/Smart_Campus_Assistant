import { useEffect, useState } from "react";
import { getReviews, getProfessors } from "../api";
import NavBar from "../components/NavBar";
import styles from "./Reviews.module.css";

// average rating of one professor, null if nobody rated yet
function getAverage(reviews, professorId) {
  let total = 0;
  let count = 0;
  for (let i = 0; i < reviews.length; i++) {
    if (reviews[i].professor_id === professorId) {
      total += reviews[i].rating;
      count++;
    }
  }
  if (count === 0) {
    return {average: null, count: 0};
  }
  return {average: (total / count).toFixed(1), count: count};
}

export default function Reviews({ goTo, openProfessor }) {
  const [professors, setProfessors] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    getProfessors().then(data => setProfessors(data));
    getReviews().then(data => setReviews(data));
  }, []);

  // only professors that match the search
  let professorCards = [];
  for (let i = 0; i < professors.length; i++) {
    let p = professors[i];
    let text = (p.professor_name + " " + p.professor_department).toLowerCase();
    if (search !== "" && !text.includes(search.toLowerCase())) {
      continue;
    }

    let rating = getAverage(reviews, p.professor_id);

    professorCards.push(
      <div key={p.professor_id} className={styles.professorCard} onClick={() => openProfessor(p.professor_id)}>
        <div className={styles.score}>
          {rating.average === null ? "N/A" : rating.average}
        </div>
        <div className={styles.professorInfo}>
          <h3 className={styles.professorName}>{p.professor_name}</h3>
          <p className={styles.professorMeta}>{p.professor_department}</p>
          <p className={styles.professorMeta}>
            {rating.count === 0 ? "No ratings yet" : rating.count + " ratings"}
          </p>
        </div>
        <button className={styles.primaryButton}>View</button>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <NavBar goTo={goTo} />

      <div className={styles.banner}>
        <h1 className={styles.bannerTitle}>Find a Professor</h1>
        <p className={styles.bannerText}>Search a professor to see their ratings and reviews.</p>
      </div>

      <div className={styles.content}>
        <input
          className={styles.search}
          placeholder="Search professor name"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        {professorCards}
        {professorCards.length === 0 && <p className={styles.empty}>No professors found.</p>}
      </div>
    </div>
  );
}
