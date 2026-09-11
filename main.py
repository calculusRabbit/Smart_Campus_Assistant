from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
# hey fai, added this so the frontend (localhost:5173) is allowed to talk to the backend (localhost:8000)
# without this the browser will block all requests from frontend to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET","POST"],
    allow_headers=["*"]
)
class ChatRequest(BaseModel):
    message: str

# Root endpoint
@app.get("/")
def home():
    return {"message": "Smart Campus Backend is running"}

# Events endpoint
@app.get("/events")
def get_events():
    return {
        "events": [
            {
                "event_id": 1,
                "event_name": "C++ Competition",
                "event_date": "2026-03-20",
                "event_time": "10:00 AM",
                "event_location": "Rhatigan Student Center",
                "event_description": "A coding competition for students"
            },
            {
                "event_id": 2,
                "event_name": "Career Fair",
                "event_date": "2026-03-25",
                "event_time": "1:00 PM",
                "event_location": "John Bardo Center",
                "event_description": "Meet employers and explore job opportunities"
            }
        ]
    }

# Dining endpoint
@app.get("/dining")
def get_dining():
    return {
        "dining": [
            {
                "dining_id": 1,
                "dining_name": "Chick-fil-A",
                "opening_time": "7:00 AM",
                "closing_time": "10:00 PM",
                "dining_location": "Rhatigan Student Center",
                "dining_status": "Open"
            },
            {
                "dining_id": 2,
                "dining_name": "Panda Express",
                "opening_time": "7:00 AM",
                "closing_time": "10:00 PM",
                "dining_location": "Rhatigan Student Center",
                "dining_status": "Open"
            }
        ]
    }

# Courses endpoint
@app.get("/courses")
def get_courses():
    return {
        "courses": [
            {
                "id": 1,
                "code": "CS 560",
                "name": "Machine Learning",
                "time": "TR 2:00-3:15 PM",
                "room": "Jabara 210",
                "professor": "Dr. Yang",
                "department": "Computer Science",
                "description": "Introduction to machine learning concepts and models",
                "credits": 3
            },
            
            {
                "id": 2,
                "code": "CS 598",
                "name": "Senior Design Project",
                "time": "MW 10:00-11:15 AM",
                "room": "RSC 261",
                "professor": "Dr. Smith",
                "department": "Computer Science",
                "description": "Capstone project course for senior students",
                "credits": 3
            }
        ]
    }

# Professors endpoint
@app.get("/professors")
def get_professors():
    return {
        "professors": [
            {
                "professor_id": 101,
                "professor_name": "Professor Cody AI",
                "professor_department": "Computer Science",
                "professor_email": "codyai@wsu.edu",
                "office_location": "Room 209",
                "professor_rating": 4.7
            },
            {
                "professor_id": 102,
                "professor_name": "Professor Thomas AI",
                "professor_department": "Computer Science",
                "professor_email": "thomasai@wsu.edu",
                "office_location": "Room 201",
                "professor_rating": 4.5
            }
        ]
    }

# Deadlines endpoint
@app.get("/deadlines")
def get_deadlines():
    return {
        "deadlines": [
            {
                "deadline_id": 1,
                "deadline_title": "Course Registration Deadline",
                "deadline_date": "2026-04-15",
                "deadline_description": "Last day to register for Summer classes"
            },
            {
                "deadline_id": 2,
                "deadline_title": "Add/Drop Deadline",
                "deadline_date": "2026-03-10",
                "deadline_description": "Last day to add or drop a course without penalty"
            }
        ]
    }

@app.post("/chat")
def chat(request: ChatRequest):
    message = request.message.lower()

    if "event" in message:
        return {
            "intent": "events",
            "reply": "Here are some upcoming campus events.",
            "data": [
                {
                    "event_id": 1,
                    "event_name": "C++ Competition",
                    "event_date": "2026-03-20",
                    "event_time": "10:00 AM",
                    "event_location": "Rhatigan Student Center"
                },
                {
                    "event_id": 2,
                    "event_name": "Career Fair",
                    "event_date": "2026-03-25",
                    "event_time": "1:00 PM",
                    "event_location": "John Bardo Center"
                }
            ]
        }

    elif "dining" in message or "food" in message or "eat" in message:
        return {
            "intent": "dining",
            "reply": "Here are some dining options on campus.",
            "data": [
                {
                    "dining_id": 1,
                    "dining_name": "Chick-fil-A",
                    "opening_time": "7:00 AM",
                    "closing_time": "10:00 PM",
                    "dining_location": "Rhatigan Student Center"
                },
                {
                    "dining_id": 2,
                    "dining_name": "Panda Express",
                    "opening_time": "7:00 AM",
                    "closing_time": "10:00 PM",
                    "dining_location": "Rhatigan Student Center"
                }
            ]
        }

    elif "course" in message or "class" in message:
        return {
            "intent": "courses",
            "reply": "Here are some course details.",
            "data": [
                {
                    "course_id": 101,
                    "course_code": "CS 598",
                    "course_name": "Senior Design Project"
                },
                {
                    "course_id": 102,
                    "course_code": "CS 770",
                    "course_name": "Machine Learning"
                }
            ]
        }

    elif "professor" in message or "instructor" in message:
        return {
            "intent": "professors",
            "reply": "Here are some professor details.",
            "data": [
                {
                    "professor_id": 101,
                    "professor_name": "Professor Cody AI",
                    "professor_rating": 4.7
                },
                {
                    "professor_id": 102,
                    "professor_name": "Professor Thomas AI",
                    "professor_rating": 4.5
                }
            ]
        }

    elif "deadline" in message:
        return {
            "intent": "deadlines",
            "reply": "Here are some important academic deadlines.",
            "data": [
                {
                    "deadline_id": 1,
                    "deadline_title": "Course Registration Deadline",
                    "deadline_date": "2026-04-15"
                },
                {
                    "deadline_id": 2,
                    "deadline_title": "Add/Drop Deadline",
                    "deadline_date": "2026-03-10"
                }
            ]
        }

    else:
        return {
            "intent": "unknown",
            "reply": "Sorry, I can currently help with events, dining, courses, professors, and deadlines."
        }
