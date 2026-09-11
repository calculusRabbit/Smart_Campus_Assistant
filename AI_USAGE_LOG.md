# AI Usage & Verification Log

**Project Name:** Smart Campus Assistant Platform  
**Team Name:** The Three Musketeer
**Team Member:** Teng Fai Leong  
**Role:** Backend Developer / AI Integration  

---

## Overview & AI Policy Compliance Statement

This repository utilizes Generative AI tools, primarily ChatGPT, in compliance with course AI guidelines. AI tools were used to assist with backend development, PostgreSQL integration, database migrations, Docker configuration, automated testing, CI/CD configuration, recommendation logic refactoring, debugging, and documentation.

All AI-assisted code was manually reviewed before being added to the project. Generated code and configuration were modified when necessary to match the existing project architecture. Changes were validated using Ruff static analysis, pytest automated tests, PostgreSQL migration and rollback testing, Docker execution, browser/API testing, and GitHub Actions CI.

---

## Entry 1: Prototype 1 — PostgreSQL Database Migration & Rollback

* **Date:** September 2026
* **Team Member:** Teng Fai Leong
* **Tool Used:** ChatGPT
* **Associated Git Issue:** `#XX` — Implement Prototype 1 backend foundation and PostgreSQL data layer
* **Associated Feature Branch:** `backend-testing`

### Exact Prompt Submitted:

> Original migration prompt was submitted in an earlier ChatGPT conversation. The exact wording should be copied from that conversation before final submission.

### AI Output Summary & Code Generated:

ChatGPT assisted with designing SQL migration scripts for the Prototype 1 PostgreSQL database.

The migration created the following tables:

- `events`
- `courses`
- `professors`
- `dining`
- `deadlines`
- `student_interests`

Two migration files were created:

- `migrations/001_initial_up.sql`
- `migrations/001_initial_down.sql`

The `up` migration creates the Prototype 1 schema, while the `down` migration provides rollback functionality.

### Human Review, Refactoring & Modifications Made:

- Reviewed all table names, columns, primary keys, and data types.
- Confirmed that the migration matched the existing FastAPI database functions.
- Used a separate PostgreSQL test database to avoid modifying the active development database.
- Verified that all six required tables were created.
- Reviewed the rollback file to confirm that all Prototype 1 tables were removed cleanly.

### Verification & Testing Method:

- Executed `001_initial_up.sql` against the `smart_campus_test` PostgreSQL database.
- Verified that all six expected tables were created.
- Executed `001_initial_down.sql`.
- Verified that the tables were successfully removed.
- Migration also executes as part of the GitHub Actions CI workflow.

---

## Entry 2: Prototype 1 — Docker and Development Environment

* **Date:** September 2026
* **Team Member:** Teng Fai Leong
* **Tool Used:** ChatGPT
* **Associated Git Issue:** `#XX` — Implement Prototype 1 backend foundation and PostgreSQL data layer
* **Associated Feature Branch:** `backend-testing`

### Exact Prompt Submitted:

> "actually what is docker what how can i use docker"

### AI Output Summary & Code Generated:

ChatGPT assisted with creating and explaining the Docker development environment for the Smart Campus Assistant.

The AI-assisted configuration included:

- `Dockerfile`
- `docker-compose.yml`
- `.env.example`
- `requirements.txt`

The Docker Compose environment contains separate services for:

1. FastAPI backend
2. PostgreSQL database

### Human Review, Refactoring & Modifications Made:

- Reviewed Docker ports and service configuration.
- Configured PostgreSQL environment variables for development.
- Modified `database.py` so database connection settings could be read from environment variables.
- Preserved local PostgreSQL fallback behavior for development outside Docker.
- Confirmed that development credentials were example credentials and not production secrets.
- Validated the Docker Compose configuration before running the full application.

### Verification & Testing Method:

* Ran `docker compose config` to validate the Docker Compose configuration and confirm there were no configuration errors.
* Ran `docker compose up --build` to build and start the FastAPI backend and PostgreSQL database containers.
* Confirmed that both the backend and PostgreSQL services started successfully.
* Opened `http://127.0.0.1:8000/` in the browser and verified that the Smart Campus Assistant frontend loaded correctly.
* Tested the application by sending requests through the Smart Campus Assistant interface.
* Verified the `/events` endpoint and confirmed that event data could be retrieved successfully.
* Verified the `/courses` endpoint and confirmed that course information, including CS 560, could be retrieved successfully.
* Confirmed that the FastAPI backend running inside Docker could successfully communicate with the PostgreSQL database container.
* Verified the API functionality using FastAPI Swagger documentation at `http://127.0.0.1:8000/docs`.

## Audit Certification
I certify as Team Lead that all entries above accurately represent AI usage within this project phase, all prompts have been recorded, and all code has been validated by human review and automated testing.

**Team Lead Signature:** *Arpan Dey* — **Date:** September 8, 2026