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

- QA-1 (low): profile page has no top bar, only a back to dashboard button. other pages have the bar so it looks different. fixed in the redesign (nov 25), profile and verification have the top bar now
- QA-2 (low): when backend is off the dashboard shows a fetch error in the console. page still works. open
- QA-3 (info): login/signup/delete only tested with fake auth. need to run again after the real auth is merged. done, see the nov 25 run at the bottom

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

# re-run after the real auth (nov 25)

Vu, branch feature/frontend-redesign. this time it is the real login, real backend and the seeded database, nothing is faked.

to run it (docker has to be up with the backend and the seeded db):

    make e2e

`make e2e` first sets 2 seeded students to a known status (one verified, one pending) because the seed gives every student a random status. then it runs playwright.

got 33 tests, all 33 passed. i ran the whole thing 3 times in a row and it passed all 3 times.

## what changed in the tests

- the login is kept only in memory now, so a page reload logs you out. the old tests used page.goto after login so they all had to click through the top bar dropdown instead
- the 4 delete account tests are gone, that popup does not exist any more (it is deactivate account now, with a password and a captcha). i only test that the form shows up, the captcha is a proof of work thing so a test cannot really solve it
- the accessibility scan used to only print the problems. now the test fails if there is any problem
- the accessibility scan runs on all 3 looks of the app (light, dark, color blind). 6 tests per look = 18 tests, and they scan 9 pages per look
- new tests: wrong password, sign up page + captcha, sign up password check, deactivate form, verification page, not verified student can not open reviews

## what is covered (33)

- 7 navigation (logged out redirect, login/logout, back button, dropdown pages, refresh, 404)
- 6 auth (wrong password, register link + captcha, sign up check, deactivate form, verification page, pending student blocked from reviews)
- 2 reviews (search + open professor, no match message)
- 18 accessibility tests (6 tests x 3 looks), together they scan 9 pages per look: login, signup, dashboard, reviews, professor page, profile, verification, appointments, ml classifier

## things i found

- QA-4 (info): refreshing the page logs you out, because the token is only in memory. that is on purpose (safer) but it is annoying for users. Arpan should decide if we keep it. open
- QA-5 (medium): the seed gives each student a random status (pending/open/denied/closed). some backend tests use student 1 and get a 404 when student 1 happens to be closed. 4 tests failed for me because of this (test_save_and_get_student_interests and 3 in test_students_api). that could fail CI at random. open
- QA-6 (fixed): the accessibility problems from the first log (faint gray text, 3 dropdowns and the birthday field with no label) are fixed, scans are 0 problems on every page in every look
- QA-7 (fixed): one scan failed once because it ran in the middle of a color fade. now the tests turn animations off (the app already respects the "reduce motion" setting)

## not tested yet

- really finishing a sign up or a deactivate (needs the captcha solved)
- email code / studid verification
- keyboard only check

## terminal output

from `npx playwright test --workers=1 --reporter=list`, commit 6dd05af plus the new tests

```
Running 33 tests using 1 worker


light /login: 0 problems
  ✓   1 e2e/accessibility.spec.js:34:5 › light mode › axe scan /login (886ms)

light /signup: 0 problems
  ✓   2 e2e/accessibility.spec.js:39:5 › light mode › axe scan /signup (866ms)

light /dashboard: 0 problems
  ✓   3 e2e/accessibility.spec.js:44:5 › light mode › axe scan /dashboard (1.1s)

light /reviews: 0 problems

light /professors/:id: 0 problems
  ✓   4 e2e/accessibility.spec.js:50:5 › light mode › axe scan reviews and professor page (1.2s)

light /profile: 0 problems

light /verification: 0 problems
  ✓   5 e2e/accessibility.spec.js:63:5 › light mode › axe scan /profile and /verification (1.6s)

light /appointments: 0 problems

light /ml-classifier: 0 problems
  ✓   6 e2e/accessibility.spec.js:74:5 › light mode › axe scan /appointments and /ml-classifier (1.3s)

dark /login: 0 problems
  ✓   7 e2e/accessibility.spec.js:34:5 › dark mode › axe scan /login (568ms)

dark /signup: 0 problems
  ✓   8 e2e/accessibility.spec.js:39:5 › dark mode › axe scan /signup (652ms)

dark /dashboard: 0 problems
  ✓   9 e2e/accessibility.spec.js:44:5 › dark mode › axe scan /dashboard (934ms)

dark /reviews: 0 problems

dark /professors/:id: 0 problems
  ✓  10 e2e/accessibility.spec.js:50:5 › dark mode › axe scan reviews and professor page (1.4s)

dark /profile: 0 problems

dark /verification: 0 problems
  ✓  11 e2e/accessibility.spec.js:63:5 › dark mode › axe scan /profile and /verification (1.3s)

dark /appointments: 0 problems

dark /ml-classifier: 0 problems
  ✓  12 e2e/accessibility.spec.js:74:5 › dark mode › axe scan /appointments and /ml-classifier (1.3s)

colorblind /login: 0 problems
  ✓  13 e2e/accessibility.spec.js:34:5 › colorblind mode › axe scan /login (582ms)

colorblind /signup: 0 problems
  ✓  14 e2e/accessibility.spec.js:39:5 › colorblind mode › axe scan /signup (594ms)

colorblind /dashboard: 0 problems
  ✓  15 e2e/accessibility.spec.js:44:5 › colorblind mode › axe scan /dashboard (926ms)

colorblind /reviews: 0 problems

colorblind /professors/:id: 0 problems
  ✓  16 e2e/accessibility.spec.js:50:5 › colorblind mode › axe scan reviews and professor page (1.3s)

colorblind /profile: 0 problems

colorblind /verification: 0 problems
  ✓  17 e2e/accessibility.spec.js:63:5 › colorblind mode › axe scan /profile and /verification (1.2s)

colorblind /appointments: 0 problems

colorblind /ml-classifier: 0 problems
  ✓  18 e2e/accessibility.spec.js:74:5 › colorblind mode › axe scan /appointments and /ml-classifier (1.3s)
  ✓  19 e2e/auth.spec.js:4:1 › wrong password shows an error and stays on login (578ms)
  ✓  20 e2e/auth.spec.js:12:1 › register link opens the sign up page with the captcha (414ms)
  ✓  21 e2e/auth.spec.js:27:1 › sign up needs the password to match (418ms)
  ✓  22 e2e/auth.spec.js:41:1 › profile page has the deactivate form with password and captcha (681ms)
  ✓  23 e2e/auth.spec.js:54:1 › student verification page opens from the profile (943ms)
  ✓  24 e2e/auth.spec.js:65:1 › not verified student cannot open reviews (779ms)
  ✓  25 e2e/navigation.spec.js:4:1 › logged out user is sent to the login page (442ms)
  ✓  26 e2e/navigation.spec.js:11:1 › login goes to the dashboard and logout comes back (642ms)
  ✓  27 e2e/navigation.spec.js:22:1 › logged in user cannot see the login page (545ms)
  ✓  28 e2e/navigation.spec.js:31:1 › dropdown opens each page with its own url (1.2s)
  ✓  29 e2e/navigation.spec.js:51:1 › browser back button goes to the page before (662ms)
  ✓  30 e2e/navigation.spec.js:61:1 › refresh logs you out and sends you to login (643ms)
  ✓  31 e2e/navigation.spec.js:68:1 › unknown url shows the 404 page (255ms)
  ✓  32 e2e/reviews.spec.js:5:1 › search finds a professor and opens the professor page (682ms)
  ✓  33 e2e/reviews.spec.js:27:1 › search with no match shows an empty message (602ms)

  33 passed (29.9s)
```
