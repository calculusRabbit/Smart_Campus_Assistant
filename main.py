import re
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from auth import get_current_user, require_student_owner
from database import (
    get_connection,
    get_course_details,
    get_courses_by_professor,
    get_courses_from_database,
    get_deadlines_from_database,
    get_dining_from_database,
    get_events_from_database,
    get_professors_from_database,
    get_student_interests,
    save_student_interests,
)
from models import ChatRequest, RecommendationRequest, StudentInterestsRequest
from routers.auth import router as auth_router
from routers.verification import router as verification_router
from services.event_recommender import get_recommender, profile_to_text
from services.interest_expansion import extract_event_interests
from services.ml.router import router as ml_router
from services.rag.config import RAG_ENABLED
from services.recommendation_service import RecommendationService

recommendation_service = RecommendationService()

INTEREST_GROUPS = {
    "coding": ["coding", "programming", "computer science", "technology", "software"],
    "career": ["career", "job", "jobs", "internship", "internships", "employment"],
}

app = FastAPI()
app.include_router(ml_router)

app.include_router(auth_router)
app.include_router(verification_router)

# let the react app (vite runs on 5173) call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

#handling all RequestValidationError's
@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        #input not included in response for potential PII data protection 
            # if segmented into different validation errors, input can be returned for certain ones
        content={
            "detail": [
                {
                    "loc": list(error["loc"]),
                    "msg": error["msg"],
                    "type": error["type"],
                }
                for error in exc.errors()
            ]
        },
    )



@app.get("/")
def home() -> FileResponse:
    return FileResponse("static/index.html")

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1").fetchone()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="database unreachable",
        ) from exc

    return {"status": "ready"}


@app.get("/events")
def get_events() -> dict[str, Any]:
    return {"events": get_events_from_database()}


@app.get("/dining")
def get_dining() -> dict[str, Any]:
    return {"dining": get_dining_from_database()}


@app.get("/courses")
def get_courses(
    code: str | None = Query(default=None),
    professor: str | None = Query(default=None),
) -> dict[str, Any]:
    courses = get_courses_from_database()

    if code:
        search_code = " ".join(code.upper().split())
        courses = [
            course
            for course in courses
            if (
                str(course.get("course_code") or course.get("code") or "").upper().split()[0:1]
                == [search_code]
                if search_code.isalpha()
                else " ".join(
                    str(course.get("course_code") or course.get("code") or "").upper().split()
                ).startswith(search_code)
            )
        ]

    if professor:
        matching_ids = {course["course_id"] for course in get_courses_by_professor(professor)}
        courses = [course for course in courses if course["course_id"] in matching_ids]

    return {"courses": courses}


@app.get("/professors")
def get_professors() -> dict[str, Any]:
    return {"professors": get_professors_from_database()}


@app.get("/deadlines")
def get_deadlines(
    user: Annotated[dict, Depends(get_current_user)],
):
    return {"deadlines": get_deadlines_from_database(user["student_id"])}


def find_course_by_message(message: str) -> dict[str, Any] | None:
    message = message.lower()

    for course in get_courses_from_database():
        # Support both the legacy/CI schema and Prototype 2 schema.
        course_code = course.get("code") or course.get("course_code") or ""
        course_number = course.get("course_number") or ""
        course_name = course.get("name") or course.get("course_name") or ""

        full_code = f"{course_code} {course_number}".strip()

        if (full_code and full_code.lower() in message) or (
            course_name and contains_keyword(message, course_name.lower())
        ):
            return course

    return None


def find_professor_by_message(message: str) -> dict[str, Any] | None:
    professors = get_professors_from_database()
    message = message.lower()

    # Prefer matching a professor's complete name.
    full_matches = [
        professor
        for professor in professors
        if contains_keyword(message, professor["professor_name"].lower())
    ]

    if len(full_matches) == 1:
        return full_matches[0]

    if len(full_matches) > 1:
        return None

    # Only match surnames as complete words.
    surname_matches = [
        professor
        for professor in professors
        if contains_keyword(
            message,
            professor["professor_name"].lower().split()[-1],
        )
    ]

    # Avoid guessing when multiple professors share a surname.
    if len(surname_matches) == 1:
        return surname_matches[0]

    return None


def contains_keyword(message: str, keyword: str) -> bool:
    pattern = rf"(?<!\w){re.escape(keyword)}(?!\w)"
    return re.search(pattern, message) is not None


def is_event_listing_request(message: str) -> bool:
    """Identify requests for a general list of campus events."""
    listing_phrases = (
        "show me",
        "list",
        "upcoming",
        "what events",
        "which events",
        "any events",
        "events happening",
        "events this",
        "campus events",
    )

    return any(phrase in message for phrase in listing_phrases)


# FIRST NEW HELPER
def extract_interests_from_message(message: str) -> list[str]:
    """Extract student interest categories from a chat message."""
    return recommendation_service.extract_interests(message)


# SECOND NEW HELPER
def get_event_recommendations(interests: list[str]) -> list[dict[str, Any]]:
    recommended_events = []

    normalized_interests = [interest.lower().strip() for interest in interests]

    for event in get_events_from_database():
        event_tags = {str(tag).lower().strip() for tag in (event.get("event_tags") or [])}

        if any(
            tag in event_tags
            for interest in normalized_interests
            for tag in [interest, *recommendation_service.related_interests(interest)]
        ):
            recommended_events.append(event)

    return recommended_events


@app.post("/recommendations/events")
def recommend_events(request: RecommendationRequest) -> dict[str, Any]:
    recommended_events = get_event_recommendations(request.interests)

    return {"interests": request.interests, "recommended_events": recommended_events}


@app.post(
    "/students/{student_id}/interests",
    dependencies=[Depends(require_student_owner)],
)
def set_student_interests(
    student_id: int,
    request: StudentInterestsRequest,
) -> dict[str, Any]:
    if not request.interests:
        raise HTTPException(status_code=400, detail="At least one student interest is required.")

    saved = save_student_interests(student_id, request.interests)
    if not saved:
        raise HTTPException(status_code=404, detail="Student not found.")

    return {
        "student_id": student_id,
        "interests": get_student_interests(student_id),
        "message": "Student interests saved successfully.",
    }


@app.get(
    "/students/{student_id}/interests",
    dependencies=[Depends(require_student_owner)],
)
def get_saved_student_interests(student_id: int) -> dict[str, Any]:
    interests = get_student_interests(student_id)

    return {"student_id": student_id, "interests": interests}


@app.get(
    "/students/{student_id}/recommendations/events",
    dependencies=[Depends(require_student_owner)],
)
def get_student_event_recommendations(student_id: int) -> dict[str, Any]:
    student_interests = get_student_interests(student_id)

    if not student_interests:
        raise HTTPException(status_code=404, detail="No saved interests found for this student.")

    # compare the students text with the events, the first time it loads the model
    try:
        recommended_events = get_recommender().recommend(profile_to_text(student_interests))
    except Exception as error:
        # the event files are not there, use the old way with the categories
        print("event recommender not available:", error)
        recommended_events = get_event_recommendations(student_interests)

    return {
        "student_id": student_id,
        "interests": student_interests,
        "recommended_events": recommended_events,
    }


# nothing matched in chat, ask the rag if it is on, if not say we dont know
# (this is its own function so chat is not too complex for the linter)
def get_fallback_reply(request: ChatRequest) -> dict[str, Any]:
    if RAG_ENABLED:
        from services.rag.pipeline import query_RAG

        answer, sources = query_RAG(request.message, history=[])

        return {"intent": "rag", "reply": answer, "sources": sources}

    return {
        "intent": "unknown",
        "reply": (
            "I could not understand that request. "
            "I can help with campus events, dining, courses, "
            "professors, deadlines, and student recommendations. "
            "Try asking something like 'What events are happening?' "
            "or 'Tell me about CS 560.'"
        ),
    }


def get_live_event_chat_response(message: str) -> dict[str, Any] | None:
    # Route topic-specific event requests to fresh ShockerSync recommendations.
    # Keep informational questions and existing database routes unchanged.
    event_request_terms = (
        "event",
        "events",
        "activity",
        "activities",
        "workshop",
        "workshops",
        "concert",
        "concerts",
        "performance",
        "performances",
        "meeting",
        "meetings",
    )

    identified_interests = extract_event_interests(message)

    known_event_topics = (
        "artificial intelligence",
        "machine learning",
        "ai",
        "music",
        "cybersecurity",
        "career",
        "internship",
        "python",
        "programming",
        "engineering",
        "soccer",
        "cultural",
        "culture",
    )

    has_event_request = any(contains_keyword(message, term) for term in event_request_terms)

    has_topic = any(contains_keyword(message, topic) for topic in known_event_topics)

    if has_event_request and has_topic:
        try:
            recommended_events = get_recommender().recommend(
                message,
                top_k=5,
            )
        except Exception as error:
            print("Live event recommendation unavailable:", error)
            return {
                "intent": "recommendations",
                "reply": "Live campus event recommendations are temporarily unavailable.",
                "interests": [identified_interests],
                "data": [],
            }

        return {
            "intent": "recommendations",
            "reply": (
                "Here are upcoming ShockerSync events matching your interests."
                if recommended_events
                else "I couldn't find matching upcoming ShockerSync events."
            ),
            "interests": [identified_interests],
            "data": recommended_events,
        }

    return None


def get_professor_chat_response(message: str) -> dict[str, Any] | None:
    matched_professor = find_professor_by_message(message)
    if matched_professor:
        return {
            "intent": "professors",
            "reply": f"Here are the details for {matched_professor['professor_name']}.",
            "data": matched_professor,
        }

    return None


def get_matched_course_reply(message: str) -> dict[str, Any] | None:
    matched_course = find_course_by_message(message)
    if not matched_course:
        return None
    course_code = matched_course.get("course_code") or ""
    course_number = matched_course.get("course_number") or ""
    combined_code = matched_course.get("code") or ""

    if not course_code or not course_number:
        parts = combined_code.strip().split(maxsplit=1)
        if len(parts) == 2:
            course_code, course_number = parts

    if course_code and course_number:
        detailed_reply = build_course_reply(course_code, course_number)
        if detailed_reply:
            return {
                "intent": "courses",
                "reply": detailed_reply["reply"],
                "data": matched_course,
            }

    course_name = matched_course.get("name") or matched_course.get("course_name") or ""
    full_code = f"{course_code} {course_number}".strip() or combined_code

    return {
        "intent": "courses",
        "reply": f"Here are the details for {full_code} {course_name}.",
        "data": matched_course,
    }


def get_missing_course_reply(message: str) -> dict[str, Any] | None:
    """Report a missing explicitly requested course without listing unrelated courses."""
    import re

    match = re.search(
        r"(?<![a-z0-9])([a-z]{2,6})\s*[- ]?\s*(\d{3,4}[a-z]{0,3})(?![a-z0-9])",
        message,
        re.IGNORECASE,
    )

    if not match:
        return None

    course_code = f"{match.group(1).upper()} {match.group(2).upper()}"

    return {
        "intent": "courses",
        "reply": (
            f"I couldn't find {course_code} in the current course database. "
            "Please verify the course code or check the official WSU course catalog."
        ),
        "data": [],
    }




def get_general_professor_response(message: str) -> dict[str, Any]:
    """Return WSU faculty information for general chat requests."""
    departments = (
        "Electrical and Computer Engineering",
        "Mechanical Engineering",
        "Aerospace Engineering",
        "Biomedical Engineering",
        "School of Computing",
    )

    professors = [
        professor
        for professor in get_professors_from_database()
        if professor.get("professor_department") in departments
        and str(professor.get("professor_email") or "").lower().endswith("@wichita.edu")
    ]

    matched_departments = [
        department for department in departments if contains_keyword(message, department.lower())
    ]

    if matched_departments:
        professors = [
            professor
            for professor in professors
            if professor["professor_department"] in matched_departments
        ]

    return {
        "intent": "professors",
        "reply": (
            f"Here are the professors in {matched_departments[0]}."
            if len(matched_departments) == 1
            else "Here are some WSU professor details."
        ),
        "data": professors,
    }

  

  

def get_general_event_response() -> dict[str, Any]:
    """Return upcoming ShockerSync events for general chat requests."""
    from services import event_recommender

    try:
        upcoming_events = event_recommender.list_upcoming_events(
            get_recommender().events,
            today=event_recommender.today_in_wichita(),
            limit=10,
        )
    except Exception as error:
        print("ShockerSync event listing unavailable:", error)
        return {
            "intent": "events",
            "reply": "Upcoming ShockerSync events are temporarily unavailable.",
            "data": [],
        }

    return {
        "intent": "events",
        "reply": (
            "Here are upcoming ShockerSync campus events."
            if upcoming_events
            else "I couldn't find upcoming ShockerSync campus events."
        ),
        "data": upcoming_events,
    }


def get_general_chat_response(message: str) -> dict[str, Any] | None:
    """Handle general campus information and interest recommendations."""
    event_keywords = ["event", "events", "activity", "activities", "career fair", "competition"]
    dining_keywords = ["dining", "food", "eat", "cafeteria", "restaurant", "hungry"]
    course_keywords = ["course", "courses", "class", "classes", "cs 560", "cs 598"]
    professor_keywords = [
        "professor",
        "professors",
        "faculty",
        "instructor",
        "instructors",
        "teacher",
        "teachers",
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

    detected_interests = extract_interests_from_message(message)

    if detected_interests and any(
        contains_keyword(message, keyword) for keyword in recommendation_keywords
    ):
        recommended_events = get_event_recommendations(detected_interests)
        return {
            "intent": "recommendations",
            "reply": "Here are some campus events based on your interests.",
            "interests": detected_interests,
            "data": recommended_events,
        }

    if any(
        contains_keyword(message, keyword) for keyword in event_keywords
    ) and is_event_listing_request(message):
        return get_general_event_response()

    if any(contains_keyword(message, keyword) for keyword in dining_keywords):
        return {
            "intent": "dining",
            "reply": "Here are some dining options on campus.",
            "data": get_dining_from_database(),
        }

    if any(contains_keyword(message, keyword) for keyword in course_keywords):
        return {
            "intent": "courses",
            "reply": "Here are some course details.",
            "data": get_courses_from_database(),
        }

    if any(contains_keyword(message, keyword) for keyword in professor_keywords):
        return get_general_professor_response(message)

    if any(contains_keyword(message, keyword) for keyword in deadline_keywords):
        return {
            "intent": "deadlines",
            "reply": "Here are some important academic deadlines.",
            "data": get_deadlines_from_database(user["student_id"])
        }

    return None


@app.post("/chat")
def chat(  # noqa: C901
    request: ChatRequest,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    message = request.message.lower().strip()

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    course_response = get_matched_course_reply(message)
    if course_response is not None:
        return course_response

    missing_course_response = get_missing_course_reply(message)
    if missing_course_response is not None:
        return missing_course_response

    professor_response = get_professor_chat_response(message)
    if professor_response is not None:
        return professor_response

    live_event_response = get_live_event_chat_response(message)
    if live_event_response is not None:
        return live_event_response

    general_response = get_general_chat_response(message)
    if general_response is not None:
        return general_response

    return get_fallback_reply(request)


def build_course_reply(course_code: str, course_number: str) -> dict[str, Any] | None:
    """Format course details from PostgreSQL."""
    records = get_course_details(course_code, course_number)
    if not records:
        return None
    course = records[0]
    code = f"{course['course_code']} {course['course_number']}"
    reply = f"{code}: {course['course_name']} ({course['course_credits']:g} credits)."
    if course["course_description"]:
        reply += f" Description: {course['course_description']}"
    for row in records:
        if row["offering_id"] is None:
            continue
        instructor = " ".join(
            str(row[k]) for k in ("instructor_fname", "instructor_lnames") if row[k]
        )
        if instructor:
            reply += f" Instructor: {instructor}."
        if row["session_name"]:
            reply += f" Semester: {row['session_name']}."
        break
    if course_code.upper() == "TEST":
        reply = "TEST DATA ONLY (not verified WSU information). " + reply
    return {"intent": "courses", "reply": reply, "data": records}