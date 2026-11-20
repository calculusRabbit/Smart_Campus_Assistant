// the login is only kept in memory now, so a page reload (page.goto) logs you out.
// that means after login the tests have to click around like a real user.

// seeded accounts (all use the same password). make e2e sets their status first
export const PASSWORD = "Password_123";
export const VERIFIED = "student_personal-email2@test.com"; // status open
export const PENDING = "student_personal-email4@test.com"; // not verified yet

// log in through the real login page (the only place that knows the steps,
// so if the login page changes we fix it here)
export async function login(page, email = VERIFIED, password = PASSWORD) {
  await page.goto("/login");
  await page.getByPlaceholder("Email").fill(email);
  await page.getByPlaceholder("Password").fill(password);
  await page.getByRole("button", { name: "Log In" }).click();
}

// open a page from the dropdown in the top bar
export async function openFromMenu(page, name) {
  await page.locator("nav button[aria-expanded]").click();
  await page.getByRole("button", { name, exact: true }).click();
}
