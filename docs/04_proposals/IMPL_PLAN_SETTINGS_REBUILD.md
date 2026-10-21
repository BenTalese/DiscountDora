# Settings Rebuild — Implementation Plan

**Status:** ✅ COMPLETE (Phases 1–5 landed 2026-06-23; static/tsc/lint-verified,
full browser walk pending — see `DORA_WORKLOG.md` + FU-286). Originally: brief —
ready for execution by a Claude agent.
**Raised:** 2026-06-19 (after a `/design-critique` pass + user feedback on the
current Settings surface). Round-2 deep-read findings folded in 2026-06-21
(see §2.10).
**Owns:** the entire `web_app/src/pages/settings/` directory + `SettingsShell.vue`
+ the side-nav routing and any per-section components extracted in the process.
**Cross-references:**
- `docs/01_charter/ENGINEERING_STANDARDS.md` — R-001 (componentisation),
  R-002 (theme tokens only), R-003 (single source of truth), R-007 (scope
  discipline), R-011 (framework-idiomatic Quasar/Vue), R-016 (lazy store
  hydration).
- `docs/01_charter/DASHY_DORA_CHAMPION_PLAN.md` — Charter principles
  (Effortless, Anti-creep, Honesty).
- Prior settings work: none consolidated; this brief supersedes any
  scattered settings polish in earlier prompts.

---

## 0. Read this first

This is a **rebuild brief**, not a one-shot prompt. The current Settings
surface has structural problems (information architecture) on top of visual
problems (every section reads as default-Quasar). A pure visual pass would
re-paint the same broken structure. Do the IA work first; the visual
polish lands on top of clean foundations.

The brief is decomposed into phases. Each phase is independently shippable
and ends with a clean diff + worklog entry. **Do not** roll all phases into
one PR — the user has explicitly asked for incremental delivery on this
surface before.

If you skip Phase 1 (IA / routing) and go straight to Phase 3 (visual), the
Charter check fails — the user has already said "an in-depth rebuild is
needed" and accepting that framing is the whole point.

---

## 1. Source of truth — current state

Current shell: `web_app/src/pages/SettingsShell.vue` (~178 lines).

Current sections, in display order:

**Your settings (personal):**
1. `/settings/preferences` — Appearance (theme/mode/font/size) + Weekly
   deals email + Alerts email digest + Push notifications + Money &
   budgets + Grocery budget + Nutrition mode. (One page, scrolls forever.)
2. `/settings/stock-locations` — manage zones/areas/sections.
3. `/settings/stock-groups` — manage tag-style groups for filtering.
4. `/settings/recipe-vocab` — Cuisines / Categories / Tools / Meal
   slots / Dietary tags (five types stacked on one page; Dietary tags
   uses a bespoke editor because tags carry a grouping label, the
   other four share `VocabSectionEditor`).
5. `/settings/account` — profile + sign-out. **No profile-picture
   upload today** — flagged in `docs/02_feedback/Feedback _ Fixes - as
   of [06-Jun-2026].md` L434 and `COVERAGE_GAPS.md` bucket A-5; original
   spec bullet under `docs/00_original_spec/Feature Boards/User & Global
   Options.md`. This brief folds it in (see §2.9).
6. `/settings/about` — version + project info.

**Admin · global:**
7. `/settings/admin/stores` — retail stores you shop at + logos.
8. `/settings/admin/users` — accounts, admin role, deals subs.
9. `/settings/admin/system` — install-wide toggles.
10. `/settings/admin/audit-log` — every mutation/login/crash.
11. `/settings/admin/api-access` — keys for ingestion sources.

Open observations from the user (verbatim, 2026-06-19):

- "User preferences and system setup have been mixed — stock locations,
  stock groups, etc should be in their own area/section. Not sure what to
  call it, and **stores** should be moved to this area too."
- "Several types have been grouped onto the same page and if there's a
  lot you have to scroll a long way. Feels like they should be split out
  into their own areas (everything under **recipe tags and categories**)."
- "There's just a lot that feels wrong, and an in-depth rebuild is needed
  for this area. Examples: **opens onto 'Account'** and Account is not
  first in the list. Some settings look like they should be under Account
  like username/password (the section header literally says 'Account')."

Observations from the design-critique pass (codified from the screenshots):

- Active states use **saturated brand-primary green** everywhere
  (`q-btn-toggle toggle-color="primary"`); three loud green blocks on the
  Appearance section compete with each other AND with the side-nav active
  state.
- Every section wraps in `<q-card flat bordered>` → uniform but boxy;
  every settings page reads as a "wall of cards".
- Side-nav items carry a 2-line caption each → ~22 lines of nav chrome
  for 11 destinations.
- No page-level "Settings" title; the orphaned `"Manage your account and,
  if you're an admin, the install itself."` line does double duty.
- The Recipe vocab page stacks Cuisines + Categories + Dietary tags on
  one scroll; long lists in any of the three force scrolling past the
  others.
- The Preferences page stacks ~7 cards (Appearance, Weekly deals,
  Alerts, Push, Money, Grocery budget, Nutrition); the cards are
  chrome-identical so nothing has rank.

---

## 2. Target end-state

### 2.1 Information architecture (the rebuild that has to happen first)

Three top-level groups in the side nav, in this order:

```
ACCOUNT (was: "Your settings")
  Account            (← landing page; identity + password + profile picture)
  Preferences        (Appearance ONLY — theme/mode/font/size)
  Notifications      (weekly deals + alerts digest + push — NEW page)
  Money              (money features toggle + grocery budget — NEW page)
  Voice              (mic input + speech output toggles — NEW page)
  Nutrition          (off / simple / complex mode — NEW page)
  About              (version + project info + restart onboarding)

LIBRARY (NEW group — user-curated reference data)
  Stock locations
  Stock groups
  Stores                (moved from Admin)
  Recipe cuisines       (split out of Recipe vocab)
  Recipe categories     (split out of Recipe vocab)
  Recipe tools          (split out of Recipe vocab)
  Recipe meal slots     (split out of Recipe vocab)
  Recipe dietary tags   (split out of Recipe vocab — bespoke editor)

ADMIN · GLOBAL (Stores out, System split 1→4)
  Users
  System: Timezone        (split out of System)
  System: Alert thresholds(split out of System)
  System: AI assistant    (split out of System)
  System: Feature flags   (split out of System; Product search URL folded in)
  Audit log
  API access
```

The four System children render under a single "System" parent in the
nav with a visual sub-indent (see §6.5 for the nav-pattern decision).
The routes are flat (`/settings/admin/system/timezone`,
`/settings/admin/system/alerts`, etc.) so deep links don't go through a
landing page.

**Naming carve-out:** the "Library" name is provisional. The user said
"not sure what to call it". Acceptable alternatives: **Library**,
**Catalogue**, **Data**, **References**. Recommend **Library** — it's
neutral and reads naturally for both stock taxonomy (locations / groups)
and recipe taxonomy (cuisines / categories / tags). Add a 1-line
description under the group header so the abstraction reads cleanly.

**Why this carve-out is the right shape:**
- "Your settings" was overloaded — it mixed *preferences about how the
  app behaves* (appearance, notifications) with *reference data the user
  curates* (locations, groups, recipe tags). These are different mental
  models.
- "Stores" was in Admin because it was originally a back-office concept
  (FU-189 / Phase E). After the round-19 rename it's the *user's* list of
  retail stores — closer to "Stock groups" than to "Users". It belongs
  with the rest of the user-curated taxonomy.

### 2.2 Routing changes

Migration map (old route → new route):

| Old | New | Notes |
|---|---|---|
| `/settings` | `/settings/account` | Landing on Account, not Preferences |
| `/settings/preferences` | `/settings/preferences` | Appearance only after the splits below |
| `/settings/account` | `/settings/account` | Picks up edit forms + profile pic |
| `/settings/about` | `/settings/about` | Picks up Restart onboarding |
| `/settings/stock-locations` | `/settings/library/stock-locations` | moved |
| `/settings/stock-groups` | `/settings/library/stock-groups` | moved |
| `/settings/admin/stores` | `/settings/library/stores` | moved out of Admin |
| `/settings/recipe-vocab` | (deleted) | split into 5 routes below |
| (new) | `/settings/library/recipe-cuisines` | extracted from recipe-vocab |
| (new) | `/settings/library/recipe-categories` | extracted from recipe-vocab |
| (new) | `/settings/library/recipe-tools` | extracted from recipe-vocab |
| (new) | `/settings/library/recipe-meal-slots` | extracted from recipe-vocab |
| (new) | `/settings/library/recipe-dietary-tags` | extracted from recipe-vocab |
| (new) | `/settings/notifications` | extracted from preferences |
| (new) | `/settings/money` | extracted from preferences (money toggle + grocery budget) |
| (new) | `/settings/voice` | extracted from preferences |
| (new) | `/settings/nutrition` | extracted from preferences |
| `/settings/admin/system` | (becomes redirect → `/settings/admin/system/timezone`) | split into 4 routes below |
| (new) | `/settings/admin/system/timezone` | extracted from system |
| (new) | `/settings/admin/system/alerts` | extracted from system (alert thresholds) |
| (new) | `/settings/admin/system/assistant` | extracted from system (AI assistant) |
| (new) | `/settings/admin/system/features` | extracted from system (feature flags + product search URL) |

**Backwards compatibility:** every old route gets a redirect to its new
location. Bookmarks, deep links from emails, and Dora's own help-page
links (`HelpPage.vue`) all keep working. Implement via Vue Router's
`redirect:` on the old route definitions.

### 2.3 Landing route

`/settings` → redirect to `/settings/account`. The user explicitly noted
"opens onto Account and Account is not first in the list" — currently
the shell lands on Preferences (the first entry). After the rebuild,
Account IS first AND IS the landing.

### 2.4 Per-page splits

**Preferences page** loses six concerns. It's currently 1168 lines
covering Appearance + Weekly deals + Alerts digest + Push + Money
toggle + Grocery budget + Nutrition + Voice + an "Account" card with
username/email/password edit forms. After the split, Preferences keeps
**Appearance only** (theme/mode/font/size). Everything else moves:

| Was on Preferences | Now lives on |
|---|---|
| Appearance (theme/mode/font/size) | Preferences (the only thing left) |
| Weekly deals email | Notifications |
| Alerts email digest | Notifications |
| Push notifications | Notifications |
| Money features toggle | Money |
| Grocery budget | Money |
| Nutrition mode | Nutrition |
| Voice (mic + speech output) | Voice |
| Username / email / password edit | **Account** (where they should already be) |

This is the biggest finding from the deeper read: the **`<q-card>` with
`text-h6 "Account"` on Preferences** (PreferencesSettings.vue
lines 492–604) carries the username/email/password edit forms. The
*page* called Account is read-only. User feedback: "literally says
account on the section header" — exactly correct.

**Account page** GAINS:
- Username, password change, email change — moved out of the misplaced
  "Account" card on Preferences. Lifted as-is (form, validation,
  error-handling, all of it).
- **Profile picture upload** (§2.9). Backend + SPA work, in-scope for
  this brief. Closes the open feedback bullet from 2026-06-06 + the
  original spec.
- Avatar at the top of the page adopts the new `<UserAvatar>` component
  (Phase 4) so it renders the uploaded picture instead of the current
  hard-coded initials.

**Account page** LOSES:
- **Restart onboarding** moves to the **About** page. It's a help /
  re-tour action, not identity management.
- **"Danger zone"** heading on sign-out is theatre — sign-out is benign,
  not destructive. Drop the heading entirely; the sign-out button just
  sits in the page's last section. (If a delete-account flow ever
  lands, *that* would deserve the label.)

**About page** GAINS:
- Restart onboarding (moved from Account).
- (No other changes — version / endpoint / PWA install / mascot stay.)

**System** splits 1 → 4 (admin pages, same logic as Preferences):

| Was on System | Now lives on |
|---|---|
| Timezone | System → Timezone |
| Alert thresholds | System → Alert thresholds |
| AI assistant | System → AI assistant |
| Install-wide feature flags | System → Feature flags |
| Product search URL (Phase D / FU-186) | System → Feature flags |

The Product search URL is a single input controlling a single
behaviour; it folds cleanly into Feature flags rather than getting its
own page.

**Recipe vocab page** splits 1 → 5: Cuisines / Categories / Tools /
Meal slots / Dietary tags become their own routes under `Library`.

The first four (Cuisines / Categories / Tools / Meal slots) all use
the existing `VocabSectionEditor` pattern (simple `name`-only CRUD,
with Meal slots adding reorder). Each new page is a thin wrapper that
mounts `<TaxonomyManagerPage>` (R-001 extraction) parameterised by:
- title + description
- API service (each type already has its own CRUD endpoints — verify
  in `dora_api/features/`)
- icon
- empty-state copy
- whether reorder is enabled (Meal slots = yes; the other three = no)

**Dietary tags** is the carve-out: tags carry a grouping label so the
existing page uses a bespoke editor (`text-h6 "Dietary tags"` block,
add/edit/delete with a grouping field on each tag). Lift that bespoke
editor into its own page component (`RecipeDietaryTagsSettings.vue`)
as-is; don't try to shoehorn it into `TaxonomyManagerPage`. The shared
component covers four of the five; the fifth keeps its own shape and
just gets the new `SettingsSection` chrome around it in Phase 3.

If any taxonomy is missing a CRUD endpoint, ship the corresponding
Library page read-only and log a backend follow-up (see §5).

---

### 2.5 Visual rebuild — per-page

Adopt a **left-info / right-control** layout for every settings page,
modelled on Stripe / Linear / GitHub. Extracted shared component:

```
SettingsSection.vue
  ┌────────────────────────────────────────────────────────────┐
  │  <Title (15-16px / weight 700 / -0.01em)>                  │
  │  <One-line description, max 60ch, muted>                   │
  │                                                            │
  │  <Row>  <Label + optional 1-line help>   <Control>         │
  │  <Row>  <Label>                          <Control>         │
  │  ...                                                       │
  └────────────────────────────────────────────────────────────┘
  ─── 1px divider in `color-mix(text-primary 8%, transparent)` ─
  <next section>
```

No per-section card border. The dividers between sections carry the
visual rhythm. Pages get **24-28px outer padding** (was: 16px) so they
breathe.

Page title pattern: every settings page begins with a real `<h1>`-style
title (~24px / weight 700). The page itself anchors the eye; the side
nav is supporting chrome.

### 2.6 Visual rebuild — controls

**Extract `DoraSegmented`** to replace `q-btn-toggle` everywhere it
appears in Settings (Mode, Font family, Text size, Cadence, Budget
period). Spec:

- Flat row of `<button>` elements, no per-button background fill.
- Inactive: neutral text colour (`var(--text-secondary)`), no border.
- Active: bold text + 2px accent underline (or `dora-bg-sunken` + bold
  text — see open decision §6.1).
- Hover on inactive: text → accent, no fill.
- Same rhythm as `DoraTabs` so the two read as a family.

Result: the page loses 5–8 saturated-green blocks. Active state still
reads cleanly without screaming.

**Theme cards:** swatch + family name only by default; the multi-line
"Fresh garden green + teal with a golden accent. Dora's default." blurb
moves to a `<q-tooltip>` on hover. Active state = thin 2px accent border
+ small `check_circle` badge in the top-right corner. Cards shrink to
~70% of their current vertical size.

**Mode** above Theme stays a segmented control (3-up: System / Light /
Dark) but uses the new `DoraSegmented` style, not the loud
`q-btn-toggle`.

### 2.7 Side nav rebuild

- Drop the `<q-card flat bordered>` wrapper. The nav sits directly on
  the page surface.
- Drop the 2-line caption per item. Label + icon only. (~50% height
  reduction.)
- Eyebrow group headers (`"YOUR SETTINGS"` → **`ACCOUNT`**;
  `"ADMIN · GLOBAL"` → unchanged; add new `LIBRARY` eyebrow): 11px /
  uppercase / weight 600 / muted.
- Active state: keep the soft brand-primary tint (it works); add a 3px
  accent-coloured left edge bar for stronger ranging.
- **Sticky** position so it travels with the user when the main pane
  scrolls long forms. On mobile (`<md`), collapse the nav to a top
  tab strip or a left drawer (TBD — see open decisions §6.3).
- Drop the "Admin (global) settings are only visible to admin accounts"
  banner; non-admins don't need to know the group exists.

### 2.8 Settings shell rebuild

`SettingsShell.vue` template, after rebuild:

```vue
<template>
    <div class="settings-shell">
        <header class="settings-shell__header">
            <h1>Settings</h1>
        </header>

        <div class="settings-shell__body">
            <aside class="settings-shell__nav">
                <SettingsNavGroup label="Account" :items="accountSections" />
                <SettingsNavGroup label="Library" :items="librarySections" />
                <SettingsNavGroup
                    v-if="isAdmin"
                    label="Admin · Global"
                    :items="adminSections"
                />
            </aside>

            <main class="settings-shell__main">
                <router-view />
            </main>
        </div>
    </div>
</template>
```

Extract `SettingsNavGroup.vue` so the eyebrow header + item list is
rendered consistently. Item type: `{ path, label, icon }` — no caption.

### 2.9 Profile picture

Closes the open feedback bullet ("No way to set/update a profile
picture. Should also display this on the menu bar for the user profile
button. Keep displaying the current icon if no profile picture set." —
`docs/02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md` L434) and
the original-spec bullet ("I can set my profile picture via my user
preferences" — `docs/00_original_spec/Feature Boards/User & Global
Options.md` L24). Also flips `COVERAGE_GAPS.md` bucket A-5's second
bullet from open → addressed.

**Backend (`dora_api`):**

- **Migration:** add `image` `LargeBinary` (nullable) column on the
  `User` table. Single Alembic head, batch-mode, deterministic
  constraint names (R-015). Postgres-portable (R-005).
- **Entity:** `User.image: bytes | None`.
- **Table mapping:** add the column to `user_table` in
  `dora_api/persistence/table_mappings.py`. Mirror the deferred-load
  pattern used by `Store.image` so listing users doesn't pull the
  bytes back over the wire on every fetch.
- **GET bytes endpoint:** `GET /api/users/<user_id>/image` returning
  the raw bytes with appropriate `Content-Type` (data-URL on write
  → infer MIME, persist as bytes). Mirror
  `dora_api/features/users/get_user_image.py` if it exists, or copy
  the shape from `dora_api/features/stock_items/get_stock_item_image.py`
  / `dora_api/features/stores/...`. Auth: any authenticated user can
  fetch any user's image (used by `@mention` UI etc.) — the existing
  StockItem image endpoint sets the precedent.
- **PATCH update path:** extend the existing `UpdateMeRequest` /
  admin `UpdateUserRequest` to accept an `image` field (data-URL
  string to set, null to clear, omit to leave alone — mirror the
  `image` contract on `update_stock_item.py`). Admin update path
  intentionally also accepts this (admins can clear a problematic
  user's picture).
- **DTO:** `has_image: bool` on every `User` DTO that's already public
  (current-user, user list). Don't ship the bytes inline.

**SPA — Account settings page:**

- Use the existing `ImageUploadField` component
  (`web_app/src/components/ImageUploadField.vue`) — same one
  StockItemDetail and StoresSettings already use. Wires
  `previewUrl` / `name` / `alt` / `canClear` props, `@pick` + `@clear`
  events. R-001 — no new upload component, just consume the shared
  one.
- Picker lives in a new `SettingsSection` on AccountSettings titled
  "Profile picture". Description: "Shown in the menu bar and anywhere
  Dora needs to identify you."
- On `@pick`: PATCH `/api/users/me` with `image` set to the data-URL
  string. On `@clear`: PATCH with `image: null`. Use the same
  optimistic-then-confirm pattern StockItemDetail uses today (rollback
  if the server rejects).
- Cache-bust on save: the existing `imageVersionOf` pattern from
  `stockItemStore` is the precedent — add the same to `authStore`
  (a `Record<string, number>` keyed by user_id, bumped on a successful
  image PATCH) so every consumer that paints `?v=<n>` reactively
  refreshes after upload / clear.

**SPA — menu-bar avatar:**

- Locate the existing user-profile button in `MainLayout.vue` (or
  whichever component owns the top-bar). Probably a `q-btn` with a
  default `person` icon today.
- Replace with `<UserAvatar :user-id="..." :has-image="..."
  size="32px" fallback-icon="person" />`. Component contract:
  - When `hasImage === true` AND no fetch-error has latched: render
    `<img>` against `/api/users/<id>/image?v=<imageVersionOf(id)>`.
  - Otherwise: render the fallback icon at the requested size. **Do
    not** invent a deterministic-hash-swatch placeholder for users —
    the current icon is what the feedback explicitly preserves.
- Defensive fallback latch identical to `StockItemRow`'s `imgFailed`
  pattern: if the `<img>` 404s mid-render, drop to the fallback icon
  rather than show a broken-image glyph. Reset the latch when
  `imageVersionOf(id)` bumps.
- The component is reusable — drop it anywhere the SPA renders "the
  user" (assistant UI, audit log avatars, admin user list rows etc.).

**Constraints + carve-outs:**

- **Image size cap:** mirror the StockItem ceiling
  (`max_length=6_000_000` on the Pydantic field — ~4.5 MB of base64
  data-URL). The user shouldn't be able to PATCH a 50 MB selfie.
- **Format:** accept anything `ImageUploadField` accepts (it does
  client-side resize/crop today — verify the implementation honours
  the cap before send).
- **Theme tokens (R-002):** the fallback icon path uses
  `var(--text-secondary)` or whichever token the current
  profile-button icon uses. No hex.
- **State ownership (R-003):** `has_image` is server-derived
  (`bool(User.image)`); the SPA never tries to keep its own truth
  about whether a user has a picture. Cache-bust counter is SPA-local
  view state, not domain state.

**Out of scope here (separate follow-ups if surfaced):**

- Cropper UI (use whatever `ImageUploadField` already provides).
- Per-image moderation / virus scanning.
- Backwards-compat for OAuth/Gravatar import — out of scope; the
  feedback bullet only asks for upload + display.

### 2.10 Additional findings from the deeper analysis

These bullets surfaced from reading every settings page top-to-bottom
on 2026-06-21. Each maps to a concrete fix in the relevant phase.

**Inconsistent page-header chrome (across all pages):**
- `AccountSettings` — h6 + caption + avatar block, no header icon.
- `StoresSettings` / `SystemSettings` / `UsersAdminSettings` /
  `ApiAccessSettings` — h6 with an inline 20px icon.
- `AuditLogSettings` — 32px primary-coloured icon in a side avatar,
  h6 + caption, Export CSV inline.
- `StockGroupsSettings` / `StockLocationsSettings` — h6 + caption, no
  header icon.
- Refresh button: present (icon-only flat round) on `StoresSettings`,
  `UsersAdminSettings`, `ApiAccessSettings`. Absent everywhere else.
- Fix: `SettingsSection` (§2.5) standardises page-header chrome —
  title + description + optional eyebrow icon + optional right-aligned
  primary action slot. Refresh becomes a consistent ghost icon button
  in that slot for any page that fetches a server collection.

**`AboutSettings` hardcodes the brand font:**
- `<div class="text-h6" style="font-family: 'Cute Dino'">Dashy Dora</div>`
  inline style. The same brand-mark exists in `ApplicationLogo.vue`.
- Fix: extract `<DoraBrand>` shared component (R-001 mini-extract) and
  reuse on About. Not critical; can fold into Phase 3 if cheap, log
  as follow-up if not.

**`ApiAccessSettings` uses `q-expansion-item` per source:**
- Unique list pattern in the settings area. Visually divergent.
- Fix: leave the expansion shape (it's the right UX for revealing
  per-source mapping detail), but make sure the new `SettingsSection`
  page header sits cleanly above it and the expansion items use the
  shared `var(--text-primary)` / `var(--surface-elevated)` tokens
  rather than Quasar defaults. No structural change, just chrome
  alignment.

**`AuditLogSettings` header diverges:**
- 32px primary-coloured icon + h6 + caption + inline Export CSV button.
- Fix: standardise to `SettingsSection` page-header. The Export CSV
  moves into the page header's right-action slot.

**Voice page might have nothing if browser doesn't support it:**
- `voiceInputAvailable` / `voiceOutputAvailable` both can be false on
  unsupported browsers. The current page already shows muted caption
  "Your browser doesn't expose…" — that's correct. Confirm the new
  standalone Voice page renders gracefully (both toggles disabled,
  explanatory captions visible) in that state.

**Money/Grocery budget combined into one page:**
- Currently two separate cards on Preferences (Money & budgets toggle
  + Grocery budget). They're tightly related — combining onto one
  Money page reads more naturally.
- The new Money page hosts: "Show money features" toggle (per-user
  gate, layered with admin install-flag) → if enabled, "Track a
  grocery budget" toggle → if enabled, amount + period picker. Cleaner
  conditional flow than the current two-cards split.

**Dietary-tags create/rename uses two sequential prompts:**
- `RecipeVocabSettings::onCreateDietaryTag` calls `$q.dialog({prompt:…})`
  for the name, awaits, then calls again for the category. Two
  consecutive modal dialogs to enter two fields = jarring.
- Fix: §2.11 below.

**Initials avatars across the app:**
- `AccountSettings` header → `<q-avatar color="accent" text-color="dark">{{ initials }}</q-avatar>` (60px).
- `UsersAdminSettings` rows → `<q-avatar>` with admin/non-admin colour + initials (42px).
- The menu-bar profile button (`MainLayout.vue`) → person icon.
- Fix: Phase 4's `UserAvatar` component replaces ALL THREE sites, not
  just the menu bar. The component takes a `size` prop (32px/42px/60px
  per consumer) and shows the uploaded picture when present, the
  current initials/icon fallback when not.

### 2.11 Dietary-tags single-dialog refactor

Replace `RecipeVocabSettings::onCreateDietaryTag` /
`onRenameDietaryTag` (two sequential `$q.dialog.prompt`s) with a
single `BaseDialog` containing **name** + **category** inputs in one
form. Submit hits the create or update endpoint once.

Component-wise: build `DietaryTagFormDialog.vue` (small focused
dialog, not a new abstraction layer). Takes `modelValue` (open),
`tag: DietaryTag | null` (null for create, populated for rename),
`busy`. Emits `update:modelValue` + `confirm` with `{ name, category }`.

Lives on the new `RecipeDietaryTagsSettings.vue` page (Phase 2 split).

---

## 3. Phased execution

### Phase 1 — IA + routing (foundation)

**Scope:** route definitions + redirects + side-nav structure ONLY.
Visual look stays exactly as it is today. Pages get moved under their
new URLs; deleted routes get redirects.

**Tasks:**
1. Update `web_app/src/router/routes.ts` (or wherever settings routes
   live — verify path):
   - Add `/settings` → `/settings/account` redirect.
   - Move stock-locations / stock-groups under `/settings/library/`.
   - Move admin/stores under `/settings/library/stores`.
   - Add the three new recipe-vocab routes (point at the existing page
     temporarily — Phase 2 will split it).
   - Redirect every old route to its new home.
2. Update `SettingsShell.vue` `personalSections` / `adminSections` →
   `accountSections` / `librarySections` / `adminSections`. Drop
   captions. Keep current card chrome (visual rebuild is Phase 3).
3. Update `HelpPage.vue` guide entries that link into settings
   (`/settings/admin/stores`, etc.) → new URLs.
4. Update assistant tool descriptions in `doraIntents.ts` if any
   reference settings URLs.
5. End-of-phase: every existing settings URL still works (via
   redirect); the nav reflects the new IA; everything looks the same
   pixel-wise.

**Verification:**
- `vue-tsc -p tsconfig.json --noEmit` — clean.
- `npm run lint` — clean.
- Walk every settings page in the running app; confirm:
  - `/settings` lands on Account.
  - Old URLs redirect to new ones.
  - Nav groups read Account → Library → Admin.
  - Account is first in Account group.

**Worklog entry:** "Settings Phase 1 — IA + routing".

### Phase 2 — page-level splits

**Scope:** new pages + page content moves. No visual rebuild yet.
Lots of moves; the close-gate is "every old surface still works under
its new URL" rather than "everything is now pretty".

**Tasks — splitting Preferences (1168 → many):**
1. Create `NotificationsSettings.vue` (`/settings/notifications`).
   Move from `PreferencesSettings.vue`: Weekly deals email card +
   Alerts email digest card + Push notifications card. Lift drafts +
   handlers + composables (`usePushSubscription`,
   `useFeatureFlags.emailSmtpConfigured`, etc.) wholesale.
2. Create `MoneySettings.vue` (`/settings/money`). Move Money &
   budgets card + Grocery budget card. Combine into a single
   conditional flow: "Show money features" toggle → if on, "Track a
   grocery budget" toggle → if on, amount + period.
3. Create `VoiceSettings.vue` (`/settings/voice`). Move both Voice
   toggles + their composables (`useVoiceInput`, `useSpeechOutput`).
4. Create `NutritionSettings.vue` (`/settings/nutrition`). Move
   Nutrition mode toggle + the `useNutritionMode` composable usage.
5. **The "Account" card on Preferences — username / email / password
   edit forms (lines 492–604).** Lift wholesale to
   `AccountSettings.vue`. Forms + drafts + handlers (`onSaveUsername`,
   `onSaveEmail`, `onChangePassword`) + validation. The misplaced
   "Account" `text-h6` heading goes away; on AccountSettings the
   page-title already says Account.

**Tasks — fixing Account / About:**
6. AccountSettings: move the "First-run wizard" / "Restart onboarding"
   section to AboutSettings (it's a help action, not identity). Take
   the handler + dialog + state with it.
7. AccountSettings: drop the "Danger zone" heading. The sign-out
   button stands alone in the last section. Keep the negative-coloured
   styling on the button (the action's destructiveness is signalled
   there, not in a section label).

**Tasks — splitting Recipe vocab (1 → 5):**
8. Create `<TaxonomyManagerPage>` component (R-001 extraction) —
   parameterised wrapper that renders a list + add/edit/delete +
   optional reorder. Use the existing `VocabListEditor` component
   (already shared) as the inner renderer; this new page-level
   wrapper handles the API service + busy / loading state + the
   `SettingsSection` page header.
9. Create FIVE page components under `web_app/src/pages/settings/`:
   - `RecipeCuisinesSettings.vue` → `<TaxonomyManagerPage type="cuisines" />`
   - `RecipeCategoriesSettings.vue` → `<TaxonomyManagerPage type="categories" />`
   - `RecipeToolsSettings.vue` → `<TaxonomyManagerPage type="tools" />`
   - `RecipeMealSlotsSettings.vue` → `<TaxonomyManagerPage type="meal-slots" :reorderable="true" />`
   - `RecipeDietaryTagsSettings.vue` → bespoke; uses the new
     `DietaryTagFormDialog` (§2.11) for create + rename.
10. Build `DietaryTagFormDialog.vue` (§2.11) — single BaseDialog with
    name + category inputs, replacing the two sequential prompts.
11. Delete `RecipeVocabSettings.vue`. Old route redirects to
    `/settings/library/recipe-cuisines`.
12. If any taxonomy lacks its own CRUD endpoint, ship that page
    read-only and log a backend follow-up (see §5).

**Tasks — splitting System (admin, 763 → 4):**
13. Create `AdminSystemTimezoneSettings.vue`
    (`/settings/admin/system/timezone`). Move the Timezone section's
    template + handlers (`onSaveTimezone`, `onDetectTimezone`,
    `onTimezoneFilter`).
14. Create `AdminSystemAlertsSettings.vue`
    (`/settings/admin/system/alerts`). Move the Alert thresholds
    section + its drafts.
15. Create `AdminSystemAssistantSettings.vue`
    (`/settings/admin/system/assistant`). Move the AI assistant
    section + `enabledDraft` / `baseUrlDraft` / `modelDraft` /
    `probeResult` / `onTest` / `onBaseUrlBlur`.
16. Create `AdminSystemFeaturesSettings.vue`
    (`/settings/admin/system/features`). Move both Feature flags AND
    Product search URL (one consolidated page — Product search URL
    is a single input setting).
17. Delete `SystemSettings.vue`. Old route
    (`/settings/admin/system`) redirects to
    `/settings/admin/system/timezone`.

**End-of-phase verification:**
- `vue-tsc` + lint clean.
- Every page in the new IA renders + all CRUD / save flows work.
- The old monolithic Preferences page now reads as "just Appearance".
- The old monolithic System page is gone; four focused pages exist.
- Recipe vocab is five pages.
- Account has the edit forms; About has the onboarding restart.

**Verification:**
- `vue-tsc` + lint clean.
- All four split pages render their respective data; CRUD works.
- The old monolithic Recipe vocab page is gone.
- Preferences page is shorter; Notifications page exists.

**Worklog entry:** "Settings Phase 2 — page splits".

### Phase 3 — visual rebuild

**Scope:** the look-and-feel pass. Now that IA is clean, paint.

**Tasks:**
1. Extract `SettingsSection.vue` — left-info / right-control layout
   per §2.5. Slots: `#title`, `#description`, default = controls. The
   between-section divider is rendered by the parent page (consistent
   spacing).
2. Extract `DoraSegmented.vue` — replacement for `q-btn-toggle`. Apply
   to:
   - Mode (System / Light / Dark) on Preferences.
   - Font family on Preferences.
   - Text size on Preferences.
   - Budget period (Weekly / Monthly).
   - Alerts cadence (Daily / Weekly).
3. Refactor `PreferencesSettings.vue` to use `SettingsSection`. Drop
   every `<q-card flat bordered>` wrapper.
4. Refactor `NotificationsSettings.vue` to use `SettingsSection`.
   Three rows (Weekly deals / Alerts digest / Push) collapse from
   three cards into a single section with three control rows.
5. Refactor `AccountSettings.vue`, `AboutSettings.vue`, every
   `Library/*Settings.vue`, every `admin/*Settings.vue` (including
   the four new `AdminSystem*Settings.vue` pages and the five new
   `Recipe*Settings.vue` pages) to use `SettingsSection`.
   - Standardise the page-header chrome across all pages: title +
     description + optional eyebrow icon (left of title) + optional
     right-aligned primary action slot.
   - Refresh button: any page that fetches a server collection
     (Stores, Users, API access, Audit log) gets a ghost icon-only
     refresh in the page-header's right-action slot. Same shape
     everywhere.
   - `AuditLogSettings`: its 32px primary-coloured side icon comes
     down to the standard eyebrow size; the Export CSV moves into
     the right-action slot.
   - `AboutSettings`: extract `<DoraBrand>` shared component for the
     "Dashy Dora" mark (the existing `font-family: 'Cute Dino'`
     inline style moves into the component). Reuse the mark wherever
     it shows up across the app.
6. Theme cards: compact to swatch + family name; move blurbs to
   tooltip; active state = 2px accent border + `check_circle` badge.
7. Add real page titles to every settings page (h1, 24px / weight 700).
8. Side-nav rebuild per §2.7:
   - Drop the card wrapper.
   - Drop captions.
   - 3px accent left-edge bar on active item.
   - Sticky position.
   - Extract `SettingsNavGroup.vue`.
9. Bump page padding from `q-pa-md` (16px) to ~28px.

**Verification:**
- `vue-tsc` + lint clean.
- Theme switching still works for every theme and mode.
- Every form control still saves on change (no regression on the
  drafted-then-save pattern Preferences uses today).
- Walk every settings page; the loud-green look is gone, page padding
  breathes, dividers separate sections cleanly.
- Cross-theme sanity: Pesto Light + Pesto Dark + Cherry Cola Dark at
  minimum.

**Worklog entry:** "Settings Phase 3 — visual rebuild".

### Phase 4 — profile picture (backend + SPA)

**Scope:** the §2.9 feature. Lives in its own phase because it adds a
DB column + migration + bytes endpoint + a reusable `UserAvatar`
component — none of which want to be tangled with the IA / visual work
of phases 1-3.

**Tasks (backend):**
1. Alembic migration adding `image LargeBinary NULL` on the `User`
   table. Single head, batch mode, deterministic constraint names.
2. `User.image: bytes | None` on the entity.
3. `user_table` mapping update with the deferred-load pattern (mirror
   `Store.image`).
4. `GET /api/users/<user_id>/image` endpoint returning raw bytes
   (mirror StockItem / Store image endpoints).
5. Extend `UpdateMeRequest` to accept `image: str | None` (data-URL
   string to set; null to clear; omit to leave alone). Same on the
   admin `UpdateUserRequest`.
6. Add `has_image: bool` to every User DTO surface that's already
   public.

**Tasks (SPA):**
7. Add `image: string | null` to the SPA's update-me / update-user
   commands (parallel to the backend).
8. Add `imageVersionOf(userId)` + `bumpImageVersion(userId)` to
   `authStore` (or wherever the canonical "users" map lives — verify).
   Bump on a successful image PATCH.
9. Mount `ImageUploadField` in a new `SettingsSection` on
   `AccountSettings.vue` titled "Profile picture". Wire `@pick` /
   `@clear` to the PATCH path; show busy/error via the existing
   account-page error pattern.
10. Extract `UserAvatar.vue` (R-001) — `<img>` against
    `/api/users/<id>/image?v=<imageVersionOf(id)>` when `hasImage`,
    fallback to the configured fallback (icon OR initials, see below)
    otherwise, with the `imgFailed` latch from `StockItemRow`
    defensive-fallback pattern.
    - Props: `userId`, `hasImage`, `size` (32 / 42 / 60 / arbitrary px),
      `fallback` (`'icon' | 'initials'`, default `'icon'`),
      `username` (only consumed when `fallback === 'initials'` to
      compute the first-letter).
    - The fallback choice is per-consumer:
      - **Menu-bar button** → `fallback="icon"` (preserves the current
        `person` icon — matches the feedback's explicit "keep
        displaying the current icon if no profile picture set").
      - **AccountSettings header avatar (60px)** → `fallback="initials"`
        (matches what's there today; visually richer than an icon at
        large size).
      - **UsersAdminSettings row avatar (42px)** → `fallback="initials"`
        (matches what's there today; differentiates users at a glance
        in the list).
11. Adopt `UserAvatar` at every existing avatar site:
    - **Menu-bar profile button** (`MainLayout.vue` — verify exact
      location). Identical hit area + click handler; only the visual
      changes. `fallback="icon"`.
    - **AccountSettings page header** — replace
      `<q-avatar size="60px" color="accent" text-color="dark">{{ initials }}</q-avatar>`
      with `<UserAvatar :user-id="currentUser.user_id"
      :has-image="currentUser.has_image" size="60px"
      fallback="initials" :username="currentUser.username" />`.
    - **UsersAdminSettings rows** — replace the per-row `q-avatar`
      (admin-vs-non-admin coloured initials) with `UserAvatar`. The
      admin/non-admin visual differentiation moves to the existing
      "admin" badge next to the username — it's already there, so
      the avatar can simplify.

**Verification:**
- `vue-tsc` + lint clean.
- Backend: pytest run (or pytest follow-up logged if no Python on the
  dev box, mirroring FU-189c / FU-223 handling).
- Browser: upload a picture in Account; it appears immediately on the
  menu bar (cache-bust working). Clear; menu bar reverts to the
  fallback icon. Hard-refresh; both states survive. Try a 50MB image
  — rejected at the cap with a usable error message.
- Cross-theme sanity for the avatar fallback icon.

**Worklog entry:** "Settings Phase 4 — profile picture".

**Coverage update:** flip `COVERAGE_GAPS.md` A-5 second bullet from
`[OPEN]` to addressed; cite this brief.

### Phase 5 — mobile pass

**Scope:** verify and adjust for narrow viewports. The split layout
should already collapse cleanly thanks to Quasar's responsive grid; this
phase confirms and adjusts edge cases.

**Tasks:**
1. Decide nav-on-mobile pattern (open decision §6.3): top tab strip OR
   left drawer. Implement.
2. Verify every `SettingsSection` row collapses to label-above-control
   on `<sm`.
3. Verify theme card grid wraps to 2-up or 1-up on narrow.
4. Verify `DoraSegmented` segments wrap or scroll on narrow (mirror
   the DoraTabs treatment).

**Verification:** walk every settings page at 360px / 768px / 1280px.

**Worklog entry:** "Settings Phase 4 — mobile pass".

---

## 4. Engineering standards close-gate per phase

Every phase ends with the standard close-gate:

- **R-001 (componentisation):** new shared components are extracted
  rather than copy-pasted. Phase 2 produces `TaxonomyManagerPage`;
  Phase 3 produces `SettingsSection`, `DoraSegmented`,
  `SettingsNavGroup`.
- **R-002 (theme tokens only):** zero hex / rgb / numbered Quasar
  palette classes in new code. Active states route through `var(--q-
  accent)` / `var(--brand-primary-soft)` / `dora-bg-sunken` /
  `dora-text-secondary`. The 3px accent left bar uses `var(--q-accent)`.
- **R-003 (single source of truth):** the side-nav `Section` list is
  defined ONCE in `SettingsShell.vue` (or a dedicated `settingsNav.ts`
  config). Don't duplicate the route list in router + shell + breadcrumb.
- **R-007 (scope discipline):** don't redesign unrelated surfaces
  encountered during the rebuild. Log finds as `DORA_FOLLOWUPS.md`
  items.
- **R-011 (framework-idiomatic):** use Vue 3.4 `defineModel`,
  composition API, `<script setup>`. No reaching for unfamiliar libs.
- **R-016 (lazy hydration):** taxonomy pages call
  `store.ensureLoadedAsync()` (if available on the type's store) on
  mount, not `getAllAsync()`.
- **R-005 (portable data access) + R-006 (clean migrations) + R-015
  (deterministic constraint names):** applies to Phase 4 only — the
  new `User.image` column ships a single-head Alembic migration with
  batch-mode operations and named constraints so it deploys cleanly
  to both SQLite (dev) and Postgres (production target).

---

## 5. Backend follow-ups likely surfaced

These are NOT in scope for this brief but the user / next agent should
know:

- **Per-taxonomy CRUD endpoints.** Verify each recipe vocab type
  (cuisines / categories / tools / meal slots / dietary tags) has its
  own list / create / update / delete endpoints in
  `dora_api/features/`. If any is missing, ship the corresponding
  Library page read-only and log a backend follow-up.

**Backend that IS in scope this round (Phase 4):**

- The `User.image` column + migration + GET bytes endpoint + PATCH
  update path. Profile picture is folded in here rather than deferred
  again because the brief already touches Account; doing it now means
  not re-mobilising the surface later for a single bullet.

---

## 6. Open decisions for the user

These are pending the user's verdict. Don't guess; surface them and
wait.

### 6.1 `DoraSegmented` active-state treatment

Two viable looks; pick one and apply consistently:

(a) **Underline accent** — active button is bold text + 2px accent
underline; no fill. Cleanest, most editorial. Closest to a modern
Stripe / Linear feel.

(b) **Soft sunken fill** — active button uses `dora-bg-sunken` + bold
text. Slightly more "control-y"; reads as a pressed state.

Recommend (a). Either is a strict upgrade over the current saturated
fill.

### 6.2 Naming for the new "Library" group

Pick one:
- Library *(recommended — neutral, reads naturally for both stock and
  recipe taxonomies)*
- Catalogue
- Data
- References

### 6.3 Nav on mobile

Two viable patterns:

(a) **Top tab strip** — the three groups (Account / Library / Admin)
become tabs along the top; selected tab reveals its sub-items as a
horizontally-scrolling chip strip below. Compact.

(b) **Left drawer** — desktop nav becomes a left-slide-in drawer
triggered from a settings cog in the page header. More common in
admin UIs.

Recommend (a) — the drawer pattern often gets in the way when the user
is navigating quickly between settings pages.

### 6.4 Theme card blurbs — keep or kill?

The blurbs ("Fresh garden green + teal with a golden accent. Dora's
default.") were design flavour. After moving to tooltip:

(a) Keep in tooltip. User learns the family identity once; afterwards
the swatch is enough.

(b) Drop entirely. The swatch + name carries everything the user needs
to make a choice.

Recommend (a) for first-time discovery; (b) is a safe alternate.

### 6.5 Sub-nav under Admin → System

With the System page split into four routes, the Admin group has 7
total entries (Users, 4× System children, Audit log, API access).
Pick one rendering pattern:

(a) **Indented sub-list under a "System" parent** — `SettingsNavGroup`
gains an optional second level. The 4 System children render
indented under a non-clickable "System" header. Most visually
organised; adds a nav-component feature.

(b) **Flat list with "System:" prefix** — every System child shows as
`System: Timezone`, `System: Alert thresholds`, etc. No nav-component
changes. Ugly at length.

(c) **System stays one route in the nav, sub-tabs inside the page** —
`/settings/admin/system` lands on a page with internal tabs/sub-nav
selecting Timezone / Alerts / Assistant / Features. URLs are still
split (`/settings/admin/system/timezone` etc.) but the nav stays
compact.

Recommend (a). Same nav-pattern decision applies to **Library** (8
entries: Stock locations, Stock groups, Stores, 5× Recipe children)
— pick once and apply consistently. With (a), Library could also
indent the 5 Recipe children under a "Recipe taxonomies" header.

---

## 7. Feedback coverage table

Per CLAUDE.md's cross-checking rule. The bullets the user raised on
2026-06-19 + the design-critique findings, mapped to where each is
addressed:

| Feedback bullet | Addressed in |
|---|---|
| "User preferences and system setup have been mixed; stock locations / stock groups should be in their own area; stores moved there too" | §2.1 — Library group; §2.2 routing |
| "Recipe tags and categories grouped on same page; should be split (incl. tools and meal slots)" | §2.4 page splits — 1→5 (Cuisines / Categories / Tools / Meal slots / Dietary tags); Phase 2 tasks 3-5 |
| "Opens onto Account but Account isn't first in list" | §2.3 landing route; §2.1 nav order |
| "Username/password feel like they belong under Account (header says Account)" | §2.4 — Account gains identity controls if not already there |
| "In-depth rebuild needed" | The whole brief — phased rebuild |
| Loud bright-green active states everywhere | §2.6 DoraSegmented; §6.1 active-state decision |
| Per-section card chrome reads as a wall | §2.5 SettingsSection — no card per section |
| Side-nav captions add noise | §2.7 — drop captions |
| No page-level "Settings" title | §2.8 shell header `<h1>` |
| Multi-line dynamic helper ("variant your OS is currently set to (dark)") reads as debug message | §2.5 description copy — concise, no dynamic strings unless meaningful |
| Long-form prose spans full-width | §2.5 — descriptions capped at ~60ch |
| Side nav ends mid-page; visual imbalance | §2.7 — sticky nav |
| Toggle features each in their own card (Weekly deals / Alerts / Push) | §2.4 / Phase 2 — collapse into one Notifications section |
| Theme cards too large with multi-line blurbs | §2.6 — compact + tooltip |
| (Older feedback) No way to set/update a profile picture; should also display on the menu-bar profile button; keep current icon if unset (2026-06-06 feedback L434 + original spec User & Global Options L24 + `COVERAGE_GAPS.md` A-5) | §2.9; Phase 4 |
| (Round-2 finding 2026-06-21) Preferences page is 1168 lines covering 9 concerns including a misplaced "Account" card with edit forms | §2.4 — big breakup: Preferences → Appearance only; 4 new pages (Notifications / Money / Voice / Nutrition); Account gains the edit forms |
| (Round-2 finding) SystemSettings is 763 lines covering 5 concerns | §2.4 — System splits 1→4 (Timezone / Alerts / Assistant / Features) |
| (Round-2 finding) AccountSettings has "Restart onboarding" — misplaced | §2.4 — moves to About |
| (Round-2 finding) AccountSettings has "Danger zone" for sign-out — theatrical | §2.4 — drop heading |
| (Round-2 finding) Initials avatars on AccountSettings header + UsersAdminSettings rows + menu-bar icon all diverge | §2.9 + Phase 4 — UserAvatar adopted at all three sites with per-consumer fallback choice |
| (Round-2 finding) Dietary tags create/rename uses two sequential `$q.dialog.prompt`s | §2.11 — single `DietaryTagFormDialog` |
| (Round-2 finding) Page-header chrome inconsistent across pages (icons / refresh / Export buttons drift) | §2.10 — standardised via SettingsSection page-header slot |
| (Round-2 finding) AboutSettings inline-styles the brand font | §2.10 + Phase 3 — `<DoraBrand>` shared extract |
| (Round-2 finding) AuditLogSettings header diverges (32px icon, inline Export) | §2.10 + Phase 3 — standardised |

No bullets out-of-scope.

---

## 8. Pre-flight for the executing agent

Before starting Phase 1, confirm:

1. You've read this brief in full.
2. You've read `CLAUDE.md` (especially the "On session start" section).
3. You've read the relevant standing rules in
   `docs/01_charter/ENGINEERING_STANDARDS.md` (R-001/002/003/007/011/016).
4. You've scanned `DORA_FOLLOWUPS.md` for any settings-area open items
   you might collide with.
5. You've decided how to handle the §6 open decisions — either ask
   the user, or note your default and proceed (recommend ask;
   `AskUserQuestion` exists for exactly this).

Once those are done, start Phase 1. End each phase with the standard
worklog entry + `DORA_FOLLOWUPS.md` updates per CLAUDE.md.

---

## 9. Out of scope

Explicitly NOT part of this brief — log as separate follow-ups if
encountered:

- Settings BACKEND restructure (the per-section save handlers are
  fine; only the SPA's IA and look change).
- Theme-token additions (a new `--settings-divider` token is fine if
  needed, but no broad theming work).
- Renaming / re-organising user-facing settings KEYS (`theme`,
  `font_family`, etc. stay as they are).
- New settings features (e.g. importing/exporting preferences,
  per-device overrides). This brief is purely structural + visual.
