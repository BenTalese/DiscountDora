# IMPL — FU-333 Bucket B: promote operational env vars to `AppSetting`

**Source follow-up:** `DORA_FOLLOWUPS.md` FU-333, Bucket B only.
**Status:** drafted 2026-07-05. No code yet — this is the plan a
future session picks up cold.
**Run order:** stand-alone. Buckets C (encrypt SMTP/VAPID secrets in
DB) and D (desktop first-run wizard) are separate follow-ups and
explicitly out of scope here.

FU-333's audit already answered the design question — 12 named env
vars are operational config (not bootstrap, not secrets) and belong
on `AppSetting` next to the ~19 flags already there. This plan is the
execution: which columns, which migration, which DTO fields, which
admin pages, which read sites, and how the deprecation window works.

---

## 0. Verify-state-first: no drift

Re-checked 2026-07-05 against the live code — one small path
correction to FU-333's audit table, everything else stands:

- **`AppSetting`** ([dora_api/domain/entities/app_setting.py](dora_api/domain/entities/app_setting.py))
  already holds 19 columns. Adding 12 more fits the established
  shape — same file, same `Fields` inner class, same
  `get_or_create_app_setting()` accessor.
- **`UpdateAppSettingsRequest`** ([dora_api/features/app_settings/update_app_settings.py:22](dora_api/features/app_settings/update_app_settings.py)) is the single
  PATCH DTO. Each new column adds one optional field; the "only
  fields present are changed" semantics are already implemented.
- **`AppSettingsDto`** + `_to_dto()` in `get_app_settings.py` is the
  read shape — mirror the 12 new fields there.
- **Env-read call sites — verified live** (FU-333 audit paths, one
  correction):
  | Env var | File:line today | Notes |
  |---|---|---|
  | `DORA_EMAIL_ENABLED` | [dora_api/features/health/health_check.py:66](dora_api/features/health/health_check.py) | FU-333 said `features/health_check.py:63` — the module was reshuffled into a `health/` sub-package since. Also referenced in [dora_api/infrastructure/profile.py:83](dora_api/infrastructure/profile.py) (docstring only). |
  | `DORA_AUDIT_RETENTION_DAYS` | [dora_api/infrastructure/audit_retention.py:24](dora_api/infrastructure/audit_retention.py) | still valid. |
  | `DORA_PUBLIC_URL` | [dora_api/infrastructure/auth_helpers.py:236](dora_api/infrastructure/auth_helpers.py) | FU-333 said :188 — actual site is :236 (two-step resolution helper starting at :229). |
  | `DORA_SMTP_HOST` / `PORT` / `USERNAME` / `PASSWORD` / `FROM` / `USE_TLS` | [dora_api/infrastructure/email_sender.py](dora_api/infrastructure/email_sender.py) header + reads | six reads in one module. |
  | `DORA_VAPID_PUBLIC_KEY` / `SUBJECT` | [dora_api/infrastructure/push_sender.py:51,53](dora_api/infrastructure/push_sender.py) | `DORA_VAPID_PRIVATE_KEY` at :52 is **Bucket C** — leave it env for this plan. |
  | `DORA_PIPER_BIN` | [dora_api/features/tts/tts_synthesize.py:61](dora_api/features/tts/tts_synthesize.py) | still valid. |
  | `DORA_PIPER_BUNDLED_VOICE_DIR` | [dora_api/features/tts/voice_provision.py:81](dora_api/features/tts/voice_provision.py) | still valid. |
  | `DORA_PIPER_VOICE` | [dora_api/features/tts/tts_synthesize.py:70](dora_api/features/tts/tts_synthesize.py) | still valid. |
- **Admin Settings surface** is `pages/SettingsShell.vue` with focused
  sub-pages under `pages/settings/*`. The precedent for admin-only
  operational config is the four **System** pages already split from
  the old monolithic System page — Timezone, Alerts, Assistant,
  Features (see [routes.ts:358-387](web_app/src/router/routes.ts)).
  New sections here follow the same shape.
- **Migration mechanism** — Alembic under
  [`dora_api/persistence/migrations/versions/`](dora_api/persistence/migrations/versions/).
  Reference the most recent successful pattern: `d1f9c3a8b2e4_20260704_stocktake_engine_setup.py`
  batch-adds two `AppSetting` columns with server_defaults + R-005
  batch-mode for SQLite. Follow that shape exactly.

**One design call to lock in before coding starts:** the migration
should backfill each new AppSetting column from its corresponding
env var *at migration time* if the env is set. That lets an existing
operator upgrade without their SMTP host silently reverting to
"unconfigured". Fresh installs get the seeded default. Details in
Chunk 1 below.

---

## 1. Chunked plan (each chunk = one reviewable PR)

Three chunks, in order. Each is self-contained; you can stop after
Chunk 1 if you want the migration + backend + read-site cutover
without the admin UI. But the operator-onboarding win only shows up
once Chunk 3 lands.

### Chunk 1 — Schema, migration, DTO, deprecation seam

**Closes the load-bearing plumbing.** After this chunk the AppSetting
row holds all 12 new fields, existing env vars still work as
fallback, and every read site uses `AppSetting` first + env second.

**Backend:**

- **Extend `AppSetting`** ([app_setting.py](dora_api/domain/entities/app_setting.py))
  with 12 columns. Group in the file by concern with a section
  comment (matching how the existing file groups by chunk source):

  ```python
  # FU-333 Bucket B — SMTP operational config (was env DORA_SMTP_*).
  # Password stays env (Bucket C) until encrypted-at-rest lands.
  smtp_host: str = ""
  smtp_port: int = 587
  smtp_username: str = ""
  smtp_from: str = ""
  smtp_use_tls: bool = True

  # FU-333 Bucket B — push (was env DORA_VAPID_PUBLIC_KEY / _SUBJECT).
  # Private key stays env (Bucket C) until encrypted-at-rest lands.
  vapid_public_key: str = ""
  vapid_subject: str = "mailto:admin@dora.local"

  # FU-333 Bucket B — TTS / Piper (was env DORA_PIPER_*).
  piper_bin: str = ""
  piper_bundled_voice_dir: str = ""
  piper_voice: str = ""

  # FU-333 Bucket B — misc operational (was env DORA_*).
  email_enabled: bool = False
  audit_retention_days: int = 365
  public_url: str = ""
  ```

  Add each to the `Fields` inner class in the same order.

- **Migration** `f<rev>_20260706_appsetting_operational_config.py`:
  - Batch-alter `AppSetting`, 12 `add_column` calls with the
    server_defaults above (matches the stocktake_engine_setup
    precedent for SQLite compatibility).
  - **Env-var backfill (one-shot, migration-time only):** in the
    `upgrade()` after the columns exist, `op.execute` an UPDATE
    that copies the env value into each column *if the row exists
    AND the env is set*. Read the envs via `os.environ.get(...)`
    inside `upgrade()`. Skip any env not set — the seeded default
    stands. Rationale: an operator whose SMTP works today via env
    upgrades and immediately keeps working; a fresh install starts
    from the defaults; nobody's SMTP silently vanishes. The
    downgrade drops the columns (env is unchanged).
  - Type/bounds match the write DTO added below.

- **Extend `UpdateAppSettingsRequest`** ([update_app_settings.py:22](dora_api/features/app_settings/update_app_settings.py))
  with 12 optional fields matching the columns. Add bounds where
  the value is bounded (`smtp_port: int | None = Field(default=None, ge=1, le=65535)`,
  `audit_retention_days: int | None = Field(default=None, ge=1, le=3650)`).
  For URL-ish fields use `max_length` only — the router never
  echoes these back as clickable content and validation is the
  operator's problem (same posture as `product_search_url`).

- **Extend `AppSettingsDto` + `_to_dto`** ([get_app_settings.py](dora_api/features/app_settings/get_app_settings.py))
  to mirror the 12 fields on the read path.

- **Read-site cutover — the "AppSetting first, env fallback" seam.**
  Introduce ONE tiny helper (call it `resolved_operational_config()`)
  that returns a small dataclass with the 12 resolved values. The
  resolver's rule per field: **if the `AppSetting` value is non-empty
  (for strings) or explicitly set (for bools/ints where the seeded
  default equals the historic env default), use it; otherwise fall
  back to the env.** The 7 read sites all switch to this helper. This
  is the deprecation window — existing installs whose SMTP is still
  driven from env keep working; new admin edits to the row take over
  immediately.
  - `health_check.py` reads `email_enabled` from resolver.
  - `audit_retention.py` reads `audit_retention_days` from resolver.
  - `auth_helpers.py:236` reads `public_url` from resolver (the two-
    step canonical-URL logic stays, only the source moves).
  - `email_sender.py` — all six reads switch. Password stays direct-
    env (Bucket C).
  - `push_sender.py` — public key + subject switch. Private key
    stays direct-env (Bucket C).
  - `tts_synthesize.py` + `voice_provision.py` — three reads switch.

**Verification for Chunk 1 (pytest, in-process client):**
- New: `tests/e2e/dora_api/test_operational_config_resolver.py` —
  matrix over "env set / AppSetting set / both / neither" for each
  of the 12 fields, asserting the AppSetting-wins-when-non-empty
  rule and the env fallback.
- Existing SMTP / VAPID / TTS suites keep passing untouched (proves
  the read-site cutover is behaviour-preserving).

**No SPA changes in Chunk 1.** The admin UI still shows the old
sections only; the new fields exist on the wire but nothing surfaces
them yet.

---

### Chunk 2 — Admin UI: four focused System sub-pages

**Closes the operator-onboarding UX.** With Chunk 1 shipped, the row
holds the data but the admin has no place to see or edit it.
Following the established System-page split pattern from Phase 2 of
the settings rebuild (see [routes.ts:358-387](web_app/src/router/routes.ts)),
add four new admin pages under `/settings/admin/system/`:

- **`/settings/admin/system/email`** → `AdminSystemEmailSettings.vue`.
  Fields: `email_enabled` toggle (governs whether the section below
  is enabled), then `smtp_host` / `smtp_port` / `smtp_username` /
  `smtp_from` / `smtp_use_tls`. R-014 reveal-and-disable: password
  input rendered *disabled* with a caption "Set `DORA_SMTP_PASSWORD`
  in the environment — encrypted-in-DB storage lands with FU-333
  Bucket C." Include a "Send test email to me" action button that
  calls a new admin-only `POST /api/admin/email/test-send` endpoint.
  The action button provides the operator's proof-the-config-works
  moment without waiting for a real alert.
- **`/settings/admin/system/push`** → `AdminSystemPushSettings.vue`.
  Fields: `vapid_public_key` + `vapid_subject`. Private key rendered
  disabled with the same Bucket-C caption. A "Regenerate VAPID
  keypair" action documented but disabled here — key rotation is
  Bucket C's territory.
- **`/settings/admin/system/voice`** → `AdminSystemVoiceSettings.vue`.
  Fields: `piper_bin` / `piper_bundled_voice_dir` / `piper_voice`.
  Sibling caption linking to the existing user-facing Voice settings
  (which govern per-user voice choice, not install-wide paths).
- **`/settings/admin/system/hosting`** →
  `AdminSystemHostingSettings.vue`. Fields: `public_url`,
  `audit_retention_days`. Two disparate operational knobs that don't
  each warrant their own page.

**Nav wiring:** each page appears in the admin sidebar under
"System", matching the existing pattern. Route registration in
`routes.ts` mirrors the four existing System sub-pages.

**Component reuse:** every field is a bog-standard `q-input` or
`q-toggle` bound to a shallow local `ref` that mirrors the DTO,
saved via the same PATCH endpoint. Use the existing
`useAppSettings()` composable (or introduce one if not present —
verify at Chunk-2 start).

**Verification for Chunk 2 (browser):**
- Each of the four pages: type a value, save → toast + reload
  survives. Blank the field → falls back to env (proves the resolver
  from Chunk 1 is doing its job).
- Non-admin user visiting the URL is bounced by the router guard.
- "Send test email" round-trips end-to-end.

---

### Chunk 3 — Deprecation window: docs, release note, one-release grace

**Closes the env-var backwards-compat story.** Chunks 1 + 2 leave
env-vars as fallbacks; Chunk 3 documents the deprecation and marks
the timeline.

- **README / docs updates:**
  - README's env-var table shrinks. The 12 vars move to a
    "Deprecated (fallback only)" table with the caption "read only
    if the corresponding AppSetting field is unset — configure via
    Settings → Admin → System instead."
  - Any inline docstrings on the read-site helpers get a `#
    FU-333 Bucket B — env fallback; deprecated one release from
    2026-07-XX` marker (marker date fixed on merge day).
- **CHANGELOG:** one entry under `[Unreleased]` naming Bucket B, the
  12 vars promoted, and the four new admin pages.
- **Deprecation window:** one full release. The next-next release
  (i.e. the one after the release that carries this plan's merges)
  drops the env fallbacks entirely — the resolver becomes a
  straight `AppSetting.x` lookup, and the 12 env reads at the 7 code
  sites go away. **That drop is its own follow-up** (open on merge of
  Chunk 1) so it doesn't get lost.

**Verification for Chunk 3:** README preview renders, CHANGELOG hits
`[Unreleased]`, one new follow-up opened tracking the eventual
fallback drop.

---

## 2. Engineering-standards note

Rules this plan is checked against, in the language of
`docs/01_charter/ENGINEERING_STANDARDS.md`:

- **R-003 (single source of truth for domain logic & constants) —
  advance.** Today the SMTP host lives in `os.environ["DORA_SMTP_HOST"]`,
  which is one place, but *conceptually* it's install-wide operational
  config alongside `timezone` and `expiring_soon_window_days`, which
  live on `AppSetting`. Bucket B unifies the two categories.
- **R-005 (portable data access & distribution posture) — advance.**
  The plan directly implements Decision 5's bootstrap-vs-runtime split
  from `RECONCILED_FINISHING_PLAN.md` §7.5. Postgres/SQLite parity is
  preserved via batch-mode migration; the resolver is DB-source-agnostic.
- **R-006 (clean migrations & explicit dev resets) — respect.** The
  migration adds columns + a one-shot env→row backfill; no idempotent
  guards, no "already exists" dodges (per the migrations rule in
  memory).
- **R-007 (scope discipline) — respect.** Buckets C (encrypt SMTP
  password + VAPID private key in DB) and D (desktop first-run
  wizard) are explicitly excluded. If Chunk 2 tempts a broader UI
  refresh of the System pages, log as a follow-up instead of
  bundling.
- **R-014 (reveal-and-disable) — respect.** SMTP-password + VAPID-
  private inputs are rendered *disabled* on the new admin pages with
  a caption pointing at Bucket C, not hidden. Operator sees the shape
  of the eventual UI even before Bucket C lands.
- **R-019 (no magic, explicit and verbose) — respect.** The resolver
  is a plain function with one branch per field; no reflection,
  no auto-discovery from a config schema. Each read site names its
  field.

No new ADR proposed for this chunk. The eventual promotion of a
recurring "operational config lives in AppSetting, not env" rule is
the natural ADR *after* Buckets B + C both ship — noting that in
FU-333's engineering-standards section as a follow-up decision.

---

## 3. Out of scope (for clarity)

- **Bucket C — encrypted secrets in DB.** SMTP password + VAPID
  private key stay in env for this plan. The `AppSetting` columns
  for them are not added here; the admin pages render the disabled
  inputs as a preview only.
- **Bucket D — desktop first-run wizard.** Paired with FU-327; not
  this plan.
- **`DORA_SECRET_KEY` / `DORA_LLM_KEY_ENCRYPTION_KEY` /
  `DORA_ENV` / `DORA_SECURE_COOKIES` / `DORA_SPA_DIR` /
  `DORA_SKIP_PROD_VALIDATION` / `DORA_ALLOW_DESTRUCTIVE`** — the 7
  Bucket A vars stay env. This plan does not touch them.
- **A "set arbitrary env vars from the admin UI" feature.** That's
  the anti-pattern FU-333 exists to *avoid*.
- **Per-user LLM config** (`User.llm_*` from FU-153) — the user's
  own config, not install config. Untouched.

---

## 4. Feedback coverage

FU-333 was not raised by a specific feedback bullet — it surfaced as
a user concern after FU-153 added the 19th `DORA_*` env var. The
motivating "feedback" is the FU itself. Nothing in
`docs/02_feedback/Feedback _ Fixes - as of 2026-06-11.md` names env
vars or self-host setup difficulty directly; the closest indirect
touchpoint is the setup-friction lens on **F45** (onboarding), but
onboarding covers *user*-facing first-run, not *operator*-facing
first-install — this plan does not close F45.

| Motivation | Section closing it |
|---|---|
| FU-333 Bucket B audit (12 env vars, operator onboarding shrinks from 19 → 7) | Chunk 1 (schema + resolver) + Chunk 2 (admin UI) |
| FU-333 engineering rationale (bootstrap-vs-runtime split, R-003 / R-005) | §2 Engineering-standards note |
| FU-333 sequencing gate (do B before C) | §3 Out of scope |

No `COVERAGE_GAPS.md` bullets flip from this plan — the gaps file
tracks per-surface feedback and this is cross-cutting infrastructure.
