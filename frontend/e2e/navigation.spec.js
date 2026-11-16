import { test, expect } from "@playwright/test";
import { login } from "./helpers";

test("logged out user is sent to the login page", async ({ page }) => {
  for (const url of ["/dashboard", "/profile", "/reviews"]) {
    await page.goto(url);
    await expect(page).toHaveURL("/login");
  }
});

test("login goes to the dashboard and logout comes back", async ({ page }) => {
  await login(page);
  await expect(page).toHaveURL("/dashboard");
  await expect(page.getByText("Hey, jane")).toBeVisible();

  await page.getByRole("button", { name: /jane/ }).click();
  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page).toHaveURL("/login");
});

test("logged in user cannot see the login page", async ({ page }) => {
  await login(page);
  await page.goto("/login");
  await expect(page).toHaveURL("/dashboard");
});

test("dropdown opens each page with its own url", async ({ page }) => {
  await login(page);

  await page.getByRole("button", { name: /jane/ }).click();
  await page.getByRole("button", { name: "Reviews" }).click();
  await expect(page).toHaveURL("/reviews");

  await page.getByRole("button", { name: /jane/ }).click();
  await page.getByRole("button", { name: "Profile" }).click();
  await expect(page).toHaveURL("/profile");

  // the profile page has no top bar, it has its own back button
  await page.getByRole("button", { name: "Back to Dashboard" }).click();
  await expect(page).toHaveURL("/dashboard");
});

test("refresh and back button keep working", async ({ page }) => {
  await login(page);
  await page.goto("/profile");
  await page.reload();
  await expect(page).toHaveURL("/profile");

  await page.goBack();
  await expect(page).toHaveURL("/dashboard");
});

test("unknown url shows the 404 page", async ({ page }) => {
  await login(page);
  await page.goto("/blah");
  await expect(page.getByText("Page not found")).toBeVisible();

  await page.getByRole("button", { name: "Go to Dashboard" }).click();
  await expect(page).toHaveURL("/dashboard");
});
