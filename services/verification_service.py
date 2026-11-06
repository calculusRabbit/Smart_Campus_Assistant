# enrollment email and manual document verification

import hashlib
import hmac
import json
import os
import re
import secrets
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import HTTPException
from psycopg.errors import UniqueViolation

from auth import JWT_KEY
from database import get_connection

# keywords to flag in emails
STAFF_LABELS = set(
    "cs cse ee ece bme math physics bio chem psych "
    "hr legal payroll office president provost dean registrar "
    "admissions financialaid bursar faculty staff".split()
)

OTP_KEY = hmac.new(
    JWT_KEY.encode(),
    b"enrollment-otp",
    hashlib.sha256,
).digest()


def code_hash(student_id: int, email: str, code: str):
    value = f"{student_id}|{email}|{code}".encode()
    return hmac.new(OTP_KEY, value, hashlib.sha256).hexdigest()


def staff_reasons(email: str):
    local, domain = email.lower().rsplit("@", 1)
    tokens = set(re.split(r"[^a-z0-9]+", local))
    tokens.update(domain.split(".")[:-2])

    reasons = sorted(tokens & STAFF_LABELS)

    if re.fullmatch(r"[a-z]+\.[a-z]+", local.split("+", 1)[0]):
        reasons.append("first.last pattern")

    return reasons


def school_for(conn, student_id: int):
    row = conn.execute(
        """
        SELECT sc.*
        FROM Enrolments e
        JOIN Schools sc USING (school_id)
        WHERE e.student_id = %s
          AND e.is_primary
        """,
        (student_id,),
    ).fetchone()

    if row is None:
        raise HTTPException(400, "No institution selected")

    return row


def require_manual(conn, student_id: int, reason: str):
    # Serialize creation of pending reviews for this account.
    conn.execute(
        """
        SELECT u.username
        FROM Users u
        JOIN Students s USING (username)
        WHERE s.student_id = %s
        FOR UPDATE OF u
        """,
        (student_id,),
    )

    existing = conn.execute(
        """
        SELECT authentication_id
        FROM Authentications
        WHERE student_id = %s AND status = 'pending'
        ORDER BY authentication_id DESC
        LIMIT 1
        """,
        (student_id,),
    ).fetchone()

    if existing:
        conn.execute(
            """
            UPDATE Authentications
            SET method = 'manual', reason = %s
            WHERE authentication_id = %s
            """,
            (reason, existing["authentication_id"]),
        )
    else:
        conn.execute(
            """
            INSERT INTO Authentications (
                student_id, status, method, reason
            )
            VALUES (%s, 'pending', 'manual', %s)
            """,
            (student_id, reason),
        )

    conn.execute(
        "UPDATE Students SET account_status = 'pending' WHERE student_id = %s",
        (student_id,),
    )

    return {
        "manual_required": True,
        "message": f"Manual enrollment verification required: {reason}",
    }


def send_email(email: str, code: str):
    key = os.environ.get("MAILJET_API_KEY")
    secret = os.environ.get("MAILJET_API_SECRET")
    sender = os.environ.get("MAILJET_FROM")

    if not all((key, secret, sender)):
        raise HTTPException(503, "Email delivery is not configured")

    try:
        response = httpx.post(
            "https://api.mailjet.com/v3.1/send",
            auth=(key, secret),
            json={
                "Messages": [
                    {
                        "From": {
                            "Email": sender,
                            "Name": "Smart Campus Assistant",
                        },
                        "To": [{"Email": email}],
                        "Subject": "Your enrollment verification code",
                        "TextPart": (
                            f"Your code is {code}. It expires in five minutes. Do not share it."
                        ),
                    }
                ],
            },
            timeout=15,
        )
        response.raise_for_status()

        if response.json()["Messages"][0]["Status"] != "success":
            raise ValueError("Email rejected")
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        raise HTTPException(503, "Email delivery unavailable") from exc


def start_otp(user: dict, email: str):
    student_id = user["student_id"]
    email = email.lower()
    now = datetime.now(UTC)
    result = None

    with get_connection() as conn:
        conn.execute(
            "SELECT username FROM Users WHERE username = %s FOR UPDATE",
            (user["username"],),
        )

        school = school_for(conn, student_id)

        # This mapping is administrator-controlled, not browser-supplied.
        config = json.loads(os.environ.get("INSTITUTION_EMAIL_DOMAINS") or "{}")
        allowed = config.get(str(school["scorecard_id"]), [])
        domain = email.rsplit("@", 1)[1]

        matches = any(domain == approved or domain.endswith("." + approved) for approved in allowed)

        if not domain.endswith(".edu") or not matches:
            return require_manual(
                conn,
                student_id,
                "institution email domain is not confirmed",
            )

        pending = conn.execute(
            """
            SELECT 1 FROM Authentications
            WHERE student_id = %s
              AND status = 'pending'
              AND method = 'manual'
            """,
            (student_id,),
        ).fetchone()

        if pending:
            return {
                "manual_required": True,
                "message": "Complete your pending manual review",
            }

        old = conn.execute(
            "SELECT * FROM Enrollment_otps WHERE student_id = %s",
            (student_id,),
        ).fetchone()

        if old and old["failures"] >= 3:
            return require_manual(
                conn,
                student_id,
                "OTP guesses exhausted",
            )

        if old and (now - old["last_sent"]).total_seconds() < 60:
            raise HTTPException(429, "Wait one minute before resending")

        failures = old["failures"] if old else 0
        code = f"{secrets.randbelow(1_000_000):06d}"

        conn.execute(
            """
            INSERT INTO Enrollment_otps (
                student_id, email, code_hash, failures,
                expires_at, last_sent
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (student_id) DO UPDATE SET
                email = EXCLUDED.email,
                code_hash = EXCLUDED.code_hash,
                failures = EXCLUDED.failures,
                expires_at = EXCLUDED.expires_at,
                last_sent = EXCLUDED.last_sent,
                consumed = FALSE
            """,
            (
                student_id,
                email,
                code_hash(student_id, email, code),
                failures,
                now + timedelta(minutes=5),
                now,
            ),
        )

        try:
            send_email(email, code)
        except HTTPException:
            conn.execute(
                "UPDATE Enrollment_otps SET consumed = TRUE WHERE student_id = %s",
                (student_id,),
            )
            result = require_manual(
                conn,
                student_id,
                "email delivery unavailable",
            )

    return result or {
        "message": "Code sent. It expires in five minutes.",
    }


def complete_otp(user: dict, code: str):
    student_id = user["student_id"]
    error = None
    result = None

    try:
        with get_connection() as conn:
            conn.execute(
                "SELECT username FROM Users WHERE username = %s FOR UPDATE",
                (user["username"],),
            )

            row = conn.execute(
                """
                SELECT * FROM Enrollment_otps
                WHERE student_id = %s
                FOR UPDATE
                """,
                (student_id,),
            ).fetchone()

            if row is None or row["consumed"]:
                error = "No active code"
            elif row["failures"] >= 3:
                result = require_manual(
                    conn,
                    student_id,
                    "OTP guesses exhausted",
                )
            elif row["expires_at"] <= datetime.now(UTC):
                error = "Code expired. Request another code."
            elif not hmac.compare_digest(
                row["code_hash"],
                code_hash(student_id, row["email"], code),
            ):
                conn.execute(
                    """
                    UPDATE Enrollment_otps
                    SET failures = failures + 1
                    WHERE student_id = %s
                    """,
                    (student_id,),
                )

                if row["failures"] == 2:
                    result = require_manual(
                        conn,
                        student_id,
                        "OTP guesses exhausted",
                    )
                else:
                    error = "Incorrect code"
            else:
                conn.execute(
                    "UPDATE Enrollment_otps SET consumed = TRUE WHERE student_id = %s",
                    (student_id,),
                )

                reasons = staff_reasons(row["email"])

                if reasons:
                    result = require_manual(
                        conn,
                        student_id,
                        ", ".join(reasons),
                    )
                else:
                    # A previous staff/manual flag cannot be bypassed
                    # simply by switching verification methods.
                    pending = conn.execute(
                        """
                        SELECT 1 FROM Authentications
                        WHERE student_id = %s
                          AND status = 'pending'
                          AND method = 'manual'
                        """,
                        (student_id,),
                    ).fetchone()

                    if pending:
                        result = {
                            "manual_required": True,
                            "message": "Complete your pending manual review",
                        }
                    else:
                        conn.execute(
                            """
                            UPDATE Students
                            SET edu_email = %s, account_status = 'open'
                            WHERE student_id = %s
                            """,
                            (row["email"], student_id),
                        )
                        conn.execute(
                            """
                            INSERT INTO Authentications (
                                student_id, status, method, reviewed_time
                            )
                            VALUES (
                                %s, 'approved', 'email_otp',
                                CURRENT_TIMESTAMP
                            )
                            """,
                            (student_id,),
                        )
                        result = {
                            "approved": True,
                            "message": "Email verification complete",
                        }
    except UniqueViolation as exc:
        raise HTTPException(
            409,
            "This institutional email is already linked to an account",
        ) from exc

    # Raise outside the transaction so failed guesses remain counted.
    if error:
        raise HTTPException(400, error)

    return result
