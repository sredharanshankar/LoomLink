import { test, expect } from "@playwright/test";

test("owner login navigates to /app/dashboard", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel(/employee.?code/i).fill("OWN-001");
  await page.getByLabel(/password/i).fill("password");
  await page.getByRole("button", { name: /login/i }).click();
  await expect(page).toHaveURL(/\/app\/dashboard/, { timeout: 10_000 });
});
