// log in through the real login page (the only place that knows the steps,
// so if the login page changes we fix it here)
export async function login(page, email = "jane@wsu.edu") {
  await page.goto("/login");
  await page.getByPlaceholder("Email").fill(email);
  await page.getByPlaceholder("Password").fill("password123");
  await page.getByRole("button", { name: "Log In" }).click();
}
