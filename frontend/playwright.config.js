import { defineConfig } from "@playwright/test";

// e2e tests open the real app in chrome and click around like a user
export default defineConfig({
  testDir: "./e2e",
  // use the chrome that is already installed, no extra download
  use: {
    baseURL: "http://localhost:5173",
    channel: "chrome",
    screenshot: "only-on-failure",
  },
  // start the vite dev server for us (or reuse it if it is already running)
  webServer: {
    command: "npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: true,
  },
});
