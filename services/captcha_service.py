# ALTCHA verification w/ single-use CAPTCHAs

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta

from altcha import create_challenge, verify_solution
from fastapi import HTTPException

from auth import JWT_KEY
from database import get_connection

# generate purpose-specific key
CAPTCHA_KEY = hmac.new(
    JWT_KEY.encode(),
    b"captcha",
    hashlib.sha256,
).hexdigest()


def create_captcha(action: str):
    expires = datetime.now(UTC) + timedelta(minutes=5)

    challenge = create_challenge(
        algorithm="PBKDF2/SHA-256",
        cost=5000,
        hmac_secret=CAPTCHA_KEY,
        expires_at=expires,
    ).to_dict()

    with get_connection() as conn:
        conn.execute("DELETE FROM Captcha_challenges WHERE expires_at < CURRENT_TIMESTAMP")
        conn.execute(
            "INSERT INTO Captcha_challenges VALUES (%s, %s, %s)",
            (challenge["signature"], action, expires),
        )

    return challenge


def check_captcha(payload: str, action: str):
    try:
        if not payload or len(payload) > 8192:
            raise ValueError("Missing CAPTCHA")

        if not verify_solution(payload, CAPTCHA_KEY).verified:
            raise ValueError("Invalid CAPTCHA")

        decoded = json.loads(base64.b64decode(payload, validate=True))
        signature = decoded["challenge"]["signature"]
    except (
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        RecursionError,
    ) as exc:
        raise HTTPException(
            400,
            "Please complete a new CAPTCHA and try again",
        ) from exc

    with get_connection() as conn:
        used = conn.execute(
            """
            DELETE FROM Captcha_challenges
            WHERE signature = %s AND action = %s AND expires_at > CURRENT_TIMESTAMP
            RETURNING signature
            """,
            (signature, action),
        ).fetchone()

    if used is None:
        raise HTTPException(400, "CAPTCHA expired or already used")
