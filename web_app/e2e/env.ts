// Single source for the e2e backend's address — imported by BOTH
// playwright.config.ts (webServer + baseURL) and fixtures.ts (the
// runtime-URL override injected into every browser context).
//
// NOT 5170 (the dev backend's port): the built SPA's env default is
// `${hostname}:5170/api`, and the config's `reuseExistingServer` probes the
// port — on 5170 both would silently target a live dev backend and the
// suite would mutate the real dev database. A dedicated port makes that
// impossible.
export const E2E_PORT = 5171;
export const E2E_BASE_URL = `http://localhost:${E2E_PORT}`;
