import { expect, test } from "@playwright/test";

test("app loads and shows header", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "LLM Debate" })).toBeVisible();
});
