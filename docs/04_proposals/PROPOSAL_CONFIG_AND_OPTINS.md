# C-cross — Config, opt-ins & taxonomy settings → `PROPOSAL_CONFIG_AND_OPTINS.md`

**Type:** 🔵 design brief — produces this proposal, changes **NO code.**

**Why this brief exists.** Five of the per-surface Wave-C briefs each hit the same
wall: they define a *vocabulary* or an *opt-in*, then defer the actual config
surface to "C-cross". C-4 (cookbook) defines dietary-tag / cuisine / category /
tools vocabularies and a money-gated cost estimate and an off/simple/complex
nutrition mode; C-5 (onboarding) wants first-login feature enable/disable mirrored
in admin settings; C-1 (stock overview) needs a "show the zone, not the shelf"
location-display policy; C-9 (alerts) wants per-type opt-in. Rather than scatter
six half-specs of "a settings editor" across those docs, this brief owns the
cross-cutting config layer once, so the per-surface briefs can consume it.

**Scope boundary — settings-as-a-surface is still deferred.** The master plan
defers the *settings page redesign* (look/nav/polish) along with dashboard,
reports, waste, mobile. C-cross does **not** redesign the settings shell. It
designs the **specific config editors and opt-in switches** that approved
per-surface briefs explicitly require to function — the data models, the
ownership (per-user vs install-wide), and the minimum UI each needs. When the
settings surface is later picked up, it inherits these editors; it does not
re-litigate them.

**Charter check.** Effortless + Anti-creep is the tiebreak. Every opt-in here
defaults **off / hidden**, so a user who never touches settings sees a simpler
Dora, not a busier one (Principle: the core flow is never taxed by an add-on).
The money and nutrition surfaces in particular stay invisible until explicitly
turned on — the user was emphatic that "some people may not want to know how many
dollars they are eating."

---

## 1. Current state (grounded in code)

- **Per-user preferences** live on `User` (`dora_api/domain/entities/user.py`):
  `theme`, `font_family`, `font_size`, `deals_email_enabled/compact`,
  `voice_input_enabled`, `voice_output_enabled`, and — already — an **opt-in
  budget**: `budget_amount: float | None` (NULL = feature off) + `budget_period`.
  The voice flags are the existing precedent for "off by default, never silently
  activated"; the budget pair is the existing precedent for "NULL ⇒ the whole
  money surface is hidden." C-cross extends these patterns rather than inventing
  a new one.
- **Install-wide settings** live on `AppSetting`
  (`dora_api/domain/entities/app_setting.py`) — a single admin-edited row,
  currently only the bring-your-own-LLM fields (`llm_enabled`, `llm_base_url`,
  `llm_model`). This is the natural home for **install-level feature flags**.
- **Settings UI** is `SettingsShell.vue` + `pages/settings/*`
  (`PreferencesSettings` per-user; `SystemSettings`/`AccountSettings`/
  `UsersAdminSettings`/`MerchantsSettings`/`StockGroupsSettings`/
  `StockLocationsSettings`/`AuditLogSettings`/`AboutSettings`). Theme/font swatches
  in `PreferencesSettings` are the only legitimate template hex in the app
  (THEME_AUDIT DEC-10). There is **no taxonomy editor, no feature-flag panel, and
  no nutrition/money master switch today** — recipe tags / cuisine / category are
  seeded/hardcoded vocabularies with no add/edit/remove surface.
- **Locations** (`dora_api/domain/entities/stock_location.py`) are a fixed
  3-level hierarchy: **zone → area → section** (`kind` enum, app-enforced depth).
  "Zone" is the top level — this is the "main zone" the feedback wants surfaced.
  Today the UI shows the deepest node ("right shelf"), which is meaningless out of
  context.

> **Verify-state caveat:** the budget feature is partly built (`budget_amount`
> exists, dashboard + assistant read it) but there is **no explicit money master
> switch** — "budget off" is currently inferred from `budget_amount IS NULL`.
> §2.2 resolves whether that inference is enough or a real flag is needed (cost
> estimates want money-on *without* a budget number).

---

## 2. The design

### 2.0 Two tiers of config — the governing model

Everything below sorts into exactly one of two homes. Picking the wrong home is
the main design risk, so the rule is explicit:

| Tier | Lives on | Edited by | Use when… | Examples here |
|---|---|---|---|---|
| **Per-user preference / opt-in** | `User` | the user themselves | the choice is personal taste or "do *I* want to see this" | money opt-in, nutrition mode, location-detail level |
| **Install-wide config** | `AppSetting` (+ new taxonomy tables) | admin (household-shared) | the choice is a shared vocabulary or an install capability | feature flags, tag/cuisine/category/tools taxonomies, nutrition-DB source |

Dora is a **single-household** install — the taxonomies (what counts as a
"cuisine", which "tools" exist) are shared across the handful of users, not
per-person. So taxonomies are install-wide, seeded with today's defaults,
editable in settings. Whether *displaying* nutrition is on is personal, so the
**mode** is per-user; whether the nutrition *data source* exists is an install
capability, so it's admin.

### 2.1 The opt-in pattern (one shape, reused)

Every opt-in switch follows the existing budget/voice pattern:

- **Default state is off / hidden.** A fresh install and a never-touched-settings
  user get the minimal Dora.
- **Off means *gone*, not greyed.** When money is off, no budget card, no cost
  estimate, no "$" anywhere — not a disabled control. Same for nutrition.
- **The switch lives in one obvious place** (Preferences for per-user, a new
  Features panel for install-wide) and every consuming surface reads it; no
  surface invents its own copy (state-ownership principle — the flag is a
  server-owned fact, the client reads it).

### 2.2 Money opt-in — governs every dollar surface (L254)

**One per-user master switch** that gates *all* money/budget features as a group:
the dashboard budget card, the assistant's budget answers, **the recipe cost
estimate (C-4 §2.8)**, and **meal-plan budgets (C-2)**. The one explicit
exception the user named: **basic product-search price info stays visible** — it's
core deal-hunting, not an "add-on" (L254).

**Model decision (open §4-1):** today "money on" is implied by
`budget_amount IS NULL`. But the cost estimate is useful to a user who wants to
see per-recipe/per-plan dollars *without* setting a spending budget. So the clean
model is a dedicated flag — `money_features_enabled: bool` (default `False`) —
with `budget_amount` becoming the *optional sub-setting* (set a cap or not) once
money is on. Recommend the explicit flag; it's one column and removes the
overloaded-NULL smell.

- **Where it surfaces:** Preferences → a single "Show cost & budget features"
  toggle, with the budget-amount/period inputs revealed underneath when on.
- **Ripple:** C-4 §2.8 (cost estimate hidden when off), C-2 (plan budget hidden),
  dashboard budget card (deferred surface — already reads `budget_amount`; it
  gains the flag read), assistant budget tools.

### 2.3 Nutrition opt-in — off / simple / complex (L262, L263, L287)

Replace today's free-form nutrition textarea with a **per-user mode**:
`nutrition_mode ∈ {off, simple, complex}`, default **off**.

- **off** — nutrition is hidden everywhere (recipe detail, cards, cook mode). No
  field, no column shown.
- **simple** — a single **kcal** number per recipe, typed in; sortable/comparable
  in the cookbook (feeds C-4's compare/sort axes). No data-source needed.
- **complex** — auto-derived from stock-items linked to a **nutrition-facts DB**.
  This needs a *source*, which is **install-wide config** (admin): a
  `nutrition_db_source` setting (which DB / which fields). The user is openly
  unsure complex is worth the quantity→nutrition-conversion accuracy cost and
  says "maybe just stick to off and simple."
- **Recommend:** ship **off + simple** as the C-cross deliverable; treat
  **complex (the nutrition-DB editor + conversion) as a separately-gated later
  layer** — C-cross reserves the `nutrition_mode` enum value and the admin
  source-setting seam, but does not build the DB integration now (mirrors how
  C-10 reserves the `source` seam for C-8).
- **Placement:** with nutrition reduced to one number (simple) or auto (complex),
  the cramped "separate collapsed dropdown" complaint (L287) dissolves — simple is
  one field inline; complex shows a read-only derived block. C-4 §2.9 owns the
  recipe-form placement; C-cross owns the mode switch + the source seam.

### 2.4 Taxonomy settings editors — the shared CRUD surface (L238, L264, L283, L284, L310)

Four user-configurable vocabularies, **install-wide**, each seeded with today's
defaults, each gaining **add / edit / remove** in settings. The per-surface briefs
define *how each is used*; C-cross defines *the editor*.

| Taxonomy | Used by (defined in) | Selection semantics | Notes |
|---|---|---|---|
| **Dietary tags** | C-4 §2.2 | multi, tri-state filter (must/must-not/neutral) | the green +/red −/grey cycle is C-4's filter; C-cross just owns the list |
| **Cuisine** | C-4 §2.2 | single-select | **not** lumped with category, **not** a "tag" (L235, L255, L260) |
| **Category** | C-4 §2.2 | single-select | fate tied to C-4 open-decision 1 (keep vs collapse into cuisine) |
| **Tools required** | C-4 §2.6, consumed by C-3 | multi, inclusion/exclusion filter | e.g. food processor, 5L pot |

**One reusable editor component**, instantiated four times — a simple titled list
with inline add / rename / delete and drag-reorder. Shared concerns handled once:

- **Delete safety:** deleting a term that recipes still reference must not orphan
  them. Offer **reassign-or-clear on delete** (pick a replacement, or set the
  field empty) — same pattern as any taxonomy delete; never a silent FK break
  (cf. B4 delete-cascade discipline).
- **Seeding:** on first run, seed each list from today's hardcoded defaults so
  nothing regresses for existing installs (migration backfills from existing
  recipe values where possible).
- **Ownership:** install-wide (household-shared vocabulary), editable by any user
  by default — confirm admin-only vs all-users (§4-3).

> **Boundary with C-4:** C-cross builds the *editors and storage*; C-4 wires the
> recipe form's single-selects / tri-state filter to read these lists. If C-4's
> open-decision 1 collapses category into cuisine, C-cross simply drops the
> Category editor — the shape is unaffected.

### 2.5 Location-display policy — zone by default, breadcrumb on demand (L81, L107, L128)

The complaint: a location chip showing "right shelf" / "left shelf" is meaningless
out of context; it should show the **main zone** (fridge, pantry). Locations are
zone → area → section, so:

- **Default display = the top-level zone.** Everywhere a location is shown as a
  compact chip (stock overview row, stock detail, recipe ingredient grouping), the
  chip text is the **zone** name, not the deepest node.
- **Full breadcrumb on demand.** The complete `zone › area › section` path is
  available on hover/tap/expand for users who keep deep hierarchies. Cook-mode
  ingredient grouping already wants **base-location-only** grouping (C-3, L321) —
  same policy: group by zone, ignore sub-areas.
- **Detail level as a light per-user pref (optional, §4-4):** a
  `location_detail ∈ {zone, full}` preference for users who *want* the full path
  inline. Recommend shipping **zone-default with hover-for-full** and treating the
  pref as optional polish — it may be unnecessary.
- **L128 (location editable inline, no separate dropdown)** is a stock-detail
  *interaction* change, not a config one — it belongs to the stock-detail polish
  cluster, not C-cross. Noted here as the related bullet so it isn't lost; owned
  there.

This is a **display policy**, not a stored taxonomy — it changes how existing
location data is rendered. The only possible new state is the optional per-user
detail pref.

### 2.6 Feature-flag panel — install-wide enable/disable (L42)

The onboarding brief (C-5 §2.3) wants the **first-login admin step** to pick which
parts of Dora are enabled, and says explicitly *"need to add this there too"* —
i.e. a matching panel in admin settings, because what onboarding sets must be
changeable later. C-cross owns that panel + its storage; C-5's wizard step writes
to it.

- **Storage:** install-wide on `AppSetting` (extends the existing single-row
  pattern that already holds the LLM toggle). A small set of boolean capability
  flags, not a free-form list.
- **Which features are toggleable (open §4-2):** candidate set — deals email,
  the assistant (already has `llm_enabled` — fold it in, don't duplicate),
  meal-planning, the money/cost surfaces (note: this is the *install* capability;
  §2.2's per-user money opt-in still governs *personal* visibility), nutrition,
  the companion/ingestion surfaces. Recommend a **small, conservative set** of
  genuinely-optional whole features — not every minor toggle — to avoid a wall of
  switches (Anti-creep).
- **Relationship to per-user opt-ins:** install flag = "is this feature available
  on this install at all"; per-user opt-in = "do I personally want to see it." A
  feature off at the install level hides it for everyone regardless of personal
  prefs; on at install level, per-user opt-ins still apply. Document this
  precedence so the two layers don't fight.
- **Relationship to C-9 alert opt-ins:** the per-type alert on/off (L441) is
  **owned by C-9**, not here — it's a finer-grained, per-user, per-alert-type
  setting living in the alerts control centre. C-cross's feature panel can carry a
  single coarse "alerts feature on/off"; the per-type matrix stays C-9. Cross-ref,
  don't absorb.

### 2.7 What C-cross deliberately does NOT do

- Does **not** redesign the settings shell / nav (deferred surface).
- Does **not** build the nutrition-DB integration or quantity→nutrition
  conversion (reserved seam only — §2.3).
- Does **not** own the cuisine-vs-category keep/collapse decision (that's C-4's
  open-decision 1; C-cross just provides whichever editors result).
- Does **not** own the per-type alert matrix (C-9) or the inline location-edit
  interaction (stock-detail polish).
- Does **not** touch merchant/provider enable-disable (companion / C-8 scope,
  though the original spec lists it as a global option — see §6).

---

## 3. Data-model summary

| Change | Home | Default | Gated feature |
|---|---|---|---|
| `money_features_enabled: bool` (new) | `User` | `False` | §2.2 — all dollar surfaces |
| `budget_amount`/`budget_period` (exist) | `User` | NULL/weekly | becomes sub-setting under money-on |
| `nutrition_mode: str{off,simple,complex}` (new) | `User` | `off` | §2.3 |
| `nutrition_db_source` (new, reserved) | `AppSetting` | empty | §2.3 complex (later) |
| `location_detail: str{zone,full}` (new, optional) | `User` | `zone` | §2.5 |
| Taxonomy tables: dietary-tag, cuisine, category, tool (new) | install-wide | seeded defaults | §2.4 |
| Feature-flag booleans (new; fold in existing `llm_enabled`) | `AppSetting` | conservative | §2.6 |

All new columns/tables ship with **clean Alembic migrations** (no idempotent
guards), seeding taxonomies from existing values, per the repo's migration
discipline.

---

## 4. Open decisions (for co-design)

1. **Money switch shape (§2.2)** — dedicated `money_features_enabled` flag
   (recommended; lets cost-estimate run without a budget number), or keep
   inferring "money on" from `budget_amount IS NULL`?
2. **Feature-flag set (§2.6)** — which whole features are toggleable? Recommend a
   small conservative set (assistant [existing], deals email, meal-planning,
   money, nutrition, companion-ingestion). Confirm the list and that the
   onboarding step writes the same flags.
3. **Taxonomy edit permission (§2.4)** — admin-only, or any user (household-shared
   vocab)? Recommend **any user** for a single-household install; admin-only if you
   expect multi-tenant later.
4. **Location detail pref (§2.5)** — ship zone-default + hover-for-full only
   (recommended), or also add the per-user `location_detail` toggle now?
5. **Nutrition complex scope (§2.3)** — confirm **off + simple now, complex
   (nutrition-DB) deferred** as a reserved seam, mirroring C-10/C-8.

---

## 5. Ripple & dependencies

- **C-4 (cookbook)** — consumes every taxonomy editor (§2.4), the money opt-in for
  cost estimate (§2.2), the nutrition mode (§2.3). C-4 should land *after* the
  C-cross editors exist, or stub them.
- **C-5 (onboarding)** — its first-login feature step (§2.3 there) writes the §2.6
  flags; the two must agree on the flag set (§4-2).
- **C-2 (meal plans)** — plan budgets hidden when money off (§2.2).
- **C-3 (cook mode)** — tools list (§2.4) drives per-step tool highlighting;
  base-zone ingredient grouping shares §2.5's zone policy.
- **C-1 (stock overview)** — location chip shows the zone per §2.5.
- **C-9 (alerts)** — coarse alerts on/off may sit in §2.6; the per-type matrix
  stays in C-9.
- **State-ownership** — every flag/mode is a **server-owned fact** the client
  reads, never a client-side copy (aligns with the standing principle + the
  state-ownership impl plan).
- **Deferred surfaces** — the settings *shell* redesign and the dashboard budget
  *card* are deferred; C-cross gives them the data/editors they'll later present.

---

## 6. From the original spec (historical — `docs/00_original_spec/`)

Non-authoritative; the charter/feedback override. From the **User & Global
Options** Feature Board:

| Original note | Verdict | Effect |
|---|---|---|
| *"I can disable features I don't wish to use at any time"* + *"I can re-enable features I've disabled at any time"* | **keep — grounds §2.6** | Direct corroboration that a feature enable/disable panel was always intended; the feedback (L42) just adds the first-login entry point. |
| *"I can navigate to a separate settings page that configures all parts of Dora (MAPI, emailer, etc)"* | **consider / mostly superseded** | The settings shell already exists; C-cross adds the missing config editors rather than a new page. The "all parts" ambition is the deferred settings-surface work. |
| *"I can disable/enable merchants from being searched entirely"* | **superseded → companion** | Merchant enable/disable is C-8/companion scope (master Decision 1), not Dora-core C-cross. Noted so the dropped intent is traceable. |
| *"I can change the language used in the UI (multi-language support)"* | **out of scope** | No feedback demand; large effort. Recorded for the record, not pursued. |
| *"buttons with text vs just icon buttons"* / *"page default state compact/expanded"* | **superseded by Wave A** | Button standard is A2; per-page view-state is ephemeral client state, not C-cross config. |

The board confirms the feature-flag intent predates this branch — §2.6 is
finishing a long-standing want, not inventing one.

---

## 7. Feedback coverage

Maps the cross-cutting config/opt-in bullets that motivated C-cross (per the
CLAUDE.md rule for cross-cutting briefs: the bullets this work answers, not every
app bullet). Source:
`docs/02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md`.

| Bullet | Summary | Where |
|---|---|---|
| L42 | Admin first-login feature enable/disable + matching settings panel | §2.6 (panel) ← C-5 (wizard step) |
| L81 | Location chip → main zone, not "right shelf" | §2.5 |
| L107 | "Left shelf" meaningless on its own | §2.5 |
| L128 | Location editable inline, no separate dropdown | §2.5 note → stock-detail polish (owned there) |
| L235 | Cuisine/category not lumped, not "tags" | §2.4 (editors) ← C-4 §2.2 (vocabulary/semantics) |
| L238 | Settings page for recipe tags (seed + add/edit/remove) | §2.4 |
| L254 | Recipe cost estimate; all money features opt-out (core flow untouched) | §2.2 |
| L255 | Cuisine/category single-select, not multi | §2.4 ← C-4 §2.2 |
| L260 | Why is cuisine ≠ category? | C-4 open-decision 1; §2.4 provides resulting editors |
| L262 | Nutrition currently noise | §2.3 |
| L263 | Nutrition opt-in; off/simple/complex; nutrition-DB configurable | §2.3 |
| L264 | Dietary tags configurable (toggle / add/edit/delete) | §2.4 |
| L283 | Category → configurable filterable dropdown in settings | §2.4 ← C-4 §2.2 |
| L284 | Cuisine → same as category | §2.4 ← C-4 §2.2 |
| L287 | Nutrition field placement (out of place collapsed) | §2.3 (mode-driven) → C-4 §2.9 (form placement) |
| L310 | Tools required — configurable dropdown in settings | §2.4 |
| L321 | Ingredients grouped by base location only | §2.5 (zone policy) → C-3 (cook-mode grouping) |
| L441 | Opt in/out of alert types | **C-9** (per-type); §2.6 carries only a coarse on/off |

Out-of-scope here, owned elsewhere: per-type alert matrix (C-9); inline
location-edit interaction (stock-detail polish); merchant enable/disable (C-8 /
companion); cuisine-vs-category keep/collapse (C-4 open-decision 1); nutrition-DB
integration build (reserved seam, later layer).

---

## 8. Suggested sequencing

1. **Feature-flag panel + storage (§2.6)** first — C-5 onboarding and several
   surfaces gate on it; it's the lowest-risk (booleans on the existing
   `AppSetting` row).
2. **Money opt-in flag (§2.2)** — one `User` column + read-sites; unblocks C-4
   cost estimate and C-2 plan budgets.
3. **Taxonomy editors (§2.4)** — the shared CRUD component ×4, seeded + delete-safe;
   unblocks C-4's tag/cuisine/category/tools.
4. **Nutrition mode off+simple (§2.3)** — enum + kcal field; reserve the
   nutrition-DB source seam, don't build complex.
5. **Location-display policy (§2.5)** — rendering change + optional pref; coordinate
   with C-1 and C-3 so the zone rule is applied once.

No code until approved — this is a brief. On approval, each numbered item becomes
its own implementation prompt (or folds into the consuming per-surface prompt).
