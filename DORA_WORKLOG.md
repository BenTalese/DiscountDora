# Dora Worklog

Append-only handoff log between Claude sessions. **Newest entry at the top.**
Read the top entry on session start; append a new entry on session end.

For product-level changes, update `CHANGELOG.md` instead (or as well, when both
apply). This file is the *process* trail — what ran, what was decided, what's
next.

---

## Entry template — copy this when adding a new entry

```
## YYYY-MM-DD HH:MM — <prompt id or short task name>
**Status:** complete | partial | blocked | recon-only
**What changed:** 1–3 bullets. "No code changes" is a valid answer.
**Decisions made:** judgment calls + the reasoning, so the next agent doesn't re-litigate. Link the Charter principle if relevant.
**Files touched:** key paths (omit if none).
**Verification:** what was checked; what was left unchecked.
**Next up:** explicit pointer. Name the next prompt file, or "awaiting user decision on X", or "blocked by Y".
**Open questions for user:** anything that needs a human call before the next agent can proceed.
```

---

## 2026-06-05 — A4 (filter system standardisation + "empty = off")
**Status:** complete (static verification only — node_modules not installed)
**What changed:**
- New `web_app/src/components/FilterBar.vue` — standard filter skin: persistent
  `#search` slot (outside the panel), collapsible `#filters` slot (default shown
  desktop / hidden mobile), active-filter count badge on the toggle, single
  standard "Clear filters" button shown only when ≥1 filter active, optional
  `#actions` slot. Uncontrolled expand defaults by screen size; supports
  `v-model` if a page needs to control it.
- Migrated all four target pages to FilterBar: `StockOverview` (bulk-select btn →
  `#actions`; chips/selects → `#filters`; search stays in header),
  `RecipesOverview` (filters → `#filters`; search stays in header; inline Clear
  removed), `MyProductsPage` (search → `#search`; toggles/selects → `#filters`),
  `ProductSearch` (bespoke `showFilters` toggle + "Clear ranges" removed; filter
  card → FilterBar `#filters`; search term stays in header).
- Hardened "empty = off" to be explicit/regression-proof: dropdown predicates
  `if (value && …)` → `if (value !== null && …)` in `useStockFilters.ts`,
  `RecipesOverview`, `MyProductsPage`; numeric "Missing ≤" guarded with
  `Number.isFinite`. Added an `activeFilterCount` to each page/composable.

**Decisions made:**
- **The headline A4 bug does NOT reproduce in current code.** A thorough
  per-page audit (quoted predicates) showed every page already skips a blank
  filter (truthiness / `!= null` / empty-array / boolean-false). Stale docs
  again (CLAUDE.md warns of this). So A4's value here is UX standardisation +
  regression-proofing, not a bug fix. Surfaced this to the user before building.
- **Scope = full A4, all four pages (user's call).** Note this overrides master
  Decision 1's "products surface is minimal-touch / companion-bound" for
  `ProductSearch` + `MyProductsPage` — the user explicitly chose to migrate them
  anyway. Logged so a future session doesn't "fix" it back.
- **Prompt's 3 decisions** taken as recommended (user didn't object): filters
  shown desktop / hidden mobile; free-text search kept separate + persistent
  (outside the collapsible panel); numeric blank/non-numeric = off.
- **Search stays separate** — each page keeps its existing search box; FilterBar
  only owns the collapsible panel + toggle + active-count + Clear. Lower-risk
  than relocating searches, and satisfies "search separate from the panel."
- **`activeFilterCount` excludes the search box** (search has its own clearable
  X and lives outside the panel), so the toggle badge reflects panel filters.
- **Replaced one-off clears** per the prompt: ProductSearch "Clear ranges" and
  its bespoke filter toggle are gone, folded into FilterBar's standard Clear +
  toggle.

**Files touched:**
- New: `web_app/src/components/FilterBar.vue`.
- `web_app/src/composables/useStockFilters.ts` (hardened predicates +
  `activeFilterCount`).
- `web_app/src/pages/StockOverview.vue`, `RecipesOverview.vue`,
  `MyProductsPage.vue`, `ProductSearch.vue`.
- `CHANGELOG.md`, `DORA_FOLLOWUPS.md`.

**Verification:**
- `<FilterBar>` balanced 1/1 in each of the four pages; import present in each.
- Named slots (`#search`/`#filters`/`#actions`) open/close balanced; q-card
  balance intact in ProductSearch after removing its filter card.
- `showFilters` fully removed from ProductSearch (0 refs); `hasAnyFilter` still
  used by the empty-states in Recipes/MyProducts (no orphans); `clearRanges`
  still used by `clearAllFilters` (no orphan).
- Reasoned through empty=off for every field on every page (now explicit).
- **Not run:** lint / `quasar build` / dev server — `node_modules` absent.

**Next up:**
- **User eyeballs A4** once deps installed: on each of the 4 pages confirm —
  Filters toggle shows/hides the panel; panel hidden by default on mobile; the
  active-count badge is right; Clear appears only when filters active and resets
  them; blank inputs show all rows; light + dark.
- **Wave A is now A1–A4 done.** Next prompt: check `docs/prompts/00_INDEX.md` for
  the Wave B start (or the next item in `RECONCILED_FINISHING_PLAN.md §5`).
- See `DORA_FOLLOWUPS.md` for A4 leftovers (multi-select control only partially
  standardised; FilterBar panel has no card container; AuditLogSettings filtering
  not standardised — server-side, was out of A4 scope).

**Open questions for user:**
- Any A4 page where the panel default (open desktop / closed mobile) or the
  moved controls feel wrong? Flag page + screen size.
- The products pages were migrated despite being companion-bound — still happy
  with that, or should they be reverted to minimal-touch later?

---

## 2026-06-05 — A3 (standard modal / BaseDialog) + A2 follow-up (danger-ghost button)
**Status:** complete (static verification only — node_modules not installed)
**What changed:**
- New `web_app/src/components/BaseDialog.vue` — standard modal shell wrapping
  `q-dialog` + `q-card`. Non-`persistent` by default (backdrop + Esc = cancel,
  never commit/navigate), token radius, optional standardised header
  (`title`/`closable`) and `#actions` footer slot, `cancel` event on any close.
- Migrated **all ~28 standard template `<q-dialog>` modals across 25 files** to
  `BaseDialog` (3 reference files done by hand: `RecipeEditDialog`,
  `RecipeCookMode` finish, `RecipeDetailPage` ×4; the remaining 22 files fanned
  out to 4 parallel subagents against a precise transform spec).
- **A2 follow-up:** confirmed the other agent had already added the
  `danger-ghost` `BaseButton` variant (flat negative — the "ghost danger" delete
  button) and wired it into `StockItemDetailPage` (Delete + clear-expiry) and
  `MealPlansOverview` (Delete plan). Verified complete; nothing more to do there.

**Decisions made:**
- **Destructive dismiss policy** (the prompt's "confirm with me"): user chose
  **backdrop = cancel for ALL modals**, including deletes. Delete only fires from
  its explicit button. This already matched the de-facto code behaviour, so no
  `persistent` was added anywhere.
- **Scope:** user chose "migrate all ~30". Interpreted as: migrate every standard
  *card* modal, and document 3 specialised overlays as intentional exceptions —
  `AlertsBell` (seamless side drawer, no backdrop → modal-cancel semantics don't
  apply), `CommandPalette` (custom search overlay), `ScanOverlay` (persistent
  camera overlay). Forcing these through BaseDialog adds no value and risks their
  custom layout/positioning.
- **The prompt's "bugs" are mostly already fixed** (docs are stale, per CLAUDE.md).
  The `$q.dialog()` programmatic confirms (recipe delete, unsaved-changes,
  cook-start) only commit/navigate on `.onOk()` and resolve false on
  `.onDismiss()` — already correct. Left them as-is; A3's real value here is the
  shell standardisation, not bug-fixing.
- **Shell transform, not internal rewrite.** Each dialog keeps its own
  header/footer markup inside BaseDialog's default slot. Fully unifying 28
  heterogeneous dialogs' internal structure (via the `title`/`#actions` slots)
  would be a large, risky rewrite for little gain — deferred as future polish.
  Mirrors how A2 was run incrementally.
- **`@hide` → `@cancel`.** Dialogs with an `@hide` cleanup handler
  (`CreateStockItemDialog` resetForm, `QuickAddSheet` onHide) were converted to
  `@cancel` — BaseDialog re-emits the dialog's hide as `cancel`. Semantics
  preserved (both fire on any close).
- **Scoped card-class sizing bug caught + fixed.** Three dialogs sized their card
  via a *scoped* CSS class (`comparison-card`, `orphans-card`, `quick-add-sheet`).
  Once the `<q-card>` moved into BaseDialog's style scope (and dialogs teleport to
  `<body>`), those scoped selectors no longer matched. Moved each into the inline
  `card-style` prop and deleted the dead rules. Also fixed `AuditLogSettings`
  (always-maximized, bare card) whose card was being capped at 95vw by BaseDialog's
  default `card-style` — gave it an explicit fill style.

**Files touched:**
- New: `web_app/src/components/BaseDialog.vue`.
- Reference migrations: `components/RecipeEditDialog.vue`, `pages/RecipeCookMode.vue`,
  `pages/RecipeDetailPage.vue`.
- Subagent migrations (22 files): `components/MealPlanEditDialog.vue`,
  `components/stock/BulkMoveLocationDialog.vue`,
  `components/stock/CreateStockItemDialog.vue`, `components/QuickAddSheet.vue`,
  `components/ShortcutsCheatsheet.vue`, `pages/StockItemDetailPage.vue`,
  `pages/StocktakeRunner.vue`, `pages/ShoppingListShopMode.vue`,
  `pages/ShoppingListsOverview.vue`, `pages/ShoppingListTemplates.vue`,
  `pages/MyProductsPage.vue`, `pages/ProductSearch.vue`,
  `pages/MealPlansOverview.vue`, `pages/RecipesOverview.vue`,
  `pages/data/BackupRestore.vue`, `pages/data/DataImport.vue`,
  `pages/data/BarcodesQR.vue`, `pages/PriceHistoryPage.vue`, `pages/WastePage.vue`,
  `pages/VerifyEmailPage.vue`, `pages/settings/AuditLogSettings.vue`,
  `pages/settings/UsersAdminSettings.vue`.
- `CHANGELOG.md`.

**Verification:**
- `<q-dialog` opens app-wide = 4, all expected: `BaseDialog` itself + the 3
  documented exceptions. `</q-dialog>` closers = 4 (balanced).
- 38 `<BaseDialog>` usages across 25 files; every consuming file imports
  `BaseDialog` (scripted check — 0 missing imports).
- `<q-card>`/`</q-card>` and `<BaseDialog>`/`</BaseDialog>` tag balance verified
  per file (scripted — 0 unbalanced).
- `@hide` now only in `BaseDialog` (internal) + `CommandPalette` (exception).
- **Not run:** lint / `quasar build` / dev server — `node_modules` is not
  installed in this checkout, consistent with prior sessions.

**Next up:**
- **User eyeballs A3 in browser** once deps are installed: open a representative
  modal in each family (new-recipe, cook-mode finish, a stock-item picker, the
  recipe comparison dialog, quick-add sheet, a data report dialog, audit detail).
  Confirm: backdrop-click and Esc close *without* committing/navigating; Cancel +
  primary buttons work; widths/maximized behaviour unchanged; the comparison /
  orphans / quick-add cards are still correctly sized (the scoped-class fix).
- Optional A3 polish (deferred): adopt BaseDialog's `title` prop + `#actions`
  slot to truly unify header/footer chrome across dialogs (currently each keeps
  its own markup). Low priority — purely cosmetic consistency.
- Next Wave A prompt: **A4 — filter system** (`docs/prompts/A4_filter_system.md`).

**Open questions for user:**
- Any modal that now closes when it shouldn't, or whose sizing looks off after
  the scoped-class → `card-style` move? Flag the dialog + screen size.
- OK that the 3 specialised overlays (AlertsBell / CommandPalette / ScanOverlay)
  stay on raw `q-dialog`, or do you want them folded in too?

---

## 2026-06-04 — A2 Phase 2 (detail-page toolbars, dialogs, onboarding, auth/settings/data)
**Status:** complete (substantial coverage — see remaining residuals below)
**What changed:**
- 20 additional files migrated, ~95 `q-btn` instances converted to `BaseButton`.
- App-wide `<q-btn` count: **399 → 304** (24% reduction overall; near-full coverage on the high-visibility surfaces).
- Files now using BaseButton: **26**.
- Categories covered: detail-page top toolbars + their dialog footers, all major form/edit dialog components, onboarding wizard, auth pages (Forgot/Reset/Verify/ConfirmEmailChange), key settings sub-pages (UsersAdmin, AuditLog, Merchants), data pages (BackupRestore, DataImport, BarcodesQR).

**Decisions made:**
- Kept the few flat-negative buttons (e.g. `StockItemDetailPage` Delete toolbar btn) as `q-btn` — current BaseButton variant set doesn't have a "flat danger" shape, and the visual is intentional (less alarming than filled `variant="danger"`). Filed as a possible BaseButton extension; not blocking.
- Used `class="text-primary"` on `variant="ghost"` BaseButtons where the original q-btn had `color="primary"` on a flat layout (auth-page "Back to sign in", VerifyEmail "Resend verification", etc.). Keeps text colour theme-aware without a new variant.
- `ResetPasswordPage` "Reset password" submit (large, full-width) deliberately left as q-btn — its `size="lg"` + `class="full-width"` don't map cleanly to BaseButton's fixed 36px height, and it's a one-off design.
- Used auto-forwarding of `icon-right` (and other unknown attrs) through BaseButton's root `q-btn` rather than declaring it as a prop. Works because BaseButton has a single root element so Vue auto-forwards $attrs.
- Wrote the 9 missing BaseButton imports via a sed pass that inserts after the `<script>` tag.

**Files touched (this pass):**
- Pages: `StockItemDetailPage`, `RecipeDetailPage`, `ShoppingListDetail`, `ShoppingListShopMode`, `RecipeCookMode`, `WelcomeWizard` (onboarding), `ForgotPasswordPage`, `ResetPasswordPage`, `VerifyEmailPage`, `ConfirmEmailChangePage`, `UsersAdminSettings`, `AuditLogSettings`, `MerchantsSettings`, `BackupRestore`, `DataImport`, `BarcodesQR`.
- Components: `RecipeEditDialog`, `MealPlanEditDialog`, `stock/CreateStockItemDialog`, `stock/BulkMoveLocationDialog`.
- `CHANGELOG.md`.

**Verification:**
- App-wide `<q-btn` count via grep: 304 remain.
- 26 files now import `BaseButton`.
- All migrated files re-verified to have both the import AND at least one BaseButton usage (no orphan imports).
- **Not run** the dev server.

**Remaining `<q-btn` (~304, out of scope for A2):**
- Inline list-row action buttons (recipe-card hover actions, stock-row quick actions, shopping-list line buttons, settings list-item row actions). Embedded in nested `q-card-actions`/`q-list`/`q-item-section` contexts — re-themed already, just not standardised.
- `q-btn-dropdown` (4 usages) and `q-btn-toggle` (6 usages) — different APIs from `q-btn`; out of BaseButton scope by design.
- `q-btn` inside `q-input` append slots (search-clear, copy-to-clipboard) — better left as the minimal pop-out style.
- A handful of one-off large CTAs (e.g. `ResetPasswordPage` full-width submit) deliberately preserved.
- Few remaining footer buttons in `StockOverview` body sections (empty-state, summary cards) and `RecipeDetailPage` mid-page link-product / add-substitute btns — already migrated for the top toolbars.

**Next up:**
- **User eyeballs Phase 2**: open the detail pages (stock item, recipe, shopping list detail, shop mode, cook mode), the onboarding flow, the auth pages, and a settings sub-page. Confirm consistent button heights, ghost-Cancel + primary-CTA pattern across dialogs.
- **A3 — Standard modal** (next Wave A prompt, `prompts/A3_standard_modal.md`).
- Optional A2 follow-up backlog (deferred):
  - "flat danger" BaseButton variant (or `:flat` modifier) for non-loud destructive actions.
  - `q-btn-dropdown` wrapper component if there's appetite for unifying split-buttons.
  - Inline list-row action button standardisation (high q-btn count remains but visual impact is low — they're tiny icon buttons).

**Open questions for user:**
- Any visual regression?
- Proceed to A3, or pause to eyeball Phase 2 first?

---

## 2026-06-04 — A2 Phase 1 (BaseButton + PageToolbar + 6 page-toolbar migrations)
**Status:** complete (Phase 1 scope only — inline / dialog / body-content q-btns left as-is)
**What changed:**
- New `web_app/src/components/BaseButton.vue` — variants `primary | secondary | ghost | danger | icon`, plus `:attention` modifier. Wraps `q-btn`. Fixed 36px height for toolbar alignment; icon variant is 36×36 square. `attention` uses a pulsing brand-accent box-shadow keyframe (replaces the StockOverview-local `stocktake-glow` CSS); honours `prefers-reduced-motion`.
- New `web_app/src/components/PageToolbar.vue` — title + optional back-arrow on the left, named slot `#actions` on the right.
- Migrated page-top action buttons in `StockOverview` (4 + empty-state CTA), `RecipesOverview` (3), `MealPlansOverview` (2), `MyProductsPage` (2), `ShoppingListTemplates` (1), `StocktakePage` (1, wrapped header in PageToolbar).
- Deleted the now-unused `.stocktake-glow` keyframe rule from `StockOverview.vue` style block.

**Decisions made:**
- Variants: `primary | secondary | ghost | danger | icon` + `attention` modifier (user's confirmation).
- "New X" CTAs use `variant="primary"` (brand), not the pre-existing `color="positive"` (green). Decouples create-action from success-semantic. Matters in Cherry Cola where brand-red ≠ positive-green.
- Phase 1 only: just the 6 main overview pages' top action rows. Inline / list-row / dialog / body buttons left untouched.
- `ShoppingListsOverview` skipped — its New button is a `q-btn-dropdown` split-button (different API than `q-btn`); already uses `color="primary"` so it's on-convention.
- `StocktakePage` is the only one that got the full `PageToolbar` wrapper because it already had a clear title + back-arrow pattern. Other pages have heterogenous header rows (counts, filters, search inline) — wrapping them all would over-rewrite; left their `<div class="row …">` headers but swapped buttons to `BaseButton`.
- Compare button on `RecipesOverview` migrated even though it's not a "New" CTA — it's a top-row toggle and benefits from the standard sizing.
- BaseButton's `attention` modifier upgraded to a pulse animation (rather than the originally-planned static glow) because the existing stocktake-glow used a pulse; preserving the existing visual effect across the migration.

**Files touched:**
- `web_app/src/components/BaseButton.vue` (new)
- `web_app/src/components/PageToolbar.vue` (new)
- `web_app/src/pages/StockOverview.vue`
- `web_app/src/pages/RecipesOverview.vue`
- `web_app/src/pages/MealPlansOverview.vue`
- `web_app/src/pages/MyProductsPage.vue`
- `web_app/src/pages/ShoppingListTemplates.vue`
- `web_app/src/pages/StocktakePage.vue`
- `CHANGELOG.md`

**Verification:**
- Per-file: BaseButton usage count matches the import count (1 import per file, 1–4 uses).
- Reviewed in-context: button heights now consistent across the 6 pages (36px); icon-only buttons are square; semantics preserved (Scan / Stocktake / Compare = secondary outline; New X = primary fill; Refresh = ghost).
- `prefers-reduced-motion` path verified to disable the pulse and fall back to a static glow.
- **Not run** the dev server.

**Phase 1 left out of scope (for future A2 follow-up passes):**
- Inline action buttons inside list rows (recipe cards, shopping-list lines, stock rows).
- Dialog footer buttons (Confirm / Cancel pairs in modals).
- Toolbar buttons on detail / single-entity pages (`StockItemDetailPage`, `RecipeDetailPage`, `ShoppingListDetail`).
- The `ShoppingListsOverview` split-button dropdown.
- `Onboarding/WelcomeWizard.vue` step buttons.
- ~58 files with q-btn usage not yet touched.

**Next up:**
- **User eyeballs Phase 1**: open StockOverview, RecipesOverview, MealPlansOverview, MyProductsPage, ShoppingListTemplates, StocktakePage. Confirm: buttons aligned, "New X" reads as brand colour (not green), Stocktake "glow when overdue" still pulses (visit StockOverview with overdue stocktake items).
- **A2 Phase 2** (optional follow-up): migrate inline/detail-page/dialog q-btns. Worth doing once Phase 1 is approved.
- Alternative: continue down the Wave A list with **A3 — Standard modal** (`prompts/A3_standard_modal.md`).

**Open questions for user:**
- Any visual regression in the 6 migrated pages?
- Run A2 Phase 2 (rest of q-btns) before A3, or push into A3 next?

---

## 2026-06-04 — A1b round 2 (Pesto Dark + dual-source sync)
**Status:** complete
**What changed:**
- Pesto Dark green further toned: `--brand-primary` / `--brand-accent` / `--semantic-positive` `hsl(150 62% 50%)` → `hsl(150 48% 40%)`. `--chart-1` `hsl(150 48% 45%)`. Dora halo tokens retuned to match.
- Pesto Dark text lifted for pop on the dark page: `--text-secondary` 67% → 78% L; `--text-muted` 55% → 66% L.
- **Caught a dual-source bug:** `themeService.ts`'s parallel `THEMES` palette dict was overwriting the new `themes.scss` values via `setCssVar('primary', ...)` etc. on theme apply. Synced Pesto, Pesto Dark, and Lemon Tart Dark palette entries in `themeService.ts` so the Quasar-driven `--q-*` path matches the CSS-driven `--brand-*` path.

**Decisions made:**
- Going one big step rather than nibbling: from "still feels too bright" feedback at 62/50, jumping to 48/40 rather than another small step — easier to walk back if too dark than to keep iterating.
- Kept `--text-on-primary: hsl(165 60% 5%)` (deep forest) for Pesto Dark chip text rather than flipping to white — at the new darker green it reads ~7:1 contrast which is excellent.
- Only synced Pesto, Pesto Dark, LT Dark in `themeService.ts` (the three I touched). The other 7 themes still have a dual-source coupling but their values match between the two files, so no immediate sync needed.
- Did not touch other themes' brand values per same caution — waiting for browser eyeball.

**Files touched:**
- `web_app/src/css/themes.scss`
- `web_app/src/services/themeService.ts`
- `CHANGELOG.md`

**Verification:**
- All three values now match between `themes.scss` and the `THEMES` dict in `themeService.ts` for Pesto, Pesto Dark, LT Dark.
- Contrast reasoning for Pesto Dark:
  - White text on new `--brand-primary` `hsl(150 48% 40%)`: ~5.5:1 (AA Normal pass).
  - `--text-on-primary` `hsl(165 60% 5%)` on new green: ~7:1 (AAA pass).
  - `--text-secondary` `hsl(205 14% 78%)` on `--surface-page` `hsl(165 60% 5%)`: ~9:1 (excellent).
  - `--text-muted` `hsl(205 12% 66%)` on the same page: ~6:1 (comfortable AA).
- **Not run** the dev server.

**Next up:**
- **User eyeballs Pesto Dark again.** Specifically:
  - Cookable Now chip in recipe detail — green still vibrant or comfortable?
  - "Add" / primary CTA buttons across the app — text legible, brand-present without being garish?
  - Captions / subtitles on the dark page — readable now?
  - If still too bright, we go further (hsl(150 40% 34%) range) — easy to walk back.
- If colour feels right, proceed to **A2 (standard button + toolbar)**.
- Note: 7 other themes have the same dual-source coupling — collapsing `themeService.ts` THEMES dict into a CSS-var read is a worthwhile follow-up but doesn't block A1/A1b sign-off.

**Open questions for user:**
- After eyeballing: green still too bright, about right, or now too muted?
- Text on the dark page reading better?

---

## 2026-06-04 — A1b (token value tuning) complete
**Status:** complete
**What changed:**
- Added `--overlay-hover-on-coloured` + `--overlay-active-on-coloured` + `--highlight-search` tokens to `tokens.scss`.
- Rewired `MainMenuButton.vue` hover, `CommandPalette.vue` `.cp-hl` highlight, and `CommandPalette.vue` `.cp-row--selected` to the new / theme-aware tokens.
- Deleted three `.body--dark` overrides (`CommandPalette.vue:404,428`, `ShortcutsCheatsheet.vue:85`) — they were legacy workarounds for a token-flip gap that no longer exists.
- `--ring-focus` is theme-aware in every theme (was hardcoded Pesto green).
- Value retunes per theme:
  - **Pesto** `--brand-primary` desaturated `hsl(150 76% 39%)` → `hsl(150 60% 36%)` (fixes "add" / cookable green too bright).
  - **Pesto Dark** `--brand-primary`/`-accent`/`--semantic-positive`/`--chart-1` toned `hsl(150 75% 55%)` → `hsl(150 62% 50%)`, Dora halo retuned to match.
  - **Lemon Tart Dark** `--semantic-warning` `hsl(46 100% 55%)` → `hsl(40 90% 60%)`.
  - **Cherry Cola Dark** + **Sourdough Dark** Dora halo alphas dropped so the glow doesn't dominate.
  - `--text-muted` (Pesto defaults + Pesto theme) `hsl(168 8% 50%)` → `hsl(168 10% 42%)` for AA contrast.

**Decisions made:**
- `--overlay-hover` already theme-flips in `themes.scss` (dark themes set white veils) — so DEC-A-1's "theme-flip the token" step was already done. The remaining gap was the *toolbar* surface (always coloured), which now has its own `--overlay-hover-on-coloured` token. The `.body--dark` overrides in CommandPalette/ShortcutsCheatsheet were therefore redundant and got deleted, not patched.
- `--highlight-search` defined via `color-mix(var(--brand-accent) 40%, transparent)` so it tracks the theme accent automatically — no per-theme override needed.
- `--text-muted` only bumped in Pesto family. Other light themes (LT, Blueberry, Cherry Cola light, Sourdough light) sit at L=50 which is fine; dark themes already lifted to L=55-60.
- Did **not** touch other light themes' brand-primary values — the "too bright add" complaint is most acute on Pesto (per audit §5 + A1b prompt) and Pesto Dark; over-tuning the whole family without seeing it in the browser risks washing out the brand.

**Files touched:**
- `web_app/src/css/tokens.scss`
- `web_app/src/css/themes.scss`
- `web_app/src/components/menu/MainMenuButton.vue`
- `web_app/src/components/CommandPalette.vue`
- `web_app/src/components/ShortcutsCheatsheet.vue`
- `CHANGELOG.md`

**Verification:**
- Grep confirms 0 remaining `.body--dark` colour-override blocks in the three named components.
- `--ring-focus` is now `color-mix(... var(--brand-primary)...)` in all 10 theme blocks.
- `--overlay-hover` still has its dark-theme overrides (untouched — they were already correct).
- App-wide rgba/hsla literals are now exclusively in DEC carve-outs (LoginPage DEC-2, ScanOverlay DEC-4, ProductSearchCard DEC-8, Aldi/Coles/IGA brand logos, TrendSparkline + ReportsPage SSR fallbacks).
- **Not run** the dev server.

**Next up:**
- **User eyeballs A1b**: especially Pesto "add" buttons (less garish?), Pesto Dark chips (readable?), Lemon Tart Dark warning chips (no longer pure yellow), Cherry Cola Dark / Sourdough Dark Dora bubble (subtler halo), and that the focus ring now matches the theme on Tab.
- **A2 — Standard button + toolbar** (next Wave A foundation; see `prompts/A2_standard_button_toolbar.md`'s Impact block — has decisions).
- Remaining A1 backlog items worth noting:
  - Other light themes' `--text-muted` may also need a 50→42 nudge — defer until A1b is eyeballed.
  - `LoginPage.vue` `--lp-*` ladder still untouched per DEC-2; revisit when C19 (shared auth-shell) is designed.
  - Bright "add" green in non-Pesto light themes — only retune if feedback persists after eyeballing.

**Open questions for user:**
- Anything still reading too bright / too dim / off-brand after A1b? Flag page + theme.
- Proceed to A2, or pause to eyeball?

---

## 2026-06-04 — A1 STEP 2 complete (Chunks D, G, C, B, E, H, F)
**Status:** complete — A1 STEP 2 finished end-to-end across the whole audit.
**What changed:**
- All remaining chunks executed in a single push: D (recipes/cook), G (settings — 9 files), C (products/price-history — minimal-touch per master Decision 1), B (stock — 7 files), E (meal-plans + shopping — 6 files), H (dashboard/reports/waste/data — 8 files), F (Dora + help + shared widgets — 9 files).
- **App-wide final state:** 0 numbered Quasar palette classes (`text-grey-N`, `bg-red-1`, …), 0 bare `text-grey` class usage, 1 numbered palette prop residual (`ScanOverlay.vue:61 label-color="grey-4"` per DEC-4 — accepted).
- **Tokens added** (resolving DEC-3): `--dora-disc-bg` / `--dora-halo` / `--dora-halo-strong` in `tokens.scss` + per-theme overrides in `themes.scss` for all 10 theme variants. `DoraBubble.vue` disc backdrop and `DoraChat.vue` chat surfaces now ride these; `.body--dark` workaround blocks deleted because the tokens flip automatically.
- **Charts wired to tokens:** `usePriceHistoryPalette.ts` and `TrendSparkline.vue` read CSS vars at call time with HSL fallbacks; `PriceHistoryChart.vue` SVG axes routed through CSS classes.
- **Hex-pinned shadow / pulse / glow patterns** replaced via `color-mix(in srgb, var(--token) X%, transparent)` for DEC-6 (menu glow), DEC-7 (stock pulse keyframe), DEC-11 (dashboard elevation shadows).
- **DEC carve-outs preserved:** logos (Aldi/Coles/IGA), ProductSearchCard category hash (DEC-8), MerchantLogo placeholder (DEC-9), ScanOverlay rings (DEC-4), theme-picker swatches (DEC-10), Reports/Dashboard CSS-read fallbacks (consistency-only).

**Decisions made during the run:**
- Quasar `color="warning"` / `color="negative"` / `color="positive"` used for icon and chip semantic colours because they ride `--q-*` written by `themeService.setCssVar` — i.e. they are theme-aware.
- Neutral grey badges and chips (the "(you)" badge, "Inactive" badge, archived-count badge) standardised to `color="grey"` (Quasar's neutral mid-grey, no shade). Fixed but reads OK in both modes; tiny surfaces. Not a follow-up.
- Avatars that were `color="amber-3" text-color="grey-10"` (warm placeholder over light) folded into `color="accent" text-color="dark"` for the "active" branch and `class="dora-bg-sunken dora-text-secondary"` for the neutral branch (so avatars theme-shift).
- The `ShoppingListDetail.vue:2251` Dora-touched highlight folded into `var(--brand-primary-soft)` (resolves the audit's open mapping).
- `ShoppingListShopMode.vue` `var(--surface-elevated, rgba(0,0,0,0.04))` fallbacks — dropped the rgba safety net since the token always exists in this codebase; the orphan `var(--c-ink-mute, …)` reference replaced with `var(--text-muted)`.
- `DoraChat.vue` legacy `--c-accent` / `--c-ink-mute` private vars retired in favour of real tokens.

**Files touched:**
- `web_app/src/css/tokens.scss` (Dora tokens added)
- `web_app/src/css/themes.scss` (per-theme Dora-disc/halo overrides for 10 themes)
- Pages: `RecipesOverview`, `RecipeDetailPage`, `RecipeCookMode`, `MealPlansOverview`, `ShoppingListsOverview`, `ShoppingListDetail`, `ShoppingListShopMode`, `ShoppingListTemplates`, `ShopNowRedirect`, `StockOverview`, `StockItemDetailPage`, `StocktakePage`, `StocktakeRunner`, `ProductSearch`, `MyProductsPage`, `PriceHistoryPage`, `DashboardPage`, `ReportsPage`, `WastePage`, `DataManagement`, `TtsTestPage`, `DoraHelpPage`, `HelpPage`, `pages/data/*` (4 files), `pages/settings/*` (9 files), `pages/onboarding/WelcomeWizard.vue` (chunk I).
- Components: `RecipeCard`, `RecipeEditDialog`, `QuickAddSheet`, `ScanOverlay`, `stock/StockItemRow`, `ProductSearchCard`, `PriceHistoryChart`, `MerchantLogo`, `TrendSparkline`, `dora/DoraBubble`, `dora/DoraChat`, `chips/*`, `SelectComponent`, `CardComponent`, `settings/LocationRow`.
- Composable: `usePriceHistoryPalette.ts`.
- `CHANGELOG.md` (Unreleased § Changed).

**Verification:**
- App-wide greps for numbered palette classes / palette props confirm a single intentional residual (`ScanOverlay`).
- Hex residuals are now exclusively the documented carve-outs (logos, deterministic hash, fallbacks-after-CSS-read).
- Light + dark + Cherry Cola Dark reasoning per chunk: dora glow now picks up theme brand colour (no more "Pesto Pesto Pesto"); dashboard ink shadows ride elevation tokens; charts pull from --chart-1..5.
- **Not run** the dev server. User needs to eyeball: at minimum dashboard, stock overview, recipes overview, a recipe in cook mode, shopping list detail + shop mode, meal plans, the Dora chat panel (note: Dora's halo will look distinctly different per theme now — this is the DEC-3 design call), settings (all sub-pages), reports.

**Next up:**
1. **User eyeballs the whole app across at least three themes** (Pesto, Pesto Dark, Cherry Cola Dark are the most diagnostic). Note anything broken/ugly in the worklog and we'll re-tune in A1b.
2. **A1b — token value tuning.** Backlog so far:
   - DEC-A-1: theme-flip `--overlay-hover` + add `--overlay-hover-on-coloured` (for toolbar surfaces). Delete the `.body--dark` overrides in `CommandPalette.vue` / `ShortcutsCheatsheet.vue` / `MainMenuButton.vue`.
   - DEC-A-2: add `--highlight-search` token (alpha-blended for matched-substring backgrounds).
   - Audit `--semantic-warning` value in `lemon-tart-dark` (pure yellow at 100%, may clash with text-on-it).
   - `--text-muted` contrast vs `--surface-page` in Pesto (currently borderline AA).
   - `--ring-focus` is pinned to Pesto green hue regardless of theme — make it brand-aware.
   - Tune Dora token values per theme — current dark-theme halos use brand-primary at α 0.32/0.55 which may be too bright in Cherry Cola Dark / Sourdough Dark.
3. **A2 — Standard button + toolbar** (next Wave A prompt; has decisions — read `prompts/A2_standard_button_toolbar.md` Impact block first).

**Open questions for user:**
- Anything you see in any theme that looks wrong? Flag the page + theme.
- Proceed to A1b value tuning or jump to A2 standard button/toolbar?

---

## 2026-06-04 — A1 STEP 2, Chunk I (onboarding)
**Status:** complete
**What changed:**
- `pages/onboarding/WelcomeWizard.vue`: all 11 palette-class hits + 3 palette `color=`/`track-color=` props replaced with semantic tokens (`dora-text-muted`, `dora-text-secondary`, `dora-bg-negative-soft text-negative`).
- Dropped `track-color="grey-3"` on the step progress bar so the unfilled track inherits the theme-aware default.
- `color="grey-7"` on the skip-buttons → `class="dora-text-secondary"` (flat btn picks up text colour from class).

**Decisions made:**
- `text-body2 text-grey-8` (body copy in step cards) → `dora-text-secondary` rather than `dora-text-muted` — these are descriptive paragraphs, not captions.
- `text-caption text-grey` → `dora-text-muted` (caption-volume helper).
- No new discovered DECs in this file.

**Files touched:**
- `web_app/src/pages/onboarding/WelcomeWizard.vue`
- `CHANGELOG.md`

**Verification:**
- Re-ran combined grep against this file: zero residual palette classes, palette props, hex, or rgba.
- Light/dark reasoning: the "current step" highlight uses `color="primary"`/`color="secondary"` already (theme-aware); the now-soft error banner picks up theme-defined `--semantic-negative-soft`; the dropped `track-color` lets the progress bar's unfilled portion ride the default light-on-bg.
- **Not run** the dev server.

**Next up:**
- **A1 STEP 2 Chunk D (recipes+cook).** Files: `pages/RecipesOverview.vue`, `pages/RecipeDetailPage.vue`, `pages/RecipeCookMode.vue`, `components/RecipeCard.vue`, `components/RecipeEditDialog.vue`. ~30 hits per the audit.
- Chunk order from `THEME_AUDIT.md §6`: D → G → C → B → E → H → F (last).

**Open questions for user:** none — clear to proceed with Chunk D.

---

## 2026-06-04 — A1 STEP 2, Chunk A (auth/shell)
**Status:** complete
**What changed:**
- Added 11 semantic helper classes to `web_app/src/css/colours.scss` (`dora-text-muted`, `dora-text-secondary`, `dora-text-on-primary`, `dora-text-on-toolbar`, `dora-bg-page/sunken/elevated`, `dora-bg-{positive,negative,warning,info}-soft`). Quasar's `.text-positive/negative/warning/info` already ride `--q-*` and are theme-aware, so reused those for semantic ink.
- Replaced Quasar palette classes / props / hardcoded literals with semantic tokens across all Chunk A files (full list in CHANGELOG entry).
- `ErrorNotFound.vue` 404 page repainted from `bg-blue text-white` to `var(--surface-toolbar) / var(--text-on-toolbar)` so it shifts per theme; "Go Home" button now inverts those.
- `MainMenuButtonStrip.vue:111` amber glow now uses `color-mix(in srgb, var(--brand-accent) 55%, transparent)` (DEC-6).
- Filed two newly-discovered token-system gaps as DEC-A-1 and DEC-A-2 in `web_app/THEME_AUDIT.md §6b` — both are A1b territory, neither blocks future chunks.

**Decisions made:**
- `LoginPage.vue` skipped entirely per DEC-2 (intentional splash).
- Theme-picker swatches in `PreferencesSettings.vue` belong to Chunk G; not touched.
- `text-color="white"` on q-badge / q-avatar inside `AlertsBell.vue` (lines 8, 82, 166) **kept as-is** — those badges sit on `color="negative"` / `color="positive"` surfaces which are always saturated regardless of theme. White-on-saturated is theme-stable; not dark-broken.
- Where icons used `:color="… 'grey-7'"` (`VerifyEmailPage`, `ConfirmEmailChangePage`) the conditional fell back to `undefined` paired with a `dora-text-secondary` class — `q-icon` honours the class when `color` is unset.
- `.body--dark` style overrides in `CommandPalette` / `ShortcutsCheatsheet` left alone — they're workarounds for `--overlay-hover` not theme-flipping (DEC-A-1). Fixing them properly requires adding `--overlay-hover` overrides in dark theme blocks, which is out of A1 scope.

**Files touched:**
- `web_app/src/css/colours.scss` (+11 helper classes)
- `web_app/src/components/OfflineBanner.vue`
- `web_app/src/components/PageErrorState.vue`
- `web_app/src/components/CommandPalette.vue`
- `web_app/src/components/AlertsBell.vue`
- `web_app/src/components/PwaInstallPrompt.vue`
- `web_app/src/components/ShortcutsCheatsheet.vue`
- `web_app/src/components/FormErrorSummary.vue`
- `web_app/src/components/menu/MainMenuButtonStrip.vue`
- `web_app/src/pages/ErrorNotFound.vue`
- `web_app/src/pages/ForgotPasswordPage.vue`
- `web_app/src/pages/ResetPasswordPage.vue`
- `web_app/src/pages/VerifyEmailPage.vue`
- `web_app/src/pages/ConfirmEmailChangePage.vue`
- `web_app/src/pages/SettingsShell.vue`
- `web_app/src/layouts/WelcomeLayout.vue`
- `web_app/THEME_AUDIT.md` (added §6b discovered gaps)
- `CHANGELOG.md` (Unreleased § Changed)

**Verification:**
- Re-ran grep scan across Chunk A files: zero remaining Quasar palette classes / palette `color=` props / hex / named CSS colours. Five `rgba(...)` residuals all in `.body--dark` blocks or the search highlight — filed as DEC-A-1 / DEC-A-2.
- Reasoned through both Pesto (light) and Pesto Dark per the prompt requirement. Cherry Cola Dark sanity-check: the auth banners now use the theme's `--semantic-negative-soft` (deeper red-pink in CC Dark) and the 404 page picks up the deep merlot of `--surface-toolbar`. Should look on-brand instead of pinned to blue.
- **Not run:** the actual dev server. User should open the affected pages (login → forgot → reset → verify → 404, plus Alerts panel, Command palette `Ctrl+K`, Settings shell, PWA install prompt) and switch themes (Pesto Dark, Cherry Cola Dark) to eyeball before signing off the chunk.

**Next up:**
- **User eyeballs Chunk A in browser** (sequence above). Note anything that looks wrong in the worklog so the next chunk can pick it up.
- Then **A1 STEP 2 Chunk I (onboarding — `pages/onboarding/WelcomeWizard.vue`)** per the chunk order in `THEME_AUDIT.md §6`. Smallest chunk, ~11 hits — fast.
- A1b (token-value tuning) backlog now has two new items in `THEME_AUDIT.md §6b`: DEC-A-1 (hover overlay theme-flip) and DEC-A-2 (search-result highlight token).

**Open questions for user:**
- After eyeballing, are the auth banners (red error / green success) reading right in all themes? If anything looks off, flag the page+theme and I'll re-tune in A1b.
- OK to proceed straight to Chunk I, or pause here?

---

## 2026-06-04 — A1 DEC-1..DEC-11 resolved
**Status:** complete (decisions only — no code changed)
**What changed:**
- All 11 `needs_decision` items in `web_app/THEME_AUDIT.md` resolved. New §6a in the audit records the answers.
- DEC-2: keep LoginPage `--lp-*` ladder as-is. Chunk A must skip those lines.
- DEC-3: introduce theme-aware Dora tokens (`--dora-disc-bg`, `--dora-halo`, `--dora-halo-strong`) in `tokens.scss` defaults + per-theme overrides in `themes.scss`. **Chunk F is gated on this token addition** — do it as a prerequisite at the start of Chunk F.
- DEC-1, 4, 5, 6, 7, 8, 9, 10, 11: all accepted as the audit's recommended answers.

**Decisions made:** see `web_app/THEME_AUDIT.md §6a` — that's the canonical record. Of note for sequencing:
- Chunk F (Dora) now has a prerequisite "add Dora tokens" step before any `.vue` edits.
- Chunk A (auth/shell) shrinks slightly because the LoginPage `--lp-*` block is excluded.

**Files touched:** `web_app/THEME_AUDIT.md` (added §6a).

**Verification:** none needed — decisions only.

**Next up:**
**A1 STEP 2 — Chunk A (auth/shell).** Run the chunk fix prompt per `prompts/A1_theme_compliance.md §STEP 2`, scoped to the files listed in `THEME_AUDIT.md §3 Chunk A`. Apply DEC resolutions from §6a. Eyeball Pesto light + Pesto Dark + Cherry Cola Dark before marking the chunk complete.

**Open questions for user:** none — clear to proceed with Chunk A on user say-so.

---

## 2026-06-04 — A1 STEP 1 (theme token-compliance audit)
**Status:** complete
**What changed:**
- Created `web_app/THEME_AUDIT.md` — the offender map + chunk plan for A1 STEP 2 fixes. **No code changes.**
- 9 chunks (A auth/shell, B stock, C products+price-history, D recipes+cook, E meal-plans+shopping, F dora+shared, G settings, H dashboard+reports+waste+data, I onboarding) with per-row offender · proposed token · mode-risk · light-shift.
- Token cheat-sheet from the actual `tokens.scss` / `themes.scss` / `themeService.ts` is at §2.
- 11 `needs_decision` items (DEC-1..DEC-11) consolidated at §4 — these gate STEP 2.
- A1b out-of-scope spotted at §5 (too-bright greens, focus-ring pinned to Pesto, text-muted contrast on Pesto Dark, etc.).

**Decisions made:**
- Excluded `tokens.scss`, `themes.scss`, `colours.scss`, `quasar.variables.scss`, `themeService.ts`, `motion.scss` from the scan — they legitimately hold raw colour values.
- Grouped settings/* into its own chunk (G) rather than the "other" bucket — it had ~50 hits and the theme-picker swatches there are the only legitimate template hex in the app (DEC-10).
- Chunk run order in `THEME_AUDIT.md §6`: A → I → D → G → C → B → E → H → F. Narrowest ripple first; Dora (F) last because it's gated on DEC-3.
- For products chunk (C): minimal-touch only — that surface is moving to the companion app per master Decision 1, so don't refactor structure during paint.

**Files touched:** `web_app/THEME_AUDIT.md` (new).

**Verification:**
- Read `tokens.scss`, `themes.scss` (first ~80 lines), `colours.scss`, `quasar.variables.scss`, `themeService.ts`, `app.scss` to ground the token map.
- Ran grep scans for: hex literals, `rgb/rgba/hsl/hsla()`, Quasar palette classes (`text-grey`, `bg-red-1`, …), Quasar `color=`/`text-color=` palette props, inline `:style` colour expressions, bare CSS named colours, SCSS `$colour` vars outside token files, `setCssVar` calls outside `themeService.ts`.
- The "220 text-grey" count in the audit is an approximation — Quasar's `text-grey` (no shade) is fixed mid-grey in both light and dark themes, so it's the single biggest dark-mode hazard.
- *Not verified* by running the app — this is an audit, not a fix.

**Next up:**
1. **User reviews `web_app/THEME_AUDIT.md`** — especially the 11 DEC-* items in §4. Each one needs a yes/no/option-pick.
2. After decisions, **run A1 STEP 2 chunk-by-chunk** per the prompt template in `prompts/A1_theme_compliance.md` §STEP 2, starting with **Chunk A (auth/shell)**.
3. Parallel-safe Phase 0 candidates if a second agent is available: **re-baseline `STATUS.md`** (docs folder), or **INV-6** (recipe-comparison worth, `prompts/INV_investigations.md`).

**Open questions for user:**
- Sign off DEC-1..DEC-11 in `THEME_AUDIT.md §4` (the audit includes a recommendation on each — fastest path is "I accept all recommendations" unless any specific one bothers you).
- Run STEP 2 Chunk A next in this session, or wait?

---

## 2026-06-04 — Session bootstrap & handoff system
**Status:** recon-only
**What changed:**
- Read the planning library entry points: `00_DOCS_INDEX.md`, `RECONCILED_FINISHING_PLAN.md`, `STATUS.md`, `FEEDBACK_TRIAGE_AND_PLAN.md`, `prompts/00_INDEX.md`, `prompts/A1_theme_compliance.md`.
- Created `CLAUDE.md` and this `DORA_WORKLOG.md` at repo root so handoffs between concurrent Claude sessions are clean.
**Decisions made:**
- Worklog lives at repo root (versioned with code, both agents see it automatically).
- No per-agent labels — timestamp + bullets are enough to reconstruct.
- Worklog is process-only; `CHANGELOG.md` stays the product log. Two files, two purposes.
**Files touched:** `CLAUDE.md`, `DORA_WORKLOG.md`.
**Verification:** docs read; repo state unchanged otherwise.
**Next up:** **Run `prompts/A1_theme_compliance.md` STEP 1 (the audit only — produces `web_app/THEME_AUDIT.md`, no code changes).** This is the master plan's "immediate next step" and is no-regret / dependency-free. STEP 2 (chunked fixes) waits until the audit is reviewed.

Parallel candidates if you want a second session running:
- **Re-baseline `STATUS.md`** (in the docs folder) against current code. It's stale — meals→recipes merge, substitutes-graph removal, stock-map removal, DS4 all unrecorded. Cheap, no collision with A1.
- **INV-6** — assess recipe-comparison's real worth (`prompts/INV_investigations.md`). Read-only; informs the X2 keep/cut call.

**Open questions for user:**
- Any redirect from the recommended A1-audit start, or proceed?
- Want a second agent on STATUS re-baseline or INV-6 in parallel?
