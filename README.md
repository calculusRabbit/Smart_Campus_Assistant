# Smart Campus Assistant Platform

## Overview

The Smart Campus Assistant Platform is a web-based application designed to make university information easier for students to access. Campus information is often distributed across different systems, making it difficult to quickly find information about courses, professors, dining, academic deadlines, and campus events.

The platform brings this information together through a student dashboard, an ML recommendation engine, and an LLM chatbot. Prototype 3 adds event classification, more WSU campus data, and professor appointment requests. Students can explore campus resources, manage their interests, and receive personalized event recommendations.

## Prototype 3 Features

- Student dashboard with campus information and event recommendations
- Login and signup interfaces
- Student profiles and interest management
- Campus events, dining, courses, professor information, and academic deadlines
- Professor review interfaces with ratings and voting
- Professor appointment requests and request history
- ML Classifier page for predicting event categories from a title and description
- Interest-based event recommendations using semantic similarity and ML theme scoring
- WSU faculty and course data collection, with ShockerSync event links
- Natural-language chatbot with structured database responses and retrieval-augmented generation (RAG)
- Campus knowledge collection, document processing, and semantic search
- PostgreSQL database integration with pgvector support
- REST API with interactive documentation
- Containerized development environment and automated testing

The current interface still uses demonstration authentication and browser-local reviews. Account deletion and its 30-day recovery window are simulated in local storage. Use synthetic accounts for demonstrations. Appointment requests are saved to PostgreSQL as pending requests; they are not confirmed bookings with professors.

## Technology Stack

### Backend

- Python 3.12
- FastAPI and Uvicorn
- Psycopg 3
- Pydantic

### Frontend

- React 19
- Vite 8
- JavaScript, HTML, and CSS modules
- Node.js 22 for the containerized frontend

### Database

- PostgreSQL 16
- pgvector
- Supabase project dashboard

### AI and Recommendations

- Sentence Transformers: `sentence-transformers/all-MiniLM-L6-v2`
- FAISS for semantic retrieval
- Ollama for local language-model inference
- `qwen3-direct`, based on `qwen3:4b`
- Category-based and semantic event recommendation services
- Scikit-learn event classifiers using TF-IDF and logistic regression

### Development and Quality Tools

- Docker and Docker Compose
- Pytest and pytest-cov
- Ruff and ESLint
- GitHub Actions
- Gitleaks
- Mypy, Bandit, Complexipy, and pip-audit for additional analysis

## System Architecture

```mermaid
flowchart TD
    Student[Student] --> Frontend[React / Vite Frontend]
    Frontend --> API[FastAPI REST API]
    API --> Database[PostgreSQL / pgvector]
    API --> Recommendations[Event Recommendation Services]
    Recommendations --> EventIndex[Semantic Event Data / FAISS]
    Recommendations --> ML[ML Category Predictions / Theme Scoring]
    API --> Appointments[Professor Appointment Requests]
    Appointments --> Database
    API --> Chat[Chat Intent Routing]
    Chat --> Database
    Chat --> RAG[RAG Pipeline]
    RAG --> Retrieval[Document Embeddings / FAISS]
    RAG --> Ollama[Ollama Inference]
    Collection[Campus Web Collection] --> Processing[Filtering / Chunking / Ingestion]
    Processing --> Retrieval
```

The frontend communicates with the backend through `frontend/src/api.js`. The backend retrieves campus information, stores student interests and appointment requests, and generates recommendations. Chat requests use structured campus data first and use the RAG pipeline for additional campus knowledge when enabled.

The RAG pipeline retrieves relevant document chunks and sends them to Ollama to generate source-grounded responses. Document search uses FAISS artifacts; PostgreSQL stores the platform's relational data and defines vector-enabled knowledge tables.

Additional documentation:

- [Architecture Overview](https://github.com/calculusrabbit/smart_campus_assistant/wiki/Architecture-Overview)
- [Database Schema](https://github.com/calculusrabbit/smart_campus_assistant/wiki/Database-Schema)
- [Core Conventions](https://github.com/calculusrabbit/smart_campus_assistant/wiki/Core-Conventions)
- [Developer Onboarding](docs/DEVELOPER_ONBOARDING.md)

## Repository Structure

```text
frontend/                       React student interface
main.py                         FastAPI routes and chat request handling
models.py                       API request models
database.py                     Database access and response formatting
services/
  event_recommender.py           Semantic event recommendations
  recommendation_service.py     Interest and category matching
  recommender_config.py         Recommendation settings
  appointments.py              Appointment requests and history
  ml/                          Event classifiers, training scripts, and models
  rag/                          Retrieval, generation, and knowledge processing
    data/                       Document data and FAISS artifacts
    processing/                 Filtering, chunking, and ingestion
    scrapers/                   Campus information collection
    tests/                      RAG and scraper tests
static/                         Backend-served web interface
tests/                          API, database, recommendation, and chat tests
docs/                           Developer documentation
migrations/                     Initial schema and appointment migrations/rollbacks
sca_database_v0.4.0.sql          Expanded database schema
sca_database_v0.4.0_DOWN.sql     Expanded schema teardown
seed.py                         Development/test seeding entry point
dummy_data_populator_v0.5.0.py   Synthetic data generator
.github/workflows/              Automated CI and PR validation
AI_USAGE_LOG.md                 AI usage and verification records
```

The frontend uses React state for page navigation. Backend responsibilities are separated into API routing, data access, request validation, recommendation services, and RAG processing. The recommendation services encapsulate matching and ranking logic separately from the UI and API routes.

## Database

The database supports the following domains:

| Domain | Tables |
| --- | --- |
| Institutions and locations | `schools`, `departments`, `locations` |
| Accounts and students | `users`, `students`, `authentications` |
| Academics | `courses`, `sessions`, `instructors`, `offerings`, `enrolments`, `registrations`, `attendance`, `deadlines` |
| Events | `events`, `event_responses`, `event_embeddings` |
| Dining | `dining`, `dining_items` |
| Reviews | `reviews_generic`, `review_replies`, `review_votes`, `reviews_educational`, `reviews_dining`, `reviews_resources` |
| Communities | `groups`, `memberships`, `notifications` |
| Campus knowledge | `scraped_information` |
| Appointments | `appointments` (separate migration) |

The schema defines relational constraints, validation checks, indexes, trigger functions, and 384-dimensional vector columns. Student interests are stored in `students.interests`; professor-facing API responses are assembled from instructor data. The appointment migration adds student/instructor references, a requested date and time, a reason, and a request status.

### Supabase Project

[Open the Smart Campus Assistant Supabase dashboard](https://supabase.com/dashboard/project/qlivdhjehiohlptbzlpn/)

Access requires an authorized Supabase account. Local Docker development uses its own PostgreSQL instance; the dashboard link is not a database connection string.

## Environment Variables

Copy the sanitized configuration template before starting the application:

```bash
cp .env.example .env
```

Set a local database password and configure the following values as needed:

| Variable | Purpose | Default / example |
| --- | --- | --- |
| `POSTGRES_DB` | Database name | `smart_campus` |
| `POSTGRES_USER` | Database username | `smartcampus` |
| `POSTGRES_PASSWORD` | Database password | Set locally |
| `POSTGRES_HOST` | Database hostname inside Compose | `db` |
| `POSTGRES_PORT` | Internal database port | `5432` |
| `API_HOST_PORT` | Backend host port | `8000` |
| `FRONTEND_HOST_PORT` | Frontend host port | `5173` |
| `RAG_ENABLED` | Enable the RAG chat fallback | `true` |
| `HF_TOKEN` | Optional Hugging Face access token | Leave empty unless needed |

Compose also accepts `DB_MEMORY_LIMIT`, `BACKEND_MEMORY_LIMIT`, and `FRONTEND_MEMORY_LIMIT` for container resource limits. The `APP_ENV` setting authorizes synthetic database seeding when explicitly set to `development` or `test`.

Use the default application ports with the current API client and CORS configuration. The database is accessible to Compose services without publishing a host port. Model names, Ollama connectivity, retrieval paths, and chunk settings are configured in `services/rag/config.py`.

Do not commit `.env`, access tokens, database credentials, or real student information.

## Running with Docker

### Prerequisites

- Git
- Docker and Docker Compose v2
- Ollama for local AI-generated responses
- Node.js 22 and npm if generating the frontend dependency lockfile locally

### Start the Application

```bash
git clone https://github.com/calculusrabbit/smart_campus_assistant.git
cd smart_campus_assistant
cp .env.example .env
```

Edit `.env` and set `POSTGRES_PASSWORD`. For a database-backed demonstration without AI generation, set `RAG_ENABLED=false`.

The frontend lockfile is included. Use `npm ci` from `frontend/` for local frontend development.

Build and start the development stack:

```bash
docker compose up --build
```

| Component | URL |
| --- | --- |
| Student interface | http://localhost:5173 |
| Backend web interface | http://localhost:8000 |
| Interactive API documentation | http://localhost:8000/docs |
| OpenAPI specification | http://localhost:8000/openapi.json |

Inspect services and logs:

```bash
docker compose ps
docker compose logs --tail=100 backend frontend db
```

Stop the application:

```bash
docker compose down
```

Named volumes preserve local data between runs. Use volume deletion only for an intentional disposable-environment reset.

## Database Setup and Schema Changes

The expanded schema is defined in `sca_database_v0.4.0.sql`. PostgreSQL runs the configured initialization SQL when creating a new database volume.

The appointment table is added separately. After the database starts, copy its migration into the database container and run it from the repository root:

```bash
docker compose cp migrations/002_professor_appointments_up.sql db:/tmp/appointments_up.sql
docker compose exec db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/appointments_up.sql'
```

Its rollback is `migrations/002_professor_appointments_down.sql`.

To initialize an explicitly empty database manually:

```bash
docker compose exec -T db sh -c \
  'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < sca_database_v0.4.0.sql
```

For schema work:

- Pair changes with executable rollback scripts and verify both directions on a disposable database.
- Record migration and rollback results in the associated GitHub Issue.
- Back up existing data before applying changes.
- Use `sca_database_v0.4.0_DOWN.sql` only for an intentional expanded-schema teardown.


## Seed Data

Populate a disposable local database with synthetic data:

```bash
docker compose exec -e APP_ENV=development backend python seed.py
```

This resets application data and invokes `dummy_data_populator_v0.5.0.py`. Use only a verified development/test database. Synthetic data supports repeatable testing and demonstrations without exposing real student records.

## AI and Campus Knowledge

### Ollama Setup

With Ollama running on the host, execute from the repository root:

```bash
ollama pull qwen3:4b
ollama create qwen3-direct -f Modelfile.qwen3-direct
ollama list
```

The backend configuration uses `http://host.docker.internal:11434` for Ollama. Ensure the backend container can reach that address; Linux environments may require a host-gateway mapping and suitable host listener configuration.

Set `RAG_ENABLED=true` in `.env` and recreate the backend after changing its environment:

```bash
docker compose up -d --force-recreate backend
```

### Knowledge Processing

Campus knowledge preparation follows this sequence:

```text
Campus source collection
        -> Content filtering
        -> Page chunking
        -> Document normalization and ingestion
        -> Embedding generation
        -> FAISS index creation
```

Document retrieval uses the matching `chunks.json` and `document_index.faiss` files in `services/rag/data/`. To rebuild the document index from prepared chunks:

```bash
python -m services.rag.embed_and_load
```

Run this command in a Python environment with the project dependencies installed. Keep chunk records and index vectors aligned, and restart the backend after replacing retrieval artifacts.

Semantic event recommendations use a separate `all_events.json` and `events_index.faiss` pair. Recommendation thresholds and date windows are defined in `services/recommender_config.py`; category matching provides the alternate recommendation path.

### Event Classification

The ML Classifier page sends an event title and description to `/ml/predict-event`. The trained model returns category predictions and probabilities. Recommendation ranking also uses ML theme scores alongside semantic similarity and an upcoming-event boost.

Model files are stored in `services/ml/models/`. The category training script is `python -m services.ml.train`; it reads labeled events from `services/rag/data/all_events.json`. Theme training is in `services/ml/train_themes.py`. Retraining replaces model artifacts, so review the evaluation output before using a new model.

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/events` | Campus events |
| GET | `/dining` | Dining information |
| GET | `/courses` | Courses; optional `code` and `professor` filters |
| GET | `/professors` | Professor information |
| GET | `/deadlines` | Academic deadlines |
| POST | `/recommendations/events` | Recommendations from supplied interests |
| GET | `/students/{student_id}/interests` | Read saved interests |
| POST | `/students/{student_id}/interests` | Save student interests |
| GET | `/students/{student_id}/recommendations/events` | Recommendations from a saved student profile |
| POST | `/chat` | Natural-language campus questions |
| POST | `/ml/predict-event` | Predict categories for an event title and description |
| POST | `/appointments` | Submit a professor appointment request |
| GET | `/students/{student_id}/appointments` | List a student's appointment requests |

Example requests:

```bash
curl --fail http://localhost:8000/events

curl --fail http://localhost:8000/recommendations/events \
  -H 'Content-Type: application/json' \
  -d '{"interests":["coding","career"]}'

curl --fail http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What events are happening on campus?"}'
```

Chat responses include an intent and reply, with structured data or retrieved sources as appropriate. Interactive request and response schemas are available at `/docs`.

## Code Quality

Install Python development dependencies in a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
```

Run Python linting and configured type analysis:

```bash
ruff check .
mypy
```

Ruff configuration includes a cyclomatic complexity limit of 10. Keep methods focused, encapsulate business logic in services, and document public interfaces and non-obvious behavior.

Run frontend validation:

```bash
cd frontend
npm ci
npm run lint
npm run build
```

## Testing

Tests cover campus API responses, database access, interest management, recommendation ranking, ML predictions, chat routing, retrieval, and generation handling. Unit tests check individual functions; integration tests check API behavior and database reads/writes. Some AI and external-service calls are mocked to keep results repeatable. Run against a seeded, disposable test database with the appropriate `POSTGRES_*` environment variables.

With the Docker backend running, install the test tools and run the main backend suite:

```bash
docker compose exec backend python -m pip install -r requirements-dev.txt
docker compose exec backend python -m pytest tests -v
```

RAG/scraper and ML tests also live outside `tests/`. Run them separately, or omit the folder argument to discover all Python tests:

```bash
python -m pytest tests -q
python -m pytest services/rag/tests -q
python -m pytest services/ml -q
```

Run the combined suite with coverage and exported reports:

```bash
python -m pytest -q \
  --cov=main --cov=database --cov=services \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml \
  --cov-report=html:htmlcov \
  --cov-fail-under=60 \
  --junitxml=test-results.xml
```


## Security and Data Privacy

Prototype 3 security checks should cover authentication and session handling, password hashing, secret management, OWASP Top 10 risks, dependency vulnerabilities, PII protection, and soft-delete behavior.

The frontend on this branch uses `FAKE_AUTH` in `frontend/src/api.js`. It does not provide production authentication or server-enforced access control for student data. The appointment API also needs authorization before use with real accounts.

The schema includes hashed-password storage and `deleted_timestamp` fields for applicable account/review records. Security review should verify their behavior through the application workflows. Use sanitized configuration, synthetic test data, and restricted project/database access.

Useful audit commands include:

```bash
pip-audit
bandit -r main.py models.py database.py services

# from frontend/:
npm audit
```

## Continuous Integration

GitHub Actions provide:

1. Secret scanning with Gitleaks
2. Python 3.12 environment and dependency setup
3. Ruff static analysis
4. PostgreSQL/pgvector service setup
5. Expanded schema initialization and synthetic seeding
6. Automated tests with a 60% coverage threshold
7. Uploaded test and coverage reports
8. Separate RAG tests for applicable changes
9. Conventional PR-title validation
10. Frontend linting, production build, and dependency auditing
11. Python formatting, type, complexity, and security checks

CI logs and reports should be linked from the associated issues and prototype submission. Run the frontend lint/build and applicable security checks as part of release validation, and enforce required checks through repository branch protection.

## Development Workflow

- Use GitHub Issues for implementation tasks, bugs, test results, security findings, and refactoring work.
- Create `feature/*` or `chore/*` branches for development.
- Use [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) and provide a scope where helpful.
- Link feature and bug-fix PRs to their issues, for example `Closes #42`.
- Require at least one other team member's approval before merging into `main`.
- Follow [Semantic Versioning 2.0.0](https://semver.org/) and maintain an automated changelog or semantic-release history.
- Update setup instructions, architecture diagrams, schema documentation, and tests alongside implementation changes.

Example commit messages:

```text
feat(recommendations): add semantic event matching
fix(api): validate student interests
test(database): cover profile updates
ci(security): add dependency auditing
docs(readme): update prototype 3 setup instructions
```

## Prototype Milestones and Submission Package

Prototype 3 targets the `v0.9.0-beta` release. Keep the earlier setup, testing, and security evidence, and include the following in the submission:

- Peer-reviewed feature changes merged into `main`, the beta release tag, and release history
- Reproducible local setup, sanitized environment examples, synthetic seed data, and verified schema rollback evidence
- Updated README, visual architecture documentation, schema reference, and developer onboarding guide
- Integration test reports with at least 60% coverage and issue-linked results
- Static-analysis metrics, dependency audit results, OWASP review, and remediation evidence
- Verified authentication, privacy, and soft-delete workflows
- Environment feature-toggle documentation, including `RAG_ENABLED`
- A cumulative, Team Lead-reviewed [AI Usage Log](AI_USAGE_LOG.md) recording prompts, generated output, human changes, and validation through the beta phase
- Repository/release link and CI run URL for submission
- Browser E2E test results for the main user journeys, with QA findings, severity, and resolution status tracked in GitHub Issues
- Load/stress test results showing API latency and throughput
- WCAG 2.1 AA audit results for contrast, keyboard navigation, and screen reader support
- `/health` and `/ready` probes, structured JSON logs, and updated maintenance documentation

This list describes the submission requirements, not a record of completed checks. The current main branch does not yet include browser E2E scripts, health/readiness endpoints, or load-test and accessibility reports. Verify these items against the final release and link the actual results before submission. After the beta submission, focus on fixes and regression testing during the feature freeze.

## Team
### The Three Musketeers
#### Arpan Dey, Vu Nguyen, Teng Fai Leong
Wichita State University Senior Design Project
