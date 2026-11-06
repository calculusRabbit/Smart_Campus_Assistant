# shortcuts so we do not have to type the long commands

# backend tests (needs docker), like CI but without the seed step (seed resets the data)
test:
	docker compose run --rm backend sh -c "pip install -q pytest pytest-cov && python -m pytest -q --cov=main --cov=database --cov=services --cov-report=term --cov-fail-under=60"

# frontend e2e tests with playwright
e2e:
	cd frontend && npm run e2e

.PHONY: test e2e
