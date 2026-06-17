# Implementation Plan — Onboarding Redesign (C-5 impl)

> **⚠️ UPDATE (2026-06-17) — personas + `products_enabled` removed; see
> `PROPOSAL_PRODUCTS_AS_OVERLAY.md` §5.** C-5.3's **persona fork is cut** and the
> `products_enabled` flag it set is **dropped** (products are now gated on data-presence, not a
> flag). Any persona-driven step here is superseded: onboarding is **one un-personalized "show
> everything" path** with **no product framing and no stock-vs-product explainer**. The
> structural chunks (C-5.1/.2/.4/.5/.6 minus persona previews/tailoring) stand;
> **money/budgeting is a Settings toggle only**, not an onboarding fork. New build tracked as
> FU-210. Note: the C-5.3 fork and the `products_enabled` flag have **already shipped** in code,
> so this is a *removal* job, not just a plan edit.

**Status:** Plan for review · **Date:** 2026-06-15 · **No code yet** — phased plan +
reviewable chunks.
**Source proposal:** `PROPOSAL_ONBOARDING.md` (co-designed 2026-06-15; decisions resolved §4).
**Adjacent IMPL plans / surfaces:**
- `IMPL_PLAN_CONFIG_AND_OPTINS.md` (C-cross, **done**) — the install feature-flag panel
  (`SystemSettings.vue` + `AppSetting` flags + admin `PATCH /api/app-settings` +
  `useFeatureFlags`/health exposure) **already exists**; the persona presets are a thin writer
  over it, and the new `products_enabled` flag joins that same machinery.
- `IMPL_PLAN_COOK_MODE.md` (C-3, **done**) — `RecipeCookMode.vue:545-547` has a TODO waiting
  for `household_headcount`; C-5 adds the field, cook mode reads it.
- **FU-182** (`MINIMAL_USER_PRODUCTS_OFF_FRICTION.md`) — C-5 delivers the **persona fork +
  `products_enabled` flag**; **FU-182's chunk consumes the flag** to collapse every Products
  surface. C-5 establishes the lever, FU-182 does the app-wide sweep. Promote that scratch
  alongside this work.
- **FU-180** — absorbs the dropped **preferred-stores** idea (§2.8 of the proposal).
- `PROPOSAL_HELP_OVERLAY.md` / `HelpPage.vue` (**exists**) — the finish step deep-links into
  the existing guides; no new help surface built here.
**Phase:** Master plan **Phase 1 (the loop) / Phase 3 on-ramp** — onboarding is the front door
to the "zero-input pantry" champion. Touches **§7.5 distribution posture** (new flags are
config; flags whose effect needs external setup — SMTP/companion/LLM — degrade gracefully).

---

## 0. Verify-state-first: no drift

Re-checked 2026-06-15 against `WelcomeWizard.vue`, `onboarding.py`, `seed.py`, the seed JSON,
`AppSetting`/`User` entities, `SystemSettings.vue`/`PreferencesSettings.vue`, `HelpPage.vue`,
`RecipeCookMode.vue`, `Merchant`.

**Already true (do NOT rebuild / re-propose):**
- **Feature-flag admin panel exists** — `SystemSettings.vue` edits `AppSetting`
  {`meal_planning_enabled`, `money_enabled`, `nutrition_enabled`, `companion_ingestion_enabled`,
  `deals_email_enabled`, `scanning_enabled`, `llm_enabled`} via admin `PATCH /api/app-settings`;
  `useFeatureFlags` reads them through `/api/health`. Per-user `money_features_enabled` +
  `nutrition_mode` edited in `PreferencesSettings.vue`.
- **B5 dead-nav fixed**; **theme** = system/light/dark; **admin step** says "Invite teammates
  later" (L29 ✅); **inline "(N added)" counter** present; **draft** persists to localStorage.
- **Help/guides section exists** (`HelpPage.vue`).
- **Meal slots seeded by migration** `b9f6d3a8c1e2` — onboarding need not touch them.
- **Seed today = groups + locations only** (`default_stock_groups.json`,
  `default_locations.json`, idempotent by name).

**Not built (this plan delivers):**
- No persona fork / branching; no `products_enabled` flag (product surfaces always on).
- No vision/values intro; no stock-vs-product explainer.
- No `household_headcount` (cook mode's TODO).
- No starter-item packs; no demo recipe/meal/plan seed; import is a nav-away + names Grocy.
- No celebration; tour is 4 fixed cards (stock/shopping/alerts/help).
- Prefs/seed persist incrementally, not draft-until-finish; "Skip everything" not yet "Skip".

**Tests:** check for `tests/e2e/dora_api/test_onboarding*.py`; each backend chunk adds/extends
e2e there. Migrations: plain, reversible, portable (SQLite + Postgres), single Alembic head
(chain from the head at build time — note the C-9 alert migration may land first).

---

## 1. Chunked plan (each chunk = one reviewable PR)

### C-5.1 — Copy / label / persistence + theme mapping ★ FIRST CHUNK (quick wins)
**Closes:** L35, L30, L28, L32/L33 (confirm); fixes the cheap rough edges first.

- **Frontend (`WelcomeWizard.vue`):**
  - "Skip everything" → **"Skip"** (L35).
  - **Draft-until-Finish** — stop persisting prefs on the welcome step and seeding on the seed
    step; **collect everything into the local draft and apply once in `complete()`** (prefs via
    `updateMeAsync`, seeds via the seed endpoints). A mid-wizard bail leaves nothing applied
    (L35). (Keep the localStorage draft for refresh-resume.)
  - **Inline import** copy: "import from a spreadsheet or another app" **on the page**, **don't
    name Grocy** in primary copy (the importer page still supports it) (L30).
  - **Theme** map System/Light/Dark explicitly to **system / pesto-light / pesto-dark** (L28) —
    coordinate with the theme system (A8); the persona/palette split.
- **Verify (no code unless it reproduces):** the "you already have groups/locations" copy on a
  **clean DB** doesn't show on genuine first-run (**FU-041**); confirm no migration pre-creates
  *user* groups/locations.
- **Risk:** Low. The trap is the draft-until-finish refactor changing when side effects fire —
  test the bail path.
- **Close-gate:** R-002 (tokens), R-007 (only the listed edits), R-003 (no domain copy
  duplicated). *Acceptance:* skip says "Skip"; bailing mid-wizard applies nothing; import is
  inline + unnamed; theme picks map to pesto palettes; clean-DB first-run shows no "already
  have…" copy.

---

### C-5.2 — Cinematic intro + `OnboardingLoop` hero + motion / nav / progress shell ★ EXPERIENCE SPINE
**Closes:** L41, L43, L24 (the "sell it" core). Proposal §2 (the whole experience section).

This is the biggest experience chunk — it builds the *feel*, not just a step.
- **Narrative scenes (§2.2):** 3–4 full-screen, auto-advancing-but-skippable scenes (problem →
  the loop → Dora-the-brain → you're in control), one idea each, big type + a hero visual,
  almost no text. Persistent **"Skip to setup"** from scene 1.
- **`OnboardingLoop` component (§2.3) — the hero, reused at finish (R-001):** the ring of stages
  with **Dora at centre**, **hybrid interaction** (auto-reveals once, then every stage + Dora is
  tappable to drill in). No persona-dimming. Built the way the approved prototype
  (`onboarding_loop_hybrid_v2`) demonstrates, re-skinned to the app (dark canvas + real Dora
  yellow). **Loop stages + copy are PROVISIONAL — gated by FU-184 (below).**
- **Navigation & progress shell (§2.5):** two sections (Story / Setup) with **instant
  cross-jump**; a persistent **non-linear step rail** (jump to any section, nothing gated) that
  doubles as the progress indicator; **draft-until-finish** (move all side effects into
  `complete()` — overlaps C-5.1).
- **Motion language (§2.4):** transform/opacity reveals with eased curves, staggered; the loop
  draws itself; tight 60fps budget. **Mandatory `prefers-reduced-motion`** path (cross-fades,
  no autoplay, final-state shown) + full keyboard nav + visible focus + labelled visuals.
- **Display name + theme + font** fold into a light "make it yours" beat, not a blocking form.
- **★ FU-184 gate (P3 Honest):** every loop stage's sell-line must be **verified true against
  the running app** before this ships; cut/soften anything aspirational; the emerging
  Insight/Spend-smarter beat must **not** be promised until it's a real feature. Needs the
  running app — cannot be cleared by a static read.
- **Risk:** High — the marquee UI; motion + a11y + the reusable hero + nav model. Keep the
  motion budget tight so it feels snappy, not slow.
- **Close-gate:** R-001 (one `OnboardingLoop` reused here + finish; reusable scene/rail
  components), R-002 (tokens, dark-mode + the production dark canvas), §7.5 n/a, **P3 (FU-184
  copy honesty)**, a11y (reduced-motion + keyboard). *Acceptance:* first-run opens on a
  skimmable cinematic that a user can skip-to-setup instantly; the hero auto-plays then is
  tappable; the rail lets them jump anywhere; reduced-motion users get a calm equivalent; every
  on-screen claim matches real behaviour.

---

### C-5.3 — Persona fork + `products_enabled` flag + branching ★ THE REFRAME
**Closes:** L42, L46 (conditional explainer); the spine FU-182 builds on.

- **Backend:**
  - **New `AppSetting.products_enabled`** (bool, **default True** — existing installs unchanged;
    the *Cooking persona* is what turns it off). Entity + table-mapping + migration; expose via
    the same admin `PATCH /api/app-settings` + `/api/health` feature block the other flags use
    (R-003 — one flag machinery, no parallel path).
  - The persona presets write flags through the **existing** `PATCH /api/app-settings` (install
    flags) + `PATCH /api/users/me` (first-user per-user `money_features_enabled`/`nutrition_mode`
    to match). No new "apply persona" endpoint needed unless the two-write sequence wants
    atomicity — if so, a thin `POST /api/onboarding/persona {preset}` that sets both is cleaner
    (decide in build; prefer reuse).
- **Frontend (`WelcomeWizard.vue`):**
  - **Persona step:** 3 preset cards — **Pantry & cooking / Pantry + spend tracking /
    Everything** (reframed from "grocery savings" now scraping is divorced; the middle persona
    is price-memory + waste reduction, not deals) — each with a one-line promise + the flags it
    sets (per proposal §3.2 table), plus a **"Customise"** card → the flat feature-toggle list.
    Selection updates the **draft** (applied on Finish per C-5.1).
  - **Branching:** the visible-steps computed keys off the chosen persona/`products_enabled`:
    the **stock-vs-product explainer step shows only when products are on** (Savings/Everything);
    Cooking skips it. (Preferred-stores step is **not built** — dropped, §2.8.)
  - **Conditional stock-vs-product explainer step** (L46) — content/UI, shown before any
    add-items step.
- **Scope guard (R-007):** C-5 **only adds + sets** `products_enabled`. The per-surface
  hiding (nav, stock-item detail, shopping-list checklist mode, etc.) is **FU-182** — do not
  start the app-wide sweep here; log/keep it in FU-182.
- **Risk:** Medium — new flag threading + wizard branching + draft-applied-on-finish ordering.
- **Close-gate:** R-003 (one flag machinery; persona is a thin writer), R-005/R-006 (portable
  reversible migration; single head), R-007 (flag only, gating is FU-182), §7.5 (flags needing
  external config degrade gracefully). *Acceptance:* picking Cooking sets `products_enabled=off`
  + a shorter wizard (no explainer); Savings/Everything set it on + show the explainer;
  Customise opens the flag list; flags land only on Finish; existing installs keep products on.

---

### C-5.4 — Household headcount
**Closes:** L44; unblocks cook-mode scaling.

- **Backend:** **`User.household_headcount`** (int, nullable) — entity + table-mapping +
  migration; `PATCH /api/users/me` accepts it (mirrors the existing scalar-pref columns).
- **Frontend:** a small "How many people do you usually cook for?" field (its own step or
  folded into the household section), into the draft. **`RecipeCookMode.vue`** initialises its
  serving scaler from `household_headcount` instead of the recipe `servings` default (resolve
  the `:545-547` TODO).
- **Risk:** Low-medium (one field + the cook-mode read).
- **Close-gate:** R-003 (server-owned default; cook mode reads, doesn't hardcode), R-005/R-006.
  *Acceptance:* setting headcount in onboarding makes cook mode open pre-scaled to it; absent →
  current recipe-servings behaviour.

---

### C-5.5 — Starter data: packs + demo + preview + inline import + added-list ★ BIG ROCK
**Closes:** L34, L37, L38, L36.

- **Backend:**
  - **`starter_packs.json`** — packs → items → default group/location *names* (resolved against
    the seeded or user catalogues at apply time). New seed endpoint (extend `/api/onboarding/
    seed` or a sibling `POST /api/onboarding/seed-items`), idempotent (dedupe by name) like
    today's groups/locations seed.
  - **Demo payload(s)** — a demo recipe (+ optional meal/meal-plan) seed; **plain rows, no
    `is_demo` marking** (user deletes like any other). New endpoint or a `demo` flag on the seed
    request.
- **Frontend:** the seed step becomes a **starter-data** step:
  - groups/locations with **all/none/some + a preview** of the hierarchy (L34);
  - **starter-packs** — toggle packs, expand to tick individual items, customise (L37);
  - **demo toggles** with a clear "creates demo data" warning (L38);
  - **inline import** (from C-5.1 copy);
  - **first stock item** with a **slim running "added" list** (L36), the count folded in.
  - All into the draft; created on Finish.
- **Risk:** Medium-high — biggest chunk; new seed content + endpoints + the packs UI. Keep seed
  idempotent + name-resolved so re-runs don't duplicate.
- **Close-gate:** R-003 (seed/dedupe server-side), R-005/R-006 (if any schema), R-001 (reusable
  pack/preview components), R-007. *Acceptance:* ticking packs + Finish creates exactly those
  items pre-located; re-running doesn't duplicate; demo toggle seeds a real removable recipe/
  plan; the added-list tracks first-item adds.

---

### C-5.6 — Finish: celebration + workflow flow-cards → help
**Closes:** L39, L40, L43; fixes **FU-015**.

- **Frontend:** a Finish step with a **confetti / "you're all set!"** moment (L39); a **recap of
  the loop using the same `OnboardingLoop` component** (bookend, R-001); then **flow-cards** for
  the **persona-relevant** key areas (Cooking → pantry/recipes/meals/cook; Spend-tracking → +
  price memory / spend insight; always → Dora the assistant), each **linking into the existing
  `/help` guides** (L43, L40). The Alerts card points at `/alerts` (FU-015).
- **Risk:** Low-medium (visual; confetti via a lightweight CSS/canvas animation, reduced-motion
  aware).
- **Close-gate:** R-001 (reuse `OnboardingLoop` + flow component), R-002 (tokens), a11y
  (reduced-motion confetti), **P3/FU-184** (flow-card copy matches real behaviour).
  *Acceptance:* Finish celebrates, recaps the loop, shows persona-relevant flow cards that
  deep-link into help, and completes onboarding (router guard clears).

---

## 2. Sequencing & dependencies
1. **C-5.1** (quick wins) → **C-5.2** (vision) — independent, low risk, ship first.
2. **C-5.3** (persona + `products_enabled` + branching) — the reframe; later steps assume the
   persona/branch state.
3. **C-5.4** (headcount) — small; unblocks cook mode.
4. **C-5.5** (starter data) — the big rock; new seed content.
5. **C-5.6** (finish) — reuses C-5.2's diagram component.

**Hard dependencies:** C-5.3 reuses the **existing** C-cross flag machinery (✓). C-5.4 pairs
with cook mode's waiting TODO (✓). C-5.6 reuses C-5.2's component. **FU-182 depends on C-5.3's
`products_enabled`** (downstream, not blocking C-5). No multi-user dependency.

## 3. Cross-cutting close-gate (every chunk)
Portable reversible migrations (SQLite + Postgres, §7.5, single head); A1 tokens only (R-002);
shared components over duplication (R-001 — one `OnboardingLoop`, reused); server owns
flags/seed/defaults (R-003); scope discipline — **the Products-off surface sweep is FU-182, not
C-5** (R-007); no dead code (R-008); **all motion honours `prefers-reduced-motion`** + full
keyboard nav + visible focus + labelled visuals; **P3 honesty — sell-copy validated against the
running app (FU-184) before any copy chunk (C-5.1/.2/.6) closes**; `CHANGELOG.md` +
`DORA_WORKLOG.md` + follow-ups updated per chunk; e2e + vue-tsc + eslint green.

## 4. Feedback coverage
Inherits the proposal's **§8 table** (L24-46; L45 preferred-stores out-of-scope → FU-180).
After the redesign verifies in-browser, flip the now-covered ONBOARDING rows in
`docs/02_feedback/COVERAGE_GAPS.md` from gap → covered.
