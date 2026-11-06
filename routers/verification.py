from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
)
from pydantic import BaseModel, Field

from auth import get_admin_user, get_current_user
from auth_models import AccountEmail
from database import get_connection
from services.institution_service import (
    get_institution,
    search_institutions,
)
from services.verification_service import (
    complete_otp,
    require_manual,
    school_for,
    start_otp,
)

router = APIRouter(tags=["verification"])

User = Annotated[dict, Depends(get_current_user)]
Admin = Annotated[dict, Depends(get_admin_user)]


@router.get("/institutions")
def institutions(q: str = Query(min_length=2, max_length=100)):
    return search_institutions(q.strip())


@router.get("/institutions/{scorecard_id}")
def institution(scorecard_id: int):
    return get_institution(scorecard_id)


@router.get("/verification")
def verification_status(user: User, response: Response):
    with get_connection() as conn:
        school = school_for(conn, user["student_id"])
        student = conn.execute(
            "SELECT account_status FROM Students WHERE student_id = %s",
            (user["student_id"],),
        ).fetchone()
        latest = conn.execute(
            """
            SELECT status, method, reason, admin_message
            FROM Authentications
            WHERE student_id = %s
            ORDER BY authentication_id DESC
            LIMIT 1
            """,
            (user["student_id"],),
        ).fetchone()

    response.headers["Cache-Control"] = "no-store"

    return {
        "school": school["school_name"],
        "account_status": student["account_status"],
        "verification": latest,
    }


class SendOtpRequest(BaseModel):
    email: AccountEmail


class CheckOtpRequest(BaseModel):
    code: str = Field(pattern=r"^[0-9]{6}$")


@router.post("/verification/otp/send")
def send_otp(request: SendOtpRequest, user: User):
    return start_otp(user, str(request.email))


@router.post("/verification/otp/check")
def check_otp(request: CheckOtpRequest, user: User):
    return complete_otp(user, request.code)


@router.post("/verification/manual")
def manual_verification(user: User):
    with get_connection() as conn:
        return require_manual(
            conn,
            user["student_id"],
            "manual verification requested",
        )


@router.post("/verification/manual/document")
async def upload_document(user: User, file: Annotated[UploadFile, File()]):
    content = await file.read(5 * 1024 * 1024 + 1)
    await file.close()

    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(400, "Maximum document size is 5 MiB")

    if not content.startswith(b"%PDF-"):
        raise HTTPException(400, "Upload a PDF enrollment document")

    with get_connection() as conn:
        require_manual(
            conn,
            user["student_id"],
            "enrollment document submitted",
        )
        review = conn.execute(
            """
            SELECT authentication_id
            FROM Authentications
            WHERE student_id = %s AND status = 'pending'
            ORDER BY authentication_id DESC
            LIMIT 1
            """,
            (user["student_id"],),
        ).fetchone()

        conn.execute(
            """
            INSERT INTO Authentication_documents (
                authentication_id, content
            )
            VALUES (%s, %s)
            ON CONFLICT (authentication_id) DO UPDATE
            SET content = EXCLUDED.content
            """,
            (review["authentication_id"], content),
        )

    return {"message": "Document submitted for manual review"}


@router.get("/admin/verifications")
def pending_verifications(admin: Admin, response: Response):
    response.headers["Cache-Control"] = "no-store"

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT
                a.authentication_id,
                s.first_name,
                s.last_names,
                a.reason,
                a.submitted_time,
                sc.school_name,
                d.authentication_id IS NOT NULL AS has_document
            FROM Authentications a
            JOIN Students s USING (student_id)
            JOIN Users u USING (username)
            JOIN Enrolments e
              ON e.student_id = s.student_id AND e.is_primary
            JOIN Schools sc USING (school_id)
            LEFT JOIN Authentication_documents d
              ON d.authentication_id = a.authentication_id
            WHERE a.status = 'pending'
              AND a.method = 'manual'
              AND u.deleted_timestamp IS NULL
            ORDER BY a.submitted_time
            """
        ).fetchall()


@router.get("/admin/verifications/{authentication_id}/document")
def get_document(authentication_id: int, admin: Admin):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT content
            FROM Authentication_documents
            WHERE authentication_id = %s
            """,
            (authentication_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(404, "Document not found")

    return Response(
        content=bytes(row["content"]),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": 'attachment; filename="enrollment.pdf"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


class ReviewRequest(BaseModel):
    approved: bool
    message: str = Field(default="", max_length=200)


@router.post("/admin/verifications/{authentication_id}")
def review_verification(
    authentication_id: int,
    request: ReviewRequest,
    admin: Admin,
):
    with get_connection() as conn:
        review = conn.execute(
            """
            SELECT a.student_id
            FROM Authentications a
            JOIN Students s USING (student_id)
            JOIN Users u USING (username)
            WHERE a.authentication_id = %s
              AND a.status = 'pending'
              AND a.method = 'manual'
              AND u.deleted_timestamp IS NULL
            FOR UPDATE OF u
            """,
            (authentication_id,),
        ).fetchone()

        if review is None:
            raise HTTPException(404, "Pending verification not found")

        updated = conn.execute(
            """
            UPDATE Authentications
            SET status = %s,
                reviewed_time = CURRENT_TIMESTAMP,
                admin_message = %s
            WHERE authentication_id = %s AND status = 'pending'
            RETURNING student_id
            """,
            (
                "approved" if request.approved else "denied",
                f"{admin['username']}: {request.message}"[:250],
                authentication_id,
            ),
        ).fetchone()

        if updated is None:
            raise HTTPException(409, "Verification already reviewed")

        conn.execute(
            """
            UPDATE Students
            SET account_status = %s
            WHERE student_id = %s
            """,
            (
                "open" if request.approved else "denied",
                review["student_id"],
            ),
        )

        conn.execute(
            """
            DELETE FROM Authentication_documents
            WHERE authentication_id = %s
            """,
            (authentication_id,),
        )

    return {"message": "Review saved; uploaded document deleted"}
