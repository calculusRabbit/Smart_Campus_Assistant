#helps implements policies for student usernames

import re
import unicodedata

RESERVED = (
    "admin",
    "system",
    "notification",
    "alert",
)

PROFANITY_STEMS = (
    "fuck",
    "shit",
)

PROFANITY_WORDS = {
    "ass",
    "asshole",
    "bastard",
    "bitch",
    "bullshit",
    "cunt",
    "dick",
    "motherfucker",
    "piss",
    "porn",
    "pussy",
}

LEET = str.maketrans({
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "@": "a",
    "!": "i",
})


def validate_student_username(value: str) -> str:
    folded = unicodedata.normalize("NFKC", value).casefold()
    translated = folded.translate(LEET)
    compact = re.sub(r"[^a-z]", "", translated)
    word = ""
    if any(
        word in folded or word in compact
        for word in RESERVED
    ):
        raise ValueError(f"Username contains a reserved phrase: {word}")

    tokens = set(re.findall(r"[a-z]+", translated))
    tokens.update(re.findall(r"[a-z]+", folded))

    without_suffix = re.sub(
        r"[0-9]+$",
        "",
        folded,
    ).translate(LEET)

    tokens.add(
        re.sub(r"[^a-z]", "", without_suffix)
    )

    if (
        any(word in compact for word in PROFANITY_STEMS)
        or compact in PROFANITY_WORDS
        or tokens & PROFANITY_WORDS
    ):
        raise ValueError("Username contains inappropriate language, please choose another")

    return value