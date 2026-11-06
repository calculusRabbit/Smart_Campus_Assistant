"""Preview official WSU dining-hours synchronization."""

from typing import Any

from database import get_connection
from services.rag.scrapers.scrape_wsu_dining_hours import fetch_hours

RSC_AREA = "Official WSU dining area: Rhatigan Student Center"


def restaurant_location_marker(name: str) -> str:
    """Identify an RSC restaurant's individual schedule location."""
    return f"{RSC_AREA} | Restaurant: {name}"


def preview_hours_sync() -> list[dict[str, Any]]:
    """Compare published dining hours with PostgreSQL without writing."""
    schedules = fetch_hours()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT d.dining_id, d.dining_name, d.location_id,
                       l.location_notes, l.open_hours
                FROM dining AS d
                JOIN locations AS l
                  ON l.location_id = d.location_id
                WHERE l.location_notes = %s
                   OR l.location_notes LIKE %s
                """,
                (RSC_AREA, RSC_AREA + " | Restaurant: %"),
            )
            rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT location_notes
                FROM locations
                WHERE location_notes LIKE %s
                """,
                (RSC_AREA + " | Restaurant: %",),
            )
            existing_markers = {row["location_notes"] for row in cursor.fetchall()}

    results = []

    for name, schedule in schedules.items():
        matches = [
            row
            for row in rows
            if row["dining_name"] == name
            and row["location_notes"]
            in (
                RSC_AREA,
                restaurant_location_marker(name),
            )
        ]

        if len(matches) != 1:
            raise ValueError(
                f"Expected exactly one RSC dining record for {name}, found {len(matches)}"
            )

        marker = restaurant_location_marker(name)

        results.append(
            {
                "dining_id": matches[0]["dining_id"],
                "restaurant": name,
                "current_location_id": matches[0]["location_id"],
                "schedule": schedule,
                "needs_new_location": marker not in existing_markers,
            }
        )

    if len(results) != 5:
        raise ValueError("Expected five verified RSC restaurant schedules")

    return results


def upsert_restaurant_hours(cursor: Any, record: dict[str, Any]) -> tuple[int, int]:
    """Create or update an individual restaurant location and its verified hours."""
    from psycopg.types.json import Jsonb

    marker = restaurant_location_marker(record["restaurant"])

    cursor.execute(
        """
        SELECT location_id, open_hours
        FROM locations
        WHERE location_notes = %s
        """,
        (marker,),
    )
    existing = cursor.fetchone()

    if existing is None:
        cursor.execute(
            """
            INSERT INTO locations (
                location_id, location_notes, on_campus, open_hours
            )
            VALUES (
                nextval('public.locations_location_id_seq'),
                %s, TRUE, %s
            )
            RETURNING location_id
            """,
            (marker, Jsonb(record["schedule"])),
        )
        location_id = cursor.fetchone()["location_id"]
        created = 1
        updated = 0
    else:
        location_id = existing["location_id"]
        created = 0
        updated = int(existing["open_hours"] != record["schedule"])

        if updated:
            cursor.execute(
                """
                UPDATE locations
                SET open_hours = %s
                WHERE location_id = %s
                """,
                (Jsonb(record["schedule"]), location_id),
            )

    cursor.execute(
        """
        UPDATE dining
        SET location_id = %s
        WHERE dining_id = %s
        """,
        (location_id, record["dining_id"]),
    )

    return created, updated


def apply_hours_sync(commit: bool = False) -> dict[str, int | bool]:
    """Synchronize published WSU dining hours with explicit commit control."""
    records = preview_hours_sync()

    if not commit:
        return {
            "restaurants": len(records),
            "would_create_locations": sum(record["needs_new_location"] for record in records),
            "committed": False,
        }

    created = 0
    updated = 0

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT last_value, is_called
                FROM public.locations_location_id_seq
                """
            )
            state = cursor.fetchone()
            next_id = state["last_value"] + 1 if state["is_called"] else state["last_value"]

            cursor.execute("SELECT COALESCE(MAX(location_id), 0) AS maximum FROM locations")
            if next_id <= cursor.fetchone()["maximum"]:
                raise ValueError("Location ID sequence is behind existing records")

            for record in records:
                new_count, update_count = upsert_restaurant_hours(cursor, record)
                created += new_count
                updated += update_count

        connection.commit()

    return {
        "restaurants": len(records),
        "created_locations": created,
        "updated_schedules": updated,
        "committed": True,
    }
