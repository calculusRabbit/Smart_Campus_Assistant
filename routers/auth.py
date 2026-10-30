from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from auth import get_current_user, public_user, verify_password

from auth_models import (
    LoginRequest,
    ReauthenticateRequest,
    SignupRequest,
)

from database import get_connection

from services.auth_service import AuthService


router = APIRouter(tags=["authentication"])
service = AuthService()


@router.post("/signup", status_code=201)
def signup(request: SignupRequest, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return service.signup(request)


@router.post("/login")
def login(request: LoginRequest, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return service.login(request)


@router.get("/me")
def me(
    response: Response,
    user: Annotated[dict, Depends(get_current_user)],
):
    response.headers["Cache-Control"] = "no-store"
    return public_user(user)


@router.post("/logout", status_code=204)
def logout(
    user: Annotated[dict, Depends(get_current_user)],
):
    with get_connection() as conn:
        conn.execute(
            """ UPDATE auth_sessions SET revoked_at = CURRENT_TIMESTAMP
            WHERE session_id = %s AND username = %s""",
            (user["session_id"], user["username"]))

    return Response(
        status_code=204,
        headers={"Cache-Control": "no-store"})


@router.delete("/me", status_code=204)
def delete_me(
    request: ReauthenticateRequest,
    user: Annotated[dict, Depends(get_current_user)],
):
    with get_connection() as conn:
        account = conn.execute(
            """
            SELECT hashed_password FROM users
            WHERE username = %s AND deleted_timestamp IS NULL
            FOR UPDATE""", (user["username"],),
        ).fetchone()

        if account is None or not verify_password(
            request.password.get_secret_value(),
            account["hashed_password"],
        ):
            raise HTTPException(
                status_code=401,
                detail="Reauthentication failed",
            )

        conn.execute(
            """
            UPDATE users SET deleted_timestamp = CURRENT_TIMESTAMP
            WHERE username = %s""", (user["username"],),
        )
        conn.execute(
            """UPDATE students
            SET deleted_timestamp = CURRENT_TIMESTAMP, account_status = 'closed'
            WHERE student_id = %s""", (user["student_id"],),
        )
        conn.execute(
            """UPDATE auth_sessions
            SET revoked_at = CURRENT_TIMESTAMP
            WHERE username = %s AND revoked_at IS NULL """,
            (user["username"],),
        )

    return Response(
        status_code=204,
        headers={"Cache-Control": "no-store"},
    )