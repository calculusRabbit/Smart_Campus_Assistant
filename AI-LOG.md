# AI Usage Log — Smart Campus Assistant

**Project:** Smart Campus Assistant  
**Team:** The Three Musketeer  
**Development Phase:** Prototype 2 — Backend and AI Integration  
**Role:** Backend Developer / AI Integration  
**AI Tool:** ChatGPT (OpenAI)  
**Reporting Period:** September–October 2026

## 1. Purpose of AI Assistance

ChatGPT was used as a development assistant to support backend implementation, retrieval-augmented generation (RAG), debugging, automated testing, and CI/CD configuration.

AI assistance included explaining technical concepts, suggesting code modifications, generating terminal commands, interpreting test results, and helping troubleshoot issues.

The developer reviewed and applied the suggested changes and verified functionality through local testing and GitHub Actions.

## 2. Backend and RAG Integration

**Tasks:**
- Developed and tested backend functionality using FastAPI.
- Worked on integrating a local Ollama language model with the RAG pipeline.
- Reviewed document retrieval, embedding, and response-generation behavior.
- Improved retrieval reliability and response handling.
- Tested the chatbot using campus-related questions.

**AI Assistance:**
- Provided implementation guidance and debugging suggestions.
- Explained how the backend communicates with the RAG pipeline.
- Suggested commands to verify API responses and troubleshoot integration issues.

**Verification:**
- Confirmed that the backend could respond to requests through the `/chat` endpoint.
- Verified RAG responses using retrieved Wichita State University event information.

## 3. Campus Event Scraping Improvements

**Tasks:**
- Investigated event information extraction from the Wichita State University calendar.
- Corrected event location extraction.
- Added regression testing for the scraper.

**AI Assistance:**
- Helped identify potential problems in HTML parsing.
- Suggested changes to the BeautifulSoup extraction logic.
- Assisted with testing and interpreting scraper results.

**Verification:**
- Verified event information against the WSU calendar.
- Added automated tests for the updated scraper behavior.

## 4. Chatbot Event Routing Improvements

**Problem:**

The chatbot previously treated specific questions containing the word "event" as general event-listing requests.

For example, asking "What is the Love Data Week event about?" returned a list of upcoming campus events instead of answering the question.

**AI Assistance:**
- Suggested a helper function named `is_event_listing_request()`.
- Guided changes to the event-routing condition in `main.py`.
- Provided commands to test the helper function and live API endpoint.

**Implementation:**
- Added logic to distinguish general event-listing requests from specific event questions.
- Preserved event-listing behavior for general requests.
- Allowed specific event questions to reach the RAG pipeline.

**Verification:**

The following test cases produced the expected helper results:

| Question | Expected Result | Actual Result |
|---|---|---|
| Show me upcoming events | True | True |
| What events are happening? | True | True |
| What is the Love Data Week event about? | False | False |
| Where is the Cabaret event held? | False | False |

A live request to `/chat` using the Love Data Week question returned:
- HTTP status: `200`
- Intent: `rag`
- An explanation of Love Data Week
- Five relevant WSU calendar sources

## 5. Automated Testing and Code Coverage

**Tasks:**
- Ran automated backend tests using pytest.
- Measured coverage using pytest-cov.
- Verified the minimum 60% code coverage requirement.
- Generated detailed test execution and coverage reports.

**AI Assistance:**
- Suggested pytest commands for Docker.
- Explained coverage results and warnings.
- Guided generation of JUnit XML, coverage XML, and HTML reports.

**Local Test Results:**

| Metric | Result |
|---|---|
| Tests passed | 41 |
| Tests failed | 0 |
| Total code coverage | 62.15% |
| Minimum required coverage | 60% |
| Coverage requirement | Passed |

**Generated Reports:**
- `test-results.xml`
- `coverage.xml`
- `htmlcov/`

A non-failing Starlette deprecation warning was reported.

## 6. GitHub Actions CI/CD Improvements

**Tasks:**
- Updated `.github/workflows/ci.yml`.
- Added automated test coverage enforcement.
- Configured test and coverage report generation.
- Added GitHub Actions artifact uploads.

**AI Assistance:**
- Reviewed the existing workflow configuration.
- Suggested modifications without replacing the team's existing CI steps.
- Assisted with YAML indentation and whitespace corrections.
- Guided verification, committing, and pushing the changes.

**Verification:**
- YAML syntax validation passed.
- Local pytest coverage checks passed.
- GitHub Actions `lint-and-test` completed successfully.
- The test and coverage report upload step completed successfully.

The updated workflow automatically executes tests on pull requests and fails when coverage falls below 60%.

## 7. Git and Collaboration

AI assistance was used to explain Git commands and help safely manage changes in a collaborative repository.

Actions included:
- Reviewing staged changes before committing.
- Avoiding unrelated frontend modifications.
- Checking differences between the feature branch and `main`.
- Preparing pull request descriptions.
- Interpreting GitHub review and CI statuses.

**Relevant Commit:**

`b20f570` — Improve event question routing and automate CI coverage reports

**Feature Branch:**

`fix/prototype2-live-integration`

**Repository:**

https://github.com/calculusRabbit/Smart_Campus_Assistant

## 8. Developer Responsibility and AI Limitations

ChatGPT provided recommendations, code examples, debugging guidance, and testing instructions. It did not independently operate the developer's local environment or verify GitHub results without developer-provided outputs.

The developer was responsible for:
- Reviewing and implementing suggested code.
- Running commands in the local development environment.
- Testing backend functionality.
- Checking generated reports.
- Reviewing Git changes before committing.
- Coordinating pull request reviews with teammates.

AI-generated suggestions were treated as development assistance rather than automatically accepted solutions.

## 9. Outcome

AI assistance supported progress on the Prototype 2 backend and RAG integration.

The documented work improved chatbot routing, scraper reliability, automated testing, coverage enforcement, and CI/CD reporting.

The latest verified local test run completed with 41 passing tests and 62.15% code coverage. The corresponding GitHub Actions workflow also completed successfully.

This log documents the use of AI as a development and troubleshooting tool while preserving developer responsibility for implementation, verification, and project decisions.