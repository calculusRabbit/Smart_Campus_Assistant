import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { login, openFromMenu } from "./helpers";

// only the WCAG 2.0 / 2.1 level A and AA rules
const wcagTags = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

// all 3 looks of the app get scanned
const themes = ["light", "dark", "colorblind"];

// run axe on the page that is open right now, print the problems and fail if there are any
async function scan(page, name) {
  const results = await new AxeBuilder({ page }).withTags(wcagTags).analyze();

  console.log("\n" + name + ": " + results.violations.length + " problems");
  for (const v of results.violations) {
    console.log(
      "  [" + v.impact + "] " + v.id + " (" + v.nodes.length + " places)",
    );
    console.log("    " + v.help);
    for (const node of v.nodes) {
      console.log("    -> " + node.target);
    }
  }
  expect(results.violations).toEqual([]);
}

for (const theme of themes) {
  test.describe(theme + " mode", () => {
    test.beforeEach(async ({ page }) => {
      await page.addInitScript((t) => localStorage.setItem("theme", t), theme);
    });

    test("axe scan /login", async ({ page }) => {
      await page.goto("/login");
      await scan(page, theme + " /login");
    });

    test("axe scan /signup", async ({ page }) => {
      await page.goto("/signup");
      await scan(page, theme + " /signup");
    });

    test("axe scan /dashboard", async ({ page }) => {
      await login(page);
      await expect(page).toHaveURL("/dashboard");
      await scan(page, theme + " /dashboard");
    });

    test("axe scan reviews and professor page", async ({ page }) => {
      await login(page);
      await openFromMenu(page, "Reviews");
      await expect(
        page.getByPlaceholder("Search professor name"),
      ).toBeVisible();
      await scan(page, theme + " /reviews");

      await page.getByRole("button", { name: "View" }).first().click();
      await expect(page).toHaveURL(/\/professors\/\d+/);
      await scan(page, theme + " /professors/:id");
    });

    test("axe scan /profile and /verification", async ({ page }) => {
      await login(page);
      await openFromMenu(page, "Profile");
      await expect(page).toHaveURL("/profile");
      await scan(page, theme + " /profile");

      await page.getByRole("button", { name: "Student verification" }).click();
      await expect(page).toHaveURL("/verification");
      await scan(page, theme + " /verification");
    });

    test("axe scan /appointments and /ml-classifier", async ({ page }) => {
      await login(page);
      await openFromMenu(page, "Appointments");
      await expect(page).toHaveURL("/appointments");
      await scan(page, theme + " /appointments");

      await openFromMenu(page, "ML Classifier");
      await expect(page).toHaveURL("/ml-classifier");
      await scan(page, theme + " /ml-classifier");
    });
  });
}
