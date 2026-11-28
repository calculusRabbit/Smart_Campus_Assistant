import { test, expect } from "@playwright/test";
import { login, openFromMenu } from "./helpers";

test("logged out user is sent to the login page", async ({ page }) => {
  for (const url of ["/dashboard", "/profile", "/reviews", "/verification"]) {
    await page.goto(url);
    await expect(page).toHaveURL("/login");
  }
});

test("login goes to the dashboard and logout comes back", async ({ page }) => {
  await login(page);
  await expect(page).toHaveURL("/dashboard");
  await expect(
    page.getByText(/Good (morning|afternoon|evening)/),
  ).toBeVisible();

  await openFromMenu(page, "Log out");
  await expect(page).toHaveURL("/login");
});

test("dashboard shows the week calendar with the classes", async ({ page }) => {
  await login(page);

  await expect(page.getByRole("heading", { name: "This week" })).toBeVisible();
  await expect(page.getByText("Mon", { exact: true })).toBeVisible();

  // classes repeat every week, so there is always at least one block
  await expect(page.locator(".fc-timegrid-event").first()).toBeVisible();
});

test("logged in user cannot see the login page", async ({ page }) => {
  await login(page);
  await expect(page).toHaveURL("/dashboard");

  // back button goes to /login, the app should push us to the dashboard again
  await page.goBack();
  await expect(page).toHaveURL("/dashboard");
});

test("dropdown opens each page with its own url", async ({ page }) => {
  await login(page);

  await openFromMenu(page, "Reviews");
  await expect(page).toHaveURL("/reviews");

  await openFromMenu(page, "Appointments");
  await expect(page).toHaveURL("/appointments");

  await openFromMenu(page, "ML Classifier");
  await expect(page).toHaveURL("/ml-classifier");

  await openFromMenu(page, "Profile");
  await expect(page).toHaveURL("/profile");

  // profile has the top bar too now (QA-1), so go back with the dropdown
  await openFromMenu(page, "Dashboard");
  await expect(page).toHaveURL("/dashboard");
});

test("browser back button goes to the page before", async ({ page }) => {
  await login(page);
  await openFromMenu(page, "Profile");
  await expect(page).toHaveURL("/profile");

  await page.goBack();
  await expect(page).toHaveURL("/dashboard");
});

// the token is only kept in memory (on purpose, safer), so refresh = logged out
test("refresh logs you out and sends you to login", async ({ page }) => {
  await login(page);
  await openFromMenu(page, "Profile");
  await page.reload();
  await expect(page).toHaveURL("/login");
});

test("unknown url shows the 404 page", async ({ page }) => {
  await page.goto("/blah");
  await expect(page.getByText("Page not found")).toBeVisible();
});
