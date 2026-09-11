# AI Usage & Verification Log

**Project Name:** Smart Campus Assistant Platform  
**Team Name:** The Three Musketeers
**Team Member:** Teng Fai Leong  
**Role:** Backend Developer / AI Integration  

---

## Overview & AI Policy Compliance Statement

This repository utilizes Generative AI tools, primarily ChatGPT, in compliance with course AI guidelines. AI tools were used to assist with backend development, PostgreSQL integration, database migrations, Docker configuration, automated testing, CI/CD configuration, recommendation logic refactoring, debugging, and documentation.

All AI-assisted code was manually reviewed before being added to the project. Generated code and configuration were modified when necessary to match the existing project architecture. Changes were validated using Ruff static analysis, pytest automated tests, PostgreSQL migration and rollback testing, Docker execution, browser/API testing, and GitHub Actions CI.

---

## Entry 1: Prototype 1 — PostgreSQL Database Migration & Rollback

* **Date:** September 8 2026
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

* **Date:** September 8 2026
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

## Entry 3: Prototype 1 — PostgreSQL down script

* **Date:** September 8 2026
* **Team Member:** Arpan Dey
* **Tool Used:** Perplexity
* **Associated Git Issue:** #12 - Create and add PostGres database migration rollback script ('down' script)
* **Associated Feature Branch:** `feature/database`

### Exact Prompt Submitted:

> give me an example of a postgres schema migration rollback
>find any errors or major improvements for the DOWN file and give them to me one by one
>any further errors/major improvements?
>done, anything else?
>done, anything else?
>done, anything further?

### AI Output Summary & Code Generated:

Perplexity gave an example of a migration and rollback in PostGres, and identified errors in the human-written sca_database_v0.2.0_DOWN.sql file and suggested solutions.

### Human Review, Refactoring & Modifications Made:

- Reviewed AI-found errors and matched them to the .sql file.
- Found errors, determined the solution, and matched them to AI solution

### Verification & Testing Method:

- Put corrected script into online SQL syntax checker (RunSQL) and found no errors.
-Ran down script and confirmed all tables were deleted.


---

## Entry 4: Prototype 1 — PostgreSQL dummy data population script

* **Date:** September 10 2026
* **Team Member:** Arpan Dey
* **Tool Used:** Perplexity
* **Associated Git Issue:** #20 - Create and add completed database dummy data populator
* **Associated Feature Branch:** `feature/database`

### Exact Prompt Submitted:

> besides the missing inserts for the remaining tables, is there anything wrong with the dummy data populator? Find any and all errors in the script and explain them, and suggest any major improvements to be made to the code. (Provided python file and schema migration file.)

### AI Output Summary & Code Generated:

Perplexity gave corrections and potential solutions for many issues, including missing inner '()' for function arguments to make arguments sequences, and incorrect corrections like missing indentations.

### Human Review, Refactoring & Modifications Made:

- Reviewed AI-found errors and matched them to the .py file.
- Ignored unnecessary errors and their corrections
- Found errors, determined the solution, and matched them to AI solutions. Not all of them matched; some solutions the AI proposed were excessive and others did not make sense for the database schema. Those were ignored.

### Verification & Testing Method:

- Found no errors in editor. As the script is not yet complete as of the time of writing, it couldn't be run yet.

---


## Entry 5: Learn to Write Unit Test Cases

* Date: September 2026
* Team Member: Vu Nguyen
* Tool Used: GPT-5.6 Sol
* Associated Git Issue: #21 — Test Cases for RAG
* Associated Feature Branch: test/rag-unit-tests

### Exact Prompt Submitted: https://chatgpt.com/share/6aa38942-87d0-83e9-8b04-bf4d971022c6

“what is unit test, what does it look like give me example unit test case”

“what is pytest library”

“so for this code below right here can write test case for function filter_urls like i will have list of url link that have old year and unit test should test which url link suppose to drop bla bla etc”

### AI Output Summary & Code Generated:

ChatGPT was used to help me learn the fundamentals of unit testing and how to use the pytest framework in Python. The AI explained how unit tests provide controlled inputs to individual functions and verify that the returned results match the expected behavior.

ChatGPT also provided example test cases for the RAG data-processing functions, including tests for URL filtering and date-based event filtering. The examples demonstrated how to use Python assert statements and how to structure pytest test functions.

### Human Review, Refactoring & Modifications Made:

* Reviewed the AI-generated examples to understand the pytest syntax before applying them to the project.
* Adapted the example test cases to match the project’s existing RAG functions and expected behavior.
* Manually selected test inputs and expected outputs for URL filtering.
* Added test cases to verify that outdated URLs are removed and current URLs are retained.
* Reviewed Python date utilities such as date.today(), isoformat(), and timedelta() before using them in date-filtering tests.
* Modified AI examples where necessary rather than copying them directly into the project.

### Verification & Testing Method:

* Ran the unit tests using pytest.
* Verified that current-year URLs were retained by the URL filtering function.
* Tested outdated URLs to verify the expected filtering behavior and identify cases not handled by the existing implementation.
* Tested the event date-filtering function with current and older dates.
* Reviewed failed tests to distinguish between incorrect test expectations and issues in the implementation.
* Manually reviewed the final test cases to confirm that each test represented the intended behavior of the RAG pipeline.

--

## Audit Certification
I certify as Team Lead that all entries above accurately represent AI usage within this project phase, all prompts have been recorded, and all code has been validated by human review and automated testing.

**Team Lead Signature:** *Arpan Dey* — **Date:** September 10, 2026


