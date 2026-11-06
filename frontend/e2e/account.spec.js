import { test, expect } from "@playwright/test";
import { login } from "./helpers";

test("delete account asks for a password then logs you out", async ({
  page,
}) => {
  await login(page);
  await page.goto("/profile");
  await page.getByRole("button", { name: "Delete account" }).click();

  // the delete button stays off until a password is typed
  const deleteButton = page.getByRole("button", {
    name: "Delete",
    exact: true,
  });
  await expect(deleteButton).toBeDisabled();
  await page.locator("input[type=password]").fill("password123");
  await expect(deleteButton).toBeEnabled();
  await deleteButton.click();

  await expect(page).toHaveURL("/login");
  await expect(page.getByText("scheduled for deletion")).toBeVisible();
});

test("cancel closes the delete popup", async ({ page }) => {
  await login(page);
  await page.goto("/profile");
  await page.getByRole("button", { name: "Delete account" }).click();
  await expect(page.getByText("Delete your account?")).toBeVisible();

  await page.getByRole("button", { name: "Cancel" }).click();
  await expect(page.getByText("Delete your account?")).toHaveCount(0);
});

test("deleted account comes back when you log in again", async ({ page }) => {
  await login(page);
  await page.goto("/profile");
  await page.getByRole("button", { name: "Delete account" }).click();
  await page.locator("input[type=password]").fill("password123");
  await page.getByRole("button", { name: "Delete", exact: true }).click();
  await expect(page).toHaveURL("/login");

  // logging in within 30 days restores it
  await login(page);
  await expect(page).toHaveURL("/dashboard");
});

test("deleted account is blocked after 30 days", async ({ page }) => {
  await page.goto("/login");
  // pretend the account was deleted 31 days ago
  const longAgo = Date.now() - 31 * 24 * 60 * 60 * 1000;
  await page.evaluate((time) => {
    localStorage.setItem("deleted_jane@wsu.edu", time);
  }, longAgo);

  await login(page);
  await expect(page.getByText("This account was deleted.")).toBeVisible();
  await expect(page).toHaveURL("/login");
});
