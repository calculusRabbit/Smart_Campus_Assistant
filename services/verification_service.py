# enrollment email and manual document verification

import hashlib
import hmac
import json
import os
import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
from fastapi import HTTPException
from psycopg import Connection
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


def code_hash(student_id: int, email: str, code: str) -> str:
    value = f"{student_id}|{email}|{code}".encode()
    return hmac.new(OTP_KEY, value, hashlib.sha256).hexdigest()


def staff_reasons(email: str) -> list[str]:
    local, domain = email.lower().rsplit("@", 1)
    tokens = set(re.split(r"[^a-z0-9]+", local))
    tokens.update(domain.split(".")[:-2])

    reasons = sorted(tokens & STAFF_LABELS)

    if re.fullmatch(r"[a-z]+\.[a-z]+", local.split("+", 1)[0]):
        reasons.append("first.last pattern")

    return reasons


def school_for(
    conn: Connection[dict[str, Any]],
    student_id: int,
) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT sc.*
        FROM Enrolments e
        JOIN Schools sc USING (school_id)
        WHERE e.student_id = %s
        ORDER BY e.is_primary DESC, e.enrolment_id
        LIMIT 1
        """,
        (student_id,),
    ).fetchone()

    if row is None:
        raise HTTPException(400, "No institution selected")

    return row


def require_manual(
    conn: Connection[dict[str, Any]],
    student_id: int,
    reason: str,
) -> dict[str, Any]:
    # serialise creation of pending reviews for this account
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


def send_email(email: str, code: str) -> None:
    key = os.environ.get("MAILJET_API_KEY")
    secret = os.environ.get("MAILJET_API_SECRET")
    sender = os.environ.get("MAILJET_FROM")

    if not key or not secret or not sender:
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
                        "Subject": f"{code} — Your enrollment verification code",
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


def start_otp(user: dict[str, Any], email: str) -> dict[str, Any]:
    student_id = user["student_id"]
    email = email.lower()
    now = datetime.now(UTC)
    result = None

    with get_connection() as conn:
        conn.execute(
            "SELECT username FROM Users WHERE username = %s FOR UPDATE",
            (user["username"],),
        )

        school_for(conn, student_id)

        # This mapping is administrator-controlled, not browser-supplied.
        domain = email.rsplit("@", 1)[1]
        if not domain.endswith(".edu"):
            raise HTTPException(
                status_code=400,
                detail="Please use a .edu email address.",
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


def _complete_verified_otp(
    conn: Connection[dict[str, Any]],
    student_id: int,
    email: str,
) -> dict[str, Any]:
    """Consume a correct code and apply the existing verification policy."""
    conn.execute(
        "UPDATE Enrollment_otps SET consumed = TRUE WHERE student_id = %s",
        (student_id,),
    )

    reasons = staff_reasons(email)
    if reasons:
        return require_manual(conn, student_id, ", ".join(reasons))

    # A previous staff/manual flag cannot be bypassed with email OTP.
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

    conn.execute(
        """
        UPDATE Students
        SET edu_email = %s, account_status = 'open'
        WHERE student_id = %s
        """,
        (email, student_id),
    )
    conn.execute(
        """
        INSERT INTO Authentications (
            student_id, status, method, reviewed_time
        )
        VALUES (%s, 'approved', 'email_otp', CURRENT_TIMESTAMP)
        """,
        (student_id,),
    )

    return {
        "approved": True,
        "message": "Email verification complete",
    }


def complete_otp(user: dict[str, Any], code: str) -> dict[str, Any]:
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
                result = _complete_verified_otp(
                    conn,
                    student_id,
                    row["email"],
                )
    except UniqueViolation as exc:
        raise HTTPException(
            409,
            "This institutional email is already linked to an account",
        ) from exc

    # raise after leaving the transaction so failed guesses are still counted
    if error:
        raise HTTPException(400, error)

    if result is None:
        raise HTTPException(500, "verification produced no result")

    return result



# studid.io integration functions

def _studid_request(
    method: str,
    path: str,
    **kwargs: Any,
) -> dict[str, Any]:
    try:
        response = httpx.request(
            method,
            "https://api.studid.io/v2/" + path,
            timeout=15,
            headers={
                "User-Agent": "SmartCampusAssistant/1.0",
                **kwargs.pop("headers", {}),
            },
            **kwargs,
        )
        response.raise_for_status()

        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Invalid response")

        return data
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            503,
            "Studid unavailable. Please verify using .edu email OTP instead.",
        ) from exc


def _studid_entities(scorecard_id: int | None) -> list[str]:
    try:
        config = json.loads(
            os.environ.get("INSTITUTION_STUDID_ENTITIES") or "{}"
        )
        entities = config.get(str(scorecard_id), [])

        if not isinstance(entities, list) or any(
            not isinstance(item, str) for item in entities
        ):
            raise ValueError("Invalid institution mapping")

        return entities
    except (ValueError, AttributeError) as exc:
        raise HTTPException(
            503,
            "Studid institution mapping is not configured correctly",
        ) from exc


def start_studid(user: dict[str, Any]) -> dict[str, str]:
    callback = os.environ.get("STUDID_REDIRECT_URL", "")
    if not callback.startswith("https://"):
        raise HTTPException(
            503,
            "Studid needs an HTTPS callback. Please use email OTP for now",
        )

    with get_connection() as conn:
        school = school_for(conn, user["student_id"])

    if not _studid_entities(school["scorecard_id"]):
        raise HTTPException(
            503,
            "This institution isn't configured in Studid. Please use email OTP instead",
        )

    secret = secrets.token_urlsafe(32)

    data = _studid_request(
        "POST",
        "auth/verification",
        json={
            "secretToken": secret,
            "redirectUrl": callback,
            "serviceName": "Smart Campus Assistant",
            "mode": "live",
        },
    )

    try:
        verification_id = UUID(data["id"])
        link = data["link"]

        if not isinstance(link, str) or not link.startswith(
            "https://studid.io/"
        ):
            raise ValueError("Invalid verification link")
    except (KeyError, ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(
            503,
            "Invalid Studid response. Please use email OTP instead",
        ) from exc

    with get_connection() as conn:
        conn.execute(
            "DELETE FROM Studid_verifications "
            "WHERE expires_at <= CURRENT_TIMESTAMP"
        )
        conn.execute( # in case of conflict, use upsert to overwrite old verification data
            """
            INSERT INTO Studid_verifications (student_id, verification_id, secret_token)
            VALUES (%s, %s, %s)
            ON CONFLICT(student_id) DO UPDATE SET
                verification_id = EXCLUDED.verification_id,
                secret_token = EXCLUDED.secret_token,
                expires_at = EXCLUDED.expires_at
            """, (user["student_id"], verification_id, secret)
        )

    return {
        "id": str(verification_id),
        "url": link
    }


def _apply_studid(
    conn: Connection[dict[str, Any]],
    student_id: int,
    school: dict[str, Any],
    session: dict[str, Any]
) -> dict[str, Any]:
    
    entity_id = session.get("entityId")

    if entity_id not in _studid_entities(school["scorecard_id"]):
        return require_manual(
            conn,
            student_id,
            "SSO institution does not match selected institution",
        )

    identifier = session.get("authIdentifier")
    if identifier is not None and (
        not isinstance(identifier, str) or not identifier
    ):
        raise HTTPException(503, "Invalid Studid identity response")

    conn.execute(
        """UPDATE Students SET studid_entity_id = %s, studid_identifier = %s
        WHERE student_id = %s""",
        (entity_id, identifier, student_id)
    )

    affiliations = session.get("affiliations", [])
    if not isinstance(affiliations, list):
        raise HTTPException(503, "Invalid Studid affiliation response")

    roles = {role.lower().split("@", 1)[0] for role in affiliations if isinstance(role, str)}

    if roles & {"staff", "faculty", "employee"}:
        return require_manual(conn, student_id,"Institution returned staff/faculty affiliation")

    pending = conn.execute(
        """SELECT 1 FROM Authentications
        WHERE student_id = %s AND status = 'pending' AND method = 'manual' """,
        (student_id,)
    ).fetchone()

    if pending:
        return {
            "manual_required": True,
            "message": "Complete your pending manual review",
        }

    if "student" not in roles:
        if roles - {"member"}:
            return require_manual(
                conn,
                student_id,
                "Institution did not confirm student affiliation",
            )

        return {
            "email_required": True,
            "message": "SSO role not supplied; verify your .edu email below",
        }

    conn.execute(
        "UPDATE Students SET account_status = 'open' WHERE student_id = %s",
        (student_id,),
    )
    conn.execute(
        """
        INSERT INTO Authentications (
            student_id, status, method, reviewed_time
        )
        VALUES (%s, 'approved', 'studid', CURRENT_TIMESTAMP)
        """,
        (student_id,),
    )

    return {
        "approved": True,
        "message": "Institutional student verification complete",
    }


def complete_studid(
    user: dict[str, Any],
    verification_id: UUID,
) -> dict[str, Any]:
    with get_connection() as conn:
        pending = conn.execute(
            """
            SELECT secret_token
            FROM Studid_verifications
            WHERE student_id = %s
              AND verification_id = %s
              AND expires_at > CURRENT_TIMESTAMP
            """,
            (user["student_id"], verification_id),
        ).fetchone()

    if pending is None:
        raise HTTPException(
            400,
            "Verification expired or does not belong to this account",
        )

    data = _studid_request(
        "GET",
        f"auth/verification/{verification_id}",
        headers={
            "Authorization": f"Bearer {pending['secret_token']}",
        },
    )

    session = data.get("session")
    if session is None:
        return {
            "pending": True,
            "message": "Waiting for institutional login",
        }

    if not isinstance(session, dict) or session.get("test") is not False:
        raise HTTPException(
            400,
            "Test or invalid Studid sessions cannot verify enrollment",
        )

    try:
        with get_connection() as conn:
            account = conn.execute(
                """
                SELECT username FROM Users
                WHERE username = %s AND deleted_timestamp IS NULL
                FOR UPDATE
                """,
                (user["username"],),
            ).fetchone()

            if account is None:
                raise HTTPException(401, "Account is not active")

            claimed = conn.execute(
                """
                DELETE FROM Studid_verifications
                WHERE student_id = %s AND verification_id = %s AND expires_at > CURRENT_TIMESTAMP
                RETURNING student_id
                """,
                (user["student_id"], verification_id),
            ).fetchone()

            if claimed is None:
                raise HTTPException(
                    409,
                    "Verification already used or expired",
                )

            school = school_for(conn, user["student_id"])

            return _apply_studid(
                conn,
                user["student_id"],
                school,
                session,
            )
    except UniqueViolation as exc:
        raise HTTPException(
            409,
            "This institutional identity is already linked to another account",
        ) from exc