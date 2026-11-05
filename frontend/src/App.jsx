import {
  Navigate,
  Route,
  Routes,
  useNavigate,
  useParams,
} from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import SignUp from "./pages/SignUp";
import Profile from "./pages/Profile";
import Reviews from "./pages/Reviews";
import ProfessorPage from "./pages/ProfessorPage";
import NotFound from "./pages/NotFound";
import { getUser } from "./api";

// the pages still say goTo("profile"), this is the url for each page name
const urls = {
  login: "/login",
  signup: "/signup",
  dashboard: "/dashboard",
  profile: "/profile",
  reviews: "/reviews",
};

// pages that need a logged in user
function RequireLogin({ children }) {
  if (getUser() === null) {
    return <Navigate to="/login" replace />;
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
        path="/profile"
        element={
          <RequireLogin>
            <Profile goTo={goTo} />
          </RequireLogin>
        }
      />
      <Route
        path="/reviews"
        element={
          <RequireLogin>
            <Reviews goTo={goTo} openProfessor={openProfessor} />
          </RequireLogin>
        }
      />
      <Route
        path="/professors/:professorId"
        element={
          <RequireLogin>
            <ProfessorRoute goTo={goTo} />
          </RequireLogin>
        }
      />

      <Route path="*" element={<NotFound goTo={goTo} />} />
    </Routes>
  );
}

export default App;
