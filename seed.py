"""Seed the Smart Campus database with synthetic demo data."""

from database import (
    insert_sample_courses,
    insert_sample_deadlines,
    insert_sample_dining,
    insert_sample_events,
    insert_sample_professors,
)


def seed_database():
    """Populate the database with synthetic data for development and testing."""
    insert_sample_events()
    insert_sample_deadlines()
    insert_sample_courses()
    insert_sample_professors()
    insert_sample_dining()

    print("Smart Campus database seeded successfully.")


if __name__ == "__main__":
    seed_database()
