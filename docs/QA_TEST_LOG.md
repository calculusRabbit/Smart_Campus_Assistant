# QA Test Execution & Bug Log (Prototype 3)

Tool: Playwright (real Chrome), `cd frontend && npm run e2e`
Run date: 2026-11-05 on branch `feature/e2e-tests`
Mode: frontend with fake auth (`FAKE_AUTH = true`), backend off
Result: **12 passed, 0 failed**

## Test results

| # | Journey | Edge case tested | Result |
|---|---------|------------------|--------|
| 1 | Logged out user opens /dashboard, /profile, /reviews | Protected pages redirect to /login | Pass |
| 2 | Log in, then log out | Name shows on the dashboard, logout returns to /login | Pass |
| 3 | Logged in user opens /login | Redirected to /dashboard | Pass |
| 4 | Dropdown to Reviews, then Profile, then Back to Dashboard | Each page has its own url | Pass |
| 5 | Refresh on /profile, then back button | Page and history keep working | Pass |
| 6 | Open a made-up url (/blah) | 404 page, button goes to dashboard | Pass |
| 7 | Delete account with a password | Delete button disabled until a password is typed, then logged out with notice | Pass |
| 8 | Cancel the delete popup | Popup closes, account kept | Pass |
| 9 | Log in again after deleting | Account restored inside the 30 day window | Pass |
| 10 | Log in 31 days after deleting | Blocked with "This account was deleted." | Pass |
| 11 | Search a professor, open the professor page | Opens /professors/:id | Pass |
| 12 | Search with no match | "No professors found." shown | Pass |

## Findings

| ID | Severity | Finding | Status |
|----|----------|---------|--------|
| QA-1 | Low | Profile page has no top bar, only a "Back to Dashboard" button, so it is different from Dashboard and Reviews | Open |
| QA-2 | Low | With the backend off, the dashboard prints a fetch error in the console (events request fails). The page still works | Open |
| QA-3 | Info | Login, signup and delete only run against fake auth. Re-run after the real auth PR merges | Open |

## Not covered yet
- Signup flow and its validation (waiting on the auth PR)
- Real backend calls (E2E runs with the backend off)
- Accessibility audit (separate log, item 4b)
