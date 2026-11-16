import { test, expect } from "@playwright/test";
import { login } from "./helpers";

test("search finds a professor and opens the professor page", async ({
  page,
}) => {
  await login(page);
  await page.goto("/reviews");

  await page.getByPlaceholder("Search professor name").fill("cody");
  await expect(page.getByText("Professor Cody")).toBeVisible();

  await page.getByRole("button", { name: "View" }).click();
  await expect(page).toHaveURL(/\/professors\/\d+/);
  await expect(
    page.getByRole("heading", { name: "Professor Cody" }),
  ).toBeVisible();
});

test("search with no match shows an empty message", async ({ page }) => {
  await login(page);
  await page.goto("/reviews");

  await page.getByPlaceholder("Search professor name").fill("zzzzz");
  await expect(page.getByText("No professors found.")).toBeVisible();
});
