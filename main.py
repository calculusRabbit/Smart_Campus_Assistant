import re

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import (
    get_courses_from_database,
    get_deadlines_from_database,
    get_dining_from_database,
    get_events_from_database,
    get_professors_from_database,
    get_student_interests,
    save_student_interests,
)
from models import ChatRequest, RecommendationRequest, StudentInterestsRequest

INTEREST_GROUPS = {
    "coding": [
        "coding",
        "programming",
        "computer science",
        "technology",
        "software"
    ],
    "career": [
        "career",
        "job",
        "jobs",
        "internship",
        "internships",
        "employment"
    ]
}

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/events")
def get_events():
    return {"events": get_events_from_database()}


@app.get("/dining")
def get_dining():
    return {"dining": get_dining_from_database()}


@app.get("/courses")
def get_courses(
    code: str | None = Query(default=None),
    professor: str | None = Query(default=None),
):
    courses = get_courses_from_database()

    if code:
        courses = [
            course for course in courses
            if code.lower() in course["code"].lower()
        ]

    if professor:
        courses = [
            course for course in courses
            if professor.lower() in course["professor"].lower()
        ]

    return {"courses": courses}


@app.get("/professors")
def get_professors():
    return {"professors": get_professors_from_database()}


@app.get("/deadlines")
def get_deadlines():
    return {"deadlines": get_deadlines_from_database()}

def find_course_by_message(message: str):
    for course in get_courses_from_database():
        if course["code"].lower() in message or course["name"].lower() in message:
            return course
    return None

def find_professor_by_message(message: str):
    for professor in get_professors_from_database():
        name = professor["professor_name"].lower()
        last_word = name.split()[-1]
        if name in message or last_word in message:
            return professor
    return None

def contains_keyword(message: str, keyword: str):
    pattern = rf"(?<!\w){re.escape(keyword)}(?!\w)"
    return re.search(pattern, message) is not None

# FIRST NEW HELPER
def extract_interests_from_message(message: str):
    detected_interests = []

    for category, related_interests in INTEREST_GROUPS.items():
        for interest in related_interests:
            if contains_keyword(message, interest):
                detected_interests.append(interest)

    return list(set(detected_interests))

# SECOND NEW HELPER
def get_event_recommendations(interests: list[str]):
    recommended_events = []

    normalized_interests = [
        interest.lower().strip()
        for interest in interests
    ]

    for event in get_events_from_database():
        category = event["event_category"].lower()

        related_interests = INTEREST_GROUPS.get(
            category,
            [category]
        )

        if any(
            interest in related_interests
            for interest in normalized_interests
        ):
            recommended_events.append(event)

    return recommended_events


@app.post("/recommendations/events")
def recommend_events(request: RecommendationRequest):
    recommended_events = get_event_recommendations(
        request.interests
    )

    return {
        "interests": request.interests,
        "recommended_events": recommended_events
    }


@app.post("/students/{student_id}/interests")
def set_student_interests(
    student_id: int,
    request: StudentInterestsRequest
):
    if not request.interests:
        raise HTTPException(
            status_code=400,
            detail="At least one student interest is required."
        )
        
    save_student_interests(student_id, request.interests)

    return {
        "student_id": student_id,
        "interests": request.interests,
        "message": "Student interests saved successfully."
    }


@app.get("/students/{student_id}/interests")
def get_saved_student_interests(student_id: int):
    interests = get_student_interests(student_id)

    return {
        "student_id": student_id,
        "interests": interests
    }

@app.get("/students/{student_id}/recommendations/events")
def get_student_event_recommendations(student_id: int):
    student_interests = get_student_interests(student_id)

    if not student_interests:
        raise HTTPException(
            status_code=404,
            detail="No saved interests found for this student."
        )

    recommended_events = get_event_recommendations(
        student_interests
    )

    return {
        "student_id": student_id,
        "interests": student_interests,
        "recommended_events": recommended_events
    }

@app.post("/chat")
def chat(request: ChatRequest):
    message = request.message.lower().strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    event_keywords = ["event", "events", "activity", "activities", "career fair", "competition"]
    dining_keywords = ["dining", "food", "eat", "cafeteria", "restaurant", "hungry"]
    course_keywords = ["course", "courses", "class", "classes", "cs 560", "cs 598"]
    professor_keywords = [
    "professor",
    "instructor",
    "teacher",
    "who teaches",
    "dr.",
    "yang",
    "smith",
    ]
    deadline_keywords = ["deadline", "deadlines", "registration", "add/drop", "due date"]
    recommendation_keywords = [
    "recommend",
    "recommendation",
    "recommendations",
    "suggest",
    "suggestion",
    "suggestions",
    "interested",
    "interest",
    ]

    matched_course = find_course_by_message(message)
    if matched_course:
        return {
            "intent": "courses",
            "reply": f"Here are the details for {matched_course['code']} {matched_course['name']}.",
            "data": matched_course
        }

    matched_professor = find_professor_by_message(message)
    if matched_professor:
        return {
            "intent": "professors",
            "reply": f"Here are the details for {matched_professor['professor_name']}.",
            "data": matched_professor
        }

    detected_interests = extract_interests_from_message(message)

    if detected_interests and any(
        contains_keyword(message, keyword)
        for keyword in recommendation_keywords
    ):
        recommended_events = get_event_recommendations(
            detected_interests
        )

        return {
            "intent": "recommendations",
            "reply": "Here are some campus events based on your interests.",
            "interests": detected_interests,
            "data": recommended_events
        }

    if any(
    contains_keyword(message, keyword)
    for keyword in event_keywords
):
        return {
            "intent": "events",
            "reply": "Here are some upcoming campus events.",
            "data": get_events_from_database()
        }

    elif any(
    contains_keyword(message, keyword)
    for keyword in dining_keywords
):
        return {
            "intent": "dining",
            "reply": "Here are some dining options on campus.",
            "data": get_dining_from_database()
        }

    elif any(
    contains_keyword(message, keyword)
    for keyword in course_keywords
):
        return {
            "intent": "courses",
            "reply": "Here are some course details.",
            "data": get_courses_from_database()
        }

    elif any(
    contains_keyword(message, keyword)
    for keyword in professor_keywords
):
        return {
            "intent": "professors",
            "reply": "Here are some professor details.",
            "data": get_professors_from_database()
        }

    elif any(
    contains_keyword(message, keyword)
    for keyword in deadline_keywords
):
        return {
            "intent": "deadlines",
            "reply": "Here are some important academic deadlines.",
            "data": get_deadlines_from_database()
        }

    else:
        return {
            "intent": "unknown",
            "reply": (
                "I could not understand that request. "
                "I can help with campus events, dining, courses, "
                "professors, deadlines, and student recommendations. "
                "Try asking something like 'What events are happening?' "
                "or 'Tell me about CS 560.'"
            )
        }
