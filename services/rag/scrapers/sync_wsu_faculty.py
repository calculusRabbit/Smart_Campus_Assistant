"""Preview synchronization of WSU School of Computing faculty with PostgreSQL."""

from database import get_connection
from services.rag.scrapers.scrape_wsu_faculty import fetch_faculty

SCHOOL_NAME = "College of Engineering"
DEPARTMENT_NAME = "School of Computing"
DEPARTMENT_CODE = "SOC"


def preview_sync():
    faculty = fetch_faculty()

    if not faculty:
        raise RuntimeError("No faculty records extracted; synchronization aborted.")

    emails = [person["email"] for person in faculty]

    if len(emails) != len(set(emails)):
        raise ValueError("Duplicate faculty emails detected.")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT school_id FROM schools WHERE school_name = %s",
                (SCHOOL_NAME,),
            )
            school = cursor.fetchone()

            department = None

            if school:
                cursor.execute(
                    """
                    SELECT department_id
                    FROM departments
                    WHERE school_id = %s AND department_name = %s
                    """,
                    (school["school_id"], DEPARTMENT_NAME),
                )
                department = cursor.fetchone()

            cursor.execute(
                """
                SELECT instructor_id, instructor_email
                FROM instructors
                WHERE instructor_email = ANY(%s)
                """,
                (emails,),
            )

            existing = {
                row["instructor_email"].lower(): row["instructor_id"]
                for row in cursor.fetchall()
            }

    print("\n=== WSU FACULTY SYNCHRONIZATION DRY RUN ===")
    print("Faculty records:", len(faculty))

    print("\nSchool:")
    print(
        "EXISTS" if school else "WOULD CREATE",
        SCHOOL_NAME,
    )

    print("\nDepartment:")
    print(
        "EXISTS" if department else "WOULD CREATE",
        DEPARTMENT_NAME,
    )

    print("\nFaculty:")
    for person in faculty:
        email = person["email"]

        if email in existing:
            status = f"EXISTS (ID {existing[email]})"
        else:
            status = "WOULD INSERT"

        print(f"{status}: {person['name']} <{email}>")

    print("\nNo database changes were made.")


def validate_faculty(faculty):
    """Validate faculty records before database operations."""
    if not faculty:
        raise ValueError("Cannot synchronize an empty faculty list.")

    emails = [person["email"].strip().lower() for person in faculty]

    if len(emails) != len(set(emails)):
        raise ValueError("Duplicate faculty emails detected.")

    for person in faculty:
        name = person["name"].strip()
        email = person["email"].strip().lower()
        name_parts = name.split(maxsplit=1)

        if len(name_parts) != 2:
            raise ValueError(f"Invalid faculty name: {name}")

        first_name, last_name = name_parts

        if len(first_name) >= 30 or len(last_name) >= 50:
            raise ValueError(f"Faculty name exceeds database limits: {name}")

        if not email.endswith("@wichita.edu") or " " in email:
            raise ValueError(f"Invalid WSU faculty email: {email}")


def apply_sync(faculty, commit=False):
    """Synchronize verified faculty using a single database transaction."""
    validate_faculty(faculty)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO schools (school_name)
                VALUES (%s)
                ON CONFLICT (school_name)
                DO UPDATE SET school_name = EXCLUDED.school_name
                RETURNING school_id
                """,
                (SCHOOL_NAME,),
            )
            school_id = cursor.fetchone()["school_id"]

            cursor.execute(
                """
                INSERT INTO departments (
                    school_id, department_name, department_code
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (school_id, department_name)
                DO UPDATE SET department_name = EXCLUDED.department_name
                RETURNING department_id
                """,
                (school_id, DEPARTMENT_NAME, DEPARTMENT_CODE),
            )
            department_id = cursor.fetchone()["department_id"]

            inserted = 0
            existing = 0

            for person in faculty:
                name_parts = person["name"].strip().split(maxsplit=1)

                if len(name_parts) != 2:
                    raise ValueError(
                        f"Cannot split faculty name: {person['name']}"
                    )

                first_name, last_name = name_parts
                email = person["email"].strip().lower()

                cursor.execute(
                    """
                    INSERT INTO instructors (
                        instructor_fname,
                        instructor_lnames,
                        instructor_department,
                        instructor_email
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (instructor_email) DO NOTHING
                    RETURNING instructor_id
                    """,
                    (first_name, last_name, department_id, email),
                )

                if cursor.fetchone():
                    inserted += 1
                else:
                    existing += 1

            if not commit:
                connection.rollback()

    return {
        "faculty_total": len(faculty),
        "inserted": inserted,
        "already_existing": existing,
        "committed": commit,
    }


if __name__ == "__main__":
    preview_sync()
