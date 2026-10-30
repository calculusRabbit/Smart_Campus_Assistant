from psycopg.errors import UniqueViolation
from fastapi import HTTPException

from auth import (
    DUMMY_HASH,
    PASSWORDS,
    create_session,
    hash_password,
    public_user
)
from auth_models import LoginRequest, SignupRequest
from database import get_connection


class AuthService:
    #student signup and login

    def signup(self, request: SignupRequest) -> dict:
        password_hash = hash_password(request.password.get_secret_value())
        interests = [interest.lower().strip() for interest in request.interests]

        try:
            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO users (username, account_type, hashed_password)
                    VALUES (%s, 'student', %s)""",
                    (request.username, password_hash))

                conn.execute(
                    """
                    INSERT INTO students (username, first_name, last_names,
                    email, dob, zipcode, account_status, created_at, interests)
                    VALUES (%s, %s, %s, %s, %s, %s, 'pending', CURRENT_TIMESTAMP,
                    %s)""",
                    (request.username, request.first_name, request.last_name,
                        str(request.email).lower(), request.dob, request.zipcode,
                        interests),
                )
        except UniqueViolation as exc:
            raise HTTPException(
                status_code=409,
                detail="account details are unavailable",
            ) from exc

        return {
            "message": "account created; student verification is required"
        }

    def login(self, request: LoginRequest) -> dict:
        with get_connection() as conn:
            user = conn.execute(
                """
                SELECT u.username, u.hashed_password,
                    s.student_id, s.first_name, s.last_names, s.account_status
                FROM users AS u
                JOIN students AS s ON s.username = u.username
                WHERE lower(s.email) = lower(%s)
                  AND u.account_type = 'student'
                  AND u.deleted_timestamp IS NULL
                  AND s.deleted_timestamp IS NULL
                  AND s.account_status <> 'closed'
                """,
                (str(request.email),)).fetchone()

            stored_hash = (user["hashed_password"] if user else DUMMY_HASH)
            valid, upgraded_hash = PASSWORDS.verify_and_update(
                request.password.get_secret_value(), stored_hash)

            if not valid or user is None:
                raise HTTPException(
                    status_code=401,
                    detail="incorrect email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            if upgraded_hash is not None:
                conn.execute(
                    """
                    UPDATE users SET hashed_password = %s
                    WHERE username = %s""",
                    (upgraded_hash, user["username"]),
                )

            token = create_session(conn, user["username"])

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 15 * 60,
            "user": public_user(user),
        }