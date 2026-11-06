"""Validate and preview official WSU dining synchronization."""

from typing import Any

from database import get_connection
from services.rag.scrapers.scrape_wsu_dining import DINING_URL


def location_marker(area: str) -> str:
    """Create a recognizable marker for an official WSU dining area."""
    return f"Official WSU dining area: {area}"


def validate_dining(records: list[dict[str, Any]]) -> None:
    """Validate dining records before any database operation."""
    if not records:
        raise ValueError("No dining records supplied")

    seen = set()

    for record in records:
        name = record["dining_name"]
        area = record["dining_location"]
        key = (name.casefold(), area.casefold())

        if not name.strip() or len(name) > 75:
            raise ValueError(f"Invalid dining name: {name!r}")

        if not area.strip() or len(location_marker(area)) >= 250:
            raise ValueError(f"Invalid dining area: {area!r}")

        if record["source_url"] != DINING_URL:
            raise ValueError(f"Unexpected dining source: {name}")

        if not record["verified"]:
            raise ValueError(f"Unverified dining record: {name}")

        if key in seen:
            raise ValueError(f"Duplicate dining record: {name} at {area}")

        seen.add(key)


def preview_sync(records: list[dict[str, Any]]) -> dict[str, int]:
    """Compare official dining records with PostgreSQL without writing."""
    validate_dining(records)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT location_id, location_notes
                FROM locations
                WHERE location_notes LIKE 'Official WSU dining area: %'
            """)

            existing_areas = {
                row["location_notes"]: row["location_id"] for row in cursor.fetchall()
            }

            cursor.execute("""
                SELECT d.dining_name, l.location_notes
                FROM dining AS d
                JOIN locations AS l
                  ON d.location_id = l.location_id
                WHERE l.location_notes LIKE 'Official WSU dining area: %'
            """)

            existing_dining = {
                (
                    row["dining_name"].casefold(),
                    row["location_notes"],
                )
                for row in cursor.fetchall()
            }

    markers = {location_marker(record["dining_location"]) for record in records}

    new_locations = sum(marker not in existing_areas for marker in markers)

    already_existing = sum(
        (
            record["dining_name"].casefold(),
            location_marker(record["dining_location"]),
        )
        in existing_dining
        for record in records
    )

    return {
        "dining_total": len(records),
        "would_insert_dining": len(records) - already_existing,
        "already_existing_dining": already_existing,
        "would_insert_locations": new_locations,
        "already_existing_locations": len(markers) - new_locations,
    }


def apply_sync(
    records: list[dict[str, Any]],
    commit: bool = False,
) -> dict[str, int | bool]:
    """Synchronize official dining data with explicit commit control."""
    preview = preview_sync(records)

    if not commit:
        return {
            "dining_total": preview["dining_total"],
            "inserted_dining": preview["would_insert_dining"],
            "inserted_locations": preview["would_insert_locations"],
            "committed": False,
        }

    inserted_locations = 0
    inserted_dining = 0

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT last_value, is_called
                FROM public.locations_location_id_seq
            """)
            location_sequence = cursor.fetchone()
            next_location_id = (
                location_sequence["last_value"] + 1
                if location_sequence["is_called"]
                else location_sequence["last_value"]
            )

            cursor.execute("""
                SELECT COALESCE(MAX(location_id), 0) AS highest_id
                FROM locations
            """)
            if next_location_id <= cursor.fetchone()["highest_id"]:
                raise ValueError("Location ID sequence is behind existing records")

            cursor.execute("""
                SELECT last_value, is_called
                FROM public.dining_dining_id_seq
            """)
            dining_sequence = cursor.fetchone()
            next_dining_id = (
                dining_sequence["last_value"] + 1
                if dining_sequence["is_called"]
                else dining_sequence["last_value"]
            )

            cursor.execute("""
                SELECT COALESCE(MAX(dining_id), 0) AS highest_id
                FROM dining
            """)
            if next_dining_id <= cursor.fetchone()["highest_id"]:
                raise ValueError("Dining ID sequence is behind existing records")

            cursor.execute("""
                SELECT location_id, location_notes
                FROM locations
                WHERE location_notes LIKE 'Official WSU dining area: %'
            """)
            locations = {row["location_notes"]: row["location_id"] for row in cursor.fetchall()}

            for record in records:
                marker = location_marker(record["dining_location"])

                if marker not in locations:
                    cursor.execute(
                        """
                        INSERT INTO locations (
                            location_id,
                            location_notes,
                            on_campus
                        )
                        VALUES (
                            nextval('public.locations_location_id_seq'),
                            %s,
                            %s
                        )
                        RETURNING location_id
                        """,
                        (
                            marker,
                            True,
                        ),
                    )
                    locations[marker] = cursor.fetchone()["location_id"]
                    inserted_locations += 1

            cursor.execute("""
                SELECT d.dining_name, d.location_id
                FROM dining AS d
                JOIN locations AS l
                  ON d.location_id = l.location_id
                WHERE l.location_notes LIKE 'Official WSU dining area: %'
            """)
            existing = {
                (row["dining_name"].casefold(), row["location_id"]) for row in cursor.fetchall()
            }

            for record in records:
                marker = location_marker(record["dining_location"])
                location_id = locations[marker]
                key = (record["dining_name"].casefold(), location_id)

                if key in existing:
                    continue

                cursor.execute(
                    """
                    INSERT INTO dining (
                        dining_id,
                        dining_name,
                        location_id,
                        cuisine,
                        reservations,
                        event_status
                    )
                    VALUES (
                        nextval('public.dining_dining_id_seq'),
                        %s, %s, %s, NULL, NULL
                    )
                    RETURNING dining_id
                    """,
                    (record["dining_name"], location_id, record["cuisine"]),
                )
                cursor.fetchone()
                existing.add(key)
                inserted_dining += 1

        connection.commit()

    return {
        "dining_total": len(records),
        "inserted_dining": inserted_dining,
        "inserted_locations": inserted_locations,
        "committed": True,
    }
