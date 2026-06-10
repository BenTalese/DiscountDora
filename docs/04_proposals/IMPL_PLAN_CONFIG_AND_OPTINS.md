# IMPL — Config & Opt-ins (C-cross)

**Source proposal:** `04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md`
**Status:** drafted 2026-06-10. Decisions in proposal §4 resolved inline
in this plan where called out; the rest follow the proposal's
recommended path.
**Run order:** C-cross is **foundational** — consumed by C-1, C-2, C-4
(Chunk 9 specifically), C-5, C-9. Land this before those consume the
opt-ins; consumers stay on the existing "feature-on-everywhere" path
until each chunk gates the relevant render.

The proposal's **opt-in pattern** (§2.1, mirroring ADR-002) is the spine
of every chunk: server owns the flag → `/api/health` `features.*`
exposes install-wide flags, `/api/users/me` exposes per-user flags →
client reads through a tiny composable (`useFeatureFlags()`,
`useImagePrefs()`, etc.), **never** a duplicated Pinia store per flag
(R-001 / R-003).

---

## 0. Verify-state-first: no drift

Re-checked 2026-06-10 against the live code:

- **`AppSetting` row (`table_mappings.py:59`)** currently holds:
  `id, llm_enabled, llm_base_url, llm_model, scanning_enabled`.
  That's *two* install-wide capability flags so far + the LLM config
  trio. Everything else the proposal §2.6 wants — deals-email,
  meal-planning, money, nutrition, companion-ingestion — is **not yet
  on the row**; it'll be added cleanly here.
- **`/api/health` `_feature_flags()`** (`health_check.py:48`) exposes:
  `auth, audit, scanning, multi_user, email, assistant`. The
  scanning + assistant flags already read from AppSetting via
  `get_or_create_app_setting()`. The pattern works — extend it; do
  not introduce a parallel registration.
- **`User` row** (`user.py`) carries `budget_amount` / `budget_period`
  (P2-05). No `money_features_enabled`, no `nutrition_mode`, no
  `location_detail`, no `show_*_images` yet. All five new per-user
  columns land in this plan.
- **Taxonomy editors (proposal §2.4)** are **already shipped** —
  C-4 Chunk 2 landed Cuisine / Category / DietaryTag (with Settings →
  "Recipe tags & categories" CRUD), and C-4 Chunk 5 landed Tool with
  the same editor. The `VocabListEditor` component already
  generalises the pattern. **No work here** — the IMPL plan skips
  §2.4 entirely; the data model + UI already exist.
- **Recipe.nutrition** is the freeform string column (`recipe_table`)
  and is rendered in `RecipeDetailPage.vue:466-475` inside the
  "Nutrition (optional)" expansion. C-cross Chunk 3 below leaves the
  column in place (data preservation) but the chunk that consumes
  the mode (**C-4 Chunk 9**) stops rendering/editing it.
- **`Recipe.image` (bytes, data-URL)** + recipe-card / detail render
  paths already exist (C-4 Chunk 5). The C-cross image-display opt-in
  is a guard-only patch on those existing render sites — no new image
  pipeline. **`StockItem.image`** still has no render surface (FU-033
  deferred), so the stock-side guard is a no-op until that ships;
  C-cross still declares the flag now so FU-033 doesn't need to add
  it later.
- **Settings UI** (`pages/SettingsShell.vue` + per-area pages) is the
  surface for every opt-in toggle here. No nav redesign (proposal
  §2.7 — out of scope); chunks slot into the existing shell.

So the work falls into **six chunks**, ordered by dependency: foundational
opt-in pattern first, then each per-user flag in the order downstream
consumers need them.

---

## 1. Chunked plan (each chunk = one reviewable PR)

### Chunk 1 — Opt-in plumbing + install feature-flag panel ★ FIRST REVIEWABLE CHUNK

**Closes:** proposal §2.1 + §2.6 + L42.

Establishes the opt-in pattern as code (so every later chunk plugs into
it) and lands the install-wide feature-flag panel C-5 (onboarding wizard
step) needs to write to.

- **Backend:**
  - **Extend `AppSetting`** with the conservative install-flag set
    (§4-2 open decision answered with the proposal's recommended
    list): `meal_planning_enabled`, `money_enabled`,
    `nutrition_enabled`, `companion_ingestion_enabled`,
    `deals_email_enabled`. **Existing** `llm_enabled` /
    `scanning_enabled` stay where they are — the proposal explicitly
    wants them folded in, not duplicated. Defaults are conservative
    (all new flags `False` except `meal_planning_enabled = True`
    because meal-planning is already on for everyone today; we don't
    silently disable it for existing installs).
  - **Migration** `f<rev>_20260611_appsetting_install_flags.py`:
    batch-mode add the five new columns. No data migration — defaults
    are the entire seed.
  - **Extend `/api/health` `_feature_flags()`** to surface the new
    flags as `features.meal_planning`, `features.money`,
    `features.nutrition`, `features.companion_ingestion`,
    `features.deals_email`. Single source of read — the per-page
    composable hits health, not AppSetting directly. Keys never
    removed (the health endpoint contract, line 79–80).
  - **New `PATCH /api/admin/feature-flags`** endpoint — admin-only
    (existing `is_admin` check). Body is partial: `{ "money_enabled":
    true }` flips a single flag without affecting the others.
- **Frontend:**
  - **`useFeatureFlags()` composable** (`src/composables/`) — fetches
    `/api/health` once per session, caches in a ref, exposes
    `features` reactive object: `features.money.value`, etc. **Not a
    Pinia store** (R-001 / ADR-002 — single composable, not one per
    flag).
  - **New Settings → System → "Features" panel** (admin-only;
    hidden for non-admins). Toggles for each install-wide flag with a
    one-line "what this affects" caption. Posts to the new admin
    endpoint; refreshes the composable on success.
  - **Existing scanning + LLM toggles** stay in their current settings
    panels (don't churn working UI); the Features panel cross-links
    to them so users find every flag from one place.
- **Pattern record (ADR-005 candidate):** "C-cross opt-in pattern —
  install-wide booleans live on `AppSetting`, surface via
  `/api/health` `features.*`, consumed via a single composable per
  feature *family* (not per flag). Per-user opt-ins live on `User`,
  surface via `/api/users/me`, consumed the same way." Promote
  to ADR + R-0NN at end-of-chunk if it survives review.

**Engineering close-gate notes:**
- R-001: one shared composable, not one per flag.
- R-002: settings toggles theme-aware via existing `Q-toggle` tokens.
- R-003: server owns the boolean; client doesn't cache or shadow it.
- R-005/R-006: clean batch migration; no idempotent guards.
- R-007: scope stops at the panel + plumbing — no consumer chunks
  here. Existing scanning/LLM toggles untouched.
- R-008: terse; the chunk is wiring, not policy.
- R-011: `q-toggle` + `q-card` primitives.

*Acceptance:* admin sees the Features panel; a flipped toggle round-
trips through PATCH + refreshes the health cache; non-admins don't
see the panel; `features.*` keys appear on `/api/health`.

### Chunk 2 — Money opt-in (per-user) — §2.2

**Closes:** §2.2 + L254 + §4-1.

§4-1 open decision answered with the proposal's recommended path: a
dedicated `money_features_enabled` flag, **not** "money on when
budget_amount IS NOT NULL". The flag lets cost estimates (C-4 Chunk 9)
run without forcing a budget number.

- **Backend:**
  - **`User.money_features_enabled: bool`** (default `False`).
    Migration `f<rev>_20260611_user_money_optin.py`.
  - **`/api/users/me` DTO** exposes `money_features_enabled`. Existing
    `PATCH /me` already supports per-field updates; the new column is
    just a field on the request model.
  - **No render gates inside this chunk** — only the flag + storage.
    Consumers (dashboard budget card, assistant budget surfaces,
    C-2 plan budgets, C-4 Chunk 9 cost estimate) gate in their own
    chunks. Document the layering in the chunk's worklog note:
    **install `features.money` AND per-user `money_features_enabled`
    both must be true** for any dollar surface to render.
- **Frontend:**
  - **`useMoneyEnabled()` composable** — reads the user flag from
    `/me`, AND the install flag from the Chunk 1 composable, returns
    a single boolean `moneyEnabled.value` = `install && user`. This
    is the *only* read site downstream consumers should use.
  - **Settings → Account → "Money & budgets" section** — toggle for
    the per-user flag with copy explaining the layering ("This
    install also has to have money features enabled — admin
    setting."). When the user toggle is off, the existing
    `budget_amount` / `budget_period` controls hide (data
    preserved).
  - **No callers wired here.** Logged as ripple — each consumer
    chunk adds `v-if="moneyEnabled"` on its dollar render site when
    that work happens.

**Engineering close-gate:**
- R-001: one composable; layering happens there once.
- R-003: server owns; budget data preservation matters (don't null
  on toggle-off — the user expects their budget back when they
  re-enable).
- R-007: storage + plumbing only; no consumer rewrites.

*Acceptance:* a per-user toggle flips `money_features_enabled` via
`PATCH /me`; the composable returns `false` when either flag is off
and `true` when both are on; budget controls hide visually when
off but the saved budget value survives a toggle round-trip.

### Chunk 3 — Nutrition mode (per-user) — §2.3, off + simple now

**Closes:** §2.3 + L262 / L263 + §4-5.

§4-5 answered: ship **off + simple** now; **complex** is a reserved
seam (enum value + admin source-setting column present, no
implementation). Mirror C-10/C-8 reservation pattern.

- **Backend:**
  - **`User.nutrition_mode: str`** with `CHECK(nutrition_mode IN
    ('off','simple','complex'))` (or a Python-side
    `NUTRITION_MODE_VALUES` set + validation at the boundary per R-010
    carve-out for SQLite-portable enums). Default `'off'`.
  - **`AppSetting.nutrition_db_source: str`** default `''` —
    **reserved seam** for §2.3 complex. Column lands now so complex
    has a home when (if) it ships; no UI for it yet.
  - Migration `f<rev>_20260611_user_nutrition_mode.py` adds both
    columns.
  - `/api/users/me` exposes `nutrition_mode`. Validation rejects
    `'complex'` writes when `AppSetting.nutrition_db_source` is empty
    (so a user can't pick a broken mode).
- **Frontend:**
  - **`useNutritionMode()` composable** — returns the mode as a ref
    + a derived `nutritionEnabled = mode !== 'off'` boolean for
    quick gates.
  - **Settings → Account → "Nutrition" section** — three-way
    `q-btn-toggle` (Off / Simple / Complex). Complex disabled with a
    tooltip when `nutrition_db_source` is empty
    ("Configure a nutrition database first — coming later.").
  - **No Recipe.kcal column, no detail-page field, no kcal sort
    axis.** All of that lives in **C-4 Chunk 9**, which reads
    `nutritionEnabled` to gate every render.

**Engineering close-gate:**
- R-010 carve-out: status-sentinel pattern (`NUTRITION_MODE_VALUES =
  ('off','simple','complex')` + single validation point); name the
  carve-out in the validator comment per ENGINEERING_STANDARDS.md.
- R-007: scope stays at the mode + seam; no Recipe schema touched.

*Acceptance:* mode toggles via `/me`; the composable returns the
right boolean; the `complex` option is gated by the seam value; no
recipe surfaces change yet (proves the foundation lands cleanly
ahead of consumers).

### Chunk 4 — Location-display policy — §2.5, zone-default + tooltip

**Closes:** §2.5 + L81 / L107 / L128 + §4-4.

§4-4 answered: **zone-default + hover-for-full only**; the per-user
`location_detail` toggle is deferred (cheap to add later if users ask).
This chunk is a small cross-cutting render change.

- **Backend:** **none.** The locations tree already returns the full
  breadcrumb; the policy is a client-side rendering rule.
- **Frontend:**
  - **New `formatLocation(locationId, mode: 'zone' | 'full')`** helper
    in `src/helpers/locationDisplay.ts`. `'zone'` returns the
    **top-level** node name; `'full'` returns the breadcrumb joined
    with ` › `. The locations store already exposes a `breadcrumb()`
    method this helper sits on top of.
  - **Apply at every location-chip render site:** stock-overview
    row, stock-item detail header, recipe ingredient rows (detail +
    cook mode — C-3 Chunk 3 already groups by base zone, this
    aligns the rendering when the location ALSO appears on the row),
    shopping-list line location chips. Grep `breadcrumbFor(\|
    stock_location_breadcrumb` — those are the sites.
  - Every chip wraps in a `q-tooltip` showing the full breadcrumb on
    hover (desktop) / long-press (mobile). Theme-aware via existing
    A1 tokens.

**Engineering close-gate:**
- R-001: one helper, called from every render site. No copies.
- R-003: the rendering rule is a single decision in one file.
- R-007: ~6 render sites touched; no behaviour change beyond
  "show less, show full on hover".

*Acceptance:* every location chip shows only its zone; hover/long-
press reveals the full breadcrumb; nothing regresses on screens that
were already showing only "Pantry" (those collapse safely to the same
behaviour).

### Chunk 5 — Image-display opt-in (per-user) — §2.8

**Closes:** §2.8 + §4-6 + folds in FU-090.

§4-6 answered with the proposal's recommendations: **default on** for
both flags; **two separate flags**, not one. The toggle UX changed
2026-06-10 (user revision) — **no Settings page entry**; the toggles
live as inline buttons on the surfaces they affect, and the persisted
`User` flag rides across sessions.

- **Backend:**
  - **`User.show_recipe_images: bool`** (default `True`).
  - **`User.show_stock_images: bool`** (default `True`).
  - Migration `f<rev>_20260611_user_image_optins.py`.
  - `/api/users/me` exposes both; `PATCH /me` accepts either as a
    partial-update field. Existing `authStore.updateMeAsync()`
    handles the wire shape — no new endpoint.
  - **FU-090 fold-in** — the recipe list query currently loads the
    full image bytes blob even though only the `has_image` flag is
    needed. Convert to a deferred column / `defer()` so the bytes
    only load on detail. The bandwidth-saving promised by "images
    off" is otherwise hollow.
- **Frontend — composable + recipe surfaces (build now):**
  - **`useImagePrefs()` composable** returning
    `{ showRecipeImages, showStockImages, setRecipeImages(bool),
      setStockImages(bool) }`. The setters PATCH `/me` and update
    the local ref optimistically (rollback on error) — single write
    path everywhere, same pattern as the existing
    `authStore.updateMeAsync({ voice_output_enabled })` flow in
    cook mode.
  - **`RecipesOverview.vue` inline toggle** — small icon button in
    the header next to "Import from URL" / "New recipe". Icon flips
    between `image` (on) and `image_not_supported` (off); ghost
    variant so it doesn't compete visually. Pressed-state visual
    when off. Tooltip: "Show recipe photos · saved across sessions".
    Calls `setRecipeImages(!showRecipeImages.value)`.
  - **Recipe consumer surfaces** (read-only — no per-surface
    button; gate render on `showRecipeImages`):
    - `RecipeCard.vue` — the card photo / placeholder.
    - `RecipeDetailPage.vue` — the header image.
    - `RecipeEditDialog.vue` — preview (only the *displayed*
      preview is gated; the editor itself stays usable so the user
      can still upload/change/remove).
    - `RecipeCookMode.vue` — any image surface (currently none
      relevant; sanity-check).
    - `ExportPrint.vue` — print view image.
    Guard shape: `v-if="showRecipeImages && recipe.has_image"`.
    When false, the placeholder renders (the existing coloured-
    initial tile already handles the no-image case — same path).
  - **Skip the image-bytes fetch when off.** The
    `recipeImageUrl(id)` helper currently returns the URL
    unconditionally; the consumers pass it to `<img :src>` which
    triggers the GET. With the flag off the `v-if` short-circuits
    before the `<img>` mounts, so no network call. Verify in
    DevTools Network tab during browser-verify.
- **Frontend — stock surfaces (backend ready, frontend deferred):**
  - **`StockOverview.vue` collapse/expand button** — **NOT BUILT in
    this chunk.** The C-1 row redesign (Stock Overview IMPL plan
    Chunk 3) will land it together with the row-layout work, so
    the collapse affordance shares the row geometry decisions
    rather than fighting them. The flag + composable are ready
    for that chunk to consume.
  - **Stock-item ingredient rows on recipe detail / cook mode** —
    wire the guard NOW (cheap; they consume `showStockImages`),
    no-ops while FU-033 hasn't shipped stock-image rendering yet.
    Documents the contract so the eventual surface doesn't drift.
  - **Logged as FU-106** — surface the stock-overview button when
    C-1 next touches the row layout.

**Engineering close-gate:**
- R-001: one composable; one guard shape; one in-context toggle
  button (recipe overview) — stock toggle defers to C-1 redesign
  per the proposal's surface-author owns-the-control principle.
- R-003: server owns flags + `has_image`; client gates rendering
  + writes back through one composable setter.
- R-005/R-006: clean migration with defaults.
- R-007: stock-overview button **deliberately** deferred so the
  next C-1 chunk owns its row geometry; not built here.
- R-008: terse; the guards are one-liners; the inline toggle is a
  single `<BaseButton variant="ghost">` per surface.
- R-011: framework-idiomatic — uses `useQuasar` / `<BaseButton>`
  primitives + the existing `authStore.updateMeAsync()` channel,
  not a new Pinia store.
- FU-090: closed via the deferred-column fix.

*Acceptance:* both flags round-trip via `PATCH /me`; the recipes-
overview inline button flips `show_recipe_images` and the change
persists across reload; flipping recipe-images off makes every
recipe surface render the placeholder; DevTools confirms the
image-bytes endpoint isn't hit; toggling back on restores photos;
saved images survive a toggle round-trip; the recipe list endpoint
no longer loads image blobs (FU-090 closes); `show_stock_images`
field exists + round-trips even though no stock-overview button is
wired yet (logged as FU-106 for the C-1 redesign).

### Chunk 6 — Taxonomy editors (§2.4) — **NO WORK**

**Closes:** §2.4 (already shipped).

§2.4 was C-4 Chunks 2 (cuisine / category / dietary tags) + 5 (tools).
The `VocabListEditor` component, the four CRUD endpoints, the
Settings → "Recipe tags & categories" page — all live. This chunk
exists in the run order only as a marker so reviewers can confirm
nothing is owed here. **Skip on build; verify already in place during
the C-cross browser-verify pass.**

---

## 2. First reviewable chunk — definition of done

**Chunk 1 (opt-in plumbing + install feature-flag panel).**

- `AppSetting` carries the five new install flags + the two existing
  ones; migration applies cleanly on SQLite **and** Postgres;
  defaults are conservative (meal-planning preserves today's
  always-on behaviour).
- `/api/health` `features.*` carries seven flags
  (`auth`/`audit`/`multi_user`/`email` keep their always-on
  resolution; `assistant`/`scanning` keep their existing DB-backed
  resolution; the five new ones added).
- `PATCH /api/admin/feature-flags` returns 403 for non-admins; 200
  for admins; partial body updates only the named flag(s).
- `useFeatureFlags()` composable returns reactive `features.*`
  booleans; admin Settings → System → Features panel toggles round-
  trip cleanly.
- Existing scanning + LLM toggles in their current settings panels
  still work (no regression).
- Engineering close-gate: R-001 (single composable; one panel
  component), R-003 (no client-side flag caching beyond the
  composable), R-005 (Postgres + SQLite both pass), R-007 (no
  consumer wiring), R-011 (Quasar primitives, Vue 3.4 idioms).

---

## 3. Risks & open decisions

**Risks:**

- **Migration safety on existing installs** — the five new
  `AppSetting` flags arrive with conservative defaults so nothing
  silently changes for users on Chunk 1. Worth double-checking
  `meal_planning_enabled = True` default on the migration so existing
  meal-plan users don't lose their feature on first boot post-deploy.
- **Composable cache freshness** — flipping a flag in admin Settings
  needs to refresh `useFeatureFlags()`'s cached `/health` response.
  Trivial via a manual `refresh()` call after PATCH; skip a polling
  loop (R-007).
- **Per-user + install layering surprises** — a user with money on
  individually but install money off sees nothing. The Settings
  toggle copy must make the layering legible (Chunk 2 includes this
  in its copy plan).

**Open decisions answered inline:**

- **§4-1 Money switch shape:** dedicated `money_features_enabled`
  flag (recommended). Resolved in Chunk 2.
- **§4-2 Feature-flag set:** the proposal's conservative set
  (`meal_planning, money, nutrition, companion_ingestion,
  deals_email`) + the existing `llm`/`scanning`. Resolved in
  Chunk 1.
- **§4-3 Taxonomy edit permission:** **any user** — already shipped
  this way in C-4 Chunks 2 + 5. No revisit.
- **§4-4 Location detail pref:** zone-default + hover-for-full only,
  no per-user toggle. Resolved in Chunk 4.
- **§4-5 Nutrition complex scope:** off + simple now; complex
  reserved seam. Resolved in Chunk 3.
- **§4-6 Image-display defaults + flag count:** default on; two
  separate flags. Resolved in Chunk 5.

**Cross-refs:**

- **C-4 Chunk 9** consumes Chunks 2 (money) + 3 (nutrition).
  Schedule C-4 Chunk 9 *after* C-cross Chunks 2 + 3 land so its
  render gates have something real to read.
- **C-2 (meal plans)** consumes Chunk 2 (per-meal-plan budget hide
  when money off) — fold the gate into the next C-2 work.
- **C-1 (stock overview)** consumes Chunk 4 (location chip) and
  Chunk 5 (stock images) — both fold into the next C-1 work.
- **C-5 (onboarding)** consumes Chunk 1 (its first-login feature
  step writes to the same flags). Confirm the flag set the wizard
  exposes matches §2.6's conservative list.
- **C-9 (alerts)** consumes Chunk 1's coarse alerts-on/off (if we
  add it to §2.6) — open question, may stay C-9-owned per the
  proposal.

---

## 4. Feedback coverage

Cross-cutting brief — maps the bullets that *motivated* C-cross
(per the CLAUDE.md cross-cutting rule), not every app bullet.

| Bullet | Summary | Closed by |
|---|---|---|
| L42 | Admin first-login feature enable/disable + matching settings panel | Chunk 1 (panel) + C-5 (wizard, separate) |
| L81 | Location chip → main zone, not "right shelf" | Chunk 4 |
| L107 | "Left shelf" meaningless on its own | Chunk 4 |
| L128 | Location editable inline | out-of-scope here (stock-detail polish) — Chunk 4 only changes display |
| L235 | Cuisine/category not lumped, not "tags" | already shipped (C-4 Chunk 2) |
| L238 | Settings page for recipe tags (seed + add/edit/remove) | already shipped (C-4 Chunk 2) |
| L254 | Recipe cost estimate; all money features opt-out | Chunk 2 (foundation); C-4 Chunk 9 (render) |
| L255 | Cuisine/category single-select, not multi | already shipped (C-4 Chunk 2) |
| L260 | Why is cuisine ≠ category? | C-4 open-decision 1 (separate) |
| L262 | Nutrition currently noise | Chunk 3 (foundation); C-4 Chunk 9 (render) |
| L263 | Nutrition opt-in; off/simple/complex; DB configurable | Chunk 3 |
| L264 | Dietary tags configurable | already shipped (C-4 Chunk 2) |
| L283 | Category → configurable dropdown in settings | already shipped (C-4 Chunk 2) |
| L284 | Cuisine → same as category | already shipped (C-4 Chunk 2) |
| L287 | Nutrition field placement | Chunk 3 (mode) + C-4 Chunk 9 (placement) |
| L310 | Tools required — configurable dropdown | already shipped (C-4 Chunk 5) |
| L321 | Ingredients grouped by base location only | C-3 Chunk 3 (cook-mode); Chunk 4 aligns chips with the same zone policy |
| L441 | Opt in/out of alert types | **C-9** (per-type matrix); Chunk 1 may carry a coarse on/off |
| **2026-06-10 user ask** | Image-display opt-in for recipe + stock-item photos | Chunk 5 |

---

## 5. Suggested run order

Matches proposal §8 with the additions from §2.8:

1. **Chunk 1** — Feature-flag panel + opt-in plumbing. Foundational;
   every later chunk plugs into the composable + admin panel
   patterns it establishes.
2. **Chunk 2** — Money opt-in (per-user). Unblocks C-4 Chunk 9 cost
   estimate, C-2 plan budgets, dashboard budget render gates.
3. **Chunk 3** — Nutrition mode (off + simple) + reserved complex
   seam. Unblocks C-4 Chunk 9 kcal field.
4. **Chunk 4** — Location-display policy (zone + hover). Aligns the
   C-1 / C-3 / shopping-list chip rendering on the zone rule with
   no schema change.
5. **Chunk 5** — Image-display opt-in. Lands the recipe-side gates
   on shipped Chunk-5 surfaces + folds FU-090 deferred-column fix;
   stock-side is a no-op consumer awaiting FU-033.
6. **Chunk 6** — taxonomy editors (already shipped; verify-only).

After C-cross ships, the consumer roadmap is:

- **C-4 Chunk 9** (cost + simple nutrition) — first big consumer.
  Gate its renders on `useMoneyEnabled()` + `useNutritionMode()`.
- **C-2 / Dashboard / Assistant** money surfaces — gate on
  `useMoneyEnabled()` as those pages get touched.
- **C-1 stock overview** — adopt Chunk 4 location chips + Chunk 5
  image guards when its next chunks ship.
- **C-5 onboarding** — wizard's first-login feature step writes to
  the AppSetting flags Chunk 1 establishes.

No code until approved — Chunks 1–5 each become their own
implementation PR (Chunk 6 is verify-only).
