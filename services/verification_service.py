import hashlib
import hmac
import os
import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID, uuid4

import httpx
from fastapi import HTTPException
from psycopg import Connection
from psycopg.errors import UniqueViolation

from auth import JWT_KEY
from database import get_connection
from services.institution_identity import (
    entity_matches,
    require_institution_email,
    resolve_identity,
)
from services.institution_service import get_institution

# keywords to flag in emails
STAFF_LABELS = set(
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
    except (
        httpx.HTTPError,
        ValueError,
        KeyError,
        IndexError,
        TypeError,
    ) as exc:
        raise HTTPException(
            503,
            "Email delivery unavailable",
        ) from exc


def _lock_account(
    conn: Connection[dict[str, Any]],
    user: dict[str, Any],
) -> None:
    account = conn.execute(
        """
        SELECT u.username, s.account_status
        FROM Users u
        JOIN Students s USING (username)
        WHERE u.username = %s
          AND s.student_id = %s
          AND u.deleted_timestamp IS NULL
        FOR UPDATE OF u
        """,
        (user["username"], user["student_id"]),
    ).fetchone()

    if account is None:
        raise HTTPException(401, "Account is not active")

    if account["account_status"] in {"closed", "denied"}:
        raise HTTPException(
            403,
            "This account cannot complete automatic verification",
        )


def _pending_manual(
    conn: Connection[dict[str, Any]],
    student_id: int,
) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM Authentications
        WHERE student_id = %s
          AND status = 'pending'
          AND method = 'manual'
        """,
        (student_id,),
    ).fetchone()

    return row is not None


def _manual_result() -> dict[str, Any]:
    return {
        "manual_required": True,
        "message": "Complete your pending manual review",
    }


def _identity(school: dict[str, Any]) -> dict[str, Any]:
    scorecard_id = school.get("scorecard_id")

    if scorecard_id is None:
        raise HTTPException(
            409,
            "Select an institution from the institution search.",
        )

    return resolve_identity(get_institution(scorecard_id))


def otp_status(
    row: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if row is None:
        return None

    return {
        "email": row["email"],
        "challenge_id": (
            str(row["challenge_id"])
            if row["challenge_id"]
            else None
        ),
        "school_id": row["school_id"],
        "consumed": row["consumed"],
        "expires_at": row["expires_at"],
        "resend_available_at": (
            row["last_sent"] + timedelta(seconds=60)
        ),
        "locked_until": row["locked_until"],
    }


def _check_send_limits(
    old: dict[str, Any] | None,
    now: datetime,
) -> int:
    if old is None:
        return 0

    locked_until = old["locked_until"]

    if locked_until and locked_until > now:
        wait = max(
            1,
            int((locked_until - now).total_seconds()) + 1,
        )
        raise HTTPException(
            429,
            "Too many incorrect codes. Try again later.",
            headers={"Retry-After": str(wait)},
        )

    resend_at = old["last_sent"] + timedelta(seconds=60)

    if resend_at > now:
        wait = max(
            1,
            int((resend_at - now).total_seconds()) + 1,
        )
        raise HTTPException(
            429,
            "Wait one minute before resending.",
            headers={"Retry-After": str(wait)},
        )

    if locked_until and locked_until <= now:
        return 0

    return old["failures"]


def start_otp(
    user: dict[str, Any],
    email: str,
) -> dict[str, Any]:
    student_id = user["student_id"]
    now = datetime.now(UTC)

    with get_connection() as conn:
        _lock_account(conn, user)

        school = school_for(conn, student_id)
        email = require_institution_email(
            email,
            _identity(school),
        )

        if _pending_manual(conn, student_id):
            return _manual_result()

        old = conn.execute(
            """
            SELECT *
            FROM Enrollment_otps
            WHERE student_id = %s
            FOR UPDATE
            """,
            (student_id,),
        ).fetchone()

        failures = _check_send_limits(old, now)
        challenge_id = uuid4()
        code = f"{secrets.randbelow(1_000_000):06d}"

        conn.execute(
            """
            INSERT INTO Enrollment_otps (
                student_id,
                email,
                code_hash,
                failures,
                expires_at,
                last_sent,
                school_id,
                challenge_id,
                locked_until
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL)
            ON CONFLICT (student_id) DO UPDATE SET
                email = EXCLUDED.email,
                code_hash = EXCLUDED.code_hash,
                failures = EXCLUDED.failures,
                expires_at = EXCLUDED.expires_at,
                last_sent = EXCLUDED.last_sent,
                school_id = EXCLUDED.school_id,
                challenge_id = EXCLUDED.challenge_id,
                locked_until = NULL,
                consumed = FALSE
            """,
            (
                student_id,
                email,
                code_hash(student_id, email, code),
                failures,
                now + timedelta(minutes=5),
                now,
                school["school_id"],
                challenge_id,
            ),
        )

        # old unfinished SSO attempts must not complete
        conn.execute(
            """
            DELETE FROM Studid_verifications
            WHERE student_id = %s
            """,
            (student_id,),
        )

        try:
            send_email(email, code)
        except HTTPException:
            conn.execute(
                """
                UPDATE Enrollment_otps
                SET consumed = TRUE
                WHERE student_id = %s
                """,
                (student_id,),
            )

            # returning normally -> challenge invalidation
            return {
                "sent": False,
                "manual_available": True,
                "resend_available_at": (
                    now + timedelta(seconds=60)
                ),
                "message": (
                    "We couldn't send your email. Try again later, "
                    "change email, or use manual verification."
                ),
            }

    return {
        "sent": True,
        "email": email,
        "challenge_id": str(challenge_id),
        "expires_at": now + timedelta(minutes=5),
        "resend_available_at": now + timedelta(seconds=60),
        "message": "Code sent. It expires in five minutes.",
    }


def _complete_verified_otp(
    conn: Connection[dict[str, Any]],
    student_id: int,
    email: str,
    school: dict[str, Any],
) -> dict[str, Any]:
    conn.execute(
        """
        UPDATE Enrollment_otps
        SET consumed = TRUE
        WHERE student_id = %s
        """,
        (student_id,),
    )

    reasons = staff_reasons(email)

    if reasons:
        return require_manual(
            conn,
            student_id,
            "Office/staff email indicators: " + ", ".join(reasons),
        )

    if _pending_manual(conn, student_id):
        return _manual_result()

    evidence = conn.execute(
        """
        SELECT affiliations
        FROM Student_sso_evidence
        WHERE student_id = %s
          AND school_id = %s
          AND expires_at > CURRENT_TIMESTAMP
        """,
        (student_id, school["school_id"]),
    ).fetchone()

    roles = set(evidence["affiliations"]) if evidence else set()

    if roles & {"staff", "faculty", "employee"}:
        return require_manual(
            conn,
            student_id,
            "Institution returned staff/faculty affiliation",
        )

    conn.execute(
        """
        UPDATE Students
        SET edu_email = %s,
            account_status = 'open'
        WHERE student_id = %s
        """,
        (email, student_id),
    )

    reason = (
        "Institution mailbox confirmed; office-name heuristic passed; "
    )

    if "student" in roles:
        reason += "same-application-account SSO student role observed"
    else:
        reason += "student role not asserted"

    conn.execute(
        """
        INSERT INTO Authentications (
            student_id,
            status,
            method,
            reviewed_time,
            reason
        )
        VALUES (
            %s,
            'approved',
            'email_otp',
            CURRENT_TIMESTAMP,
            %s
        )
        """,
        (student_id, reason),
    )

    return {
        "approved": True,
        "message": "Email verification complete",
    }


def _check_otp_attempt(
    conn: Connection[dict[str, Any]],
    student_id: int,
    school: dict[str, Any],
    row: dict[str, Any] | None,
    code: str,
    challenge_id: UUID,
) -> tuple[dict[str, Any] | None, str | None]:
    if row is None or row["consumed"]:
        return None, "No active code. Request a new code."

    if row["challenge_id"] != challenge_id:
        return None, "This code belongs to an older verification attempt."

    if row["school_id"] != school["school_id"]:
        conn.execute(
            """
            UPDATE Enrollment_otps
            SET consumed = TRUE
            WHERE student_id = %s
            """,
            (student_id,),
        )
        return (
            None,
            "Your institution changed. Request a new verification code.",
        )

    if row["expires_at"] <= datetime.now(UTC):
        return None, "Code expired. Request another code."

    if row["failures"] >= 3:
        return None, "Too many incorrect codes. Try again later."

    correct = hmac.compare_digest(
        row["code_hash"],
        code_hash(student_id, row["email"], code),
    )

    if not correct:
        locked_until = (
            datetime.now(UTC) + timedelta(minutes=15)
            if row["failures"] == 2
            else None
        )

        conn.execute(
            """
            UPDATE Enrollment_otps
            SET failures = failures + 1,
                locked_until = %s,
                consumed = %s
            WHERE student_id = %s
            """,
            (
                locked_until,
                locked_until is not None,
                student_id,
            ),
        )

        if locked_until:
            return {
                "otp_locked": True,
                "locked_until": locked_until,
                "manual_available": True,
                "message": (
                    "Too many incorrect codes. Wait 15 minutes "
                    "or use manual verification."
                ),
            }, None

        return None, "Incorrect code"

    # recheck institution metadata when consuming OTP
    email = require_institution_email(
        row["email"],
        _identity(school),
    )

    return (
        _complete_verified_otp(
            conn,
            student_id,
            email,
            school,
        ),
        None,
    )


def complete_otp(
    user: dict[str, Any],
    code: str,
    challenge_id: UUID,
) -> dict[str, Any]:
    student_id = user["student_id"]

    try:
        with get_connection() as conn:
            _lock_account(conn, user)
            school = school_for(conn, student_id)

            row = conn.execute(
                """
                SELECT *
                FROM Enrollment_otps
                WHERE student_id = %s
                FOR UPDATE
                """,
                (student_id,),
            ).fetchone()

            result, error = _check_otp_attempt(
                conn,
                student_id,
                school,
                row,
                code,
                challenge_id,
            )
    except UniqueViolation as exc:
        raise HTTPException(
            409,
            "This institutional email is already linked to an account",
        ) from exc

    if error:
        raise HTTPException(400, error)

    if result is None:
        raise HTTPException(
            500,
            "Verification produced no result",
        )

    return result


def cancel_otp(user: dict[str, Any]) -> dict[str, bool]:
    with get_connection() as conn:
        _lock_account(conn, user)

        conn.execute(
            """
            UPDATE Enrollment_otps
            SET consumed = TRUE
            WHERE student_id = %s
            """,
            (user["student_id"],),
        )

    # Don't delete row, preserve failures and resend cooldown
    return {"cancelled": True}


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
            follow_redirects=False,
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
            "Studid unavailable. Please use .edu email OTP instead.",
        ) from exc


def start_studid(
    user: dict[str, Any],
) -> dict[str, str]:
    callback = os.environ.get("STUDID_REDIRECT_URL", "")

    try:
        parsed = urlsplit(callback)
        valid_callback = (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and not parsed.username
            and not parsed.password
        )
    except ValueError:
        valid_callback = False

    if not valid_callback:
        raise HTTPException(
            503,
            "Studid needs a public HTTPS callback. "
            "Please use email OTP.",
        )

    with get_connection() as conn:
        school = school_for(conn, user["student_id"])
        _identity(school)

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
        target = urlsplit(link)

        if (
            target.scheme != "https"
            or target.netloc != "studid.io"
            or not target.path.startswith("/")
        ):
            raise ValueError("Invalid verification link")
    except (
        KeyError,
        ValueError,
        TypeError,
        AttributeError,
    ) as exc:
        raise HTTPException(
            503,
            "Invalid Studid response. Please use email OTP.",
        ) from exc

    with get_connection() as conn:
        _lock_account(conn, user)
        current = school_for(conn, user["student_id"])

        if current["school_id"] != school["school_id"]:
            raise HTTPException(
                409,
                "Your institution changed. Start verification again.",
            )

        conn.execute(
            """
            INSERT INTO Studid_verifications (
                student_id,
                verification_id,
                secret_token,
                school_id
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (student_id) DO UPDATE SET
                verification_id = EXCLUDED.verification_id,
                secret_token = EXCLUDED.secret_token,
                school_id = EXCLUDED.school_id,
                expires_at = EXCLUDED.expires_at
            """,
            (
                user["student_id"],
                verification_id,
                secret,
                school["school_id"],
            ),
        )

        conn.execute(
            """
            DELETE FROM Student_sso_evidence
            WHERE student_id = %s
            """,
            (user["student_id"],),
        )

        conn.execute(
            """
            UPDATE Enrollment_otps
            SET consumed = TRUE
            WHERE student_id = %s
            """,
            (user["student_id"],),
        )

    return {
        "id": str(verification_id),
        "url": link,
    }


def _apply_studid(
    conn: Connection[dict[str, Any]],
    student_id: int,
    school: dict[str, Any],
    session: dict[str, Any],
) -> dict[str, Any]:
    entity_id = session.get("entityId")
    identifier = session.get("authIdentifier")
    affiliations = session.get("affiliations", [])

    if not isinstance(entity_id, str) or not entity_id:
        raise HTTPException(
            503,
            "Invalid Studid institution response",
        )

    if identifier is not None and (
        not isinstance(identifier, str)
        or not identifier.strip()
    ):
        raise HTTPException(
            503,
            "Invalid Studid identity response",
        )

    if (
        not isinstance(affiliations, list)
        or any(
            not isinstance(role, str)
            for role in affiliations
        )
    ):
        raise HTTPException(
            503,
            "Invalid Studid affiliation response",
        )

    if not entity_matches(_identity(school), entity_id):
        return {
            "email_required": True,
            "message": (
                "Your institutional sign-in worked, but we couldn't "
                "match it to your selected institution. Please verify "
                "your selected institution's .edu email through OTP."
            ),
        }

    roles = sorted({
        role.casefold().split("@", 1)[0]
        for role in affiliations
    })

    conn.execute(
        """
        INSERT INTO Student_sso_evidence (
            student_id,
            school_id,
            entity_id,
            identifier,
            affiliations,
            expires_at
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (student_id) DO UPDATE SET
            school_id = EXCLUDED.school_id,
            entity_id = EXCLUDED.entity_id,
            identifier = EXCLUDED.identifier,
            affiliations = EXCLUDED.affiliations,
            expires_at = EXCLUDED.expires_at
        """,
        (
            student_id,
            school["school_id"],
            entity_id,
            identifier,
            roles,
            datetime.now(UTC) + timedelta(hours=1),
        ),
    )

    conn.execute(
        """
        UPDATE Students
        SET studid_entity_id = %s,
            studid_identifier = %s
        WHERE student_id = %s
        """,
        (entity_id, identifier, student_id),
    )

    if set(roles) & {"staff", "faculty", "employee"}:
        return require_manual(
            conn,
            student_id,
            "Institution returned staff/faculty affiliation",
        )

    if _pending_manual(conn, student_id):
        return _manual_result()

    # authIdentifier is account-linking data
    return {
        "email_required": True,
        "message": (
            "Your institutional sign-in worked, but we couldn't "
            "verify your email address. Please confirm your .edu "
            "email address through OTP verification."
        ),
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

    if (
        not isinstance(session, dict)
        or session.get("test") is not False
    ):
        raise HTTPException(
            400,
            "Test or invalid Studid sessions cannot verify enrollment",
        )

    try:
        with get_connection() as conn:
            _lock_account(conn, user)

            # recheck under the same account lock used by cancellation
            pending = conn.execute(
                """
                SELECT school_id
                FROM Studid_verifications
                WHERE student_id = %s
                  AND verification_id = %s
                  AND expires_at > CURRENT_TIMESTAMP
                FOR UPDATE
                """,
                (user["student_id"], verification_id),
            ).fetchone()

            if pending is None:
                raise HTTPException(
                    409,
                    "Verification cancelled, already used, or expired",
                )

            school = school_for(conn, user["student_id"])

            if pending["school_id"] != school["school_id"]:
                conn.execute(
                    """
                    DELETE FROM Studid_verifications
                    WHERE student_id = %s
                    """,
                    (user["student_id"],),
                )
                return {
                    "email_required": True,
                    "message": (
                        "Your institution changed. Verify your "
                        "current institution's email."
                    ),
                }

            result = _apply_studid(
                conn,
                user["student_id"],
                school,
                session,
            )

            conn.execute(
                """
                DELETE FROM Studid_verifications
                WHERE student_id = %s
                """,
                (user["student_id"],),
            )

            return result
    except UniqueViolation as exc:
        raise HTTPException(
            409,
            "This institutional identity is already linked "
            "to another account",
        ) from exc


def cancel_studid(
    user: dict[str, Any],
    verification_id: UUID,
) -> dict[str, bool]:
    with get_connection() as conn:
        _lock_account(conn, user)

        conn.execute(
            """
            DELETE FROM Studid_verifications
            WHERE student_id = %s
              AND verification_id = %s
            """,
            (user["student_id"], verification_id),
        )

    return {"cancelled": True}