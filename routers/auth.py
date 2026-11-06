from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, SecretStr

from auth import DUMMY_HASH, create_session, get_current_user, public_user, verify_password
from auth_models import (
    DeactivateRequest,
    LoginRequest,
    SignupRequest,
)
from database import get_connection
from services.auth_service import AuthService
from services.captcha_service import check_captcha, create_captcha

router = APIRouter(tags=["authentication"])
service = AuthService()


@router.post("/signup", status_code=201)
def signup(request: SignupRequest, response: Response):
    check_captcha(request.captcha, "signup")
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
def logout(user: Annotated[dict, Depends(get_current_user)]):
    service.logout(user["session_id"], user["username"])
    return Response(status_code=204, headers={"Cache-Control": "no-store"})


#delete user - non-permanent (soft-delete)
@router.delete("/me", status_code=204)
def delete_me(
    request: DeactivateRequest,
    user: Annotated[dict, Depends(get_current_user)],
):
    check_captcha(request.captcha, "deactivate")
    with get_connection() as conn:
        account = conn.execute(
            """
            SELECT hashed_password FROM Users
            WHERE username = %s AND deleted_timestamp IS NULL
            FOR UPDATE""", (user["username"],)
        ).fetchone()

        if account is None or not verify_password(
            request.password.get_secret_value(),account["hashed_password"],
        ):
            raise HTTPException(
                status_code=403,
                detail="password confirmation failed",
            )

        conn.execute(
            """
            UPDATE Users
            SET deleted_timestamp = CURRENT_TIMESTAMP, self_deactivated = TRUE
            WHERE username = %s
            """,
            (user["username"],),
        )
        conn.execute(
            """UPDATE Students SET deleted_timestamp = CURRENT_TIMESTAMP
            WHERE student_id = %s""", (user["student_id"],)
        )
        conn.execute(
            """UPDATE auth_sessions SET revoked_at = CURRENT_TIMESTAMP
            WHERE username = %s AND revoked_at IS NULL """, (user["username"],),
        )

    return Response(
        status_code=204,
        headers={"Cache-Control": "no-store"},
    )

@router.get("/captcha/{action}")
def captcha(action: str, response: Response):
    if action not in {"signup", "deactivate"}:
        raise HTTPException(400, "Unknown CAPTCHA action")

    response.headers["Cache-Control"] = "no-store"
    return create_captcha(action)

class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=30)
    password: SecretStr = Field(max_length=128)



@router.post("/admin/login")
def admin_login(request: AdminLoginRequest, response: Response):
    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT username, hashed_password
            FROM Users
            WHERE username = %s
              AND account_type = 'admin'
              AND deleted_timestamp IS NULL
            """,
            (request.username,),
        ).fetchone()

        stored_hash = user["hashed_password"] if user else DUMMY_HASH
        valid = verify_password(
            request.password.get_secret_value(),
            stored_hash
        )

        if not valid or user is None:
            raise HTTPException(401, "Incorrect administrator credentials")

        token = create_session(conn, user["username"])

    response.headers["Cache-Control"] = "no-store"
    return {
        "access_token": token,
        "token_type": "bearer",
    }