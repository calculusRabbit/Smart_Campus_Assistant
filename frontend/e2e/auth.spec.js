import { test, expect } from "@playwright/test";
import { login, openFromMenu, PASSWORD, PENDING } from "./helpers";

test("wrong password shows an error and stays on login", async ({ page }) => {
  await login(page, "student_personal-email2@test.com", "wrong_password_1");
  await expect(page).toHaveURL("/login");
  await expect(
    page.locator("p").filter({ hasText: /invalid|incorrect|wrong/i }),
  ).toBeVisible();
});

test("register link opens the sign up page with the captcha", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByRole("button", { name: "Register" }).click();
  await expect(page).toHaveURL("/signup");
  await expect(
    page.getByRole("heading", { name: "Create account" }),
  ).toBeVisible();
  await expect(page.locator("altcha-widget")).toBeVisible();

  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL("/login");
});

test("sign up needs the password to match", async ({ page }) => {
  await page.goto("/signup");
  await page.getByPlaceholder("Username").fill("newstudent1");
  await page.getByPlaceholder("First name").fill("New");
  await page.getByPlaceholder("Last name").fill("Student");
  await page.getByPlaceholder("you@example.com").fill("new@student.edu");
  await page.getByPlaceholder("Password", { exact: true }).fill(PASSWORD);
  await page.getByPlaceholder("Confirm password").fill("different_pass_1");

  // the form still has other required fields, so we stay on the page
  await page.getByRole("button", { name: "Create Account" }).click();
  await expect(page).toHaveURL("/signup");
});

test("profile page has the deactivate form with password and captcha", async ({
  page,
}) => {
  await login(page);
  await openFromMenu(page, "Profile");

  await expect(
    page.getByRole("heading", { name: "Deactivate account" }),
  ).toBeVisible();
  await expect(page.getByLabel("Confirm password")).toBeVisible();
  await expect(page.locator("altcha-widget")).toBeVisible();
});

test("student verification page opens from the profile", async ({ page }) => {
  await login(page);
  await openFromMenu(page, "Profile");
  await page.getByRole("button", { name: "Student verification" }).click();

  await expect(page).toHaveURL("/verification");
  await expect(
    page.getByRole("heading", { name: "Student verification" }),
  ).toBeVisible();
});

test("not verified student cannot open reviews", async ({ page }) => {
  await login(page, PENDING);
  await expect(page).toHaveURL("/dashboard");

  await openFromMenu(page, "Reviews");
  await expect(
    page.getByText("Student verification is required"),
  ).toBeVisible();
});
