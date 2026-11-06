from uuid import UUID

from fastapi import HTTPException
from psycopg.errors import UniqueViolation

from auth import (
    ACCESS_TOKEN_MINUTES,
    DUMMY_HASH,
    create_session,
    hash_password,
    public_user,
    verify_password,
)
from auth_models import LoginRequest, SignupRequest
from database import get_connection
from services.institution_service import get_institution


class AuthService:
    # student signup and login

    def signup(self, request: SignupRequest) -> dict:
        institution = get_institution(request.scorecard_id)
        programs = {program["value"]: program["label"] for program in institution["programs"]}

        if request.program and request.program not in programs:
            raise HTTPException(
                status_code=400,
                detail="Choose a program from this institution's list",
            )

        password_hash = hash_password(request.password.get_secret_value())
        interests = [interest.lower().strip() for interest in request.interests]

        try:
            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO Users (username, account_type, hashed_password)
                    VALUES (%s, 'student', %s)""",
                    (request.username, password_hash),
                )

                conn.execute(
                    """
                    INSERT INTO Students (username, first_name, last_names,
                    email, dob, zipcode, account_status, created_at, interests)
                    VALUES (%s, %s, %s, %s, %s, %s, 'pending', CURRENT_TIMESTAMP,
                    %s)""",
                    (
                        request.username,
                        request.first_name,
                        request.last_name,
                        str(request.email).lower(),
                        request.dob,
                        request.zipcode,
                        interests,
                    ),
                )

                student = conn.execute(
                    "SELECT student_id FROM Students WHERE username = %s",
                    (request.username,),
                ).fetchone()

                conn.execute(
                    "UPDATE Schools SET scorecard_id=%s "
                    "WHERE school_name=%s AND scorecard_id IS NULL",
                    (institution["id"], institution["name"]),
                )

                school = conn.execute(
                    """
                    INSERT INTO Schools (school_name, scorecard_id) VALUES (%s, %s)
                    ON CONFLICT (scorecard_id) DO UPDATE
                    SET school_name = EXCLUDED.school_name
                    RETURNING school_id""",
                    (institution["name"], institution["id"]),
                ).fetchone()

                if student is None or school is None:
                    raise HTTPException(
                        500,
                        "Account records could not be created",
                    )

                conn.execute(
                    "INSERT INTO Enrolments (student_id, school_id, majors) VALUES (%s, %s, %s)",
                    (
                        student["student_id"],
                        school["school_id"],
                        [programs[request.program]] if request.program else [],
                    ),
                )

        except UniqueViolation as exc:
            raise HTTPException(
                status_code=409,
                detail="account details are unavailable",
            ) from exc

        return {"message": "account created, student verification is required"}

    def login(self, request: LoginRequest) -> dict:
        with get_connection() as conn:
            user = conn.execute(
                """
                SELECT
                    u.username, u.hashed_password, u.deleted_timestamp,
                    u.self_deactivated, s.student_id, s.first_name, s.last_names, s.account_status
                FROM Users AS u
                JOIN Students AS s ON s.username = u.username
                WHERE lower(s.email) = lower(%s) AND u.account_type = 'student'
                FOR UPDATE OF u, s
                """,
                (str(request.email),),
            ).fetchone()

            stored_hash = user["hashed_password"] if user else DUMMY_HASH
            valid = verify_password(request.password.get_secret_value(), stored_hash)

            if not valid or user is None:
                raise HTTPException(
                    status_code=401,
                    detail="incorrect email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            if user["deleted_timestamp"] is not None:
                if not user["self_deactivated"]:
                    raise HTTPException(
                        status_code=403,
                        detail="This account cannot be restored through login",
                    )

                conn.execute(
                    """
                    UPDATE Users
                    SET deleted_timestamp = NULL, self_deactivated = FALSE
                    WHERE username = %s
                    """,
                    (user["username"],),
                )
                conn.execute(
                    """
                    UPDATE Students SET deleted_timestamp = NULL
                    WHERE student_id = %s
                    """,
                    (user["student_id"],),
                )

            if user["account_status"] == "closed":
                raise HTTPException(
                    status_code=403,
                    detail="This account is closed",
                )

            token = create_session(conn, user["username"])

        return {
            "access_token": token,
            # auth label, not a password/secret
            "token_type": "bearer",  # nosec B105
            "expires_in": ACCESS_TOKEN_MINUTES * 60,
            "user": public_user(user),
        }

    def logout(self, session_id: UUID, username: str) -> None:
        # revoke login without affecting user's other sessions, if any
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE Auth_sessions SET revoked_at = CURRENT_TIMESTAMP
                WHERE session_id = %s AND username = %s
                """,
                (session_id, username),
            )
