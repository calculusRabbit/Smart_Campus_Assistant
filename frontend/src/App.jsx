import { useState } from 'react'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import SignUp from './pages/SignUp'
import Profile from './pages/Profile'
import Reviews from './pages/Reviews'
import ProfessorPage from './pages/ProfessorPage'
import { getUser } from './api'

function App() {
  // no router library, just keep track of which page we are on
  const [page, setPage] = useState(getUser() ? "dashboard" : "login")
  // which professor was clicked in the reviews list
  const [professorId, setProfessorId] = useState(null)

  function openProfessor(id) {
    setProfessorId(id)
    setPage("professor")
  }

  // pages that need a logged in user
  const loggedIn = getUser() !== null
  if (!loggedIn && (page === "dashboard" || page === "profile" || page === "reviews" || page === "professor")) {
    return <Login goTo={setPage}/>
  }

  if (page === "signup") {
    return <SignUp goTo={setPage}/>
  }
  if (page === "dashboard") {
    return <Dashboard goTo={setPage}/>
  }
  if (page === "profile") {
    return <Profile goTo={setPage}/>
  }
  if (page === "reviews") {
    return <Reviews goTo={setPage} openProfessor={openProfessor}/>
  }
  if (page === "professor") {
    return <ProfessorPage goTo={setPage} professorId={professorId}/>
  }
  return <Login goTo={setPage}/>
}

export default App
