# Smart Campus Assistant Platform

## Overview

The Smart Campus Assistant Platform is a web-based application designed to make university information easier for students to access. Campus information is often distributed across different systems, which can make it difficult for students to quickly find information about courses, professors, dining, academic deadlines, and campus events.

The platform provides a centralized interface where students can ask natural-language questions and receive relevant campus information. The current prototype focuses on building the backend, database, development environment, and basic chatbot functionality required for future development.

## Prototype 1 Features

The current Prototype 1 implementation includes:

- Campus event information
- Dining information
- Course information
- Professor information
- Academic deadlines
- Student interest storage
- Interest-based event recommendations
- Natural-language chatbot interface
- PostgreSQL database integration
- REST API endpoints
- Web-based frontend interface

## Technology Stack

### Backend

- Python
- FastAPI
- Uvicorn

### Database

- PostgreSQL 16
- Psycopg

### Frontend

- HTML
- CSS
- JavaScript

### Development and Quality Tools

- Docker
- Docker Compose
- Pytest
- Ruff
- GitHub Actions
- Gitleaks

## System Architecture

The Prototype 1 architecture follows this general flow:

```text
Web Browser
     |
     v
HTML / CSS / JavaScript Frontend
     |
     v
FastAPI REST API
     |
     v
PostgreSQL Database

```

The frontend communicates with the FastAPI backend. The backend processes requests, retrieves information from PostgreSQL, and returns structured responses to the frontend.

## Database

The PostgreSQL database currently contains the following tables:

- `events`
- `courses`
- `professors`
- `dining`
- `deadlines`
- `student_interests`

Synthetic development data is provided for testing and demonstration purposes.

## Environment Variables

The application uses PostgreSQL environment variables for database configuration. A sanitized example configuration is available in:

```text
.env.example
```

Do not commit real credentials or a local `.env` file to the repository.

## Running with Docker

Docker and Docker Compose provide a reproducible development environment.

Build and start the application with:

```bash
docker compose up --build
```

The application can then be accessed at:

```text
http://127.0.0.1:8000/
```

FastAPI interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

To stop the containers:

```bash
docker compose down
```

## Database Migrations

Prototype 1 includes reproducible SQL migration and rollback scripts:

```text
migrations/
├── 001_initial_up.sql
└── 001_initial_down.sql
```

Apply the migration:

```bash
docker compose exec -T db psql \
  -U smartcampus \
  -d smart_campus \
  < migrations/001_initial_up.sql
```

Rollback the migration:

```bash
docker compose exec -T db psql \
  -U smartcampus \
  -d smart_campus \
  < migrations/001_initial_down.sql
```

## Seed Data

Synthetic development data can be inserted with:

```bash
docker compose exec backend python seed.py
```

The synthetic data allows the application to be tested and demonstrated without using real student information.

## API Endpoints

The current backend provides API endpoints for:

- `/events`
- `/dining`
- `/courses`
- `/professors`
- `/deadlines`
- `/recommendations/events`
- `/chat`

Additional endpoints support saving student interests and generating event recommendations.

## Code Quality

Ruff is used for Python linting and static analysis.

Run:

```bash
ruff check .
```

## Testing

Pytest is used for automated backend testing.

Run:

```bash
python -m pytest -q
```

The current Prototype 1 test suite verifies the home page, events endpoint, and courses endpoint.

## Continuous Integration

GitHub Actions provides automated continuous integration.

The CI workflow performs:

1. Secret scanning with Gitleaks
2. Python environment setup
3. Dependency installation
4. Ruff static analysis
5. PostgreSQL database setup
6. Database migration
7. Synthetic database seeding
8. Pytest execution

The CI workflow must pass before code is considered ready for integration.

## Development Workflow

Development work should be completed on development or feature branches instead of directly on the main branch.

The project uses Conventional Commit messages, such as:

```text
feat: add event recommendation endpoint
fix: correct database connection
test: add API endpoint tests
ci: update continuous integration workflow
docs: update developer documentation
```

Changes should be submitted through pull requests and reviewed before being merged into the main branch.

## Prototype Version

Prototype 1 release:

```text
v0.1.0-alpha
```

## Team

Smart Campus Assistant Platform
Wichita State University Senior Design Project
