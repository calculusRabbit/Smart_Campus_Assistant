// all the backend calls are in this file
const BASE_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000";

let accessToken = null;
let currentUser = null;

// Remove obsolete credentials left by the demonstration implementation.
localStorage.removeItem("token");
localStorage.removeItem("user");

export function getUser() {
  return currentUser;
}

export async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers);

  if (accessToken !== null) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const response = await fetch(BASE_URL + path, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      accessToken = null;
      currentUser = null;
    }

    const body = await response.json().catch(() => null);
    const message =
      typeof body?.detail === "string"
        ? body.detail
        : `Request failed (${response.status})`;

    throw new Error(message);
  }

  return response;
}

export async function login(email, password) {
  const response = await apiFetch("/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const data = await response.json();
  accessToken = data.access_token;
  currentUser = data.user;
  return currentUser;
}

export async function signup(form) {
  const response = await apiFetch("/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(form),
  });

  return response.json();
}

export async function logout() {
  try {
    if (accessToken !== null) {
      await apiFetch("/logout", { method: "POST" });
    }
  } finally {
    accessToken = null;
    currentUser = null;
  }
}

export function getUser() {
  const saved = localStorage.getItem("user");
  if (saved === null) {
    return null;
  }
  return JSON.parse(saved);
}

export function logout() {
  localStorage.removeItem("user");
  localStorage.removeItem("token");
}

export async function login(email, password) {
  if (FAKE_AUTH) {
    const user = { id: 1, name: email.split("@")[0], email: email };
    localStorage.setItem("user", JSON.stringify(user));
    localStorage.setItem("token", "fake-token");
    return user;
  }

  const res = await fetch(BASE_URL + "/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    throw new Error("Wrong email or password.");
  }
  const data = await res.json();
  localStorage.setItem("token", data.access_token);
  localStorage.setItem("user", JSON.stringify(data.user));
  return data.user;
}

export async function signup(form) {
  if (FAKE_AUTH) {
    return { message: "fake signup ok" };
  }

  const res = await fetch(BASE_URL + "/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(form),
  });
  if (!res.ok) {
    throw new Error("Could not create account.");
  }
  return res.json();
}

export async function getEvents() {
  const res = await fetch(BASE_URL + "/events");
  const data = await res.json();
  return data.events;
}

// sample data for when the backend is off, remove later
const sampleProfessors = [
  {
    professor_id: 101,
    professor_name: "Professor Cody",
    professor_department: "Computer Science",
    professor_email: "cody@wsu.edu",
    office_location: "Room 209",
    professor_rating: 4.7,
  },
];

const sampleCourses = [
  {
    id: 1,
    code: "CS 560",
    name: "Machine Learning",
    time: "TR 2:00-3:15 PM",
    room: "Jabara 210",
    professor: "Professor Cody",
    department: "Computer Science",
    credits: 3,
  },
  {
    id: 2,
    code: "CS 598",
    name: "Senior Design Project",
    time: "MW 10:00-11:15 AM",
    room: "RSC 261",
    professor: "Professor Cody",
    department: "Computer Science",
    credits: 3,
  },
];

export async function getCourses() {
  try {
    const res = await fetch(BASE_URL + "/courses");
    const data = await res.json();
    return data.courses;
  } catch {
    return sampleCourses;
  }
}

// recommended events for a student, empty if no interests
export async function getRecommendedEvents(studentId) {
  const response = await apiFetch(
    `/students/${studentId}/recommendations/events`,
  );
  const data = await response.json();
  return data.recommended_events;
}

export async function getInterests(studentId) {
  const response = await apiFetch(
    `/students/${studentId}/interests`,
  );
  const data = await response.json();
  return data.interests;
}

export async function saveInterests(studentId, interests) {
  const response = await apiFetch(
    `/students/${studentId}/interests`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ interests }),
    },
  );
  return response.json();
}

export async function sendChat(message) {
  const response = await apiFetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  return response.json();
}

export async function getProfessors() {
  try {
    const res = await fetch(BASE_URL + "/professors");
    const data = await res.json();
    return data.professors;
  } catch {
    return sampleProfessors;
  }
}

// TODO: no reviews endpoint yet so reviews are saved in the browser
// change these to fetch() when the backend has it
const sampleReviews = [
  {
    id: 1,
    professor_id: 101,
    course: "CS 598",
    rating: 5,
    title: "Best senior design class",
    comment:
      "Very clear about what he wants and gives feedback every week. Lots of work but you learn a lot.",
    tags: ["Extra Credit offered"],
    author: "student_a",
    anonymous: true,
    date: "2026-09-02",
    upvotes: 12,
    downvotes: 1,
    voters: {},
  },
  {
    id: 2,
    professor_id: 101,
    course: "CS 560",
    rating: 4,
    title: "Hard but fair",
    comment:
      "Exams are tough and the homework takes time, but office hours help a lot.",
    tags: ["High failure rate"],
    author: "student_b",
    anonymous: false,
    date: "2026-05-14",
    upvotes: 5,
    downvotes: 0,
    voters: {},
  },
  {
    id: 3,
    professor_id: 102,
    course: "CS 560",
    rating: 3,
    title: "Okay class",
    comment:
      "Lectures are a bit boring and the slides are hard to follow. Grading is lax though.",
    tags: ["Lax Grading"],
    author: "student_c",
    anonymous: true,
    date: "2025-12-10",
    upvotes: 2,
    downvotes: 2,
    voters: {},
  },
  {
    id: 4,
    professor_id: 102,
    course: "CS 598",
    rating: 2,
    title: "Not organized",
    comment: "Deadlines kept changing and it was hard to know what was due.",
    tags: [],
    author: "student_d",
    anonymous: false,
    date: "2024-04-21",
    upvotes: 1,
    downvotes: 4,
    voters: {},
  },
];

function saveReviews(reviews) {
  localStorage.setItem("reviews_v2", JSON.stringify(reviews));
}

export async function getReviews() {
  const saved = localStorage.getItem("reviews_v2");
  if (saved === null) {
    saveReviews(sampleReviews);
    return sampleReviews;
  }
  return JSON.parse(saved);
}

export async function addReview(review) {
  const reviews = await getReviews();

  // one review per student per professor per course
  for (let i = 0; i < reviews.length; i++) {
    let r = reviews[i];
    if (
      r.author === review.author &&
      r.professor_id === review.professor_id &&
      r.course === review.course
    ) {
      throw new Error("You already reviewed this professor for this class.");
    }
  }

  review.id = Date.now();
  review.date = new Date().toISOString().slice(0, 10);
  review.upvotes = 0;
  review.downvotes = 0;
  review.voters = {};
  reviews.push(review);
  saveReviews(reviews);
  return review;
}

// value is 1 for upvote and -1 for downvote
export async function voteReview(reviewId, username, value) {
  const reviews = await getReviews();

  for (let i = 0; i < reviews.length; i++) {
    let r = reviews[i];
    if (r.id !== reviewId) {
      continue;
    }

    // take away the old vote first
    const oldVote = r.voters[username] || 0;
    if (oldVote === 1) {
      r.upvotes = r.upvotes - 1;
    }
    if (oldVote === -1) {
      r.downvotes = r.downvotes - 1;
    }

    // clicking the same button again removes your vote
    const newVote = oldVote === value ? 0 : value;
    if (newVote === 1) {
      r.upvotes = r.upvotes + 1;
    }
    if (newVote === -1) {
      r.downvotes = r.downvotes + 1;
    }

    if (newVote === 0) {
      delete r.voters[username];
    } else {
      r.voters[username] = newVote;
    }
  }

  saveReviews(reviews);
  return reviews;
}
