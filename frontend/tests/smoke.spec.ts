import { test, expect } from "@playwright/test";

test("dashboard loads leads and stats", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("客户开发看板")).toBeVisible();
  await expect(page.getByText("客户总数")).toBeVisible();
  // table has at least one data row
  await expect(page.locator("table tbody tr").first()).toBeVisible();
});

// SAFETY: only checks the panel/button exists — never clicks 发送邮件 (that would send real email).
test("outreach panel is present", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("button", { name: "发送邮件" })).toBeVisible();
  await expect(page.getByText(/邮件触达/)).toBeVisible();
});

// SAFETY: only checks the panel exists — never clicks 搜索深挖/导入 (would hit network / write DB).
test("discovery panel is present", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("button", { name: "搜索深挖" })).toBeVisible();
  await expect(page.getByText(/客户开发（搜索/)).toBeVisible();
});

// SAFETY: only checks the panel exists — never clicks 连接 (would launch a real browser).
test("connection panel is present", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("渠道连接")).toBeVisible();
});
