import os
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID, uuid4

import jwt

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from database import get_connection


JWT_KEY = os.environ.get("JWT_KEY", "")
if len(JWT_KEY.encode("utf-8")) < 32:
    raise RuntimeError("JWT_KEY isn't set to a generated secret")

JWT_ISSUER = "smart-campus-assistant"
JWT_AUDIENCE = "smart-campus-api"
ACCESS_TOKEN_MINUTES = 15

PASSWORDS = PasswordHash((Argon2Hasher(), BcryptHasher()))
DUMMY_HASH = PASSWORDS.hash("not-a-real-account-password")
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return PASSWORDS.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    return PASSWORDS.verify(password, stored_hash)


def create_session(conn, username: str) -> str:
    #create session within the caller's transaction and return JWT
    session_id = uuid4()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=ACCESS_TOKEN_MINUTES)

    conn.execute("INSERT INTO Auth_sessions (session_id, username, expires_at) "
                 "VALUES (%s,%s,%s)", (session_id, username, expires_at),
    )

    return jwt.encode(
        {
            "sub": username,
            "sid": str(session_id),
            "type": "access",
            "iss": JWT_ISSUER,
            "aud": JWT_AUDIENCE,
            "iat": now,
            "exp": expires_at,
        },
        JWT_KEY,
        algorithm="HS256",
    )


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer),
    ],
) -> dict:
    #validate the JWT, active session, and current student account
    unauthorized = HTTPException(
        status_code=401,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        claims = jwt.decode(
            credentials.credentials,
            JWT_KEY,
            algorithms=["HS256"],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
            options={
                "require": ["sub", "sid", "type", "iss", "aud", "iat", "exp"]
            },
        )

        if claims["type"] != "access" or not isinstance(claims["sub"], str):
            raise jwt.InvalidTokenError("invalid token claims")

        session_id = UUID(claims["sid"])
    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
        AttributeError,
    ) as exc:
        raise unauthorized from exc

    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT
                u.username, u.account_type,
                s.student_id, s.first_name, s.last_names, s.account_status,
                a.session_id
            FROM auth_sessions AS a
            JOIN users AS u ON u.username = a.username
            JOIN students AS s ON s.username = u.username
            WHERE a.session_id = %s
              AND u.username = %s
              AND a.revoked_at IS NULL
              AND a.expires_at > CURRENT_TIMESTAMP
              AND u.account_type = 'student'
              AND u.deleted_timestamp IS NULL AND s.deleted_timestamp IS NULL
              AND s.account_status <> 'closed'
            """,
            (session_id, claims["sub"]),
        ).fetchone()

    if user is None:
        raise unauthorized

    return user


def require_student_owner(
    student_id: int,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    #only allow to the student's own data
    if user["student_id"] != student_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return user


def require_open_student(
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    # require student verification
    if user["account_status"] != "open":
        raise HTTPException(
            status_code=403,
            detail="Verified student account required",
        )
    return user


def public_user(user: dict) -> dict:
    #return exactly the fields needed by the frontend
    return {
        "id": user["student_id"],
        "username": user["username"],
        "name": f"{user['first_name']} {user['last_names']}",
        "account_status": user["account_status"],
    }