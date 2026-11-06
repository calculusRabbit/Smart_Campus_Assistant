import { useState, useEffect } from "react";
import Dashboard from "./pages/Dashboard";
import MLClassifier from "./pages/MLClassifier";
import Login from "./pages/Login";
import SignUp from "./pages/SignUp";
import Profile from "./pages/Profile";
import Reviews from "./pages/Reviews";
import ProfessorPage from "./pages/ProfessorPage";
import { getUser } from "./api";
import Verification from "./pages/Verification";

function App() {
  // no router library, just keep track of which page we are on
  const [page, setPage] = useState(getUser() ? "dashboard" : "login");
  // which professor was clicked in the reviews list
  const [professorId, setProfessorId] = useState(null);

  useEffect(() => {
    function handleAuthExpired() {
      setPage("login"); //re-render frontend
    }
    //install listener, then unmount and uninstall
    window.addEventListener("auth-expired", handleAuthExpired);
    return () => {
      window.removeEventListener("auth-expired", handleAuthExpired);
    };
  }, []);

  function openProfessor(id) {
    setProfessorId(id);
    setPage("professor");
  }

  // pages that need a logged in user
  const user = getUser();
  const loggedIn = user !== null;

  if (
    user !== null &&
    user.account_status !== "open" &&
    (page === "reviews" || page === "professor")
  ) {
    return (
      <main>
        <p>Student verification is required to access reviews.</p>
        <button onClick={() => setPage("dashboard")}>Back to dashboard</button>
      </main>
    );
  }
  if (
    !loggedIn &&
    (page === "dashboard" ||
      page === "ml-classifier" ||
      page === "profile" ||
      page === "reviews" ||
      page === "professor" ||
      page === "verification")
  ) {
    return <Login goTo={setPage} />;
  }

  if (page === "signup") {
    return <SignUp goTo={setPage} />;
  }
  if (page === "ml-classifier") {
    return <MLClassifier goTo={setPage} />;
  }
  if (page === "dashboard") {
    return <Dashboard goTo={setPage} />;
  }
  if (page === "profile") {
    return <Profile goTo={setPage} />;
  }
  if (page === "verification") {
    return <Verification goTo={setPage} />;
  }
  if (page === "reviews") {
    return <Reviews goTo={setPage} openProfessor={openProfessor} />;
  }
  if (page === "professor") {
    return <ProfessorPage goTo={setPage} professorId={professorId} />;
  }
  return <Login goTo={setPage} />;
}

export default App;
