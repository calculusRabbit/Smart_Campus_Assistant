# QA test log - prototype 3

Vu, Nov 6. branch feature/e2e-tests

I used playwright to open the app in chrome and click around like a user. login is still fake and the backend is off, so this is only the frontend.

to run it:

    cd frontend
    npm run e2e

got 18 tests, all 18 passed (12 user flows + 6 accessibility scans, one for each page)

## what i tested

1. opened /dashboard /profile /reviews while logged out -> sent to /login (ok)
2. logged in then logged out -> name shows up, logout goes back to /login (ok)
3. opened /login while logged in -> goes to /dashboard (ok)
4. dropdown to reviews, profile, then back to dashboard -> every page has its own url (ok)
5. refresh on /profile, then back button -> still works (ok)
6. typed a fake url /blah -> shows "Page not found" and the button goes back to dashboard (ok)
7. delete account -> button is disabled till i type a password, then logs me out with a message (ok)
8. delete popup then cancel -> popup closes (ok)
9. deleted account then logged in again -> account comes back (ok)
10. fake the account being deleted 31 days ago then login -> blocked, "This account was deleted." (ok)
11. searched "cody" in reviews, clicked View -> goes to /professors/101 (ok)
12. searched "zzzzz" -> "No professors found." (ok)

## things i found

- QA-1 (low): profile page has no top bar, only a back to dashboard button. other pages have the bar so it looks different. open
- QA-2 (low): when backend is off the dashboard shows a fetch error in the console. page still works. open
- QA-3 (info): login/signup/delete only tested with fake auth. need to run again after the real auth is merged. open

the accessibility stuff (labels, low contrast) is in the accessibility log, not here

## not tested yet

- sign up page (waiting for the new auth)
- anything that really calls the backend
- keyboard only check

## terminal output

from `npx playwright test --workers=1 --reporter=list`

```
E2E test run, 2026-11-06 07:02, branch feature/e2e-tests, commit 6fe7911
command: npx playwright test --workers=1 --reporter=list


Running 18 tests using 1 worker


/login: 0 problems
  ✓   1 e2e/accessibility.spec.js:30:3 › axe scan /login (776ms)

/signup: 1 problems
  [critical] label (1 places)
    Form elements must have labels
    -> input[type="date"] |   Element does not have an implicit (wrapped) <label>
  ✓   2 e2e/accessibility.spec.js:30:3 › axe scan /signup (698ms)

/dashboard: 1 problems
  [serious] color-contrast (2 places)
    Elements must meet minimum color contrast ratio thresholds
    -> ._scheduleItem_sfasz_124:nth-child(2) > ._scheduleProfessor_sfasz_141 |   Element has insufficient color contrast of 3.54 (foreground color: #888888, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1
    -> ._scheduleItem_sfasz_124:nth-child(3) > ._scheduleProfessor_sfasz_141 |   Element has insufficient color contrast of 3.54 (foreground color: #888888, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1
  ✓   3 e2e/accessibility.spec.js:37:3 › axe scan /dashboard (728ms)

/reviews: 0 problems
  ✓   4 e2e/accessibility.spec.js:37:3 › axe scan /reviews (663ms)

/professors/101: 2 problems
  [serious] color-contrast (2 places)
    Elements must meet minimum color contrast ratio thresholds
    -> ._reviewCard_1ck2b_170:nth-child(4) > ._reviewTop_1ck2b_180 > ._date_1ck2b_200 |   Element has insufficient color contrast of 3.54 (foreground color: #888888, background color: #ffffff, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 4.5:1
    -> ._reviewCard_1ck2b_170:nth-child(5) > ._reviewTop_1ck2b_180 > ._date_1ck2b_200 |   Element has insufficient color contrast of 3.54 (foreground color: #888888, background color: #ffffff, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 4.5:1
  [critical] select-name (1 places)
    Select element must have an accessible name
    -> select |   Element does not have an implicit (wrapped) <label>
  ✓   5 e2e/accessibility.spec.js:37:3 › axe scan /professors/101 (670ms)

/profile: 1 problems
  [critical] select-name (1 places)
    Select element must have an accessible name
    -> select |   Element does not have an implicit (wrapped) <label>
  ✓   6 e2e/accessibility.spec.js:37:3 › axe scan /profile (778ms)
  ✓   7 e2e/account.spec.js:4:1 › delete account asks for a password then logs you out (748ms)
  ✓   8 e2e/account.spec.js:25:1 › cancel closes the delete popup (533ms)
  ✓   9 e2e/account.spec.js:35:1 › deleted account comes back when you log in again (674ms)
  ✓  10 e2e/account.spec.js:48:1 › deleted account is blocked after 30 days (492ms)
  ✓  11 e2e/navigation.spec.js:4:1 › logged out user is sent to the login page (470ms)
  ✓  12 e2e/navigation.spec.js:11:1 › login goes to the dashboard and logout comes back (572ms)
  ✓  13 e2e/navigation.spec.js:21:1 › logged in user cannot see the login page (386ms)
  ✓  14 e2e/navigation.spec.js:27:1 › dropdown opens each page with its own url (744ms)
  ✓  15 e2e/navigation.spec.js:43:1 › refresh and back button keep working (553ms)
  ✓  16 e2e/navigation.spec.js:53:1 › unknown url shows the 404 page (569ms)
  ✓  17 e2e/reviews.spec.js:4:1 › search finds a professor and opens the professor page (437ms)
  ✓  18 e2e/reviews.spec.js:20:1 › search with no match shows an empty message (389ms)

  18 passed (12.4s)
```
