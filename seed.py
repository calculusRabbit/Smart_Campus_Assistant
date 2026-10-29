import os
import runpy
import sys

from psycopg.conninfo import make_conninfo

# fills the database with fake data, it runs the dummy data script
# the script deletes everything in the tables first so it only runs for development and test


def seed_database():
    if os.environ.get("APP_ENV") not in {"development", "test"}:
        raise SystemExit("Refusing to reset data, set APP_ENV to development or test")

    dsn = make_conninfo(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )

    sys.argv = ["dummy_data_populator_v0.5.0.py", "--dsn", dsn, "--reset"]
    runpy.run_path("dummy_data_populator_v0.5.0.py", run_name="__main__")


if __name__ == "__main__":
    seed_database()
