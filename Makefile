# shortcuts so we do not have to type the long commands

# backend tests (needs docker), like CI but without the seed step (seed resets the data)
test:
	docker compose run --rm backend sh -c "pip install -q pytest pytest-cov && python -m pytest -q --cov=main --cov=database --cov=services --cov-report=term --cov-fail-under=60"

# the seed gives every student a random status, so set the two the e2e tests need
# (open = verified student, pending = not verified yet). needs docker and the seeded db
e2e-prepare:
	docker compose exec -T db psql -U smartcampus -d smart_campus -c "UPDATE students SET account_status='open' WHERE email='student_personal-email2@test.com'; UPDATE students SET account_status='pending' WHERE email='student_personal-email4@test.com';"

# frontend e2e tests with playwright (backend + seeded db must be running)
e2e: e2e-prepare
	cd frontend && npm run e2e

.PHONY: test e2e e2e-prepare
