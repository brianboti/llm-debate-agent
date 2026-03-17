import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "tests-e2e",
  timeout: 60_000,
  use: {
    baseURL: "http://localhost:5173",
  },
  webServer: {
    command: "npm run dev -- --host 127.0.0.1 --port 5173",
    url: "http://localhost:5173",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    stdout: "ignore",
    stderr: "pipe",
  },
});

