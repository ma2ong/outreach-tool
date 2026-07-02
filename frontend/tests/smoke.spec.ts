import { test, expect } from "@playwright/test";

test("dashboard loads leads and stats", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("客户开发看板")).toBeVisible();
  await expect(page.getByText("客户总数")).toBeVisible();
  // table has at least one data row
  await expect(page.locator("table tbody tr").first()).toBeVisible();
});
