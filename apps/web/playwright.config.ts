import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  reporter: [["list"], ["html", { outputFolder: "../../output/playwright-report", open: "never" }]],
  outputDir: "../../output/playwright",
  use: {
    baseURL: "http://127.0.0.1:15173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command: "powershell -NoProfile -ExecutionPolicy Bypass -File ../../scripts/start-qa-api.ps1",
      url: "http://127.0.0.1:18000/health",
      timeout: 120_000,
      reuseExistingServer: false,
    },
    {
      command: "powershell -NoProfile -Command \"$env:VITE_API_BASE_URL='http://127.0.0.1:18000'; npm run dev -- --host 127.0.0.1 --port 15173\"",
      url: "http://127.0.0.1:15173",
      timeout: 120_000,
      reuseExistingServer: false,
    },
  ],
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
