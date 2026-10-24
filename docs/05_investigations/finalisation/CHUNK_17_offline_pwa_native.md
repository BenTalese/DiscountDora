# Chunk 17 — Offline / PWA / native

**Session:** 2026-10-23 overnight (solo, no subagents) · **Stage:** 1 (analysis only — no code changed)
**Surface:** everything that makes the SPA an *app*: the Workbox service worker (`quasar.config.ts` `pwa` block, GenerateSW), the manifest + shortcuts + share target, `register-service-worker.ts`, the read-only offline story (`useNetworkStatus` → `OfflineBanner`, the `dora-api` NetworkFirst cache, `apiResponseCache` eviction on sign-out), the frontend-update flow (`usePwaLifecycle` → `UpdateBanner`), the install flow (`PwaInstallPrompt` on About), the screen wake lock (`useWakeLock`), the push-only second service worker (`public/push-sw.js`, registered by `usePushSubscription`), the Capacitor shells (`src-capacitor/{capacitor.config.json,android,ios,www}`, `boot/capacitor.ts`, `backendUrl.ts`, the native first-run gate), the mobile-keyboard inset boot, and `public/offline.html`.
**Boundaries:** `/setup/backend` page + `SplashScreen` "Change instance URL" → chunk 15 (15-R16 fixes its raw axios probe); push *content*, VAPID admin page, the push job → chunk 9 (this chunk owns only the SW-registration mechanics); backend version check on Help/About → chunk 13; desktop PyInstaller bundle, Docker/nginx, release versioning → chunk 19; `/api/client-logs` → chunk 20; scan overlay / camera → chunks 5/6 (only `cameraAvailability.ts`'s native check is read here).

---

## 0. Reading list + files walked

**Governing docs read:** `ENGINEERING_STANDARDS.md` R-052 (offline is read-only — cache reads, never buffer writes; evict user content on sign-out/401), `PLATFORM_BUILDS_AUDIT.md` (FU-327; TL;DR + spun-off FUs), `FINALISATION_PLAN.md` §3 (line 212) + §4 row 17, `DORA_VERIFY.md` sections "Offline is read-only (2026-08-23)", "Offline sync + Retry, end to end (2026-08-17)", "Native Android build (P8-10)", "PWA install + offline — origin FU-336"; feedback `# MOBILE VIEW` (empty) + `# Technical Considerations` (2 bullets). Open FUs: FU-724 (dead `custom-service-worker.ts`), FU-660 (conflict UI), FU-661 (six queued mutation kinds), FU-640 (**two entries share this id** — the 4xx-logging one and the iOS `NSCameraUsageDescription` one), FU-389 (P5-04 field test), FU-906 (install flags). Resolved and consulted: FU-336 (PWA build mode), FU-552 (iOS icons), FU-287 (iOS autoplay primer), the 2026-08-23 queue removal (372 + 649 lines).

**Files walked in full (1,506 lines + config):**

| File | Lines | Role |
|---|---|---|
| `web_app/quasar.config.ts:255–440` | 186 | `pwa` block — manifest, shortcuts, share target, GenerateSW runtime caching; `capacitor`, `electron` stubs |
| `web_app/src-pwa/custom-service-worker.ts` | 36 | InjectManifest template — **never built** (FU-724) |
| `web_app/src-pwa/register-service-worker.ts` | 42 | Quasar template, every hook an empty comment |
| `web_app/src-pwa/manifest.json` | 32 | Quasar template (`#027be3`, `icons/icon-*.png`) — every field overridden by `extendManifestJson` |
| `web_app/src/boot/capacitor.ts` | 34 | loads the persisted backend URL; native status bar + splash |
| `web_app/src/boot/pwaLifecycle.ts` | 10 | installs the lifecycle listeners once |
| `web_app/src/boot/keyboardInset.ts` | 36 | `--vv-inset-*` for iOS keyboard |
| `web_app/src/composables/useNetworkStatus.ts` | 261 | singleton `/health` poller, backoff, visibility re-probe, 5 toasts |
| `web_app/src/composables/usePwaLifecycle.ts` | 148 | install prompt, installed state, SW `controllerchange` → update |
| `web_app/src/composables/useWakeLock.ts` | 103 | Screen Wake Lock wrapper |
| `web_app/src/composables/usePushSubscription.ts` | 164 | registers `/push-sw.js` (mechanics read here; content is chunk 9) |
| `web_app/src/components/{OfflineBanner,UpdateBanner,PwaInstallPrompt}.vue` | 79+89+83 | the three shell banners |
| `web_app/src/services/api/{apiResponseCache,backendUrl}.ts` | 40+135 | cache eviction; runtime backend URL |
| `web_app/src/helpers/cameraAvailability.ts` | 48 | secure-context / native check |
| `web_app/public/{offline.html,push-sw.js}` | 47+84 | offline fallback page; push SW |
| `web_app/src-capacitor/capacitor.config.json`, `android/app/src/main/AndroidManifest.xml:40–44`, `android/app/build.gradle:7–11`, `ios/App/App/Info.plist` | — | native shells |
| `web_app/src/router/index.ts:84–100`, `routes.ts:26–38`, `layouts/MainLayout.vue:120–130`, `pages/settings/AboutSettings.vue:48–62, 340–385`, `index.html:10`, `.gitignore:46–56`, `nginx.conf:45` | — | mounts, gate, metas, ignore rules |

**Tests read:** `web_app/test/unit/` has **no** spec for `useNetworkStatus` (FU-539's note: "intentionally left — low value, awkward singleton"), `usePwaLifecycle`, `useWakeLock`, `backendUrl`, or `apiResponseCache`; the offline-queue specs were deleted with the queue. Resilience specs that remain (`rollbackRegistry`, `globalErrorHandler`, `errorBoundary`, `useUnsavedChangesGuard`) → chunk 20.

**Verification greps run:** `useOfflineQueue|conflictCount|discardConflict|retryConflict|tryWithQueue` in `web_app/src` + `web_app/test` (**none** — the queue and its conflict pile are gone; FU-660/661 describe deleted code); `\.request<|\.request(` consumers of `AxiosHttpClient.request` (**none** — only the wake-lock's unrelated `wl.request`; the method's own comment says "used by the offline queue when draining"); `offline.html` references (only the two comments in `quasar.config.ts:257, 364`; `navigateFallback` is `'index.html'` and `pwaOfflineHtmlFilename` is commented out → the file is never served); `merchant-images|/data/images` in `dora_api` + `web_app/src` (**none** — two of the three runtime-cache URL patterns match routes that no longer exist); `ls web_app/public/icons` (no `icon-128x128.png` … `icon-512x512.png` → the template manifest's icons don't exist; `extendManifestJson` replaces them); `git check-ignore web_app/src-capacitor/www` → **not ignored** (`.gitignore:51` is rooted `/src-capacitor/www`, but the folder is `web_app/src-capacitor/www`; `web_app/src-capacitor/www/index.html` is tracked); `usesCleartextTraffic|networkSecurityConfig` in the Android manifest (**none**; `capacitor.config.json` has `allowMixedContent: true`); `NS.*UsageDescription` in `Info.plist` (**none** — FU-640-iOS stands); `push-sw|scope|controllerchange` in `CHUNK_09` (records the file as "coexists with the PWA SW" — the same-scope collision below is **not** recorded there); `nginx.conf:45` no-cache rule covers both `sw.js` and `push-sw.js` ✓; `OfflineBanner` mounts (`MainLayout.vue:126`, `WelcomeLayout.vue:14`; the three page comments naming it only explain Quasar's live `offset`, no height is duplicated); bare icon strings in `OfflineBanner.vue:10, 20` (`'sync_problem'`, `'wifi_off'`, `'sync'`, `'refresh'`); `install|offline|android|pwa|home screen` in the feedback file (no bullets on this surface beyond the two under Technical Considerations).

---

## A. Full Systems Test — Offline / PWA / native

### A1. Preconditions
- A **built** frontend (`npm run build` → `dist/spa` in PWA mode) served over HTTPS or `localhost` (the SW will not register on plain HTTP); a plain-HTTP LAN install too, for the "install needs HTTPS" and camera-warning paths.
- Chrome desktop + Chrome Android (installed from the address-bar prompt), Safari iOS (Add to Home Screen), Firefox desktop (no install prompt).
- The Android APK (`quasar build -m capacitor -T android` → Android Studio) on a real phone; a LAN backend at `http://192.168.x.x:5170`.
- Two user accounts for the cache-eviction check; DevTools → Network → Offline.

### A2. Golden path (persona: a household member on a phone)
| # | Step | Expect |
|---|---|---|
| G1 | First HTTPS load | DevTools → Application → Service Workers shows `sw.js` active; Manifest shows "Dashy Dora", theme `#f5c462`, standalone, 3 shortcuts (Primary list · Shop now · Add item), share target → `/cookbook`. |
| G2 | Settings → About → **Install as an app** | Chrome: "Install Dora as an app" button → native prompt → accepted → toast "Installing Dora…"; the section then reads "Dora is installed on this device." iOS Safari: the Share → Add to Home Screen banner. Plain HTTP: "Installing needs HTTPS. This Dora is on plain http://". Firefox: "Install isn't available in this browser…". |
| G3 | Launch from the home screen | Standalone window, no browser chrome; `display-mode: standalone` marks it installed so the button never nags. |
| G4 | Long-press the icon (Android) | The three shortcuts; "Shop now" lands on `/shop-now` → the primary list's shop route (or the lists overview). Share a recipe URL from Chrome → Dora appears in the share sheet → `/cookbook` opens the paste-import dialog pre-filled. |
| G5 | Go offline (airplane mode) | Toast "You're offline. You can look around, but not make changes."; red sticky `OfflineBanner` with the same text + Retry; pages already visited render from the `dora-api` cache; a stock-level change fails, rolls back, and is reported — nothing says "queued". |
| G6 | Server stopped, network up | Banner "Can't reach Dora. You can look around, but not make changes."; probe backs off 5 s → 60 s; Retry shows a spinner then "Still can't reach the server." |
| G7 | Reconnect / server back | Within one probe (immediately if the app was backgrounded and comes back — `visibilitychange` re-probes): banner slides away, toast "Back online.", no phantom changes. |
| G8 | Deploy a new frontend build, then navigate | New SW installs with `skipWaiting` + `clientsClaim`; `controllerchange` fires with a controller already in place → accent `UpdateBanner` "A new version of Dora is ready. Reload to pick it up." → Reload → new build. Dismiss hides it for this page load. |
| G9 | Sign out, sign in as another user | `clearApiResponseCache()` ran on logout (and on any 401): no trace of the first user's pantry/lists/recipes from cache. |
| G10 | Cook mode / Shop mode | Screen stays on for the whole session (Wake Lock); re-acquired after the phone is unlocked; released on leaving the page. Unsupported browsers silently skip. |
| G11 | Android APK first launch | `/setup/backend` before anything else; enter the LAN URL → "Connected…" → `/` → login. Second launch skips the gate (Preferences). Settings → About shows the saved URL + Change. |
| G12 | APK: open a dialog with the keyboard up | Dialog stays above the keyboard (`interactive-widget=resizes-content`; iOS uses the `--vv-inset-*` fallback). |

### A3. Edge cases
- `navigator.onLine` lies (captive portal, half-dropped mobile data): the banner says offline; **Retry forces the probe** and a success flips `online` back (the 2026-08-17 fix) — pin it.
- Slow backend (> 5 s): the SW's `NetworkFirst` timeout serves the **cached** GET while axios still believes it is live → the page shows yesterday's data with no indicator (C8, 17-D2).
- Toggle **Push notifications** on Settings → Notifications: `usePushSubscription` registers `/push-sw.js` at scope `/` — the same scope `sw.js` controls → the registration is *replaced*, the Workbox worker (and all offline caching) is gone until the next load re-registers `sw.js`, and each swap fires `controllerchange` → a spurious **"A new version of Dora is ready"** banner (17-R1).
- Visiting Settings → Notifications at all (not just toggling) runs `refresh()` → `ensureRegistration()` → the same swap (17-R1).
- Plain-HTTP LAN install: no SW, no install prompt, no wake lock (SecurityError swallowed), camera "may not allow" warning; everything else works.
- Capacitor: `caches` may be absent → eviction is a no-op (by design); Push reads "unsupported" (no PushManager in the WebView); the About install section still renders the "Try Chrome on Android…" caption inside the native app (17-R9).
- Native, LAN backend over `http://`: the WebView origin is `https://localhost`, so every API call is mixed content — `allowMixedContent: true` is what makes it work; whether Android 9+'s cleartext policy also needs `usesCleartextTraffic` is **unverified** (17-R10).
- Idle PWA tab for a day: `dora-api` cache entries expire at 24 h / 200 entries; images at 7 / 30 days.
- A user who dismissed the update banner, then opens a second tab: the second tab boots on the new SW → no banner there (correct).
- Backgrounded tab: the health poll stands down (`scheduleNext` on hidden); the bell poll does the same (chunk 9) — both re-probe on `visibilitychange`.

### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (install prompt on first visit) | – | – | ✓ (APK, instance URL) | – | ✓ (G9 cache eviction) | ✓ (HTTP vs HTTPS behaviour; `nginx.conf` SW no-cache) | ✓ (HTTPS → full PWA) |

### A5. Load-bearing conditions
- **Android PWA** (G1–G8), **native Capacitor** (G11–G12), **iOS PWA** (G2 banner; wake lock on Safari 16.4+), **bad network / offline** (G5–G7, A3 first three), **360×640** (banner + Retry wrap), **all themes × light/dark** (`--q-negative` / `--q-accent` banners on `--text-on-primary`), **reduced-motion** (banner transitions use `--motion-*`).

### A6. Release-gate rows
1. G5–G7 on a phone: offline banner copy, no "queued" promise anywhere (incl. `offline.html` — 17-R2), Retry corrects `navigator.onLine`.
2. G8 after a real redeploy: exactly one update banner; **no** banner from visiting Settings → Notifications (17-R1).
3. G9 two-user cache eviction on one device.
4. G11 APK first-run → LAN `http://` backend reachable (17-R10 confirm).

---

## B. Help content — Offline / PWA / native

### B1. Current help audit
- **Nothing.** `HelpPage.vue` has no entry for offline, install, update, wake lock, the Android app or the instance URL; `app_knowledge.py` says nothing about any of it. The only "update" copy in Help is the **backend** version banner (`HelpPage.vue:43–52`, chunk 13) — a different thing from the frontend `UpdateBanner`, and users will conflate them.
- In-app copy is consistent and honest since 2026-08-23 (banner + toasts say "look around, not make changes") **except** `public/offline.html:41–44`, which still says changes "are held locally and replayed on reconnect" (17-R2).
- `PwaInstallPrompt` + About "Install as an app" section carry good copy already; `BackendSetupPage` copy is chunk 15's.

### B2. Help entries

#### Use Dora when the connection drops
- **Group:** Getting around *(new group, or "Settings & admin" if the owner prefers fewer groups)*
- **What it does:** When your phone is offline or the Dora server can't be reached, a red strip appears at the top and you can keep **looking** at anything you've opened before. Changes aren't possible until you're back — Dora never saves a change "for later", so what you see is always what the server has.
- **When it fires / how to trigger it:** Automatically, within a few seconds of losing the server; it checks again more and more slowly, and immediately when you come back to the app. **Retry** checks right now.
- **What controls it:** Always on — no setting. Works best when Dora is installed as an app over HTTPS (that's what stores pages for offline).
- **What it costs / might get wrong:** A page you've never opened while online has nothing stored, so it shows empty or an error. Over plain `http://` nothing is stored for offline at all. If the server is slow (over 5 s) you may briefly see an older copy of a page.
- **Related:** Install Dora on your phone or computer · A new version is ready.
- **Chip:** none (the banner is the surface).
- **Source:** R-052 / ADR-052; `useNetworkStatus.ts`, `quasar.config.ts` `dora-api` NetworkFirst.

#### Install Dora on your phone or computer
- **Group:** Getting around
- **What it does:** Puts a Dora icon on your home screen or launcher and opens it full-screen like any app. Long-press the icon for shortcuts (primary list, Shop now, Add item); on Android you can also **share** a recipe web page straight into Dora's cookbook.
- **When it fires / how to trigger it:** Settings → About → **Install as an app**. On iPhone/iPad: Safari's Share → **Add to Home Screen**.
- **What controls it:** `/settings/about`. Needs Dora served over **HTTPS** (or `localhost`) — on plain `http://` the page says so instead of blaming the browser.
- **What it costs / might get wrong:** Firefox desktop and some browsers never offer install. Installing doesn't change your data or sign you in anywhere new; it is the same website in its own window.
- **Related:** Use Dora when the connection drops · The Android app and your Dora address.
- **Chip:** `AboutSettings.vue:53–56` (section title) → `<HelpHint topic="Install Dora on your phone or computer">`.
- **Source:** `usePwaLifecycle.ts`, `PwaInstallPrompt.vue`, manifest `shortcuts`/`share_target`.

#### A new version is ready (reload)
- **Group:** Getting around
- **What it does:** After Dora is updated on the server, your installed app or browser tab fetches the new version in the background and shows a blue strip: *A new version of Dora is ready. Reload to pick it up.* Reload when convenient; **Dismiss** hides it until next time.
- **When it fires / how to trigger it:** On the first navigation after a new build is downloaded. This is about the **app on your device**; the yellow "newer version available" notice on Help/About is about the **server** itself and is for whoever runs it.
- **What controls it:** Always on — no setting.
- **What it costs / might get wrong:** Reloading mid-edit loses unsaved typing in a dialog, so finish first. Only this device is affected; everyone's browser updates on its own.
- **Related:** Use Dora when the connection drops.
- **Chip:** none.
- **Source:** `usePwaLifecycle.ts:131–147`, `UpdateBanner.vue`; GenerateSW `skipWaiting`/`clientsClaim`.

#### The screen stays on while you cook or shop
- **Group:** Cooking *(Cook mode group, chunk 4)* — cross-listed under Shopping
- **What it does:** In Cook mode and in Shop mode the phone doesn't lock, so a timer or the next step stays readable with wet hands, and the list stays up between aisles.
- **When it fires / how to trigger it:** Automatically on entering Cook mode or starting a shop; released when you leave.
- **What controls it:** Always on — no setting. Needs a browser with the Screen Wake Lock feature (Chrome, Edge, Safari 16.4+, Firefox 126+) and HTTPS; elsewhere the phone locks as usual.
- **What it costs / might get wrong:** Battery, modestly. If you switch apps the lock drops and comes back when you return.
- **Related:** Cook mode · Shop mode.
- **Chip:** none.
- **Source:** `useWakeLock.ts`; callers `RecipeCookMode.vue:837`, `ShoppingListDetail.vue:1243`.

#### The Android app and your Dora address
- **Group:** Getting around
- **What it does:** The Android app is the same Dora in a native wrapper. On first launch it asks for your Dora's address (for example `http://192.168.1.20:5170`) because, unlike the website, it can't guess where your server is.
- **When it fires / how to trigger it:** First launch; afterwards Settings → About → **Dora API endpoint** → Change (the app reloads).
- **What controls it:** Stored on the device only. Use the full address including `http://` or `https://`.
- **What it costs / might get wrong:** Push notifications aren't available inside the Android app (use the installed web app for those). Camera and screen-on work as on the web.
- **Related:** Install Dora on your phone or computer · Choose your instance (chunk 15's entry).
- **Chip:** `AboutSettings.vue` "Dora API endpoint" row → `<HelpHint topic="The Android app and your Dora address">`.
- **Source:** `backendUrl.ts`, `router/index.ts:88–96`, `boot/capacitor.ts`.

### B3. DoraBot corpus delta
Add to `APP_OVERVIEW` (nothing exists today):
> - Offline: when the server can't be reached a red strip appears; pages already opened still show, but nothing can be changed until the connection is back. Dora never queues changes.
> - Install: Settings → About → Install as an app puts Dora on the home screen (needs HTTPS). A blue "new version ready" strip means reload this device; the yellow version notice on Help is about the server.
> - Android app: the same Dora in a native shell; it asks for the server address on first launch (Settings → About to change it). Push notifications work in the installed web app, not inside the Android app.

---

## C. Senior review — Offline / PWA / native

### C1. Bugs (verified or high-confidence latent)

**17-R1 — Two service workers fight over the same scope; the push SW evicts the Workbox SW and fires a false "new version" banner.** class: high-confidence latent (spec-level, verified by read) · where: `usePushSubscription.ts:19, 56–67` (`navigator.serviceWorker.register('/push-sw.js')`, no `scope`), `register-service-worker.ts:7–12` (`sw.js`, no `scope`), `push-sw.js:3–5` ("the two coexist at different paths"), `usePwaLifecycle.ts:135–146` (the `hadControllerAtBoot` guard, whose own comment names "the Notifications page registering the push SW" as the false positive it works around) · what's wrong: a registration is keyed by **scope**, not script URL; both default to `/`. Registering `/push-sw.js` where `/sw.js` already controls `/` is an *update* of that one registration — the browser installs push-sw, `skipWaiting` + `clients.claim()` (`push-sw.js:17–27`) make it take over immediately, and the Workbox worker (precache, `dora-api` NetworkFirst, image caches) is gone until the next full load re-registers `sw.js`, which then evicts push-sw and the push subscription's SW with it. Each swap fires `controllerchange`; when a controller existed at boot the guard passes and `UpdateBanner` shows. `refresh()` runs on **mount** of Settings → Notifications, so merely opening that page triggers the swap. · exact change: ship **one** worker — GenerateSW `importScripts: ['push-sw.js']` in `extendGenerateSWOptions` (Workbox supports it), strip push-sw's own `install`/`activate` handlers (Workbox owns those), and have `usePushSubscription.ensureRegistration()` use `await navigator.serviceWorker.ready` / `getRegistration()` instead of registering; keep a dev-only fallback that registers `/push-sw.js` when no registration exists (SPA/dev mode has no `sw.js`). Then the `hadControllerAtBoot` guard can stay as belt-and-braces. · blast: M (push + offline both touched; needs G8 + the Notifications-page check in a built PWA) · guard: D1 · verdict: **execute** · cross-ref: chunk 9 (`push-sw.js` content unchanged).

**17-R2 — `public/offline.html` promises offline replay that no longer exists — and is never served anyway.** class: verified · where: `offline.html:41–44` ("Ticks, stock-level bumps, restock marks and expiry pushes that you make while offline are held locally and replayed on reconnect"); `quasar.config.ts:364–366` comment says "fall back to /offline.html" but sets `navigateFallback = 'index.html'`; `pwaOfflineHtmlFilename` commented out (:257); no other reference · what's wrong: R-052 forbids copy that promises syncing; the file also hard-codes brand hex and would be stale the day it *was* served. Under R-052 the SPA shell *is* the right offline fallback, so the page has no job. · exact change: delete `web_app/public/offline.html`; fix the comment at :364 to say the shell is the fallback; drop the `DORA_VERIFY` bullet "navigating to an uncached route shows Dora's `offline.html`" (PWA section) since it can never pass. · blast: S · guard: none (build) · verdict: **execute**.

**17-R3 — `.gitignore` misses the Capacitor build output; `src-capacitor/www/index.html` is tracked.** class: verified · where: `.gitignore:50–51, 55` are rooted (`/src-capacitor/www`) but the folder is `web_app/src-capacitor/www` (Quasar's template `.gitignore` assumed the repo root is `web_app/`); `git ls-files` shows 1 tracked file; `node_modules` and `android/app/build` happen to be clean · exact change: `web_app/src-capacitor/www/`, `web_app/src-capacitor/node_modules/`, `web_app/src-cordova/**` patterns in the root `.gitignore` (or a `web_app/src-capacitor/.gitignore`); `git rm --cached web_app/src-capacitor/www/index.html` (Stage 2 — **touches the index**, so flag it in the handoff; no commit without the owner). · blast: S · verdict: **execute**.

**17-R4 — Stale planning artefacts describe the deleted offline queue.** class: verified docs · where: `FINALISATION_PLAN.md:212` ("the offline queue (`useOfflineQueue`) vs Workbox background sync") and `:313` (row 17 "offline queue"); `DORA_VERIFY.md` "Offline sync + Retry, end to end (2026-08-17)" (asks to confirm "Synced everything" and "sync on re-open" — contradicts the "Offline is read-only (2026-08-23)" section 500 lines earlier; only its **Retry** bullets are still true); `DORA_FOLLOWUPS.md` **FU-660** (conflict pile) and **FU-661** (six queued kinds) describe code that no longer exists (grep: none). · exact change: plan — replace both mentions with "read-only offline (R-052): the `dora-api` NetworkFirst cache + `useNetworkStatus`"; VERIFY — delete the sync bullets, merge the Retry bullets into the 08-23 section; FUs — move 660 + 661 to RESOLVED as *superseded by R-052 (2026-08-23 queue removal)*. · blast: S · verdict: **execute** (orchestrator does the ledger move).

**17-R5 — Duplicate follow-up id: two `[OPEN] FU-640` entries.** class: verified ledger defect · where: `DORA_FOLLOWUPS.md` — "FU-640 — A user-visible failure produced an empty log bundle: 4xx responses aren't logged" and `:3831` "FU-640 — iOS Capacitor shell has no `NSCameraUsageDescription`" · exact change: renumber the iOS one to the next free id (orchestrator; from FU-929) and fix any `[[FU-640]]` links that meant it. The iOS finding itself still stands (`Info.plist` has no usage strings — grep). · verdict: **execute** (ledger).

**17-R6 — `AxiosHttpClient.request()` is dead and its comment names the deleted queue.** class: verified · where: `axiosHttpClient.ts:436–449` ("Raw config-bearing call used by the offline queue when draining"); grep: no caller · exact change: delete the method. · blast: S · guard: `vue-tsc` · verdict: **execute**.

**17-R7 — Sign-out eviction clears the API cache but not the image caches.** class: verified vs R-052's own rule ("a cache that holds user content is evicted on sign-out and on 401") · where: `apiResponseCache.ts:22, 34` matches only `'dora-api'`; `quasar.config.ts:380–400` also fills `dora-merchant-images` and `dora-stock-images` (stock-item photos **are** user content; product images are catalogue). · exact change: `API_CACHE_NAME_FRAGMENTS = ['dora-api', 'dora-stock-images']` (keep merchant/product images — shared catalogue, and the R-045 authed-image helper from 10-R35/13-R41 bypasses the SW cache anyway); rename the module `swCacheEviction.ts`. · blast: S · guard: D3 · verdict: **execute**.

**17-R8 — Two of the three runtime-cache URL patterns target routes that don't exist.** class: verified · where: `quasar.config.ts:386` `/\/products\/.*\/image|merchant-images/` (`merchant-images` left with `merchant_api`, Phase D) and `:397` `/\/stock-items\/.*\/image|\/data\/images\//` (`/data/images/` — no such route; grep none) · exact change: drop the dead alternations; keep `/products/<id>/image` and `/stock-items/<id>/image`. (Note the authed-image helper in chunks 10/13 fetches images via axios with credentials — those requests still pass through the SW `fetch` handler, so the rules still apply.) · blast: S · verdict: **execute** (ride-along with 17-R7).

**17-R9 — The About "Install as an app" section renders inside the native Android app and tells the user to "try Chrome".** class: verified by read · where: `AboutSettings.vue:52–61` has no native guard; `PwaInstallPrompt.vue:37–40` final `v-else`; `isInstalled()` is only standalone/`appinstalled` (Capacitor's WebView reports neither) · exact change: `v-if="!isNativePlatform()"` on the section (import from `backendUrl.ts`), or have `PwaInstallPrompt` render "You're using the Dora app." when native. · blast: S · verdict: **execute**.

**17-R10 — Android cleartext policy for an `http://` LAN backend is unverified.** class: finding (medium confidence) · where: `capacitor.config.json:8–10` `allowMixedContent: true`; `AndroidManifest.xml` has no `android:usesCleartextTraffic` / `networkSecurityConfig` · what's wrong: Android 9+ blocks cleartext by default in WebView; Capacitor's own guidance for http servers is to set `usesCleartextTraffic="true"`. The P8-10 VERIFY row ("enter the LAN URL… → Connected") has never been ticked, so it is unknown whether the APK can reach an `http://192.168…` backend on a current phone. · exact change: none until confirmed — if the device test fails, add `android:usesCleartextTraffic="true"` to `<application>` (or a network-security-config allowing cleartext to private ranges only). · verdict: **FU** (confirm on device; see §E).

### C2. Redundancy / DRY (R-001, R-003)

**17-R11 — Offline copy is written in six places.** where: `useNetworkStatus.ts:151, 163, 172, 189, 221` (five `Notify.create` strings) + `OfflineBanner.vue:43–44` — the two "look around, but not make changes" sentences appear 3×. The 2026-08-23 correction note (`:144–147`) had to be applied in two files. · exact change: `offlineCopy.ts` exporting `OFFLINE_COPY = { offline, unreachable, backOnline, stillDown, networkDetected }`; banner + toasts read it. Also drop the stale "the queue drain (which watches `apiReachable`) can run" comment at `:139–141`. · blast: S · verdict: **execute**.

**17-R12 — `OfflineBanner.vue` and `UpdateBanner.vue` are the same component.** where: identical template shape (icon · text · `q-space` · ghost actions), identical 40-line scoped CSS (sticky, `z-index: 2500`, `--elevation-1`, enter/leave transform) differing only in `--q-negative` vs `--q-accent` and the enter/leave class names. · exact change: `ShellBanner.vue` (props `tone: 'negative' | 'accent'`, `icon`, default slot, `#actions` slot, `role=status aria-live=polite`); both become ~20-line wrappers. `DemoBanner.vue` (chunk 19) is a third candidate consumer. · blast: S · verdict: **execute** (R-001).

**17-R13 — `src-pwa/manifest.json` is the untouched Quasar template; `extendManifestJson` rewrites every field.** where: `manifest.json:2–31` (`#027be3`, `#ffffff`, `icons/icon-128…512.png` — files that don't exist in `public/icons`) vs `quasar.config.ts:274–317` · exact change: make `manifest.json` the source of truth (real name, colours, display, icons) and shrink `extendManifestJson` to the parts that need code comments (`share_target`, `shortcuts`); or delete the base fields the hook overrides. One place, not two (R-003). · blast: S · guard: FU-336's build check (manifest emitted) · verdict: **execute**.

**17-R14 — `backendUrl.ts` declares the same key twice.** where: `:23–24` `PREF_KEY === LS_KEY === 'dora.backendBaseUrl'` · exact change: one `STORAGE_KEY`. · verdict: **execute** (trivial ride-along).

### C3. Dead code / unused fields / unread endpoints

**17-R15 — `src-pwa/custom-service-worker.ts`** — never built (GenerateSW); tracked: **FU-724**, whose point stands: it is the file a future agent would edit. · exact change: delete it (Quasar regenerates the scaffold only in InjectManifest mode) and add a two-line comment at the top of the `pwa` block in `quasar.config.ts`: "the SW that ships is generated from `extendGenerateSWOptions` below — there is no hand-written worker" (plus `push-sw.js` once 17-R1 imports it). The eslint-ignore FU-336 added for it goes too. · verdict: **execute** (resolves FU-724).

**17-R16 — `register-service-worker.ts`** — eight empty hook stubs from the template. Not dead (Quasar needs the file to register `sw.js`) but noise. · exact change: keep `register(...)` with only the hooks that matter: `updated()` → nothing (the `controllerchange` path in `usePwaLifecycle` is the real signal), `error(err)` → `console.warn`. · verdict: **execute** (S) — or **waive** as template; recommend the trim.

**17-R17 — `useNetworkStatus` exports `lastSeenOnline`** — grep: no consumer outside the composable (`OfflineBanner` destructures five other fields). · exact change: drop the ref and its two writes. · verdict: **execute**.

**17-R18 — `useWakeLock` returns `{ active, supported }`** — both callers (`RecipeCookMode.vue:837`, `ShoppingListDetail.vue:1243`) call it for the side effect and discard the return; `supported` is a ref that is never updated after init. · exact change: return nothing (or keep `active` only if a chip ever wants it — none does); use lib.dom's `WakeLockSentinel` type and `navigator.wakeLock` directly instead of the local alias + two casts (TS ≥ 4.4 ships it). · verdict: **execute**.

### C4. Componentisation opportunities (R-001)
- 17-R12 (`ShellBanner`). Nothing else — the surface is already composable-sized.

### C5. Placement / layering (R-003, R-005)

**17-R19 — `boot/pwaLifecycle.ts` and `boot/capacitor.ts` are two boot files for one concern (platform shell).** Fine as is; Quasar boot files are the right layer. **waive**.

**17-R20 — `isNativePlatform()` lives in `services/api/backendUrl.ts`** but is imported by `cameraAvailability.ts`, `router/index.ts`, `boot/capacitor.ts`, `SplashScreen` for non-URL reasons. · exact change: `helpers/platform.ts` exporting `isNativePlatform`, `isIosSafari` (from `usePwaLifecycle.ts:48–53`), `isSecureContext()`; `backendUrl.ts` imports it. · blast: S · verdict: **execute**.

### C6. Naming & idiom

**17-R21 — Bare Material icon strings in `OfflineBanner.vue:10, 20`** (`'sync_problem'`, `'wifi_off'`, `'sync'`, `'refresh'`) while `UpdateBanner`/`PwaInstallPrompt` use `ICONS`. · exact change: add `wifi_off`/`sync_problem`/`sync` to `ICONS` (refresh exists) and use them. · verdict: **execute** (same class as 13-R39/15's bare-icon sweep).

**17-R22 — `apiResponseCache.ts` is named for what it clears, not what it is** — it is the SW-cache eviction hook; see 17-R7's rename. **execute with 17-R7**.

### C7. Efficiency

**17-R23 — Two `/health` pollers.** `useNetworkStatus` probes `/health` every 60 s per tab; chunk 13 (13-R37) found `/health` also probed up to 9× per cold load by other readers. The shared `healthProbe` 13-R37 proposes should feed `apiReachable` too (one request, two consumers). · verdict: **execute under 13-R37**.

**17-R24 — `NetworkFirst` `networkTimeoutSeconds: 5` on `/api/**`** vs axios's own timeouts: a slow-but-alive backend yields stale cached data silently. Design-level → 17-D2. **waive** here.

### C8. Design-level findings — out of Stage-2 scope
- **17-D1 — iOS target.** `Info.plist` has no camera/photo usage strings (FU-640-iOS), `src-capacitor/ios` has never been built; `PLATFORM_BUILDS_AUDIT` puts iOS in Tier 3 ("PWA first"). Recommendation: leave unbuilt; keep the FU with its "before the first device run" trigger.
- **17-D2 — Stale-data indicator.** When the SW serves a cached API response (timeout or offline) the page can't tell. A `X-Dora-From-Cache`-style marker is impossible from GenerateSW without a plugin; the honest alternative is to drop `networkTimeoutSeconds` (serve cache only when the network *fails*) so stale data appears only when the banner is up. Owner call; recommend dropping the timeout.
- **17-D3 — `allowMixedContent: true`** is the price of an `http://` LAN backend from an `https://localhost` WebView. Document in `packaging/BUILD_NATIVE.md` (chunk 19) rather than change.
- **17-D4 — Release versioning of the APK** (`versionCode 1` / `versionName "1.0"`, `build.gradle:10–11`) is unlinked from Dora's version. Chunk 19 (release process).
- **17-D5 — Feedback "kivy P2P sync between standalone installs".** Not pursued: the product is one server + many clients (charter Decision 5, GitLab-way); R-052 explicitly forbids client-side conflict resolution. Recorded as answered.

### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `useNetworkStatus` | 261-line singleton poller + backoff | `@vueuse/core` `useNetwork`/`useOnline` | **keep** | — | VueUse only wraps `navigator.onLine`; the `/health` probe, backoff and the forced Retry are the value. |
| `usePwaLifecycle` | install prompt + `controllerchange` | `vite-plugin-pwa`'s `useRegisterSW` | **keep** | — | Quasar owns the build; the composable is 148 lines. |
| `useWakeLock` | Wake Lock wrapper | `@vueuse/core` `useWakeLock` | **replace-candidate, low priority** | S | VueUse's version does the same incl. visibility re-acquire; swap only if VueUse is adopted elsewhere (chunk 20 decides). |
| GenerateSW runtime caching | config | InjectManifest hand-written SW | **keep GenerateSW** | — | FU-724's conclusion; 17-R1 adds `importScripts` for push. |
| `backendUrl.ts` | Preferences/localStorage URL store | — | keep | — | — |
| `keyboardInset.ts` | visualViewport insets | — | keep | — | 36 lines, one listener. |

### C10. Standards drift (R-0NN)
- **R-052** — `offline.html` copy (17-R2); image caches not evicted (17-R7); stale queue references in plan/VERIFY/FUs/code comments (17-R4, 17-R6, 17-R11).
- **R-003** — offline copy ×6 (17-R11); manifest fields ×2 (17-R13); storage key ×2 (17-R14); platform check location (17-R20).
- **R-001** — two identical banners (17-R12).
- **R-035 / D-rules** — bare icons (17-R21); brand hex in `quasar.config.ts:280–281` and `offline.html` — the manifest cannot read CSS tokens, so the config hex stays with a `// D-rule carve-out: manifest colours are build-time` comment (D-002/D-004 can't apply); `offline.html` goes.
- **Repo hygiene** — `.gitignore` paths (17-R3).

### C11. Ride-along signals for FU-010 / FU-224 (theme / colour)
- Banners paint `var(--q-negative)` / `var(--q-accent)` with `--text-on-primary` — confirm the accent/on-primary pair meets D-002 in every theme (the warning-badge pattern from 16-C11 is the same risk).
- Manifest `theme_color #f5c462` is DS1's primary; if the theme system (FU-010) ever changes the default swatch the manifest won't follow — note in the theme proposal.

---

## D. Test plan — Offline / PWA / native

| # | Test | Layer | Priority | Trigger to write it |
|---|---|---|---|---|
| D1 | `usePushSubscription.ensureRegistration` uses the existing registration (`serviceWorker.ready`) and never calls `register()` when one exists; falls back to registering `/push-sw.js` only when `getRegistration()` is null | vitest (mock `navigator.serviceWorker`) | **must-write-before-ship** | with 17-R1 |
| D2 | `usePwaLifecycle`: `controllerchange` with no controller at boot → no update; with a controller → `updateAvailable`; `dismissUpdate` hides; `installUnavailableReason` → `insecure-context` when `isSecureContext === false` | vitest | nice-to-have | with 17-R1 (pins the guard the fix relies on) |
| D3 | `clearApiResponseCache` deletes `dora-api*` and `dora-stock-images*`, leaves `dora-merchant-images*`, never throws when `caches` is undefined | vitest (mock `caches`) | nice-to-have | with 17-R7 |
| D4 | `backendUrl.normaliseUrl` — scheme default, `/api` suffix, trailing-slash trim (and whatever 15-R16/`BackendSetupPage` decides about `http://` LAN defaults) | vitest | nice-to-have | when the scheme rule is next touched |
| D5 | Build check: `npm run build` emits `sw.js` containing `importScripts("push-sw.js")` and no `offline.html` reference | script / CI (`grep` on `dist/spa/sw.js`) | nice-to-have | with 17-R1/R2 — a one-line check in the build script, not a test suite |
| — | `useNetworkStatus` | — | **no** (FU-539 stance) | manual G5–G7 |

No Playwright. Device walk (`DORA_VERIFY` P8-10 + PWA sections) remains the real proof.

---

## E. Proposed follow-ups (orchestrator allocates ids)

- **urgent · bug** — `/push-sw.js` and `sw.js` share scope `/`; opening Settings → Notifications replaces the Workbox SW and shows a false "new version" banner (17-R1). Resolution: **now** (Stage 2, chunk 17; browser-verify G8 + Notifications page in a built PWA).
- **bug · copy / R-052** — `public/offline.html` promises replay and is never served (17-R2). Resolution: **now**.
- **finding · repo hygiene** — `.gitignore` Capacitor patterns are rooted at the wrong level; `src-capacitor/www/index.html` tracked (17-R3). Resolution: **now**; the `git rm --cached` needs a commit → owner.
- **finding · ledger** — duplicate id FU-640 (17-R5): renumber the iOS `NSCameraUsageDescription` entry. Resolution: **now**.
- **resolve as superseded** — FU-660, FU-661 (queue deleted 2026-08-23, R-052) (17-R4). Resolution: **now**.
- **resolve** — FU-724 once `custom-service-worker.ts` is deleted + the config comment added (17-R15).
- **finding · device check** — Android cleartext to an `http://` LAN backend from the APK is unverified; `usesCleartextTraffic` absent (17-R10). Resolution: **when the P8-10 VERIFY row is walked**; add `usesCleartextTraffic="true"` if it fails. Also append to FU-389 (field test).
- **decision** — 17-D2: drop `networkTimeoutSeconds: 5` so cached API data only appears when the network actually fails. Resolution: owner, opportunistic.
- **docs** — `FINALISATION_PLAN.md:212, 313` + `DORA_VERIFY.md` "Offline sync + Retry" section stale (17-R4). Resolution: **now**.

---

## F. Feedback coverage

`# MOBILE VIEW` has no bullets. `# Technical Considerations` (2):

| Bullet | Status | Where |
|---|---|---|
| "kivy P2P test branch — standalone no-server installs that link and sync" | ✅ answered **no** (17-D5) | charter Decision 5 (one artifact, server + clients); R-052 forbids client conflict resolution; nothing to build. |
| "single sources of truth for front-end data and operations; the more in the backend the better" | ✅ shipped as policy | R-003 + the state-ownership principle (`CLAUDE.md`); R-052 is its offline corollary (no client-side ledger). |

Other sections: `# SPLASH`, `# CANNOT CONNECT` → chunk 15 (both shipped); no feedback bullet mentions install, offline, update or the Android app (grep).

### Register summary
- **FST rows:** 12 golden + 11 edges · **Help entries:** 5 new + DoraBot 3 lines (none existed) · **Review findings:** 24 (execute 19 / FU 1 / waive 3 / decision 1) + 5 design notes · **Tests:** 5 (must-write 1) · **Bugs:** 7 (17-R1, R2, R3, R4, R5, R6, R7) + 1 to confirm on device (R10)
- **One line:** the read-only offline story is coherent and the install/update flows are solid, but a second service worker registered at the same scope quietly evicts the first every time Notifications settings opens, the unserved `offline.html` still promises the sync that was removed, and the plan/VERIFY/FU ledgers still describe the deleted queue — plus the Capacitor build output isn't ignored.
