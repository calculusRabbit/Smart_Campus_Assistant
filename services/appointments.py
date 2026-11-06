from datetime import date, datetime, time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database import LOCAL_TIMEZONE, get_connection

router = APIRouter(tags=["Appointments"])


class AppointmentRequest(BaseModel):
    student_id: int = Field(gt=0)
    instructor_id: int = Field(gt=0)
    appointment_date: date
    appointment_time: time
    reason: str = Field(min_length=1, max_length=300)


@router.post("/appointments", status_code=201)
def create_appointment(request: AppointmentRequest) -> dict[str, Any]:
    """Submit a pending professor appointment request."""

    reason = request.reason.strip()

    if not reason:
        raise HTTPException(
            status_code=422,
            detail="Please provide a reason for your appointment.",
        )

    requested_datetime = datetime.combine(
        request.appointment_date,
        request.appointment_time,
        tzinfo=LOCAL_TIMEZONE,
    )

    if requested_datetime <= datetime.now(LOCAL_TIMEZONE):
        raise HTTPException(
            status_code=400,
            detail="Please select a future appointment date and time.",
        )

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM students WHERE student_id = %s",
                (request.student_id,),
            )
            if cursor.fetchone() is None:
                raise HTTPException(
                    status_code=404,
                    detail="Student not found.",
                )

            cursor.execute(
                "SELECT 1 FROM instructors WHERE instructor_id = %s",
                (request.instructor_id,),
            )
            if cursor.fetchone() is None:
                raise HTTPException(
                    status_code=404,
                    detail="Professor not found.",
                )

            cursor.execute(
                """
                SELECT appointment_id
                FROM appointments
                WHERE student_id = %s
                  AND instructor_id = %s
                  AND appointment_date = %s
                  AND appointment_time = %s
                  AND status IN ('pending', 'approved')
                """,
                (
                    request.student_id,
                    request.instructor_id,
                    request.appointment_date,
                    request.appointment_time,
                ),
            )

            if cursor.fetchone() is not None:
                raise HTTPException(
                    status_code=409,
                    detail="You already requested this appointment.",
                )

            cursor.execute(
                """
                INSERT INTO appointments (
                    student_id,
                    instructor_id,
                    appointment_date,
                    appointment_time,
                    reason
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING appointment_id, status
                """,
                (
                    request.student_id,
                    request.instructor_id,
                    request.appointment_date,
                    request.appointment_time,
                    reason,
                ),
            )

            result = cursor.fetchone()

    if result is None:
        raise HTTPException(
            status_code=500,
            detail="Could not create appointment request.",
        )

    return {
        "message": "Appointment request submitted successfully.",
        "appointment_id": result["appointment_id"],
        "student_id": request.student_id,
        "instructor_id": request.instructor_id,
        "appointment_date": request.appointment_date.isoformat(),
        "appointment_time": request.appointment_time.isoformat(),
        "status": result["status"],
    }


@router.get("/students/{student_id}/appointments")
def get_student_appointments(student_id: int) -> dict[str, Any]:
    """List appointment requests for a student (prototype only)."""
    if student_id <= 0:
        raise HTTPException(status_code=422, detail="Invalid student ID.")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    a.appointment_id,
                    a.student_id,
                    a.instructor_id,
                    i.instructor_fname || ' ' || i.instructor_lnames
                        AS professor_name,
                    a.appointment_date,
                    a.appointment_time,
                    a.reason,
                    a.status,
                    a.created_at
                FROM appointments AS a
                JOIN instructors AS i
                  ON i.instructor_id = a.instructor_id
                WHERE a.student_id = %s
                ORDER BY a.appointment_date DESC,
                         a.appointment_time DESC,
                         a.appointment_id DESC
                """,
                (student_id,),
            )
            appointments = cursor.fetchall()

    return {"appointments": appointments}
