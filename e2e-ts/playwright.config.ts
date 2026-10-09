import { defineConfig, devices } from '@playwright/test';

// The app to test: the live Azure URL in CI, or a local server by default.
const baseURL = process.env.E2E_BASE_URL || 'http://127.0.0.1:8080';

export default defineConfig({
  testDir: './tests',
  // A cold start of the demo plus several LLM calls can take a while.
  timeout: 180_000,
  expect: { timeout: 60_000 },
  fullyParallel: false,
  // Few workers: each test costs LLM calls, and the free Azure app is small.
  workers: 2,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  // Chromium only: enough for this app, and faster in CI.
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
