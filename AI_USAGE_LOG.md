# AI Usage Log

## Smart Campus Assistant Platform — Prototype 1

This document records the use of generative AI tools during development of the Smart Campus Assistant Platform. AI was used as a development assistant for planning, debugging, documentation, code suggestions, and testing guidance. AI-generated suggestions were reviewed, modified when necessary, and manually validated before being included in the project.

## AI Tool Used

- ChatGPT by OpenAI

## 1. Backend Development

### AI Assistance

AI was used to help review and improve the FastAPI backend structure and API functionality.

Example requests included:

- Help reviewing FastAPI endpoint structure.
- Help connecting FastAPI to PostgreSQL.
- Help debugging database connection errors.
- Help implementing and testing campus information endpoints.
- Help reviewing chatbot intent handling and recommendation logic.

### Manual Review and Changes

The suggested code was reviewed before being added to the project. Backend behavior was manually tested using FastAPI Swagger documentation and the web interface.

### Validation

The following functionality was manually tested:

- Events endpoint
- Courses endpoint
- Dining endpoint
- Professors endpoint
- Deadlines endpoint
- Student interests
- Event recommendations
- Chat endpoint

## 2. PostgreSQL Database

### AI Assistance

AI was used to help migrate the backend development environment from SQLite-based development to PostgreSQL and to review database connection configuration.

AI also assisted with creating reproducible SQL migration and rollback scripts.

### Manual Review and Changes

The database schema was verified against the actual PostgreSQL database before migration scripts were finalized.

### Validation

The initial migration was applied to a separate test database.

The rollback script was then executed and the database was checked to verify that the created tables were removed.

The database tables included:

- courses
- deadlines
- dining
- events
- professors
- student_interests

## 3. Synthetic Database Seeder

### AI Assistance

AI assisted with creating `seed.py` using the existing database insertion functions.

### Manual Review and Changes

The seeder was reviewed to ensure that it used synthetic development data rather than real student information.

### Validation

The seeder was executed against the PostgreSQL test database and inserted sample campus event data successfully.

## 4. Docker Development Environment

### AI Assistance

AI provided guidance for creating:

- `Dockerfile`
- `docker-compose.yml`
- `.env.example`
- `requirements.txt`

AI also assisted with debugging Docker-to-PostgreSQL connection issues.

### Manual Review and Changes

The database connection code was updated to support environment variables inside Docker while maintaining local development support.

### Validation

The Docker configuration was validated with:

```bash
docker compose config
```

The application was then built and started with Docker Compose.

End-to-end requests were tested from the browser through FastAPI to PostgreSQL.

## 5. Static Analysis and Code Quality

### AI Assistance

AI assisted with configuring Ruff through `pyproject.toml` and identifying code-quality issues.

### Manual Review and Changes

Ruff suggestions and automatic fixes were reviewed. Duplicate backend code and formatting issues were corrected.

### Validation

Static analysis was run with:

```bash
ruff check .
```

The final local result was:

```text
All checks passed!
```

## 6. Automated Testing

### AI Assistance

AI assisted with creating initial Pytest tests for the FastAPI application.

Tests were created for:

- Home page
- Events endpoint
- Courses endpoint

### Manual Review and Changes

Initial test assumptions were corrected after comparing them with the actual API response structure.

### Validation

Tests were run locally and inside Docker.

Local validation:

```bash
python -m pytest -q
```

Result:

```text
3 passed
```

## 7. Continuous Integration

### AI Assistance

AI assisted with creating and debugging the GitHub Actions CI workflow.

The workflow includes:

- Gitleaks secret scanning
- Python setup
- Dependency installation
- Ruff
- PostgreSQL
- Database migration
- Synthetic database seeding
- Pytest

### Manual Review and Changes

The CI workflow was updated after reviewing actual GitHub Actions failures.

For example, the Gitleaks configuration was updated to provide the GitHub workflow token and checkout the full Git history required for pull-request scanning.

The `backend-testing` branch was also added as a CI push trigger during development.

### Validation

The GitHub Actions workflow was executed on GitHub and the final CI run completed successfully with a green status.

## 8. Frontend Development

### AI Assistance

AI provided suggestions for improving the Smart Campus Assistant frontend layout and displaying chatbot responses.

### Manual Review and Changes

Frontend changes were reviewed and tested manually in the browser.

### Validation

The frontend was tested with the running FastAPI and PostgreSQL Docker environment.

Example chatbot questions included:

```text
What events are happening?
Tell me about CS 560.
```

The application successfully displayed information retrieved through the backend.

## 9. Documentation

### AI Assistance

AI assisted with organizing and drafting:

- README documentation
- Developer onboarding documentation
- AI usage documentation

### Manual Review and Changes

Documentation was reviewed and updated to reflect the actual Prototype 1 implementation rather than planned features that were not yet implemented.

## 10. Human Verification

AI suggestions were not treated as automatically correct. Suggested changes were reviewed and validated using development tools and manual testing.

Verification methods included:

```text
docker compose config
docker compose up --build
ruff check .
python -m pytest -q
git diff --check
PostgreSQL migration testing
PostgreSQL rollback testing
GitHub Actions CI
Browser-based application testing
FastAPI Swagger testing
```

The development team remains responsible for the final code, testing, documentation, and submitted project.
