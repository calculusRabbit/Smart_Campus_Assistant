import { test, expect } from "@playwright/test";
import { login, openFromMenu } from "./helpers";

// the seeded professors are all called "TestFname Test last name"
test("search finds a professor and opens the professor page", async ({
  page,
}) => {
  await login(page);
  await openFromMenu(page, "Reviews");

  await page.getByPlaceholder("Search professor name").fill("testfname");
  await expect(
    page.getByText("TestFname Test last name").first(),
  ).toBeVisible();

  await page.getByRole("button", { name: "View" }).first().click();
  await expect(page).toHaveURL(/\/professors\/\d+/);
  // the professor page is the only one with this button and an h1 (the list uses h3)
  await expect(
    page.getByRole("button", { name: /Back to search/ }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { level: 1, name: "TestFname Test last name" }),
  ).toBeVisible();
});

test("search with no match shows an empty message", async ({ page }) => {
  await login(page);
  await openFromMenu(page, "Reviews");

  await page.getByPlaceholder("Search professor name").fill("zzzzz");
  await expect(page.getByText("No professors found.")).toBeVisible();
});
