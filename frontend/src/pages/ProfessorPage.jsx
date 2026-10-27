import { useEffect, useState } from "react";
import { getUser, getReviews, addReview, voteReview, getProfessors, getCourses } from "../api";
import NavBar from "../components/NavBar";
import styles from "./ProfessorPage.module.css";

const allTags = [
  "Easy A",
  "Extra Credit offered",
  "Lax Grading",
  "Best for this course",
  "High failure rate",
  "Grade booster",
  "Technical elective",
];

const maxWords = 500;

function countWords(text) {
  const trimmed = text.trim();
  if (trimmed === "") {
    return 0;
  }
  return trimmed.split(/\s+/).length;
}

function ReviewCard({review, myVote, onVote}) {
  // anonymous students still show up as Verified Student
  const who = review.anonymous ? "Verified Student" : review.author + " (Verified Student)";

  let tagList = [];
  for (let i = 0; i < review.tags.length; i++) {
    tagList.push(<span key={i} className={styles.tag}>{review.tags[i]}</span>);
  }

  return (
    <div className={styles.reviewCard}>
      <div className={styles.reviewTop}>
        <span className={styles.reviewScore}>{review.rating}/5</span>
        <span className={styles.reviewClass}>{review.course}</span>
        <span className={styles.date}>{review.date}</span>
      </div>
      <h3 className={styles.reviewTitle}>{review.title}</h3>
      <p>{review.comment}</p>
      <div>{tagList}</div>
      <div className={styles.reviewBottom}>
        <span className={styles.who}>{who}</span>
        <span>
          <button
            className={myVote === 1 ? styles.voteButton + " " + styles.voteUp : styles.voteButton}
            onClick={() => onVote(review.id, 1)}
          >
            ▲ {review.upvotes}
          </button>
          <button
            className={myVote === -1 ? styles.voteButton + " " + styles.voteDown : styles.voteButton}
            onClick={() => onVote(review.id, -1)}
          >
            ▼ {review.downvotes}
          </button>
        </span>
      </div>
    </div>
  );
}


export default function ProfessorPage({ goTo, professorId }) {
  const user = getUser();

  const [professor, setProfessor] = useState(null);
  const [courses, setCourses] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [sortBy, setSortBy] = useState("newest");

  // write review form
  const [showForm, setShowForm] = useState(false);
  const [course, setCourse] = useState("");
  const [rating, setRating] = useState(5);
  const [title, setTitle] = useState("");
  const [comment, setComment] = useState("");
  const [tags, setTags] = useState([]);
  const [anonymous, setAnonymous] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getReviews().then(data => setReviews(data));

    getProfessors().then(data => {
      for (let i = 0; i < data.length; i++) {
        if (data[i].professor_id === professorId) {
          setProfessor(data[i]);
        }
      }
    });

    getCourses().then(data => setCourses(data));
  }, [professorId]);

  // classes this professor teaches, show all classes if none match
  function getClassOptions() {
    let mine = [];
    for (let i = 0; i < courses.length; i++) {
      if (professor && courses[i].professor.toLowerCase().includes(professor.professor_name.toLowerCase())) {
        mine.push(courses[i]);
      }
    }
    if (mine.length === 0) {
      return courses;
    }
    return mine;
  }

  async function handleVote(reviewId, value) {
    setReviews(await voteReview(reviewId, user.name, value));
  }

  function toggleTag(name) {
    if (tags.includes(name)) {
      setTags(tags.filter(t => t !== name));
    } else {
      setTags([...tags, name]);
    }
  }

  function openForm() {
    const options = getClassOptions();
    if (options.length > 0) {
      setCourse(options[0].code);
    }
    setShowForm(true);
  }

  async function handleSubmit(e) {
    e.preventDefault();

    if (title.trim() === "") {
      setError("Please add a title.");
      return;
    }
    if (countWords(comment) === 0) {
      setError("Please write a review.");
      return;
    }
    if (countWords(comment) > maxWords) {
      setError("Review is over " + maxWords + " words.");
      return;
    }

    try {
      await addReview({
        professor_id: professorId,
        course: course,
        rating: Number(rating),
        title: title.trim(),
        comment: comment.trim(),
        tags: tags,
        author: user.name,
        anonymous: anonymous,
      });
      setReviews(await getReviews());

      // clear the form
      setTitle("");
      setComment("");
      setTags([]);
      setAnonymous(false);
      setRating(5);
      setError("");
      setShowForm(false);
    } catch (err) {
      setError(err.message);
    }
  }

  if (professor === null) {
    return (
      <div className={styles.page}>
        <NavBar goTo={goTo} />
        <p className={styles.empty}>Loading...</p>
      </div>
    );
  }

  // only the reviews for this professor
  let mine = [];
  let total = 0;
  for (let i = 0; i < reviews.length; i++) {
    if (reviews[i].professor_id === professorId) {
      mine.push(reviews[i]);
      total += reviews[i].rating;
    }
  }
  let average = mine.length > 0 ? (total / mine.length).toFixed(1) : "N/A";

  if (sortBy === "newest") {
    mine.sort((a, b) => b.date.localeCompare(a.date));
  } else if (sortBy === "highest") {
    mine.sort((a, b) => b.rating - a.rating);
  } else if (sortBy === "lowest") {
    mine.sort((a, b) => a.rating - b.rating);
  } else if (sortBy === "upvotes") {
    mine.sort((a, b) => b.upvotes - a.upvotes);
  }

  let reviewCards = [];
  for (let i = 0; i < mine.length; i++) {
    reviewCards.push(
      <ReviewCard
        key={mine[i].id}
        review={mine[i]}
        myVote={mine[i].voters[user.name] || 0}
        onVote={handleVote}
      />
    );
  }

  let classOptions = [];
  let options = getClassOptions();
  for (let i = 0; i < options.length; i++) {
    classOptions.push(<option key={options[i].id} value={options[i].code}>{options[i].code} - {options[i].name}</option>);
  }

  let tagPills = [];
  for (let i = 0; i < allTags.length; i++) {
    let picked = tags.includes(allTags[i]);
    tagPills.push(
      <button
        key={allTags[i]}
        type="button"
        onClick={() => toggleTag(allTags[i])}
        className={picked ? styles.pill + " " + styles.pillPicked : styles.pill}
      >
        {allTags[i]}
      </button>
    );
  }

  const words = countWords(comment);

  return (
    <div className={styles.page}>
      <NavBar goTo={goTo} />

      <div className={styles.content}>
        <button className={styles.backButton} onClick={() => goTo("reviews")}>← Back to search</button>

        {/* professor info and big score */}
        <div className={styles.header}>
          <div className={styles.bigScore}>
            <span className={styles.bigNumber}>{average}</span>
            <span className={styles.outOf}>{mine.length > 0 ? "/ 5" : ""}</span>
          </div>
          <div>
            <h1 className={styles.name}>{professor.professor_name}</h1>
            <p className={styles.meta}>{professor.professor_department} | {professor.office_location}</p>
            <p className={styles.meta}>Based on {mine.length} ratings</p>
          </div>
        </div>

        <div className={styles.toolbar}>
          <select className={styles.select} value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="newest">Newest</option>
            <option value="highest">Highest rating</option>
            <option value="lowest">Lowest rating</option>
            <option value="upvotes">Most upvoted</option>
          </select>
          <button className={styles.primaryButton} onClick={() => showForm ? setShowForm(false) : openForm()}>
            {showForm ? "Cancel" : "Write a Review"}
          </button>
        </div>

        {/* write review form */}
        {showForm &&
          <form className={styles.form} onSubmit={handleSubmit}>
            <h3 className={styles.formTitle}>Rate {professor.professor_name}</h3>
            {error && <p className={styles.error}>{error}</p>}

            <p className={styles.label}>Choose class</p>
            <select className={styles.input} value={course} onChange={(e) => setCourse(e.target.value)}>
              {classOptions}
            </select>

            <p className={styles.label}>Rating</p>
            <select className={styles.input} value={rating} onChange={(e) => setRating(e.target.value)}>
              <option value={5}>5 - Excellent</option>
              <option value={4}>4 - Good</option>
              <option value={3}>3 - Okay</option>
              <option value={2}>2 - Poor</option>
              <option value={1}>1 - Awful</option>
            </select>

            <p className={styles.label}>Title</p>
            <input
              className={styles.input}
              maxLength={30}
              placeholder="Short title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />

            <p className={styles.label}>Your review ({words}/{maxWords} words)</p>
            <textarea
              className={styles.input + " " + styles.textarea}
              placeholder="What was the class like?"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />

            <p className={styles.label}>Tags</p>
            <div className={styles.pills}>{tagPills}</div>

            <label className={styles.checkbox}>
              <input type="checkbox" checked={anonymous} onChange={(e) => setAnonymous(e.target.checked)} />
              Post anonymously (shows as "Verified Student")
            </label>

            <button type="submit" className={styles.primaryButton}>Submit Review</button>
          </form>
        }

        {/* review list */}
        {reviewCards}
        {mine.length === 0 && <p className={styles.empty}>No reviews yet. Be the first to write one!</p>}
      </div>
    </div>
  );
}
