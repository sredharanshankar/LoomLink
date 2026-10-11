/**
 * WP8 demo story e2e test.
 * Covers: login → dashboard → floor → Ripple inbox → event detail → apply fix.
 * Requires: dev server running (npm run dev) + backend seeded with demo data.
 */
import { test, expect } from "@playwright/test";

test.describe("LoomLink demo story", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/employee.?code/i).fill("OWN-001");
    await page.getByLabel(/password/i).fill("demo1234");
    await page.getByRole("button", { name: /login/i }).click();
    await expect(page).toHaveURL(/\/app\/dashboard/, { timeout: 15_000 });
  });

  test("dashboard loads with mill name", async ({ page }) => {
    await expect(page.getByText(/Everest Textile Mills/i)).toBeVisible({ timeout: 10_000 });
  });

  test("floor page shows machines", async ({ page }) => {
    await page.goto("/app/floor");
    await expect(page.getByText(/WV-0[123]/i).first()).toBeVisible({ timeout: 10_000 });
  });

  test("orders page lists active orders", async ({ page }) => {
    await page.goto("/app/orders");
    await expect(page.getByText(/ORD-10[24]/i).first()).toBeVisible({ timeout: 10_000 });
  });

  test("Ripple inbox page loads", async ({ page }) => {
    await page.goto("/app/ripple");
    // Should show either inbox title or empty state
    await expect(page.getByRole("heading", { name: /ripple/i })).toBeVisible({ timeout: 10_000 });
  });

  test("Leak Meter page shows rupee value", async ({ page }) => {
    await page.goto("/app/leak");
    await expect(page.getByText(/₹/)).toBeVisible({ timeout: 10_000 });
  });

  test("worker PIN login", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("link", { name: /pin/i }).click();
    await page.getByLabel(/pin/i).fill("1234");
    await page.getByRole("button", { name: /sign in|login/i }).click();
    // Any of the 12 workers with PIN 1234 will land on /w
    await expect(page).toHaveURL(/\/w/, { timeout: 15_000 });
  });
});
