import { test, expect } from "@playwright/test";

test.describe("Daylight & Materials page", () => {
  test("shows empty state when no room is analysed", async ({ page }) => {
    await page.goto("/");

    // Navigate to the Materials tab
    await page.getByRole("button", { name: /Daylight & Materials/i }).click();

    // Should see the empty-state prompt (no analysis loaded)
    await expect(
      page.getByText(/Upload and analyse a room photo in the/i)
    ).toBeVisible({ timeout: 10_000 });

    // The 9 material score cards should NOT be rendered
    const cards = page.locator("[data-testid='material-card']");
    await expect(cards).toHaveCount(0);
  });

  test("loads material scores when an analysed room and palette exist", async ({ page }) => {
    await page.goto("/");

    // Click 'Try Sample Room' to trigger room loading, analysis, and palette generation
    const sampleBtn = page.getByRole("button", { name: /Try Sample Room/i });
    await expect(sampleBtn).toBeVisible({ timeout: 10_000 });
    await sampleBtn.click();

    // Wait for the sample room image to be loaded into Studio preview
    await expect(page.getByAltText(/Room Thumbnail/i)).toBeVisible({ timeout: 25_000 });

    // Navigate to Daylight & Materials tab
    await page.getByRole("button", { name: /Daylight & Materials/i }).click();

    // Verify 9 substrate score cards render
    const cards = page.locator("[data-testid='material-card']");
    await expect(cards).toHaveCount(9, { timeout: 15_000 });

    // Verify score values and category labels appear inside cards
    await expect(cards.first()).toContainText(/Architectural Substrate/i);
    await expect(cards.first()).toContainText(/\/100/);
  });

  test("displays Daylight simulator presets and section headers", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: /Daylight & Materials/i }).click();

    // Section headers should always be visible
    await expect(
      page.getByText(/Chrono-Photometric Simulation/i)
    ).toBeVisible();
    await expect(
      page.getByText(/9 Architectural Substrate Scores/i)
    ).toBeVisible();

    // Preset buttons
    await expect(page.getByRole("button", { name: /Morning Sun/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /High Noon/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Overcast Sky/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Golden Hour/i })).toBeVisible();
  });

  test("shows backend-offline banner when health check fails", async ({ page }) => {
    // Intercept /health to simulate offline backend
    await page.route("**/health", (route) => route.abort("connectionfailed"));

    await page.goto("/");

    // The banner polls on mount and should display "Backend offline"
    const banner = page.getByText(/Backend offline/i);
    await expect(banner).toBeVisible({ timeout: 15_000 });
  });
});
