"""Expand student interests into descriptions of relevant campus activities."""

import re

INTEREST_ACTIVITIES = {
    "programming": "coding workshops, programming competitions, and software development events",
    "coding": "coding workshops, programming competitions, and software development events",
    "python": "Python programming workshops and software development events",
    "artificial intelligence": "AI club meetings and artificial intelligence workshops",
    "machine learning": "machine learning workshops and AI club meetings",
    "ai": "AI club meetings and artificial intelligence workshops",
    "music": "music concerts, live performances, and music club events",
    "cybersecurity": "cybersecurity workshops, information security events, and WiCyS activities",
    "computer science clubs, technology workshops, and software development events"
    ),
    "career": "career fairs, internship opportunities, and professional networking events",
    "internship": "internship opportunities, career fairs, and employer networking events",
}


def expand_interests(text):
    """Preserve the original interests and add matching activity descriptions."""
    normalized = text.casefold()
    activities = []
    seen = set()

    for interest, description in INTEREST_ACTIVITIES.items():
        if (
            re.search(r"(?<!\w)" + re.escape(interest) + r"(?!\w)", normalized)
            and description not in seen
        ):
            activities.append(description)
            seen.add(description)

    if not activities:
        return text

    return text + ". I am interested in campus activities such as " + "; ".join(activities) + "."


# Recognize common ways students describe their interests.
INTEREST_ALIASES = {
    "ai": "artificial intelligence",
    "concert": "music",
    "concerts": "music",
    "musical": "music",
    "cyber security": "cybersecurity",
    "information security": "cybersecurity",
    "infosec": "cybersecurity",
    "technology": "computer science",
    "software": "programming",
    "jobs": "career",
    "internships": "internship",
    "sports": "sports",
    "soccer": "soccer",
}


def extract_event_interests(question):
    """Extract interests from a student question for event searching."""
    normalized = question.casefold()
    interests = []

    for interest in INTEREST_ACTIVITIES:
        if re.search(r"(?<!\w)" + re.escape(interest) + r"(?!\w)", normalized):
            interests.append(interest)

    for alias, interest in INTEREST_ALIASES.items():
        if re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", normalized):
            if interest not in interests:
                interests.append(interest)

    return ", ".join(interests) if interests else question
