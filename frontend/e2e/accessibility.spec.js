import { test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { login } from "./helpers";

// pages that anyone can open, and pages that need a login
const publicPages = ["/login", "/signup"];
const privatePages = ["/dashboard", "/reviews", "/professors/101", "/profile"];

// only the WCAG 2.0 / 2.1 level A and AA rules
const wcagTags = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

async function scan(page, url) {
  const results = await new AxeBuilder({ page }).withTags(wcagTags).analyze();

  console.log("\n" + url + ": " + results.violations.length + " problems");
  for (const v of results.violations) {
    console.log(
      "  [" + v.impact + "] " + v.id + " (" + v.nodes.length + " places)",
    );
    console.log("    " + v.help);
    for (const node of v.nodes) {
      console.log(
        "    -> " + node.target + " | " + node.failureSummary.split("\n")[1],
      );
    }
  }
}

for (const url of publicPages) {
  test("axe scan " + url, async ({ page }) => {
    await page.goto(url);
    await scan(page, url);
  });
}

for (const url of privatePages) {
  test("axe scan " + url, async ({ page }) => {
    await login(page);
    await page.goto(url);
    await scan(page, url);
  });
}
