// log in through the real login page (the only place that knows the steps,
// so if the login page changes we fix it here)
export async function login(page) {
  await page.goto("/login");
  await page.getByPlaceholder("Email").fill("jane@wsu.edu");
  await page.getByPlaceholder("Password").fill("password123");
  await page.getByRole("button", { name: "Log In" }).click();
}
