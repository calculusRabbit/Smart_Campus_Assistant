# Developer Onboarding Guide

## Smart Campus Assistant Platform

This guide explains how a new developer can set up and run the Smart Campus Assistant Platform development environment.

## 1. Prerequisites

Install the following software before starting:

- Git
- Docker Desktop
- Python 3.12 or later
- GitHub account

Docker Desktop should be running before using Docker Compose.

## 2. Clone the Repository

Clone the project repository and enter the project directory:

```bash
git clone <repository-url>
cd WSU_senior_design_project_2026
```

Developers should work on an appropriate feature or development branch instead of committing directly to `main`.

Example:

```bash
git checkout -b feature/example-feature
```

## 3. Environment Configuration

The project includes a sanitized environment configuration example:

```text
.env.example
```

If local environment configuration is required, create a local `.env` file based on `.env.example`.

Never commit the `.env` file or real credentials to GitHub.

The PostgreSQL configuration uses these variables:

```text
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_HOST
POSTGRES_PORT
```

## 4. Run the Application with Docker

Build and start the application:

```bash
docker compose up --build
```

Docker Compose starts the FastAPI backend and PostgreSQL database.

The web application is available at:

```text
http://127.0.0.1:8000/
```

FastAPI Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```

Stop the environment with:

```bash
docker compose down
```

## 5. Database Migration

The database migration scripts are stored in:

```text
migrations/
```

Apply the initial migration:

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

## 6. Seed Development Data

Synthetic development data can be inserted with:

```bash
docker compose exec backend python seed.py
```

Seed data is intended for development, testing, and demonstrations.

## 7. Local Python Environment

Developers who want to run Python tools locally can create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 8. Code Quality

Run Ruff before committing Python changes:

```bash
ruff check .
```

Ruff should report:

```text
All checks passed!
```

## 9. Automated Tests

Run the test suite with:

```bash
python -m pytest -q
```

Tests should pass before submitting a pull request.

Tests are located in:

```text
tests/
```

## 10. Git Workflow

Create a branch for development work:

```bash
git checkout -b feature/example-feature
```

Use Conventional Commit messages.

Examples:

```text
feat: add new campus endpoint
fix: correct database query
test: add endpoint tests
docs: update developer documentation
ci: update GitHub Actions workflow
```

Push the branch:

```bash
git push origin feature/example-feature
```

Create a pull request on GitHub and request peer review before merging.

## 11. Continuous Integration

GitHub Actions automatically checks submitted code.

The CI pipeline includes:

- Secret scanning with Gitleaks
- Ruff linting and static analysis
- PostgreSQL database startup
- Database migration
- Synthetic data seeding
- Pytest execution

Developers should verify that the CI workflow is green before merging a pull request.

## 12. Project Structure

Important project files and directories include:

```text
.github/workflows/       GitHub Actions CI
migrations/              Database migration and rollback scripts
static/                  Frontend files
tests/                   Automated tests
database.py              PostgreSQL database operations
main.py                  FastAPI application and API endpoints
models.py                Application models
seed.py                  Synthetic database seeder
Dockerfile               Backend container definition
docker-compose.yml       Local multi-container environment
requirements.txt         Python dependencies
pyproject.toml           Ruff configuration
README.md                Main project documentation
```

## 13. Getting Help

Developers should use GitHub Issues to document implementation tasks, bugs, and development work.

Pull requests should reference the related GitHub Issue when applicable.
