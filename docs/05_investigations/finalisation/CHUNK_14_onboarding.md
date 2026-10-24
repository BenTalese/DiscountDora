# Chunk 14 — Onboarding

**Session:** 2026-10-23 overnight (solo, no subagents) · **Stage:** 1 (analysis only — no code changed)
**Surface:** the `/welcome` first-run wizard (Story → Setup: Welcome / Build your Dora / Your stock / You're all set), its components (`OnboardingStory`, `OnboardingLoop`, `OnboardingScene`, `OnboardingStepRail`, `OnboardingPickPanel`, `OnboardingConfetti`), `WelcomeLayout`, the router's onboarding gate, the seven `/api/onboarding/*` endpoints with their bundled JSON catalogues, the dashboard's "finish setting up" banner, and — read for context because they define what a fresh install looks like — the three dev/demo seeders (`seed.py`, `seed_dense.py`, `seed_showcase.py`, `seed_builders.py`).
**Boundaries:** `/setup` first-admin bootstrap, `/setup/backend` native instance picker, login/register → chunk 15; Import (ex-Grocy) → chunk 18; demo-mode reset scheduling → chunk 19; the Settings pages the wizard writes to (Cooking, Region, Stock, Stocktake, Money) → chunk 13.

---

## 0. Reading list + files walked

**Governing docs read:** `PROPOSAL_ONBOARDING.md` (v3 — §2 experience, §3 flow, §5 resolved decisions, §10 L24–L46 coverage; §2.3.a + §3.2.a "open threads" are still open headings — both were overtaken by FU-210's persona removal and the products-as-overlay pivot), `IMPL_PLAN_ONBOARDING.md` (C-5.1–C-5.6; §0 "already true" list now stale against the 2026-10-17/21 rebuild), feedback `# ONBOARDING` (L24–L46, 23 bullets), `COVERAGE_GAPS.md:172–175` (ONBOARDING row: personas retired, L46 dropped), FU-578 #38/#39/#48, FU-632 (#48 first-boot region derivation), FU-692 (icon meanings), FU-675 (`q-select` → `BaseSelect`). Resolved and consulted: FU-180, 184, 191, 193, 194, 195, 209, 210, 512, 556, 615, 616.

**Backend walked in full (4,567 lines incl. seeders):** `features/onboarding/onboarding.py` (734), `default_locations.json`, `default_stock_groups.json`, `starter_packs.json`; `persistence/seed.py` (1,129), `seed_builders.py` (321), `seed_dense.py` (1,743), `seed_showcase.py` (637).

**SPA walked in full (3,821 lines):** `pages/onboarding/{WelcomeWizard (2,078), OnboardingStory, onboardingContent}.{vue,ts}`, `components/onboarding/{OnboardingConfetti,OnboardingLoop,OnboardingPickPanel,OnboardingScene,OnboardingStepRail}.vue`, `layouts/WelcomeLayout.vue`, `models/onboarding.ts`, `services/api/onboardingApiService.ts`, `router/index.ts` (the full guard), `pages/DashboardPage.vue:575–625` (skip-reminder banner + Continue).

**Tests read:** `tests/e2e/dora_api/test_onboarding_flags.py` (9), `test_onboarding_seed_demo.py` (2), `test_seed_onboarding_unit_of_work.py` (2), `tests/test_onboarding_seed_filter.py` (17 unit tests on `SeedHandler`). No vitest for the wizard.

**Verification greps run:** `restartAsync|/onboarding/restart` consumers (one — `DashboardPage.vue:614`; the "AccountSettings 'Restart onboarding' action" both `DashboardPage.vue:606` and `user.py:188–189` cite does not exist — grep `Restart onboarding` in `web_app/src` → comments only); `dora.onboarding.skipped_at` (written by the wizard, read by the dashboard banner ✓); `store_status` / `OnboardingState.completed|completed_at` consumers (none — the wizard reads only `first_user`); `MealPlan` unique constraint on `start_date` (`table_mappings.py:996–1010` — none; no `plan_for_week` helper in `features/meal_plans`); `sorted(levels, key=lambda lvl: lvl.sequence)[0]` (×2 in `onboarding.py`) vs `domain/stock_status.level_for_status` (`:178–186`, unused here); `<OnboardingLoop` consumers (one, passing no props — `autoplay`/`interactive` always default); `normaliseHeadcount` (×2: wizard + `AdminSystemCookingSettings.vue:109`), `onTimezoneFilter` + `TIMEZONE_CHOICES` filter (×2: wizard + `AdminSystemRegionSettings.vue:346`), `Intl.DateTimeFormat().resolvedOptions().timeZone` (×2); starter-pack item names vs `_DEMO_INGREDIENTS` ("Pasta"/"Garlic"/"Olive oil" vs "Spaghetti pasta"/"Garlic cloves"/"Olive oil"); `session.get(SESSION_USER_ID_KEY)` (11 files — `onboarding.py:69–75` is another copy, FU-654); `HelpPage.vue` GUIDES (no first-run / tour / onboarding entry in any of the six groups); `app_knowledge.py` (no onboarding mention); FU-556 resolved (so `seed_showcase.py:16–20`'s "duplication is intentional … logged as a DRY follow-up" docstring is stale).

---

## A. Full Systems Test — Onboarding

### A1. Preconditions
- A fresh DB (migrations only — three stock levels, five meal slots, the fixed recipe vocab; **zero** groups/locations/items/users).
- Run A: first admin created on `/setup` (chunk 15) → lands in `/welcome` as **first user** (admin). Run B: a second account registered later → lands in `/welcome` as a **joining user** (two steps only).
- Device: a phone-width and a desktop-width pass; one pass with `prefers-reduced-motion`.

### A2. Golden path (first user)
| # | Step | Expect |
|---|---|---|
| G1 | Land on `/welcome` | Dark pinned canvas (`WelcomeLayout`), slim top row: mascot · Story/Setup rail · "Skip onboarding". Story scene 1 "The weekly shop is detective work." rises in. |
| G2 | Next ×3 | Scene 2 draws the loop ring then cascades six nodes + Dora; tapping a node swaps the sell line; scene 3 Dora "thinking"; scene 4 switch panel; last CTA "Set up in about a minute". Rail dots jump anywhere, nothing gated. |
| G3 | Setup → Welcome | Hero greets by username; avatar tile (upload or preset) + Undo; theme cards System/Light/Dark painted in their own tokens; Font segmented. Nothing saved yet. |
| G4 | Next → Build your Dora | Household panel: People (blank = per recipe), Timezone (**pre-filled with this device's zone** because the install is still UTC), Units segmented. Six feature cards seeded from `/app-settings` (Stocktakes + Auto-add on; Spend/Nutrition/Batch/Barcodes off); "Loading your install's current settings…" until the GET lands. |
| G5 | Next → Your stock | Three pick panels (locations by zone, groups, items by pack), every default ticked, `N of M` + All/None per panel, "Add your own" row (items also take Group/Location selects of the picked names). Untick Bathroom + Laundry, add "Garage", add "Coffee" in Pantry/Pantry. |
| G6 | Next → You're all set | Confetti (not under reduced motion); recap rows each with Change; Extras → "Add a demo recipe" (first user only); first-steps tiles 1–4 (+ "Watch your prices" only if Spend tracking is on, + "Pick Dora's voice"); tip linking the guides. |
| G7 | Finish | One `PATCH /auth/me` (theme/font/image), one `PATCH /app-settings` (only what changed), `POST /onboarding/seed` (filters sent only when not "all"), own group/location creates, `POST /onboarding/seed-items`, `POST /onboarding/seed-demo` if ticked, `POST /onboarding/complete`, `/auth/me` refresh → `/`. Dashboard shows the seeded items; Settings → System reflects the picks; `/health` flags refreshed in-session. |
| G8 | Re-open `/welcome` by URL | Bounced to `/` (completed). |
| G9 | Skip onboarding (from any step) | `POST /onboarding/complete` only, nothing else applied; dashboard shows the 24-h "finish setting up" banner; Continue → `POST /onboarding/restart` → back in the wizard with the saved draft. |
| G10 | Joining user (Run B) | Welcome → You're all set only; no features/stock steps; no demo toggle; Finish writes theme/font/avatar + complete. |

### A3. Edge cases
| # | Case | Expect (and what the code does today) |
|---|---|---|
| E1 | First user already created a meal plan for this week (via "Plan the week" tile then Continue-onboarding → Finish with demo ticked) | **Today a second `MealPlan` for the same `start_date` is inserted** (no uniqueness, no reuse) → 14-R1; the planner's duplicate-week hazard from chunk 2 applies. |
| E2 | Picked pack items "Pasta", "Garlic", "Olive oil" + demo recipe | **Today the demo creates "Spaghetti pasta" and "Garlic cloves" alongside them** (only "Olive oil" is reused) → 14-R2. |
| E3 | `POST /onboarding/seed-items` / `seed-demo` on a DB whose level sequences aren't 0-based | Both pick `sorted(levels)[0]` rather than the Stocked role → 14-R6 (works today because migrations seed 0/1/2). |
| E4 | Refresh mid-wizard | Draft (every pick, step, scene, household, features, own entries) restored from `localStorage` per user ✓. |
| E5 | Finish fails at `seed-items` (e.g. server down) | Prefs + settings already written; wizard stays with the error; re-Finish re-sends only the diff and the seeds are idempotent ✓ (documented partial-apply, see 14-D2). |
| E6 | Re-run the wizard with theme `blueberry` saved | No theme card highlighted; Finish leaves theme untouched ✓ (documented). |
| E7 | Install timezone already set to a real zone before the first user finishes | Wizard pre-fills the stored zone, not the device's ✓. |
| E8 | Reduced motion | Ring/nodes shown immediately, no confetti, no scene rise ✓. |
| E9 | Non-admin somehow `first_user` | Features step shown but baseline never loads → cards disabled forever, Finish sends nothing for it ✓ (documented). |
| E10 | `/onboarding/seed` with `groups:false, locations:false` | 200 with zero counts (deliberate) ✓. |
| E11 | User renames the "Dinner" meal slot before Finish | Demo plan entry still written with `slot="Dinner"` / `time_of_day="Dinner"` literals → 14-R7 (orphan slot name). |
| E12 | Story scene 4 switch panel | Shows "AI assistant — on" though AI mode is per-user and off by default → 14-D3 (honesty nit). |

### A4. Persona coverage
- **Fresh self-host admin:** full track ✓. **Joining household member:** short track ✓. **Dense/Power user:** draft survives, non-linear rail ✓. **Multi-user:** `first_user = users ≤ 1` so a second account never sees install steps ✓. **Managed/demo:** showcase `demo` user has no `onboarding_completed_at` → sees the full wizard every reset (14-D4 — owner: intended showcase or set it complete?). **Phone:** hero stacks, theme cards 3-up, chips 44 px ✓.

### A5. Load-bearing conditions
- Draft-until-Finish (L35): every advance is side-effect-free; `applyDraft` is the single write path, in dependency order ✓.
- Seeds are idempotent by name; the server resolves group/location **names**, so items can reference catalogue entries that have no ids until Finish (FU-191) ✓.
- Only the features **diff** is sent, so a richer stored value (nutrition `complex`) survives an untouched card ✓.
- Router gate: `onboarding_completed_at === null` ⇒ `/welcome`; the two auth-store refreshes after complete/restart are what stop the bounce loop ✓.

### A6. Release-gate rows
- [ ] Finish with the demo recipe on a week that already has a plan reuses that plan (after 14-R1).
- [ ] Demo ingredients reuse "Pasta" / "Garlic" / "Olive oil" from the packs (after 14-R2).
- [ ] Skip → dashboard banner → Continue → wizard restores the draft (today ✓; keep).
- [ ] A first user who leaves Timezone untouched ends with the **device** zone saved, not UTC (today ✓ — closes FU-632 #48's timezone half).

---

## B. Help content — Onboarding

### B1. Current help audit
`HelpPage.vue` has **no** entry about first-run, the tour, starter packs, or re-running the wizard (the only "welcome" hit is assistant copy at `:256`). `APP_OVERVIEW` says nothing about onboarding. In-wizard copy is good and honest (FU-184 pass holds). Two code comments promise a "Restart onboarding" entry in Settings → Account (`DashboardPage.vue:606–607`, `user.py:187–189`) that was never built — the only way back in is the 24-hour dashboard banner after a Skip (14-R3).

### B2. Help entries

#### Your first run: Story then Setup
- **Group:** Dora itself
- **What it does:** A short story (why Dora, the Stock → Plan → List → Shop → Restock → Cook loop, what Dora remembers, what you can switch off) then a one-minute setup. Nothing is saved until you press Finish.
- **When it fires / how to trigger it:** First sign-in of any account; the first user of an install gets two extra steps (features + stock).
- **What controls it:** always on; "Skip onboarding" completes it immediately.
- **What it costs / might get wrong:** Skipping leaves the install on its defaults (UTC timezone, metric, Stocktakes + Auto-add on) — the dashboard reminds you for 24 hours.
- **Related:** What Finish sets up · Running setup again. **Chip:** none. **Source:** `WelcomeWizard.vue`, PROPOSAL_ONBOARDING §2–3.

#### What Finish sets up
- **Group:** Dora itself
- **What it does:** Your look (theme, font, picture); for the first user also the household (people, timezone, units), the feature switches, Dora's default locations/groups/starter items you left ticked plus your own, and optionally one demo recipe on this week's plan.
- **What controls it:** The recap on the last step lists exactly what will be written; every row has Change.
- **What it costs / might get wrong:** Items start as Stocked; the demo recipe adds three pantry items if you didn't pick them. Everything is editable afterwards in Stock / Settings.
- **Related:** Starter packs · Stock locations: zones, areas, sections (chunk 13). **Chip:** none. **Source:** `WelcomeWizard.vue:1329–1392`.

#### Starter packs and your own items
- **Group:** Stock
- **What it does:** Five packs (fridge staples, pantry basics, fruit & veg, freezer, cleaning) you tick on or off item by item; add your own with a group and location.
- **What it costs / might get wrong:** Dedupes by name — an item you already have is skipped, not duplicated. Groups/locations are matched by name to what you picked above.
- **Related:** Add a stock item. **Chip:** none. **Source:** `starter_packs.json`, `onboarding.py:456–559`.

#### Features you can switch on at setup
- **Group:** Settings & admin
- **What it does:** Spend tracking, Nutrition (simple), Stocktakes, Auto-add essentials, Batch cooking, Barcodes & QR — the same install-wide switches as Settings → Admin.
- **What controls it:** First user only; each later lives on its own Admin page (Money, Nutrition, Stocktake, Stock, Cooking, Stock).
- **Related:** Kitchen features (admin) (chunk 13). **Chip:** none. **Source:** `WelcomeWizard.vue:782–819`.

#### Running setup again
- **Group:** Dora itself
- **What it does:** After "Skip onboarding" the dashboard offers Continue for 24 hours, which reopens the wizard with your draft. There is no other way back in today (14-R3 adds one).
- **Related:** Your first run. **Chip:** none. **Source:** `DashboardPage.vue:575–625`, `/onboarding/restart`.

### B3. DoraBot corpus delta
Add to `APP_OVERVIEW`: *"New accounts start with a short story and a one-minute setup; the first user also picks household settings, features, and starter stock. Finish applies it all at once; Skip keeps the defaults and the dashboard offers to continue for a day."* Tool nav: a `restart_onboarding` action is **not** warranted (anti-creep) — point "how do I see the tour again" at the help entry.

---

## C. Senior review — Onboarding

### C1. Bugs (verified or high-confidence latent)
- **14-R1** · bug · `onboarding.py:685–705` · `SeedDemoHandler` always inserts a **new** `MealPlan(start_date=monday)`; `MealPlan` has no week uniqueness (`table_mappings.py:996–1010`) and nothing looks for an existing plan. A user who made a plan from the "Plan the week" tile, then Continue → Finish with the demo ticked, gets two plans for one week (the planner's duplicate-week hazard, chunk 2). **Change:** look up a plan with `start_date == monday` first (reuse `features/meal_plans` list query via the repository, `EntityField(MealPlan, "start_date").eq(monday)`), append the entry to it, else create. Blast S. Guard: extend `test_onboarding_seed_demo.py` with "existing plan for the week → entry appended, plan count unchanged". **execute**.
- **14-R2** · bug (data quality) · `onboarding.py:582–586` `_DEMO_INGREDIENTS` names "Spaghetti pasta" / "Garlic cloves" vs `starter_packs.json` "Pasta" / "Garlic"; `WelcomeWizard.vue:1384–1386` claims the demo reuses the pack picks — it does for "Olive oil" only. **Change:** rename the two demo ingredients to the pack names ("Pasta", "Garlic") so by-name reuse works; fix the wizard comment. Blast S. Guard: `test_onboarding_seed_demo.py` renames list. **execute**.
- **14-R3** · bug (missing UI the code promises) · `user.py:187–189` "Cleared by the Settings → Account 'Restart onboarding' entry", `DashboardPage.vue:606–607` "Same shape as the AccountSettings 'Restart onboarding' action" — neither exists; `/onboarding/restart` is reachable only via the 24-hour skip banner. **Change (owner-neutral, small):** add a "Run the welcome tour again" row to About → Project & support (chunk 13's AboutSettings list) calling `restartAsync` + `authStore.refreshAsync` + `router.push('/welcome')`, and correct both comments. Blast S. **execute** (owner may prefer Account — default About).
- **14-R4** · latent · `onboarding.py:688–694` · `scheduled_for = today if today >= monday else monday` — `monday = today − weekday` so `today >= monday` is always true; the comment promises a Wednesday fallback the code never does (R-019). **Change:** `scheduled_for = today`; delete the dead branch + fix the comment. Blast S. **execute**.
- **14-R5** · latent · `WelcomeWizard.vue:582–590` stores System as bare `'system'` while Preferences (`themeKeyFor('system', pesto)`) stores `'system-pesto'`; both decode to the same family but two spellings of one choice violate R-003 and the bare key only survives via the legacy branch in `familyAndModeOf`. **Change:** `value: themeKeyFor('system', THEME_FAMILIES[0])` etc. — derive the three cards from themeService. Blast S. **execute**.

### C2. Redundancy / DRY (R-001, R-003)
- **14-R6** · `onboarding.py:491–498` and `:621–626` both find the Stocked level by `sorted(levels, key=sequence)[0]` while `domain/stock_status.level_for_status(levels, StockStatus…)` is the one authority for "which level is this role". **Change:** one `_stocked_level(repo)` using `level_for_status`; the create-stock-item handler's default-level logic is the same question (chunk 6) — fold there if it already exists. Blast S. **execute**.
- **14-R7** · `onboarding.py:677,698` hardcode `"Dinner"` for `time_of_day` and `slot`; meal slots are a user-editable vocabulary (`MEAL_SLOT_NAMES` is the seed, not the law). **Change:** resolve the slot from `MealSlot` rows (first by sequence whose name is "Dinner", else the last slot) and use it for both fields. Blast S. **execute**.
- **14-R8** · seven endpoint prologues repeat `_current_user_id()` → 401 → `repo.get(User).by_id` → 404 (`onboarding.py:120–127, 136–143, 151–158, 347–350, 440–443, 549–552, 723–726`); `_current_user_id` is itself an 11th copy of the session parse (FU-654). **Change:** `auth/session_user.py: require_session_user(repo) -> tuple[User|None, Response|None]` (the FU-654 helper), used here ×7 and by chunks 11/12/13's sites. Blast S here. **execute** under FU-654.
- **14-R9** · `WelcomeWizard.vue:845–853,855–860` duplicate `AdminSystemRegionSettings.vue:345–353,473` (timezone options filter + device-zone read); `WelcomeWizard.vue:861–866` duplicates `AdminSystemCookingSettings.vue:109–114` (`normaliseHeadcount`). **Change:** `components/settings/TimezoneSelect.vue` (owns `TIMEZONE_CHOICES` + filter) and `models/regionChoices.ts: deviceTimezone()`; `models/household.ts: normaliseHeadcount()` (bounds mirror the server's 1–99 — note it as the one place the TS mirror lives). Blast S (3 files). **execute**.
- **14-R10** · `GetOnboardingStateHandler` (`onboarding.py:101–128`) is built with a second `SqlAlchemyRepository()` after `repo` was already created two lines up. **Change:** pass `repo`. Blast S. **execute**.
- **14-R11** · `seed.py`, `seed_dense.py`, `seed_showcase.py` each re-declare the three `StockLevel` rows, the `canonical_pair` substitute-insert loop, the belief-shop + cook-consume helpers (`seed.py:798–826` ≈ `seed_showcase.py:257–285` ≈ `seed_dense.py:1203–1211`), and the QA-cheese fixture (`seed.py:971–1003` ≡ `seed_dense.py:1687–1715`). FU-556 moved the row builders but not these. **Change:** add `seed_levels()`, `seed_substitutes(pairs)`, `shops_for(item, …)`, `cook_consume(…)`, `seed_qa_verdict_fixture()` to `SeedBuilders`. Blast M (dev-only code). **execute** (low risk: seeds are exercised by `test_onboarding_seed_demo` + boot).

### C3. Dead code / unused fields / unread endpoints
- **14-R12** · `OnboardingStateDto.completed`, `.completed_at`, `.store_status` (`onboarding.py:82–98`) and the TS `StoreStatus`/`OnboardingState.completed*` (`models/onboarding.ts:4–14`) — grep: the wizard reads only `first_user`; `StoreStatusDto` is self-described as "kept for payload compatibility" with a shape no client reads. **Change:** trim the DTO to `{first_user}` (+ the `GET /onboarding/state` test if one lands). Blast S. **execute**.
- **14-R13** · `OnboardingLoop.vue:83–91` props `autoplay`/`interactive` — one consumer passes neither; the "Finish-step recap passes false" comment refers to a recap removed 2026-10-17; `doraMood = computed(() => 'happy')` is a constant. **Change:** drop both props and the computed; `shouldAnimate = !prefersReducedMotion`. Blast S. **execute**.
- **14-R14** · `WelcomeWizard.vue:984–985,1016–1017,1068–1073,1086–1088,1123–1129` — the pre-FU-195 `seedGroups`/`seedLocations` legacy-draft fold. The draft key is per user and the wizard was rebuilt twice since; no live draft can carry those booleans. **Change:** delete the legacy branch. Blast S. **execute**.
- **14-R15** · `models/onboarding.ts:16–35` `SeedRequest`/`SeedResult` comments and `onboarding.py:1–16` module docstring ("Four endpoints"; "Seed catalogues … groups / locations" only) describe the pre-C-5.5 surface — seven endpoints, three catalogues (R-019). **Change:** rewrite both. **execute**.
- **14-R16** · stale comments: `onboardingContent.ts:47–49` ("the price-memory claim lives on the provisional `LOOP_INSIGHT` node below" — removed), `OnboardingLoop.vue:256` ("Centre: Dora + the provisional Insight candidate"), `seed_showcase.py:16–20` ("Both seeds duplicate a handful of tiny local builders … logged as a DRY follow-up" — FU-556 shipped), `IMPL_PLAN_ONBOARDING.md §0` "already true" list (predates the rebuild). **Change:** fix the three code comments; add a one-line "superseded by the 2026-10-17/21 rebuild — see CHUNK_14" note at the top of the impl plan's §0. **execute**.

### C4. Componentisation opportunities (R-001)
- **14-R17** · `WelcomeWizard.vue` is 2,078 lines holding four steps + the finish recap + the apply pipeline. The components it already extracted (pick panel, rail, story) leave the welcome/features/finish templates and ~700 lines of CSS inline. **Change:** `OnboardingWelcomeStep.vue` (avatar + theme cards + font), `OnboardingFeaturesStep.vue` (household panel + `FEATURE_CARDS`), `OnboardingFinishStep.vue` (hero + recap + tiles); the wizard keeps state + `applyDraft`. The `.feature-card` CSS is used by both the features step and the demo toggle on Finish — one `FeatureToggleCard.vue`. Blast M (pure move, props in / events out). **execute** (same shape as the page-split FU chunk 4 raised for cook mode; do this one now because the file is already past the R-001 line).
- **14-R18** · theme card mini-mock-up (`WelcomeWizard.vue:145–158, 1687–1725`) vs Preferences' swatch strips (`PreferencesSettings.vue:44–51`) — two previews of a theme. **Change:** keep both (different fidelity on purpose) but move the `data-theme`-painted mock-up into `ThemePreviewCard.vue` so Preferences can adopt it later. Blast S. **FU** (opportunistic; owner may like the mock-up in Preferences).

### C5. Placement / layering (R-003, R-005)
- **14-R19** · `WelcomeWizard.vue:1397–1413` creates the user's own groups/locations client-side with per-name existence checks (two extra GETs + N POSTs) while `POST /onboarding/seed-items` already resolves names server-side and `SeedHandler` dedupes by name. **Change:** extend `SeedRequest` with `extra_group_names` / `extra_location_names` so the server creates them in the same unit of work (FU-512's single commit then covers the user's own entries too). Blast S/M. **execute**.
- **14-R20** · `onboarding_catalog` re-reads three JSON files per request (`onboarding.py:444–452`); `_load_seed` is called again inside `SeedHandler`. **Change:** `functools.lru_cache` on `_load_seed` (files are bundled, immutable at runtime). Blast S. **execute**.
- **14-R21** · `WelcomeLayout.vue:31–32` hardcodes `#1e2a26` / `#ffffff` while the layout already pins `data-theme="pesto-dark"` so the tokens are the right values. **Change:** `background: var(--surface-page); color: var(--text-primary);` (R-002). Blast S. **execute**.

### C6. Naming & idiom
- **14-R22** · `WelcomeWizard.vue:497` `:icon-right="isLastStep ? 'check' : 'arrow_forward'"` bare icon names (R-034). **Change:** `ICONS.check` / `ICONS.arrow_forward`. **execute**.
- **14-R23** · `onboarding.py` mixes `_LOGGER` (module const) with the codebase's `_Logger`/`logging.getLogger(__name__)` idiom used elsewhere; also `request` shadows the Flask name in four handlers (`seed_onboarding`, `seed_items_onboarding`). **Change:** rename to `_Request` per `update_app_settings.py`. **execute**.
- **14-R24** · `ICONS.mealsPrepared` (`icons.ts:353`) is the registry's only camelCase key. **Change:** `meals_prepared` + the two call sites. **execute** (fold into FU-692's icon pass).

### C7. Efficiency
- **14-R25** · `SeedHandler._find_existing` (`onboarding.py:329–342`) does a full `StockLocation.all()` scan per existing zone inside the zone loop, right after building `existing_pairs` from the same query. **Change:** build a `{(parent, name): entity}` map once and index it. Blast S. **execute** (with 14-R19).
- **14-R26** · `WelcomeWizard.vue:1143–1151` deep-watches twelve reactive sources and serialises the whole draft to `localStorage` on every keystroke. **Change:** debounce 300 ms. Blast S. **execute**.

### C8. Design-level findings — out of Stage-2 scope
- **14-D1** · Feedback L46 (stock-item vs product explainer before adding items) is **dropped by the products-as-overlay pivot** (no products exist on day 1, so the conditional explainer never fires) — `COVERAGE_GAPS.md:175` already says so. Chunk 10's help entry "Stock items vs products" is where the explanation now lives. No change.
- **14-D2** · Finish is a multi-request apply; a failure midway leaves prefs/settings written (seeds are idempotent, so re-Finish converges). A single server-side `POST /onboarding/finish` taking the whole draft would make it atomic — real work, not a tidy; owner call whether the partial-apply window matters.
- **14-D3** · Story scene 4's illustrative switches show "AI assistant — on" by default; AI mode is per-user opt-in and off. Flip the illustration to `on: false` for honesty (P3) — one-line, but it is copy, so owner's.
- **14-D4** · Showcase `demo` user is created without `onboarding_completed_at`, so every demo reset re-shows the wizard. Owner: is that the intended showcase first impression, or should the demo land on a populated dashboard?
- **14-D5** · "Skip onboarding" label vs feedback L35 "just say Skip" — the longer label was chosen when the button moved to the top row; fine either way.
- **14-D6** · Locale/currency are still not asked at first run (FU-632 #48's other half); timezone + units now are. Adding "Language & format" to the household panel (pre-filled from `navigator.language`, reusing Region's `LOCALE_CHOICES`) is a small addition the owner should OK — it changes every date/money render on the install.

### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `OnboardingConfetti.vue` | 40 CSS-animated spans, deterministic | `canvas-confetti` | **keep** | – | 70 lines, reduced-motion aware, no dep. |
| `OnboardingLoop.vue` ring | SVG circle + positioned buttons | d3 / anime.js | **keep** | – | One `pathLength` trick; no library earns its weight. |
| `OnboardingStepRail.vue` | dots rail | `q-stepper` | **keep** | – | Non-linear, two sections; q-stepper is linear by design. |
| `OnboardingPickPanel.vue` chips | role=checkbox buttons | `q-chip selectable` | **keep** | – | Caption + removable variants; q-chip can't carry both cleanly. |
| Wizard draft in `localStorage` | hand JSON round-trip | VueUse `useStorage` (not a dep) | **keep** | – | Debounce it (14-R26). |
| `q-select` ×4 in the wizard | timezone, group, location pickers | `BaseSelect` | **replace** | S | FU-675's migration list +4. |

### C10. Standards drift (R-0NN)
- **14-R27** · R-002: `WelcomeLayout.vue:31–32` hex literals (14-R21); `OnboardingConfetti.vue:25` `var(--q-info)` is a Quasar palette var, not a Dora token → `var(--semantic-info)`. **execute**.
- **14-R28** · R-034: bare icon strings (14-R22). **execute**.
- **14-R29** · R-019 comment≠code: 14-R4, 14-R15, 14-R16, and `user.py:187–189` / `DashboardPage.vue:606–607` (14-R3). **execute**.
- **14-R30** · R-021: `seed.py:72`, `seed_dense.py:123`, `seed_showcase.py:82` use `date.today()` (server-local) and `seed_dense.py:1387` stamps consumption at 19:00 **UTC**; `onboarding.py:688` correctly uses `household_today`. Dev seeders only — **waive** with an inline `# R-021 carve-out: dev fixture, server-local date is fine` on each.
- **14-R31** · D-002 ride-along: `WelcomeWizard.vue:77–78,383–384` `UserAvatar color="accent" text-color="dark"` Quasar palette names (same as 13-C11). **FU** (FU-010/224 sweep).

### C11. Ride-along signals for FU-010 / FU-224 (theme / colour)
- `WelcomeLayout` hex pair; `--q-info` in confetti; `.loop-node.is-active` uses `var(--surface-component)` as **text** colour on a brand-primary fill (should be `--text-on-primary`, FU-674's token) — `OnboardingLoop.vue:236,243`; `.finish-tile__num` already uses `--text-on-primary` ✓.

---

## D. Test plan — Onboarding

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `seed-demo` on a week that already has a `MealPlan` → entry appended to it, plan count unchanged | pytest | must-write-before-ship | 14-R1 |
| `seed-demo` after `seed-items` with the three pack names → `items_created == 0` | pytest | must-write-before-ship | 14-R2 |
| `GET /onboarding/state` → `{first_user}` only; `/complete` then `/auth/me.onboarding_completed_at` non-null; `/restart` → null | pytest | nice-to-have | 14-R12 (contract pin) |
| `SeedRequest.extra_group_names` / `extra_location_names` created in the same transaction, deduped by name | pytest (unit, `_FakeRepo`) | nice-to-have | 14-R19 |
| Wizard `THEME_OPTIONS` values equal `themeKeyFor(mode, pesto)` | vitest | nice-to-have | 14-R5 |
| `normaliseHeadcount` bounds (null / 0 / 1.7 / 150) | vitest | nice-to-have | 14-R9 |

Existing coverage is strong on the seed handlers (17 unit + 13 e2e); none on the wizard itself and that stays so (lean stance — one manual walk of A2 per release).

---

## E. Proposed follow-ups (orchestrator allocates ids)

- **urgent** · bug · demo seed inserts a second meal plan for the current week (14-R1). Stage 2.
- bug · demo ingredient names don't match the starter packs → duplicates (14-R2). Stage 2.
- bug · promised "Restart onboarding" entry doesn't exist; only the 24-h banner reaches `/restart` (14-R3). Stage 2 (About row) — owner may redirect to Account.
- finding · `WelcomeWizard.vue` 2,078 lines → three step components + `FeatureToggleCard` (14-R17). Stage 2.
- finding · own groups/locations created client-side outside the seed's unit of work (14-R19). Stage 2.
- finding · seeders still duplicate levels / substitutes / belief-shop / QA-cheese blocks post-FU-556 (14-R11). Stage 2, dev-only.
- finding · dead `OnboardingStateDto` fields + legacy draft fold + stale comments (14-R12/R14/R15/R16). Stage 2.
- decision · 14-D2 atomic `POST /onboarding/finish`. Owner.
- decision · 14-D3 story switch panel shows AI on. Owner (default: flip to off).
- decision · 14-D4 showcase demo user re-sees the wizard on every reset. Owner.
- decision · 14-D6 ask locale at first run (closes FU-632 #48 fully). Owner.
- advance · **FU-632 #48**: timezone + units are now collected on the first user's features step (since 2026-10-17); only locale remains — update the entry. **FU-578 #38** (jargon explainer) and **#39** (Price-history dead-end; no guided add-items step) are resolved by the 2026-10-17/21 rebuild — strike them in the FU body. **FU-654** +1 site (14-R8). **FU-675** +4 `q-select`s. **FU-692** +1 (`mealsPrepared` key). **FU-674** +1 (`.loop-node.is-active` ink).
- close-out · `PROPOSAL_ONBOARDING.md` §2.3.a and §3.2.a are still headed "Open thread" though both were overtaken (personas removed FU-210; products-as-overlay). Add the "Open decisions — closed" line pointing at FU-210 + `PROPOSAL_PRODUCTS_AS_OVERLAY.md`; mark `IMPL_PLAN_ONBOARDING.md` §0 superseded. Stage 2 doc tidy.

## F. Summary for the register

- FST rows: 10 golden + 12 edge + 4 gate · Help entries: 5 (all new — the surface had none) · Review findings: 31 (execute 26 / FU 2 / waive 1 / decisions 6 in C8) · Tests: 6 (must-write 2) · Bugs: 3 verified (R1–R3) + 2 latent (R4–R5)
- Feedback coverage (`# ONBOARDING` L24–L46): L24 same styling as login → dark pinned `WelcomeLayout` (login styling itself is chunk 15); L25–L27 dead Skip/Finish/Show-me → fixed (every tile finishes then navigates); L28 System/Light/Dark → Pesto → ✅ (14-R5 tidies the key); L29 admin wording → superseded (no admin step; features step instead); L30 Grocy + nav-away import → superseded (import lives in Settings → Admin → Data, chunk 18; wizard has no import); L32/L33 "you already have groups" → gone ✅; L34 pick all/none/some ✅; L35 Skip + persist-on-finish ✅ (label "Skip onboarding", 14-D5); L36 slim added list ✅; L37 starter template ✅; L38 demo recipe toggle ✅ (one toggle = recipe + plan); L39 confetti ✅; L40 tour covers more areas ✅; L41 core values ✅ (Story); L42 admin first-login features ✅; L43 workflows/diagrams → loop + numbered tiles ✅; L44 headcount ✅; L45 preferred stores → out of scope (FU-180, resolved); L46 stock-vs-product explainer → dropped by the overlay pivot (14-D1).
- One-liner: the wizard is finished and honest; the backend behind it needs two small fixes (a duplicate week plan from the demo seed, and demo ingredients that don't reuse the pack names), the promised "run the tour again" entry has to be built, and the 2,000-line wizard file wants splitting into its three steps.
