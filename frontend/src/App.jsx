import { useEffect } from "react";
import {
  Navigate,
  Route,
  Routes,
  useNavigate,
  useParams,
} from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Appointments from "./pages/Appointments";
import MLClassifier from "./pages/MLClassifier";
import Login from "./pages/Login";
import SignUp from "./pages/SignUp";
import Profile from "./pages/Profile";
import Reviews from "./pages/Reviews";
import ProfessorPage from "./pages/ProfessorPage";
import NotFound from "./pages/NotFound";
import { getUser } from "./api";
import Verification from "./pages/Verification";

// the pages still say goTo("profile"), this is the url for each page name
const urls = {
  login: "/login",
  signup: "/signup",
  dashboard: "/dashboard",
  appointments: "/resources",
  "ml-classifier": "/ml-classifier",
  profile: "/profile",
  reviews: "/reviews",
  verification: "/verification",
};

// pages that need a logged in user
function RequireLogin({ children }) {
  if (getUser() === null) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

// reviews are only for verified students (account_status is "open")
function RequireVerified({ goTo, children }) {
  const user = getUser();
  if (user.account_status !== "open") {
    return (
      <main>
        <p>Student verification is required to access reviews.</p>
        <button onClick={() => goTo("dashboard")}>Back to dashboard</button>
      </main>
    );
  }
  return children;
}

// login and sign up make no sense when you are already logged in
function LoggedOutOnly({ children }) {
  if (getUser() !== null) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
}

// the professor id comes from the url, like /professors/12
function ProfessorRoute({ goTo }) {
  const { professorId } = useParams();
  return <ProfessorPage goTo={goTo} professorId={Number(professorId)} />;
}

function App() {
  const navigate = useNavigate();

  function goTo(page) {
    navigate(urls[page]);
  }

  useEffect(() => {
    function handleAuthExpired() {
      navigate("/login");
    }
    //install listener, then unmount and uninstall
    window.addEventListener("auth-expired", handleAuthExpired);
    return () => {
      window.removeEventListener("auth-expired", handleAuthExpired);
    };
  }, [navigate]);

  function openProfessor(id) {
    navigate("/professors/" + id);
  }

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      <Route
        path="/login"
        element={
          <LoggedOutOnly>
            <Login goTo={goTo} />
          </LoggedOutOnly>
        }
      />
      <Route
        path="/signup"
        element={
          <LoggedOutOnly>
            <SignUp goTo={goTo} />
          </LoggedOutOnly>
        }
      />

      <Route
        path="/dashboard"
        element={
          <RequireLogin>
            <Dashboard goTo={goTo} />
          </RequireLogin>
        }
      />
      <Route
        path="/appointments"
        element={<Navigate to="/resources" replace />}
      />
      <Route
        path="/resources"
        element={
          <RequireLogin>
            <Appointments goTo={goTo} />
          </RequireLogin>
        }
      />
      <Route
        path="/ml-classifier"
        element={
          <RequireLogin>
            <MLClassifier goTo={goTo} />
          </RequireLogin>
        }
      />
      <Route
        path="/profile"
        element={
          <RequireLogin>
            <Profile goTo={goTo} />
          </RequireLogin>
        }
      />
      <Route
        path="/verification"
        element={
          <RequireLogin>
            <Verification goTo={goTo} />
          </RequireLogin>
        }
      />
      <Route
        path="/reviews"
        element={
          <RequireLogin>
            <RequireVerified goTo={goTo}>
              <Reviews goTo={goTo} openProfessor={openProfessor} />
            </RequireVerified>
          </RequireLogin>
        }
      />
      <Route
        path="/professors/:professorId"
        element={
          <RequireLogin>
            <RequireVerified goTo={goTo}>
              <ProfessorRoute goTo={goTo} />
            </RequireVerified>
          </RequireLogin>
        }
      />

      <Route path="*" element={<NotFound goTo={goTo} />} />
    </Routes>
  );
}

export default App;
