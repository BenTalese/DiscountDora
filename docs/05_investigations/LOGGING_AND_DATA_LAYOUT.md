# LOGGING_AND_DATA_LAYOUT — INV-3

**Date:** 2026-06-06  
**Type:** Read-only investigation. No code changes.  
**Purpose:** Explain the logging setup (no rotation observed, 46k-line wrong-dated
file, logs in two places) and the `.local`/`data` folder split, then recommend a
single coherent layout + a correct rolling config.

---

## TL;DR

- Rotation **is** configured — but it's **size-based** (`RotatingFileHandler`,
  10 MB × 5). A low-volume install never hits 10 MB, so it never rotates, and one
  file accumulates entries across many days/restarts → the "46k lines, wrong date
  span" symptom. The user expected **time-based** (per-day) rotation.
- "Logs in two places" = the **stdout handler + the file handler** (both always
  attached), and the **desktop app** writes to an OS per-user log dir while the
  web/dev run writes to `./data/logs/<service>/`.
- **There is no `.local` folder in the repo.** The "data split" is `data/`
  (persistent) vs `cache/` (regenerable) — an intentional, sound split — plus the
  desktop app's `platformdirs` per-user directories.
- Recommendation: switch to `TimedRotatingFileHandler` (midnight, keep ~14 days);
  keep the `data/` + `cache/` split as-is.

---

## (a) Logging

### Where it's configured
- Shared module: `dora_api/infrastructure/logging_setup.py` (`configure_logging`).
- Called once per service:
  - `dora_api/startup.py:58-62` → `dapi.log`
  - `merchant_api/startup.py:53-57` → `mapi.log`
  - `emailer/startup.py:47-51` → `emailer.log`
  - `desktop_app.py:128-135` (desktop file logging)
- Request-context filter (stamps `[req=…] [user=…]`): `log_context.py`.

### Handlers (this is the "two locations")
`configure_logging` attaches **two** handlers to the root logger every run
(`logging_setup.py:82-95`):
1. **StreamHandler → stdout** (for Docker-style aggregation).
2. **RotatingFileHandler → `<log_dir>/<service>.log`**.

So every line is written to *both* the console and the file by design. Combined
with the desktop app using an OS per-user log dir (below) while dev/web uses
`./data/logs/<service>/`, that's the "logs in two places" the user saw.

### Rotation — configured, but size-based
`logging_setup.py:40-42, 87-95`:
```
_FILE_MAX_BYTES   = 10 * 1024 * 1024   # 10 MB
_FILE_BACKUP_COUNT = 5                  # 5 backups → ~50 MB/service
RotatingFileHandler(maxBytes=_FILE_MAX_BYTES, backupCount=_FILE_BACKUP_COUNT)
```
This rotates **only when the file passes 10 MB**. There is no time component.

### Why the 46k-line, wrong-date file exists
The handler opens the file in append mode and rolls **only on size**. On a
low-traffic install:
- Daily volume stays well under 10 MB, so rotation **never fires**.
- Each app restart re-attaches the handler (idempotent clear/rebuild,
  `logging_setup.py:72-75`) and **appends to the same file**.
- Result: one ever-growing file spanning every day since install — exactly "46k
  lines with a date range that looks wrong."

Nothing is broken; the rotation policy simply doesn't match the expectation of
"a file per day." `werkzeug` and `sqlalchemy.engine` are correctly pinned to
WARNING (`logging_setup.py:97-99`), so the bulk isn't access-log noise.

This matches the previously-logged **FU-027**.

## (b) Data / `.local` layout

> **Verification scope (important):** the table below is the layout **resolved
> from code** (`configuration_manager.py`, `app.py`, `desktop_app.py`), read
> directly — NOT observed on disk. The repo checkout used for this audit has no
> `data/`, `cache/`, or `.local` folder because the app was never run from it,
> so the user's actual 46k-line log file and "two locations" live on whichever
> machine *did* run the app. **On-disk confirmation must be done there** (see the
> verification checklist at the end).

**There is no `.local` directory anywhere in the code or repo.** The two folders
that exist by design are `data/` and `cache/`:

### Where each thing is resolved to

| Item | Dev / web run (CWD-relative) | Desktop app run (`platformdirs`) |
|---|---|---|
| SQLite DB | `./data/dora.data.db` (`configuration_manager.py:79-88`) | `…/BenTalese/Dora/dora.data.db` |
| Config | `./data/config/dapi.appsettings.json` (`:91-97`) | `…/Dora/config/…` |
| Uploads | `./data/uploads/` (`:215-222`) | `…/Dora/uploads/` |
| Cache (images / scraped JSON) | `./cache/` (`:236-242`) | `user_cache_dir` |
| **Logs** | **`./data/logs/dapi/dapi.log`** — *nested inside* the data dir (`:224-234`) | **`user_log_dir`** — a *separate top-level* location |
| **Secret key** | `./data/.secret_key` | **also `./data/.secret_key`** (hardcoded, `app.py:23`) |

- `data/` is "must survive / back up"; `cache/` is "safe to delete". That split
  is sound. `.gitignore` covers `data/`, `cache/`, `logs/`.
- Desktop bootstrap (`desktop_app.py:48-72`) sets `DORA_DATA_DIR`/`CACHE_DIR`/
  `LOG_DIR` to the OS per-user dirs before importing `dora_api`. A one-time
  `path_migration.py` moves legacy `./data`/`./config` contents on startup.

### Two real inconsistencies the layout has (do NOT just "keep as-is")

1. **`.secret_key` ignores `DORA_DATA_DIR`** — `app.py:23` hardcodes
   `Path('data') / '.secret_key'`. So on the desktop app (where everything else
   lives under `%LOCALAPPDATA%\BenTalese\Dora`) the session secret instead writes
   to `./data/` relative to the launch CWD. Consequences: it escapes the
   configured data dir, isn't captured by a backup of that dir, and is
   CWD-dependent — launching from a different folder regenerates it and silently
   invalidates every session cookie. **Latent bug, not cosmetic** (logged as a
   follow-up). Fix: resolve it via `DORA_CONFIG.get_data_dir() / '.secret_key'`.

2. **Logs sit in a different place relative to data between run modes** — nested
   at `data/logs/dapi/` for dev, but a *separate* `user_log_dir` for desktop
   (because `get_log_dir()` uses an explicit `DORA_LOG_DIR` verbatim and skips the
   `/logs/dapi` nesting). This mode-dependent difference is itself a plausible
   source of the user's "logs in two locations" report, on top of the always-on
   stdout + file handler pair.

So the earlier "the split is correct, keep as-is" line was **too clean** — the
`data/`-vs-`cache/` split is fine, but secret-key placement and the dev-vs-desktop
log nesting are genuine inconsistencies worth tidying.

---

## Recommendation

### Logging — switch to time-based rotation (the actual fix for FU-027)
In `logging_setup.py`, replace `RotatingFileHandler` with
`TimedRotatingFileHandler`:
```python
from logging.handlers import TimedRotatingFileHandler

_FILE_BACKUP_COUNT = 14   # keep ~2 weeks of daily logs

rotating = TimedRotatingFileHandler(
    log_dir_path / f"{service_name}.log",
    when="midnight", interval=1,
    backupCount=_FILE_BACKUP_COUNT,
    encoding="utf-8",
)
```
- One file per day; rotated files get a `.YYYY-MM-DD` suffix automatically.
- `backupCount=14` ≈ two weeks; tune to taste. This directly fixes the
  "one giant wrong-dated file."
- Keep the stdout handler as-is.
- Optional belt-and-braces: a custom handler that rotates on **either** midnight
  or size — only worth it if any single day could exceed ~10 MB. Probably not
  needed here; recommend plain time-based.

### Data layout — keep the `data/`÷`cache/` split, fix two inconsistencies
- **Keep** the `data/` (persistent) ÷ `cache/` (regenerable) split + desktop
  `platformdirs` — that part is clean and conventional. No consolidation needed.
- **Fix** `.secret_key` placement: resolve via `DORA_CONFIG.get_data_dir()`
  instead of the hardcoded `Path('data')` (`app.py:23`), so it lives with the DB
  on every deployment surface. (Latent bug — see (b).)
- **Decide** the log location story: either nest desktop logs the same way as dev
  (`<data>/logs/dapi`) or document the deliberate split. The current mode-
  dependent difference is the most likely "two locations" the user saw.

### On-disk verification checklist (must run on the machine that ran the app)
This audit was code-only. To close it, on the machine where the 46k-line file
exists:
1. Locate the active log dir — desktop: `%LOCALAPPDATA%\BenTalese\Dora\` (the
   `user_log_dir`); dev: `<repo>/data/logs/dapi/`. Confirm which one holds the
   big file.
2. Check the file size vs 10 MB — confirms the "never rotated because under
   threshold" hypothesis.
3. Confirm whether a second log file exists in the *other* mode's location
   (the real "two locations").
4. Check where `.secret_key` and `dora.data.db` actually sit relative to each
   other — confirms the hardcoded-secret-key divergence.

---

## Key file references

| Concern | File | Lines |
|---|---|---|
| Logging config / handlers / rotation | `dora_api/infrastructure/logging_setup.py` | 35-99 |
| Idempotent re-init | `dora_api/infrastructure/logging_setup.py` | 72-75 |
| Per-service calls | `*/startup.py`, `desktop_app.py` | dapi 58-62 / mapi 53-57 / emailer 47-51 / desktop 128-135 |
| Request-context filter | `dora_api/infrastructure/log_context.py` | — |
| Path resolution (DB/data/cache/logs) | `dora_api/infrastructure/configuration_manager.py` | 79-242 |
| Desktop platformdirs bootstrap | `desktop_app.py` | 48-72 |
| Legacy path migration | `dora_api/infrastructure/path_migration.py` | 1-97 |
| Ignored folders | `.gitignore` | data/ cache/ logs/ |

---

## Feedback coverage

| User-flagged item | Finding |
|---|---|
| "logs not rolling" | Rolling IS configured but size-based (10 MB); low volume never trips it. Fix: time-based (midnight) rotation. |
| "46k-line file, wrong date span" | Same root cause — one append-mode file across all days/restarts because size threshold never hit (FU-027). |
| "logs in two locations" | stdout + file handlers (always both), PLUS a real mode-dependent split: dev nests logs at `./data/logs/dapi/`, desktop writes to a separate `user_log_dir`. Not purely "by design" — worth unifying or documenting. Confirm on-disk. |
| "messy `.local` / data split" | No `.local` folder exists. `data/`÷`cache/` split is sound, BUT `.secret_key` is hardcoded to `./data/` ignoring `DORA_DATA_DIR` (`app.py:23`) — a latent bug, logged as FU-037. |
