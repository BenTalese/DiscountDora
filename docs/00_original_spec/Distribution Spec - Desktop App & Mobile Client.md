# Distribution Spec — Desktop App (self-contained) & Mobile Client (remote backend)

> **Purpose**: Hand this document back to Claude later to resume work on packaging Dora for end users.
> **Scope**: Two parallel deliverables — (1) a self-contained desktop app for Windows + Linux (+ macOS stretch), and (2) thin mobile clients for Android + iOS that talk to a remote/self-hosted Dora backend.
> **Out of scope**: Hosted SaaS, multi-tenant infrastructure, marketing site.

---

## 0. Current Architecture Snapshot

Captured so a future agent can confirm nothing has drifted before planning.

- **Backend**: Python 3.11, Flask 3 + Flask-SQLAlchemy + Flask-Migrate. Clean architecture (Clapy toolkit).
- **Two API processes**:
  - `dora_api` — port `5170` (main domain: stock, shopping lists, recipes, meals)
  - `merchant_api` — port `5172` (merchant scraping / deals)
  - `emailer` — APScheduler worker, currently commented out in `startup.sh`
- **Frontend**: Quasar 2 / Vue SPA in `web_app/`, served by `quasar serve` on port `5174` in dev. Build output goes to `web_app/dist/spa`.
- **Database**: SQLite by default. Path derived in `dora_api/infrastructure/configuration_manager.py:36` as `Path().resolve() / 'data' / 'dora.data.db'` (CWD-relative — must change).
- **Container glue**: `Dockerfile` + `compose.yml` + `startup.sh` orchestrate the three processes. Named volumes for `cache`, `data`, `config`.
- **Auth**: Not yet wired (roadmap item "I cannot access anything on Dora without logging in" still pending).
- **Pre-release**: Project status memory confirms destructive schema changes are acceptable.

Before starting either deliverable, the agent should re-read these files to check for drift:
- `compose.yml`, `Dockerfile`, `startup.sh`
- `dora_api/app.py`, `dora_api/startup.py`, `dora_api/infrastructure/configuration_manager.py`
- `merchant_api/startup.py`
- `web_app/quasar.config.js`, `web_app/src/boot/*` (for API base URL handling)

---

## 1. Deliverable A — Desktop App (Self-Contained)

### 1.1 Goals
- Single installer per OS (`.exe` for Windows, AppImage for Linux, `.dmg` for macOS as stretch).
- No Docker, no Python install, no Node install on the user's machine.
- Database and config live in the platform's standard user-data directory.
- Launches a native-feeling window (no browser tab).
- Works fully offline for all features that don't intrinsically need the internet (deal scraping is the obvious exception).

### 1.2 Non-Goals
- Auto-update infrastructure (defer until there are users).
- Code signing (defer; document the SmartScreen workaround instead).
- Multi-user / sync across devices (out of scope — that's what the mobile client is for).

### 1.3 Chosen Stack — Option A
- **Bundler**: PyInstaller (one-folder mode, not one-file — faster startup, easier antivirus story).
- **Window shell**: [pywebview](https://pywebview.flowrl.com/) using the platform-native backend (Edge WebView2 on Windows, WebKitGTK on Linux, WKWebView on macOS).
- **Process model**: Single Python process. Flask runs on a background thread bound to `127.0.0.1` on a dynamically chosen free port. pywebview points its window at that URL.
- **Installer**:
  - Windows: Inno Setup (free, scriptable).
  - Linux: AppImage via `python-appimage` or `appimage-builder`.
  - macOS (stretch): `dmgbuild` + ad-hoc signing.

### 1.4 Required Code Changes

#### 1.4.1 Collapse the three processes into one
- Convert `merchant_api` into a Flask Blueprint mounted on the `dora_api` app under a path prefix (e.g. `/merchant/`). Alternatively, keep two Flask apps but run both on threads inside one process, each on its own random local port. Blueprint route is preferred — simpler frontend config.
- Frontend: update the Quasar boot file that holds API base URLs to read a single base URL (no separate merchant URL). Inject the base URL at runtime via a `window.__DORA_API__` global set by pywebview's `js_api` (avoids hardcoding ports into the built SPA).
- Delete `quasar serve` from the runtime path. Flask serves `web_app/dist/spa` directly via a catch-all route (with SPA history-mode fallback to `index.html`).
- `startup.sh` is no longer used for desktop; keep it for the Docker path if you maintain both.

#### 1.4.2 Fix the SQLite + config paths
- Add `platformdirs` to `requirements.txt`.
- Replace `Path().resolve() / 'data' / 'dora.data.db'` in `configuration_manager.py:36` with `platformdirs.user_data_dir("Dora", "BenTalese")` and ensure the directory exists at startup.
- Apply the same change to any other CWD-relative paths (cache dir for `requests_cache`, config dir, log dir). Use `user_cache_dir`, `user_config_dir`, `user_log_dir` respectively.
- Honour an env var override (`DORA_DATA_DIR`) so power users / tests can redirect storage.

#### 1.4.3 Migrations on first run
- Bundle the Alembic migration scripts as package data (`dora_api/persistence/migrations/**`). Confirm `MANIFEST.in` / PyInstaller `--add-data` includes them.
- On startup, after the data dir is resolved, run the equivalent of `flask db upgrade` programmatically (`alembic.config.main(["upgrade", "head"])` or via Flask-Migrate's `upgrade()` helper) before serving requests.
- If the DB is brand new, this also handles initial schema creation — no separate "create" path.

#### 1.4.4 Process bootstrap
New entry point file `desktop_app.py` at repo root:
1. Resolve user data dir; ensure subdirs exist.
2. Load config (env > config file > defaults).
3. Run migrations.
4. Pick a free localhost port (`socket.socket(); s.bind(("127.0.0.1", 0)); s.getsockname()[1]`).
5. Start Flask on that port in a daemon thread (use `werkzeug.serving.make_server` so it can be cleanly shut down, *not* `app.run`).
6. Wait for a `/health` endpoint to return 200 (max ~5s).
7. Launch pywebview window pointing at `http://127.0.0.1:<port>/`.
8. On window close, signal Flask to shut down and exit.

#### 1.4.5 Scheduler / scraper considerations
- APScheduler must run in-process (BackgroundScheduler), not as a separate worker.
- Long-running scrapes must not block the Flask thread — already async-friendly thanks to `Flask[Async]`, but verify.
- `requests_cache` SQLite path needs the same `platformdirs` treatment.

#### 1.4.6 Logging
- Replace any stdout-only logging with rotating file logs in `user_log_dir`. Stdout is invisible in a bundled GUI app on Windows.
- Add a "Open log folder" menu item via pywebview's menu API for support.

#### 1.4.7 Settings UI
- The emailer currently expects env vars. For desktop, expose SMTP config in a Settings page in the SPA, persisted to the SQLite DB (new `app_settings` table) or a JSON file in `user_config_dir`.

### 1.5 Build Pipeline

- **PyInstaller spec file** (`dora.spec`):
  - `--add-data` for `web_app/dist/spa` → `web_app/dist/spa`
  - `--add-data` for `dora_api/persistence/migrations` → same path
  - Hidden imports likely needed for: `sqlalchemy.dialects.sqlite`, `alembic`, `apscheduler.triggers.cron`, `apscheduler.triggers.interval`, `dependency_injector` providers if they're discovered dynamically.
  - `--noconsole` on Windows to avoid the black terminal window.
  - Icon file (need to create / source `.ico`, `.icns`, `.png`).
- **CI matrix**: GitHub Actions, jobs for `windows-latest`, `ubuntu-latest` (+ `macos-latest` stretch). Each job: `npm ci && quasar build` then `pip install -r requirements.txt && pyinstaller dora.spec` then platform packaging step.
- **Release artefact naming**: `Dora-<version>-<os>-<arch>.{exe,AppImage,dmg}`.

### 1.6 Known Gotchas
- **Windows SmartScreen / Defender** will flag unsigned PyInstaller binaries until they accumulate reputation or you buy an EV code-signing certificate (~AUD 300/yr). Document the "More info → Run anyway" workaround in the README.
- **WebView2 runtime** is present on Windows 11 by default, but on Windows 10 some users lack it. Inno Setup can bundle the bootstrapper.
- **Linux WebKitGTK** version drift: AppImage should bundle libwebkit2gtk or document the apt dependency.
- **PyInstaller + dependency_injector** has historically needed hidden-import hints; budget half a day for first-time bundling.
- **SQLite WAL files** in the user data dir: make sure backup/restore feature copies `-wal` and `-shm` alongside the main DB.

### 1.7 Acceptance Criteria
- [ ] Fresh Windows 11 VM, no Python installed: installer runs, app launches, can create a stock item, restart preserves data.
- [ ] Fresh Ubuntu 22.04 VM: AppImage runs with no apt-get dependencies beyond what ships with a default desktop install.
- [ ] Data dir is `%APPDATA%/Dora` on Windows / `~/.local/share/Dora` on Linux.
- [ ] Uninstall leaves user data intact (configurable in Inno Setup).
- [ ] Cold start to interactive UI < 5s on a mid-range laptop.
- [ ] App size < 200 MB installed.

---

## 2. Deliverable B — Mobile Client (Remote Backend)

### 2.1 Goals
- Android + iOS apps that connect to a user-hosted Dora backend (the same Flask backend used by Deliverable A, but run on a server / always-on PC / Raspberry Pi).
- Reuse the existing Quasar SPA code as much as possible.
- App provides a "Connect to your Dora" onboarding flow where the user enters their server URL + credentials.

### 2.2 Non-Goals (Initial)
- On-device offline mode (the phone is a thin client; if the server is unreachable, show a clear error).
- Push notifications (deferred — requires per-platform infrastructure).
- App Store / Play Store publishing automation (manual for v1).

### 2.3 Chosen Stack
- **Quasar Capacitor mode** (`quasar dev -m capacitor` / `quasar build -m capacitor`).
- Capacitor 5+ for native shell.
- Reuse the existing Vue SPA codebase verbatim where possible; gate any desktop-only UI behind `$q.platform.is.mobile`.

### 2.4 Required Changes

#### 2.4.1 Backend prerequisites (also benefit desktop self-hosters)
- **Authentication**: roadmap already has "I cannot access anything on Dora without logging in" — this *must* land before mobile is viable. Recommend session cookies with a "remember me" long-lived token, or a simple JWT. Don't overthink it for a single-user-per-server hobby app.
- **CORS**: mobile WebView calls the backend cross-origin. Add `Flask-Cors` (already in requirements) configuration that accepts the configured "mobile origin" and `capacitor://localhost` / `http://localhost`.
- **HTTPS**: document Caddy / Tailscale Funnel / Cloudflare Tunnel as the recommended way to expose the backend safely. Plain HTTP only allowed on local network with explicit user opt-in.
- **Health + version endpoint**: `/api/health` returning `{ version, schema_version, features }` so the mobile app can detect incompatible backend versions and prompt the user to upgrade.

#### 2.4.2 Frontend changes
- **API base URL**: introduce a "Server" setting (server URL + auth token) stored in Capacitor Preferences (`@capacitor/preferences`). Quasar boot file resolves base URL from there on mobile, falls back to `window.location.origin` on web/desktop.
- **Onboarding flow**: first-launch screen → enter server URL → ping `/api/health` → log in → store token.
- **Mobile-specific UX from existing notes** (already in `Feature Notes/`):
  - `The  add new  button is at the bottom right when on mobile and top left when on desktop.md`
  - `I can swipe right on the shopping cart button to bring up shopping list selection for which to add to.md`
  - `When using my camera to scan a product's barcode, I can take a photo and crop to the barcode.md`
- **Barcode scanning**: use `@capacitor-community/barcode-scanner` (Android + iOS native).
- **Camera**: `@capacitor/camera` for product photos.
- **Network status**: `@capacitor/network` to show "offline — last synced X ago" banner.

#### 2.4.3 Platform projects
- `web_app/src-capacitor/android/` and `web_app/src-capacitor/ios/` will be generated by Quasar. Commit these to the repo so CI can build without re-bootstrapping.
- App identifiers: `com.bentalese.dora` (or chosen reverse-DNS).
- Icons + splash screens generated via `@capacitor/assets` from a single 1024×1024 source.

#### 2.4.4 Build pipeline
- **Android**: GitHub Actions job on `ubuntu-latest` with the Android SDK, runs `quasar build -m capacitor -T android`, signs APK/AAB with a keystore stored in repo secrets.
- **iOS**: requires `macos-latest` runner, Xcode, Apple Developer account ($99/yr). Defer until there's a need — TestFlight only initially.

### 2.5 Distribution Strategy
- **Android v1**: side-loadable APK from GitHub Releases. Play Store publishing later.
- **iOS v1**: TestFlight only, invite-based. App Store later.
- Document in the README that "this is a self-hosted app, you need your own Dora backend running".

### 2.6 Known Gotchas
- **App Store review** will reject apps that require server config without a demo account. Provide a public read-only demo backend for the review team, OR ship a "Try demo mode" toggle.
- **Mixed content**: iOS WebView blocks HTTP from an HTTPS context. If the user's backend is HTTP-only on LAN, the app must be told to allow it via `App Transport Security` exceptions — risky and reviewer-unfriendly. Strongly push users toward HTTPS via Tailscale/Caddy.
- **Capacitor plugin churn**: pin plugin versions and budget time for plugin upgrades each year.
- **Quasar mobile breakpoints** may not match the desktop layout 1:1 — expect a pass of mobile-specific styling.

### 2.7 Acceptance Criteria
- [ ] Android APK installs on a clean device, onboarding flow connects to a locally-run Dora backend.
- [ ] Barcode scan creates / opens the matching stock item.
- [ ] Network loss shows a clear banner, retries on reconnect.
- [ ] Auth token persists across app restarts.
- [ ] iOS build runs in the iOS simulator (TestFlight is a v1.1 goal).

---

## 3. Sequencing & Dependencies

```
                  ┌──────────────────────────┐
                  │  Backend prerequisites   │
                  │  - Auth                  │
                  │  - CORS                  │
                  │  - /api/health           │
                  │  - platformdirs paths    │
                  │  - Programmatic migrate  │
                  └────────────┬─────────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
   ┌────────────────────┐             ┌────────────────────┐
   │ Desktop (A)        │             │ Mobile (B)         │
   │ - Process collapse │             │ - Capacitor setup  │
   │ - pywebview shell  │             │ - Onboarding flow  │
   │ - PyInstaller spec │             │ - Barcode + camera │
   │ - Installers       │             │ - APK signing      │
   └────────────────────┘             └────────────────────┘
```

The backend prerequisites block both deliverables and should land first. Desktop and Mobile can then progress in parallel.

### Suggested order
1. Backend prerequisites (1–2 weeks).
2. Desktop A end-to-end on Windows only (1–2 weeks).
3. Desktop A on Linux (a few days).
4. Mobile B on Android, side-loaded APK (2–4 weeks).
5. Desktop A on macOS — stretch.
6. Mobile B on iOS via TestFlight — stretch.

---

## 4. Open Questions for the User

Capture answers here before starting implementation:

- [ ] Is the desktop app the *primary* distribution channel, or is the Docker compose path also supported long-term? (Affects whether we keep `startup.sh` / `compose.yml` working.)
- [ ] App identifier / publisher name for code signing and store listings?
- [ ] Willingness to pay for code-signing certs and Apple Developer Program?
- [ ] Auth model: session cookies, JWT, or both?
- [ ] Single user per server, or multi-user from the start? (Roadmap mentions "Multi-user support".)
- [ ] Acceptable to drop the `quasar serve` process for desktop even though Docker users still use it?

---

## 5. How to Resume This Work Later

When handing this spec back to Claude:
1. Confirm the architecture snapshot in §0 still matches the repo (it's based on the state as of 2026-05-21).
2. Answer the open questions in §4.
3. Pick a deliverable (A or B) and a phase (prerequisites first if not done).
4. Ask Claude to produce a concrete task breakdown with file-level edits before any code changes start.
