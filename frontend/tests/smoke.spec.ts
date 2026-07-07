import { test, expect } from "@playwright/test";

test("shell loads with sidebar and leads table", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Maxcolor")).toBeVisible();
  await expect(page.getByRole("button", { name: /客户库/ })).toBeVisible();
  // leads page is default; table has at least one data row
  await expect(page.locator("table tbody tr").first()).toBeVisible();
  // full columns present
  await expect(page.getByRole("columnheader", { name: "电话 / WhatsApp" })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "IG" })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "FB" })).toBeVisible();
});

test("untouched filter option exists", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("select option[value='untouched']")).toHaveCount(1);
  await expect(page.locator("select option[value='phone']")).toHaveCount(1);
});

// SAFETY: only selects a row to reveal the action bar — never clicks 发送 (that would send real messages).
test("selecting a lead reveals outreach action bar", async ({ page }) => {
  await page.goto("/");
  await page.locator("table tbody tr").first().locator("input[type=checkbox]").check();
  await expect(page.getByText(/触达（已选/)).toBeVisible();
  await expect(page.getByRole("button", { name: "发送邮件" })).toBeVisible();
});

test("dashboard shows stats", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /仪表盘/ }).click();
  await expect(page.getByText("客户总数")).toBeVisible();
  await expect(page.getByText(/国家分布/)).toBeVisible();
});

// SAFETY: only checks the discovery page renders — never clicks 搜索深挖/导入 (would hit network / write DB).
test("discovery page is present", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /客户开发/ }).click();
  await expect(page.getByRole("button", { name: "搜索深挖" })).toBeVisible();
});

// SAFETY: only checks the channels page renders — never clicks 连接 (would launch a real browser).
test("channels page is present", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /渠道连接/ }).click();
  // topbar h2 and card h3 both say 渠道连接 — assert the card heading specifically
  await expect(page.locator(".card h3", { hasText: "渠道连接" })).toBeVisible();
});

test("theme toggle switches to light and persists attribute", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /浅色/ }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.getByRole("button", { name: /深色/ }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
});
