# Chunk 19 — Ops / self-host

**Session:** 2026-10-23 overnight (solo, no subagents) · **Stage:** 1 (analysis only — no code changed)
**Surface:** how Dora boots and runs anywhere but a dev shell — `app.py` (Flask, cookie config, naming convention, SQLite FK pragma), `startup.py` (`bootstrap`/`startup`/`init_db`/schema-drift guard/router discovery/global error handler/6 APScheduler jobs), `wsgi.py` + `gunicorn.conf.py` + `startup.sh` (the container path), `configuration_manager.py` + `profile.py` (env → JSON → profile layering, production gate), `logging_setup.py` + `log_context.py` (timed rotation, request/user ids), `path_migration.py`, `audit_retention.py`, `GET /api/health` (the capability/compat probe), `GET /api/help/version` (GitHub release check), the support channel, demo mode (`DORA_DEMO_MODE` → `reset_showcase`, `DemoBanner`), `desktop_app.py` + `dora.spec` + `packaging/build-*.sh` (PyInstaller bundle), `Dockerfile` + `compose.yml` + `compose.dev.yml` + `nginx.conf` + `.dockerignore`, `.env.example`, `scripts/{security-audit.sh,dev-restart.sh,mint_ingestion_key.py,set_product_search_url.py}`, the commented-out `.github/workflows/*`, the Alembic chain (156 revisions, single head `f2a6c8e1b4d7`), and the README "Get started / Docker / Desktop / Releasing" sections.
**Boundaries:** cookie/CSRF/session internals + `middleware.py` → chunk 15 (15-R1 `ProxyFix` lands here as the env knob only); `/api/client-logs` + error pages + security headers → chunk 20; the Capacitor/PWA build outputs → chunk 17; backups → chunk 18; the operational-config resolver *contents* (SMTP/VAPID/Piper AppSettings) → chunk 13; the companion stack's deploy (`deploy-dora.sh`, FU-790) → companion repo.

---

## 0. Reading list + files walked

**Governing docs read:** `RECONCILED_FINISHING_PLAN.md` §7.5 (distribution-posture checklist) + Decision 5; `IMPL_PLAN_ENV_TO_APPSETTING.md` §0 (env→AppSetting, Buckets B/C/D); `LOGGING_AND_DATA_LAYOUT.md` (INV-3 — its two recommendations, timed rotation + `.secret_key` under the data dir, **both landed**; the doc is now historical); `SECURITY_REVIEW.md` §7 register + §8 standing controls; `OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md` outline (worker split parked); `PLATFORM_BUILDS_AUDIT.md` (FU-327); README §Get started / §4 Docker / §Desktop bundles / §Releasing; `packaging/BUILD_NATIVE.md`; `DORA_VERIFY.md` "Deploy — the companion stack (2026-09-07)". Open FUs: FU-721 (revive CI/Release), FU-720 (verify the deployed route map), FU-719 (`_iter_submodules` swallows a failed subpackage import), FU-640 (4xx not logged / container `ERROR` level), FU-787 (Piper absent from a from-source install), FU-405 (Phase-4 ops), FU-406 (open-source release readiness), FU-626 (admin "newer release" notification), FU-520 (Postgres CI), FU-906 (install flags that gate nothing). Resolved and consulted: FU-397 (gunicorn), FU-570 (schema drift guard), FU-333 (env → AppSetting), FU-392 (demo mode), FU-388, FU-027, FU-509, FU-717 (rsync exclude deleted `features/data/`), FU-336 (PWA build mode).

**Files walked in full (backend 1,883 lines · infra 1,392 · desktop/demo 605):**

| File | Lines | Role |
|---|---|---|
| `dora_api/app.py` | 125 | Flask app, JSON provider, cookie config, `.secret_key`, SQLite FK pragma, Migrate |
| `dora_api/startup.py` | 403 | `bootstrap` (prod gate, CORS, path migrations, `init_db`, drift warn, logging, routers, scheduler), `init_db`, global handler |
| `dora_api/wsgi.py` · `gunicorn.conf.py` · `startup.sh` | 27 · 78 · 66 | production WSGI path |
| `dora_api/server_settings.py` | 5 | **legacy gunicorn settings (`workers=4`, port 1809) — dead** |
| `dora_api/infrastructure/configuration_manager.py` | 410 | `DoraConfig` — env/JSON/profile layering, dirs, DB URL resolution |
| `dora_api/infrastructure/profile.py` | 167 | `DORA_ENV`, required vars, two stderr banners |
| `dora_api/infrastructure/logging_setup.py` · `log_context.py` | 139 · 54 | timed rotation, UTF-8 console, request/user ids |
| `dora_api/infrastructure/path_migration.py` · `audit_retention.py` | 99 · 54 | legacy moves; nightly prune |
| `dora_api/features/health/health_check.py` | 388 | `/api/health` — flags + 6 policy blocks + support |
| `dora_api/features/help/get_version.py` · `support/support_channel.py` | 99 · 65 | release check; support switch |
| `desktop_app.py` · `dora.spec:40–110` · `packaging/build-linux.sh` · `BUILD_NATIVE.md` | 348 · — · 121 · 109 | desktop bundle |
| `Dockerfile` · `compose.yml` · `compose.dev.yml` · `nginx.conf` · `.dockerignore` · `.env.example` · `web_app/.env.example` | 86 · 197 · 39 · 83 · 25 · 180 · 3 | container + env catalogue |
| `scripts/{security-audit.sh,dev-restart.sh,mint_ingestion_key.py,set_product_search_url.py}` | 48 · 99 · 94 · 60 | operator scripts |
| `.github/workflows/{ci,release}.yml` | 95 · 164 | fully commented out (FU-721) |
| `web_app/src/composables/useDemoMode.ts` · `components/DemoBanner.vue` | 37 · 51 | demo pill |

**Tests read (names + docstrings):** `tests/e2e/dora_api/test_health_router.py` (2), `test_logging.py` (6 — request id + client logs), `test_operational_config_resolver.py` (7), `test_security_headers.py` (3), `test_security_injection.py` (11); unit `tests/test_compose_env_coverage.py` (3 — every env var `dora_api` reads is declared in `compose.yml` or in an omit-list with a reason), `tests/test_migrations.py` (7 — single head, linear, downgrades real, empty→head, down/up round-trip, migrated schema == ORM metadata, **head on Postgres**). No test covers `profile.py`'s production gate, `configuration_manager` resolution order, `desktop_app.py`, or `startup.sh`.

**Verification greps run:** `quasar build` in `Dockerfile:66` is **bare** (`npm run build` is `quasar build -m pwa`, `web_app/package.json:19`; `packaging/build-linux.sh:68` uses `npm run build`) → the Docker image is built in **SPA mode** — no `sw.js`, no manifest, no offline (FU-336 flipped the npm script but not the Dockerfile); `.dockerignore:3` excludes only the root `.env` — `web_app/.env` (which README step 1 tells the operator to create with `VITE_API_BASE_URL=http://localhost:5170/api`) is **copied into the image** by `COPY web_app/ ./` (`Dockerfile:48`) and baked into the SPA bundle; `git remote -v` → `github.com/BenTalese/dashy-dora.git`, `support_channel.py:53` → `BenTalese/dashy-dora` ✓, **`get_version.py:26` → `BenTalese/DashyDora`** (different slug; GitHub repo names are case-insensitive but `DashyDora` ≠ `dashy-dora`), CLAUDE.md Naming says the GitHub repo is still `DiscountDora` (stale — the remote was renamed; only the local folder wasn't); env vars documented but **never read by `dora_api`**: `DORA_API_SERVER`, `DORA_WEB_CONCURRENCY`, `DORA_WEB_THREADS`, `DORA_WEB_TIMEOUT` (read by `startup.sh`/`gunicorn.conf.py` — fine, but `test_compose_env_coverage` scans `dora_api` only); env vars read but undocumented in `.env.example`/`compose.yml`: `DORA_API_HOST`, `DORA_WEB_APP_HOST/PORT`, `DORA_SPA_DIR`, `DORA_CSRF_DISABLED`, `DORA_DISABLE_SECURITY_HEADERS`, `DORA_SKIP_PROD_VALIDATION`, `DORA_SEED_*` (compose lists them as deliberately omitted — ✓), plus `DORA_BIND`, `DORA_WEB_GRACEFUL_TIMEOUT`, `DORA_WEB_KEEPALIVE`, `DORA_GUNICORN_LOG_LEVEL` (gunicorn.conf only); stale env names surviving only in **comments/docstrings** (`tts_synthesize.py:10,162` still tells the user to "set `DORA_PIPER_BIN`" — an env var with no reader since FU-333; `auth_helpers.py:12` "Pulled from DORA_PUBLIC_URL"; `profile.py:83`); `get_log_level|get_web_app_host|get_web_app_port|_save_configuration|server_settings` callers (**none** — four dead `DoraConfig` methods + the JSON `LOG_LEVEL`/`WEB_APP_*` keys they serve + `server_settings.py`); `configure_logging` resolves the level from `debug` + raw `DORA_LOG_LEVEL` (`logging_setup.py:96–102`) while `DoraConfig.get_log_level()` layers env → JSON → profile and is **never called** — two resolution paths, one dead; `Discount ?Dora|DiscountDora` outside docs: `.env.example:2`, `nginx.conf:1`, `packaging/build-linux.sh:2,47`, `compose.yml` (comment on the old volume names — intentional), `dataset_import.py` (check), `AGENTS.md`/`CLAUDE.md` (the naming note itself); README stale lines: `:100` "There's no packaged release yet", `:135` "Start Postgres first (the standard datastore)" vs `compose.yml:85–93` "the self-host monolith defaults to **SQLite** … on purpose", `:202` "`5172` — merchant_api" (Phase D removed it), `:279` "merchant + emailer compile-check"; `.env.example:8–9` says appsettings live at `config/dapi.appsettings.json` (now `<DATA_DIR>/config/`); `dora_config:/app/config` volume (`compose.yml:179`) vs `_resolve_config_path()` → `<DATA_DIR>/config/` = `/app/data/config` — the volume only ever holds the **legacy source** that `migrate_legacy_appsettings` moves out on first boot; `dora.spec:51–53` comment says "RotatingFileHandler" (it is `TimedRotatingFileHandler` now — hidden import `logging.handlers` still right); `dora.spec:62` pins `webview.platforms.gtk` while `desktop_app.py:314–323` says pywebview was dropped for a browser launch; migration heads: **1** (`f2a6c8e1b4d7`); `health_check.py:356` logs **INFO** on every probe (every client polls `/health` every 60 s — chunk 17 — plus up to 9× per cold load — 13-R37); `health_check.py:379` reads `DORA_ENV` raw instead of `current_profile()` (an alias like `prod` is reported verbatim); `warn_if_insecure_cookies_in_production` fires on **every default `docker compose up`** because `compose.yml:77` defaults `DORA_SECURE_COOKIES=false` while defaulting `DORA_ENV=production`.

---

## A. Full Systems Test — Ops / self-host

### A1. Preconditions
- A clean Linux box with Docker Compose v2.24+; a second box (or VM) to reach the stack from another host; a reverse proxy with TLS for the HTTPS run.
- A Windows and a Linux machine for the desktop bundle (`build-windows.ps1`, `build-linux.sh --appimage`).
- A copy of a production SQLite DB from an older schema for the migration run; a Postgres 16 for the Postgres run (`compose.dev.yml`).
- `pip-audit` installed for the security script.

### A2. Golden path (persona: self-host operator, first deploy)
| # | Step | Expect |
|---|---|---|
| G1 | `git clone … && cp .env.example .env` and set `DORA_SECRET_KEY`, `DORA_CORS_ORIGINS`, `ADMIN_BOOTSTRAP_EMAIL`, `DORA_SECRET_ENCRYPTION_KEY` | Boots. Leave one of the three required vars blank → container exits non-zero with the "Refusing to start … Missing:" banner on stderr. |
| G2 | `docker compose up --build` | Image builds (Node 22, Piper, default voice); `startup.sh` picks gunicorn (production); `[startup] dora_api pid=…`; nginx foreground; `docker ps` healthy via `/healthz`. **Today the SPA is built in SPA mode (no `sw.js`) — 19-R1.** |
| G3 | Browse from another machine to `http://<host>:5174` | SPA loads, talks to `http://<host>:5170/api` (hostname fallback). **If `web_app/.env` existed at build time it talks to `localhost:5170` instead — 19-R2.** |
| G4 | First boot | Default compose → stderr WARNING "DORA_ENV=production and DORA_SECURE_COOKIES=false" (every boot, by default — 19-D1); `upgrade()` applies 156 migrations; `alembic_version` = `f2a6c8e1b4d7`; `/api/health` → `schema_version == schema_version_db`, `profile: production`, features block. |
| G5 | `docker compose exec dashy_dora python scripts/mint_ingestion_key.py --label companion` | Prints the raw key only on stdout; a second run revokes the first and mints one. `set_product_search_url.py http://host:5175` sets the nav link. |
| G6 | Redeploy a newer image | Migrations apply; `_warn_on_schema_drift` is silent; SPA caches roll (nginx `index.html` no-cache, hashed assets immutable). With a **stale DB** (old `create_all` file): boot continues and logs `SCHEMA DRIFT DETECTED … Missing columns: …`. |
| G7 | Logs | `/app/logs/dapi.log` rotates at midnight (`dapi.log.YYYY-MM-DD`, 14 kept); every line carries `[req=…] [user=…]`; `docker logs` shows gunicorn access + app stdout. At the default `DORA_LOG_LEVEL=ERROR` a 400 leaves **no trace** (FU-640). |
| G8 | Scheduler | At 03:00 server time the audit prune runs; 03:30 snooze prune; `:30` alerts push, `:45` daily brief, `:15` deals email all self-gate when unconfigured; `DORA_WEB_CONCURRENCY=2` → gunicorn boot warning about duplicated jobs. |
| G9 | Help → About | "Dashy Dora 0.7.0"; update check hits GitHub — **today `BenTalese/DashyDora`** (19-R3) → "Couldn't check for updates (HTTP Error 404…)" unless GitHub redirects. |
| G10 | `DORA_DEMO_MODE=true` | Boot drops + recreates the schema and seeds the showcase (`demo`/`demo`); the "Demo mode. This sample data resets periodically." pill shows on every page; reset every 60 min (`DORA_DEMO_RESET_MINUTES`). |
| G11 | Desktop: `.\packaging\build-windows.ps1 -Clean` → `dist\Dora\Dora.exe` | Per-user dirs under `%LOCALAPPDATA%\Dora\`, `.secret_key` + `.secret_encryption_key` generated, SQLite pinned, production profile with the gate skipped, random localhost port, default browser opens, Ctrl-C quits. Piper bin + voices seeded into `AppSetting` when bundled. |
| G12 | `scripts/security-audit.sh` | `pip-audit --strict` clean; `npm audit` only the accepted low items. |
| G13 | `pytest tests/test_migrations.py` against Postgres (`compose.dev.yml up postgres`) | 7/7 incl. `upgrade_head_runs_on_postgres`. |

### A3. Edge cases
- `DORA_ENV=prod` alias → profile production; `/health.profile` reports `"prod"` (19-R9).
- `DORA_SKIP_PROD_VALIDATION=true` on a server → gate and cookie warning both silenced (documented "never set this in a server deployment"; compose deliberately doesn't forward it, but `env_file` does — comment says so).
- `DORA_DB_URL` **and** `DORA_DB_PATH` set → URL wins; `DORA_DB_PATH=` (empty) → treated as unset; relative paths resolve against cwd (`/app` in the container).
- Legacy `./data/dora.data.db` + new `DORA_DATA_DIR` → moved once; populated target → warning, legacy left.
- `DORA_LOG_LEVEL=banana` → `getattr(logging, 'BANANA')` is None → falls back to debug/INFO default silently.
- `appsettings.json` `LOG_LEVEL`/`WEB_APP_*` edits → no effect (19-R5).
- Boot with a feature subpackage whose `__init__` fails to import → routes silently missing (FU-719); rsync exclude deleting a package → same (FU-717/720).
- `/api/health` with the DB down → still 200 with conservative defaults (`setting = None`), `schema_version_db: null`, flags false — a monitoring probe cannot tell "DB down" from "nothing configured" (19-D3).
- gunicorn `timeout=120` vs nginx has **no** `/api/` proxy (API exposed directly on 5170) → no proxy timeout mismatch today; the commented single-port block (nginx.conf:75–82) would need `proxy_read_timeout` ≥ 120 and 15-R1's `ProxyFix`.
- Container healthcheck hits nginx only → a wedged Python API keeps the container "healthy" (documented choice).
- Desktop: port 0 race; `/api/health` not answering within 5 s → exit 2 with a log line; closing the terminal kills the daemon thread.
- Demo mode on Postgres → `drop_all/create_all` on the real DB every hour (by design; disposable).

### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (G1–G4) | – | – | ✓ (scripts, env) | ✓ (About/version) | – | ✓ (whole chunk) | ✓ (same image; `DORA_DB_URL` Postgres; FU-405 Phase 4) |

### A5. Load-bearing conditions
- **SQLite + Postgres** (migrations, FK pragma only on SQLite, demo reset); **Docker** (compose defaults, volumes, healthcheck); **desktop installer** Windows + Linux (G11); **bad network** (version check timeout 4 s, cached 30 min); HTTPS behind a proxy (15-R1 knob).

### A6. Release-gate rows
1. G2 image ships **PWA mode** (`sw.js` + `manifest.json` present in `/app/web_app/dist/spa`) — 19-R1.
2. G3 from a second machine with `web_app/.env` present on the build host — 19-R2.
3. G4 fresh boot: `schema_version == schema_version_db`, no drift banner, 156 migrations, single head.
4. G9 version check resolves against the real repo — 19-R3.
5. `pytest tests/test_migrations.py tests/test_compose_env_coverage.py` green on SQLite **and** Postgres (G13).

---

## B. Help content — Ops / self-host

### B1. Current help audit
- Operator documentation lives in `README.md`, `.env.example`, `packaging/BUILD_NATIVE.md`, `docs/INGESTION_GUIDE.md` — not in the in-app Help, which is right (the Help page is for household members). The *user-facing* ops touchpoints that have no Help entry: the About **version check**, the **demo banner**, "**where is my data**" (desktop users ask), and "**how do I report a problem / where are the logs**". `HelpPage.vue` group *Dora itself* already has ops-adjacent entries (AI-mode encryption key, network topology) — these go there.
- README drift (19-R4) is the real documentation debt: four stale statements an operator will hit on day one.

### B2. Help entries

#### Where Dora keeps your data
- **Group:** Dora itself
- **What it does:** Everything lives on the Dora server, not in your browser. On a self-hosted Docker install that is the `dora_data` volume (`/app/data`: the database, uploads, backups, voices) with logs in `dora_logs`. The desktop app keeps the same layout under your user folder (`%LOCALAPPDATA%\Dora\` on Windows, `~/.local/share/Dora/` on Linux, `~/Library/Application Support/Dora/` on macOS).
- **When it fires / how to trigger it:** Always.
- **What controls it:** The operator's `DORA_DATA_DIR` / `DORA_LOG_DIR` (server) — never an in-app setting.
- **What it costs / might get wrong:** Deleting the volume or that folder deletes the install; take a backup first (Settings → Admin → Data). The browser only caches pages for offline reading (chunk 17).
- **Related:** Back up your install (chunk 18) · Use Dora when the connection drops (chunk 17).
- **Chip:** none.
- **Source:** `configuration_manager.get_data_dir/get_log_dir`, `desktop_app._bootstrap_paths`, `compose.yml` volumes.

#### Is there a newer Dora?
- **Group:** Dora itself
- **What it does:** Help → About shows the version you're running and, when the server can reach GitHub, whether a newer release exists, with a link to it. Updating is the operator's job (pull the new image / installer); Dora never updates itself.
- **When it fires / how to trigger it:** On opening Help/About; the answer is cached for 30 minutes.
- **What controls it:** Always on — no setting. Offline or rate-limited → "Couldn't check for updates (…)" and nothing else changes.
- **What it costs / might get wrong:** This is about the **server**. The blue "A new version of Dora is ready — Reload" strip is about the app on *your device* (chunk 17) and appears after the operator has already updated.
- **Related:** A new version is ready (reload) (chunk 17).
- **Chip:** `HelpPage.vue:43–52` (the version banner) → `<HelpHint topic="Is there a newer Dora?">`.
- **Source:** `get_version.py`; `version_info.CURRENT_VERSION`.

#### Why does a banner say "Demo mode"?
- **Group:** Dora itself
- **What it does:** The install was started as a public demo: sample data, a `demo`/`demo` admin, and everything resets to the sample on a timer (hourly by default). Nothing you change is kept.
- **When it fires / how to trigger it:** Operator-only (`DORA_DEMO_MODE`); it cannot be switched off from Settings, on purpose.
- **What controls it:** Env only.
- **What it costs / might get wrong:** Don't enter real data. If you're seeing this on your own install, your operator started it in demo mode.
- **Related:** Where Dora keeps your data.
- **Chip:** none (the pill is the surface).
- **Source:** FU-392; `DemoBanner.vue`, `startup.init_db`, `seed_showcase.reset_showcase`.

#### Reporting a problem (and what the operator can see)
- **Group:** Dora itself
- **What it does:** The **Report an issue** button (Help, error pages, Dora's chat) opens the project's issue tracker when the operator has set one up; otherwise there is no button. Every request carries an id (`X-Request-Id`) that appears in the server log, so quoting the time and what you did lets the operator find it. Browser-side errors are posted to the server log too.
- **When it fires / how to trigger it:** Help → Report an issue; or ask your operator to look at `dapi.log` (rotates daily, two weeks kept).
- **What controls it:** `DORA_SUPPORT_URL` / `DORA_SUPPORT_EMAIL` (operator). Log detail: `DORA_LOG_LEVEL` — at the container default (`ERROR`) a rejected request (400) leaves no line (FU-640).
- **Related:** Is there a newer Dora?
- **Chip:** none.
- **Source:** `support_channel.py`, `log_context.py`, FU-640, chunk 20 (`/api/client-logs`).

### B3. DoraBot corpus delta
Add to `APP_OVERVIEW`:
> - Where data lives: on the Dora server (the `dora_data` volume on Docker; the user's app-data folder on the desktop app), never in the browser. Settings → Admin → Data makes backups.
> - Updates: Help → About shows the running version and whether a newer release exists; installing it is the operator's job. A blue "new version ready" strip is just the app on this device catching up.
> - Demo mode: a floating "Demo mode" pill means the install is a resetting public demo; changes are not kept.

---

## C. Senior review — Ops / self-host

### C1. Bugs (verified or high-confidence latent)

**19-R1 — The Docker image builds the SPA in SPA mode, not PWA mode.** class: verified · where: `Dockerfile:66` `RUN quasar build` vs `web_app/package.json:19` `"build": "quasar build -m pwa"` (FU-336, 2026-07-13) and `packaging/build-linux.sh:68` `npm run build` · what's wrong: the self-host image — the primary deployment — ships **no service worker, no manifest, no install prompt, no offline cache**; everything chunk 17 analysed is absent in the container while `nginx.conf:45` dutifully no-caches a `sw.js` that isn't there. FU-336's resolution note verified `npm run build` locally, never the image. · exact change: `RUN npm run build` (one source of truth for the build mode); add a build-time assertion `test -f dist/spa/sw.js` after it so the image can't regress. · blast: S · guard: A6.1 + a `Dockerfile` smoke in FU-721's CI when revived · verdict: **execute** · **urgent**.

**19-R2 — A `web_app/.env` on the build host is baked into the Docker image's SPA.** class: high-confidence latent · where: `.dockerignore:3` excludes only the root `.env`; `Dockerfile:47–48` `COPY web_app/ ./`; README §1 instructs `cp web_app/.env.example web_app/.env` (`VITE_API_BASE_URL=http://localhost:5170/api`); `backendUrl.envDefault()` prefers a baked `VITE_API_BASE_URL` over the hostname fallback (`backendUrl.ts:37–39`) · what's wrong: an operator who followed README step 1 and then ran step 4 (`docker compose up --build`) gets an SPA that calls `localhost:5170` from every browser — works on the host, breaks from every other device; nothing in the build warns. · exact change: `.dockerignore` += `web_app/.env`, `web_app/.env.*`, `!web_app/.env.example` (and `**/.env` generally); README step 1 should say the frontend `.env` is for `quasar dev` only. · blast: S · guard: A6.2 · verdict: **execute**.

**19-R3 — The update check points at the wrong GitHub repo slug.** class: verified · where: `get_version.py:26` `https://api.github.com/repos/BenTalese/DashyDora/releases/latest` vs `git remote` `BenTalese/dashy-dora` (and `support_channel.py:53`, README `:115` — both `dashy-dora`) · what's wrong: unless GitHub still redirects an older name, every "Is there a newer Dora?" check 404s and Help/About shows "Couldn't check for updates (HTTP Error 404…)" forever; the error is swallowed into the DTO so nothing logs it. · exact change: one `GITHUB_REPO = "BenTalese/dashy-dora"` constant in `version_info.py`, used by `get_version.py` and `support_channel.py` (R-003); confirm with one `curl` at Stage 2. Also update CLAUDE.md Naming (the *GitHub* repo is already renamed; only the local folder is `DiscountDora`). · blast: S · guard: D4 · verdict: **execute**.

**19-R4 — README tells a new operator four things that are no longer true.** class: verified docs · where: `README.md:100` "There's no packaged release yet"; `:135` "Start Postgres first (the standard datastore)" while `compose.yml:85–93` makes SQLite the production-compose default "on purpose"; `:202` "`5172` — merchant_api" (removed Phase D); `:279` "merchant + emailer compile-check" + "CI runs on every push" (both workflows are commented out, FU-721). Plus `.env.example:8–9` appsettings path (`config/dapi.appsettings.json` → `<DATA_DIR>/config/`), `.env.example:2`/`nginx.conf:1`/`build-linux.sh:2,47` still say "DiscountDora/Discount Dora" (CLAUDE.md Naming). · exact change: rewrite those lines; state the posture once ("Postgres for dev + managed, SQLite for the single-box self-host image; both supported — Decision 5") so README and compose agree. · blast: S · verdict: **execute**.

**19-R5 — Two log-level resolvers; the layered one is dead.** class: verified · where: `DoraConfig.get_log_level()` (`configuration_manager.py:190–223`: env → JSON `LOG_LEVEL` → profile default, 30 lines) has **no caller**; `configure_logging` (`logging_setup.py:96–102`) resolves from `debug` + raw `DORA_LOG_LEVEL`. Consequences: the JSON `LOG_LEVEL` key the file generates on first boot does nothing; an invalid `DORA_LOG_LEVEL` is silently ignored in one place and mapped to `NOTSET` in the other; the comment at `.env.example:120` lists FATAL which `getattr(logging,…)` also accepts — fine. · exact change: `configure_logging(level=DORA_CONFIG.get_log_level())`, drop the env read inside `logging_setup.py`, drop the `if/elif` ladder for `logging.getLevelName`/`getattr`, and log a one-line warning for an unknown value. · blast: S · guard: D2 · verdict: **execute** (R-003).

**19-R6 — `/api/health` logs at INFO on every probe.** class: verified · where: `health_check.py:356` · what's wrong: every open client polls it every 60 s (chunk 17) and a cold load hits it up to 9× (13-R37); in an `INFO` install this is the dominant log line and drowns FU-640's signal. · exact change: `_Logger.debug(...)` or remove (gunicorn's access log already records the request). · blast: S · verdict: **execute**.

### C2. Redundancy / DRY (R-001, R-003)

**19-R7 — Repo slug ×3, product name ×N.** `DashyDora` / `dashy-dora` / `DiscountDora` across `get_version.py`, `support_channel.py`, README, compose comments, `.env.example`, `nginx.conf`, build scripts (see 19-R3/R4). · exact change: `version_info.py` owns `PRODUCT_NAME`, `GITHUB_REPO`, `CURRENT_VERSION`; shell/docs cite the one URL. · verdict: **execute**.

**19-R8 — Two "treat empty env as unset + parse int" helpers.** `configuration_manager._env/_env_int` (`:60–76`) and `gunicorn.conf._int` (`:23–30`) — gunicorn's config can't import the app (it must stay import-light), so this one is a **legitimate duplicate**; comment it as such (`# mirrors configuration_manager._env_int — gunicorn.conf must not import dora_api`). · verdict: **explain in place**.

**19-R9 — Profile read raw instead of through `current_profile()`.** `health_check.py:379` `(os.environ.get("DORA_ENV") or "development").lower()` → `current_profile().value`, so aliases (`prod`, `ci`) report canonically. · verdict: **execute** (R-003).

**19-R10 — Truthy-env parsing written five ways.** `{"1","true","yes","on"}` in `configuration_manager.py:239, 253, 306, 319, 396`, `profile.py:92, 144`, `middleware.py:263` (`("1","true","yes")` — no `on`), `desktop_app._set_default_env`. · exact change: `configuration_manager.env_flag(name, default=False)`; nine call sites. · blast: S · verdict: **execute**.

**19-R11 — The two stderr banners in `profile.py` share the box-drawing frame** (`:100–118`, `:150–164`) → `_banner(title_lines, body_lines)`. · verdict: **execute** (tiny).

### C3. Dead code / unused fields / unread endpoints

**19-R12 — `dora_api/server_settings.py`** — legacy gunicorn settings (`workers = 4`, `bind 0.0.0.0:1809`, "startup:app"); grep: no reference anywhere; contradicts `gunicorn.conf.py`'s single-worker rule. · **execute** (delete).

**19-R13 — Dead `DoraConfig` surface.** `get_log_level` (19-R5), `get_web_app_host`, `get_web_app_port`, `_save_configuration`, `is_modification_tracking_enabled` (returns `True`, unused), `is_reloader_enabled` (returns `False`; one caller — inline the constant or keep as the documented knob). The JSON `Config` model then shrinks to `API_HOST`, `API_PORT` — at which point the whole `appsettings.json` layer serves two values that env also covers (19-D2). · **execute** (delete the dead five; keep the file for now).

**19-R14 — `dora_config:/app/config` volume** (`compose.yml:179`) — the config file lives at `<DATA_DIR>/config/` (`_resolve_config_path`), i.e. inside `dora_data`; `/app/config` is only the legacy source `migrate_legacy_appsettings` moves *out of*. The comment "legacy fallback for un-env'd vars" is wrong. · exact change: drop the volume (or point it at `/app/data/config` — but that's inside `dora_data` already); note in the compose "NOTE for existing deployments". · blast: S · verdict: **execute**.

**19-R15 — Stale instructions naming env vars that no longer exist.** `tts_synthesize.py:10` and `:162` (user-facing error text!) say "set `DORA_PIPER_BIN`" — removed by FU-333 (Bucket B strict, DB-only); `auth_helpers.py:12` "Pulled from DORA_PUBLIC_URL"; `profile.py:83` docstring example; `dora.spec:51–53` "RotatingFileHandler"; `dora.spec:60–62` pins `webview.platforms.gtk` for a pywebview the app no longer uses (`desktop_app.py:314–323`). · exact change: fix the error text to "set the Piper path under Settings → Admin → System → Voice"; drop the two spec entries. · verdict: **execute** (the `:162` one is user-visible — also a copy bug).

**19-R16 — `.dockerignore` lists `docker-compose.yml` (old filename) and `**/p2ptest`, `**/.buildozer` (the kivy branch artefacts).** Tidy: `compose*.yml` isn't needed in the image either. · verdict: **execute** (with 19-R2).

**19-R17 — `startup.sh:13,24,31` default `DORA_LOG_DIR=/app/data/logs`** while compose/Dockerfile/`.env.example` say `/app/logs` and `get_log_dir()` defaults to `<DATA_DIR>/logs/dapi`. Three defaults for one path; harmless only because compose always sets it. · exact change: make `startup.sh` echo the resolved value without inventing a default (or use the same `/app/logs`). · verdict: **execute**.

### C4. Componentisation opportunities (R-001)
- None on this surface (operator scripts and config, not UI). `DemoBanner.vue` is a third `ShellBanner` consumer if 17-R12 lands.

### C5. Placement / layering (R-003, R-005)

**19-R18 — `audit_retention.py` lives in `infrastructure/` but is a feature job** (reads an `AppSetting` via a function-level import from `features/app_settings` to dodge a cycle; the other five jobs live under `features/*`). · exact change: move to `features/audit/prune_audit_events.py` beside the audit feature; `startup.py` imports it like the others. · verdict: **execute**.

**19-R19 — Scheduler wiring is 80 lines inline in `bootstrap()`** (`startup.py:106–186`) with six function-level imports. · exact change: `dora_api/jobs.py: register_jobs(scheduler)` (or `features/scheduler.py`) that lists the jobs as data (`(func, trigger, id)`); `bootstrap` calls it. Also makes FU-720's "log the job table at boot" a one-liner. · blast: S · verdict: **execute**.

**19-R20 — `health_check._feature_flags` still owns three `getattr(setting, "...", default)` reads per block** for columns that all exist on `AppSetting` (`stocktake_enabled`, `nutrition_rating_scheme`, `household_headcount`, …) — the `getattr` defaults hide a renamed column as "feature off" rather than failing. · exact change: direct attribute access (the migration chain guarantees the columns; `_warn_on_schema_drift` covers the stale-DB case). · verdict: **execute** (R-003 — one truth, no shadow defaults).

**19-R21 — Seven `except Exception: pass` blocks in `health_check.py`** (`:207, 238, 263, 284, 303, 319, 335`) — the "never fail the probe" intent is right, the silence isn't: a broken DB reports every feature as off with no log line (A3). · exact change: one `_safe(block, fallback)` helper that logs at WARNING once per probe. · verdict: **execute**.

### C6. Naming & idiom
- **19-R22** — `_Logger = logging.getLogger(__name__)` inside functions (`startup.py:315, 368`, `get_version.py:81`, `audit_retention.py:36`) vs module-level elsewhere — the same sweep as 16-R27 / 18-R25. **execute**.
- **19-R23** — `get_attributes_ending_with` has an unreachable second `return _Attributes` (`utils.py:85`). **execute** (delete).
- **19-R24** — `startup.register_routers` passes `Path() / 'dora_api' / 'features'` which `_to_package_name` turns into the dotted name — pass the string `"dora_api.features"` and drop the path pretence (the docstring already says both forms are accepted). **execute**.
- **19-R25** — `.env.example` section ordering puts the KEK (`DORA_SECRET_ENCRYPTION_KEY`) after "API server tuning" though it is one of the two secrets every server install must set; move it under "Secrets / auth" and mark it **required for email/push/AI keys**. **execute** (docs).

### C7. Efficiency
- **19-R26** — `/api/health` does three DB round-trips per probe (`alembic_version`, AppSetting, `Product.count()`) plus `complex_is_usable` and the operational-config resolver; the docstring (`:12`) still says "never touches the DB". With chunk 17's 60 s poll × N clients this is the app's hottest endpoint. · exact change: cache `_resolve_db_schema_version()` after the first non-null answer (it changes only on deploy); fix the docstring; leave the rest (they're cheap and must be fresh). **execute**.
- **19-R27** — `_warn_on_schema_drift` runs `inspector.get_columns` for ~60 tables at every boot — fine (boot-time only). **waive**.

### C8. Design-level findings — out of Stage-2 scope
- **19-D1 — Default compose boots production with `DORA_SECURE_COOKIES=false`**, so the "deliberate opt-out" banner fires on every default boot and the fail-closed default in `app.py` is defeated by the shipped compose. Either default compose to the app's default (unset → Secure on, which breaks plain-HTTP LAN installs until TLS) or keep `false` and drop the banner to a one-line INFO. Owner call; recommend: keep `false` (LAN-first self-host), keep the banner **once**, and add the TLS/proxy recipe (15-R1) to README.
- **19-D2 — Retire `appsettings.json`?** After 19-R13 it carries `API_HOST`/`API_PORT` only, both env-overridable; `path_migration.migrate_legacy_appsettings` + the `dora_config` volume exist for it. Recommend retiring the file (env-only; FU-333's direction) in a later release with a one-boot "ignored" warning.
- **19-D3 — `/api/health` can't say "degraded".** A DB outage still returns `ok: true`. Add `"db": "ok" | "unreachable"` (keys are only ever added). Small; chunk-17 banner could then say "Dora is up but its database isn't".
- **19-D4 — FU-640** (log 4xx on mutating routes at WARNING / raise the container default to WARNING) — owner policy call; the Stage-1 read supports option (a) + default `INFO` in the container (gunicorn already writes an access line per request, so the marginal cost is small).
- **19-D5 — FU-720 / FU-719** (route-map verification; `onerror` on `walk_packages`): FU-719's fix is one argument (`onerror=lambda name: _Logger.exception(...)`) — recommend executing it as part of 19-R19 rather than waiting; FU-720's "log registered route count per blueprint at boot" is the cheapest shape and fits the same place.
- **19-D6 — CI** stays off by owner policy (FU-721/405). Nothing here changes that; 19-R1 is exactly the class of regression CI would have caught.

### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `configuration_manager.py` (env → JSON → profile) | 410-line hand layering | `pydantic-settings` | **keep, shrink** | — | After 19-R13/D2 it is ~200 lines of env readers with dir side-effects; pydantic-settings would add a dependency to replace `os.environ.get`. Not worth it. |
| `profile.py` production gate | 60 lines | — | keep | — | — |
| `logging_setup.py` | stdlib handlers | `structlog` / `loguru` | **keep** | — | Request-id contextvar filter is 15 lines; structured JSON logging isn't asked for. |
| APScheduler in-process | library | Celery / RQ / cron | **keep** | — | Single-worker contract documented thrice; externalising is the parked Path-A work. |
| `get_version._semver_tuple` | 8 lines | `packaging.version` | **replace** | S | `packaging` is already a transitive dep; `Version("0.10.0") > Version("0.7.0")` is right where the naive tuple also is, but pre-release handling (`v0.8.0-rc.1`, which `release.yml` explicitly allows) is wrong in the hand version. |
| `scripts/dev-restart.sh` | 99 lines | `flask --debug` reloader | keep | — | `is_reloader_enabled()` is deliberately False (double-boot + scheduler); the script is the honest workaround. |
| Docker healthcheck via nginx `/healthz` | — | hit `/api/health` | keep | — | Documented trade-off; 19-D3 would make `/api/health` a better target later. |

### C10. Standards drift (R-0NN)
- **R-003** — build mode in two places (19-R1); repo slug ×3 (19-R3/R7); log level ×2 (19-R5); truthy parse ×9 (19-R10); log-dir default ×3 (19-R17); profile read raw (19-R9); `getattr` shadow defaults (19-R20).
- **R-005 (distribution posture §7.5)** — ✓ repository-routed data access (health uses the repo + one raw `alembic_version` read, fine); ✓ Postgres + SQLite both tested (`test_migrations` 7/7 incl. Postgres); ✓ env/config-driven differences; ✓ auth behind an interface; ✓ no `tenant_id`; ✓ managed conveniences degrade (push/email self-gate). **Drift:** README vs compose on the datastore default (19-R4).
- **R-021** — scheduler crons run in **server** TZ (`TZ=Australia/Sydney` in compose) and the household-local jobs gate internally ✓; `prune_audit_events` cutoff is UTC ✓.
- **R-030 (operational config)** — honoured; the support channel's explicit out-of-scope note stands.
- **Naming (CLAUDE.md)** — "DiscountDora/Discount Dora" in `.env.example:2`, `nginx.conf:1`, `build-linux.sh:2,47` (19-R4); CLAUDE.md's own note about the GitHub repo is stale (19-R3).
- **Security** — `.secret_key` 0o600? `app.py:81` `write_text` uses default perms (desktop: `desktop_app.py:114` same) → `Path.touch(mode=0o600)` first; `uploads.py` already does `0o600`. Add to 19-R5's neighbour fix. **execute** (S).

### C11. Ride-along signals for FU-010 / FU-224 (theme / colour)
- `DemoBanner.vue:8` bare icon `name="visibility"` → `ICONS`; `--brand-accent`/`--text-on-accent` pair is the same contrast question as 17-C11.
- `offline.html`'s brand hex (chunk 17) and `manifest` colours are the only places ops config carries theme — none here.

---

## D. Test plan — Ops / self-host

| # | Test | Layer | Priority | Trigger to write it |
|---|---|---|---|---|
| D1 | Build-time assertion in `Dockerfile`: `RUN test -f dist/spa/sw.js && test -f dist/spa/manifest.json` after the SPA build | Docker build step | **must-write-before-ship** | with 19-R1 (not a pytest; it is the only place the image's build mode is observable) |
| D2 | `test__log_level__resolves_env_then_json_then_profile` + `__unknown_value_warns_and_falls_back` | pytest (unit, `DoraConfig` with a temp config path) | nice-to-have | with 19-R5 |
| D3 | `test__profile__production_gate_lists_every_missing_var` / `__skip_flag_bypasses` (SystemExit captured) | pytest unit | nice-to-have | opportunistic — `profile.py` has zero tests |
| D4 | `test__version_check__repo_slug_matches_support_channel` (both import the one constant) | pytest unit | **must-write-before-ship** | with 19-R3 |
| D5 | `test__health__profile_reports_canonical_name` (`DORA_ENV=prod` → `"production"`) | pytest e2e | nice-to-have | with 19-R9 |
| D6 | Extend `test_compose_env_coverage` scan dirs to `gunicorn.conf.py` + `startup.sh` so `DORA_WEB_*`/`DORA_API_SERVER` are **read-side** verified, not just omit-listed | pytest unit | nice-to-have | with 19-R17 |
| D7 | `test__dockerignore_excludes_frontend_env` (string check on `.dockerignore`) | pytest unit | nice-to-have | with 19-R2 — cheap structural pin, same spirit as `test_compose_env_coverage` |
| — | Desktop bundle, compose boot, migrations on a real old DB | manual (A2) | — | release walk |

---

## E. Proposed follow-ups (orchestrator allocates ids)

- **urgent · bug** — Docker image builds the SPA without `-m pwa`; the self-host deployment has no service worker/manifest/offline (19-R1). Resolution: **now**; verify in the built image (A6.1).
- **bug** — `web_app/.env` is copied into the image and bakes `localhost:5170` into the SPA (19-R2). Resolution: **now** (`.dockerignore` + README).
- **bug** — version check targets `BenTalese/DashyDora`; remote is `dashy-dora` (19-R3). Resolution: **now**; one constant; also fix CLAUDE.md Naming (GitHub repo already renamed).
- **docs** — README/.env.example/nginx.conf/build scripts: stale ports, datastore posture, CI claim, old product name, appsettings path (19-R4). Resolution: **now**.
- **finding** — `DoraConfig.get_log_level` dead; two log-level resolvers (19-R5); `server_settings.py` + four dead config methods (19-R12/R13); `dora_config` volume unused (19-R14). Resolution: **now**.
- **copy bug** — Piper error text tells users to set a removed env var (19-R15). Resolution: **now**.
- **finding** — `/health` INFO log per probe + three DB reads with a "never touches the DB" docstring (19-R6/R26). Resolution: **now**.
- **execute FU-719's one-line fix** (`onerror` on `walk_packages`) and FU-720's cheapest shape (log route count per blueprint at boot) as part of 19-R19 — append to both FUs rather than new ids.
- **decision** — 19-D1 compose cookie default + banner; 19-D2 retire `appsettings.json`; 19-D3 `/health.db`; 19-D4 = FU-640 policy. Owner.
- **security hygiene** — `.secret_key` / `.secret_encryption_key` written with default perms (C10). Resolution: **now** (S).
- **replace** — `_semver_tuple` → `packaging.version` (C9). Resolution: **now** (S).
- **VERIFY** — add "Docker image: DevTools → Application shows `sw.js` registered" to the FU-336 PWA section once 19-R1 lands; mark INV-3 `LOGGING_AND_DATA_LAYOUT.md` as historical (both recommendations landed).

---

## F. Feedback coverage — `# NO AREA / MISC` (ops-relevant bullets) + Technical

| Bullet | Status | Where |
|---|---|---|
| "Why is the `.local` folder so messy? … logs in two different locations" | ✅ answered + shipped | INV-3: `data/` ÷ `cache/` is intentional; desktop uses OS dirs (`platformdirs`); dev logs under `<data>/logs/dapi`. Doc now historical. |
| "Are the logs rolling? 46,539 lines spanning dates" | ✅ shipped | `TimedRotatingFileHandler`, midnight, 14 kept (FU-027) — `logging_setup.py:124–135`. |
| "Let's rename everywhere to Dashy Dora" | ➗ mostly | leftovers in `.env.example`, `nginx.conf`, `build-linux.sh` (19-R4); GitHub repo already renamed; local folder not (CLAUDE.md). |
| "I'd like a way to know how people are using my app (usage tracking)" | 🔴 not built, deliberately | charter privacy posture; `/api/client-logs` is error telemetry only (chunk 20). Record as answered-no unless the owner reopens. |
| "I need a full systems QA test document … DO THIS LAST" | 🟡 in progress | this plan's `FULL_SYSTEMS_TEST.md` is assembled from the chunk §A sections at close. |
| Other MISC bullets (404 theme, undo, skeletons, menu outline, Settings in two menus, text size, Pesto button contrast, QR logo, ALDI/IGA logos, menu border, command palette, QR quick actions, UI consistency/uniqueness, dark-mode text) | → chunk 20 / 15 / 13 | not ops. |
| `# Technical Considerations` (2) | ✅ | covered in chunk 17 §F. |

### Register summary
- **FST rows:** 13 golden + 13 edges · **Help entries:** 4 new + DoraBot 3 lines (none existed) · **Review findings:** 27 (execute 23 / explain 1 / waive 1 / decision 2) + 6 design notes · **Tests:** 7 (must-write 2, one of them a Docker build assertion) · **Bugs:** 6 (19-R1, R2, R3, R4, R5, R6) + 1 copy bug (R15)
- **One line:** the boot/config/logging core is solid and well-pinned (migrations on both databases, compose env coverage), but the shipped Docker image silently builds the SPA without the service worker FU-336 added, can bake a `localhost` API URL from the operator's own `.env`, and checks for updates against a repo slug that doesn't exist; README and compose disagree about the default datastore; a legacy gunicorn file and a dead config layer are still in the tree.
