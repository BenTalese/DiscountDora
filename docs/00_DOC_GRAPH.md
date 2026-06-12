# Doc Graph — required reading per prompt

Cross-reference map. Before executing any prompt in `03_prompts/`, open its row
below and read every cited doc. Purpose: prevent drift, surface adjacent
constraints, and connect each isolated prompt back to the charter, feedback, and
open follow-ups.

## How to use

1. Find your prompt's section below.
2. Read the cited docs in order: Charter anchors → Feedback bullets → Related
   proposals → Related investigations → Original spec → Open follow-ups →
   Removed-features watchlist.
   - **Engineering rules are not per-prompt-cited on purpose.** The full
     `R-001..R-0NN` list in `01_charter/ENGINEERING_STANDARDS.md` is checked
     against **every** task (see the close-gate in `CLAUDE.md`). Cherry-picking
     a subset here would invite skipping the others — read the whole rule
     list, every time.
3. If a cited doc contradicts the prompt body, the cited doc usually wins —
   verify with the user before proceeding. Order of authority: Charter >
   Reconciled Plan > current feedback > engineering standards > proposals >
   prompt body > original spec > status doc.
4. Log any newly-discovered cross-link as a `DORA_FOLLOWUPS.md` finding so this
   file can be updated.

## Legend

- **Charter principles**: numbered P1–P12 from
  `01_charter/DASHY_DORA_CHAMPION_PLAN.md` Part II, one-word labels:
  P1 Effortless · P2 Coarse · P3 Honest · P4 Personal · P5 Loop · P6
  One-action · P7 Preview/undo · P8 Ownership · P9 No-scrape · P10
  Anti-creep · P11 Fast · P12 No-invent. Tie-break = P1 + P10.
- **Engineering rules**: the full `R-001..R-0NN` list in
  `01_charter/ENGINEERING_STANDARDS.md` is checked against every task by
  the standing close-gate; not enumerated per prompt here on purpose
  (avoids implying a subset is enough — read the whole list every time).
- **Feedback bullets**: the master feedback doc
  `02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md` uses
  **surface-headed bullet lists**, not numbered IDs. References below
  cite **surface headings** (e.g. `§STOCK OVERVIEW`) and quote a short
  phrase to anchor the relevant bullet. The coverage table in
  `02_feedback/COVERAGE_GAPS.md` records the same homing decisions.
- **Follow-ups**: `FU-NNN` from `DORA_FOLLOWUPS.md` (open only,
  resolved items omitted unless the trail matters).

## Universal pre-flight (every prompt)

Always read first, regardless of prompt:

- `CLAUDE.md` — session protocol.
- `docs/01_charter/DASHY_DORA_CHAMPION_PLAN.md` Part II — the 12 principles +
  Effortless/Anti-creep tiebreak.
- `docs/01_charter/ENGINEERING_STANDARDS.md` — full `R-001..R-010` rule list
  (close-gate; every task is evaluated against every rule).
- `docs/01_charter/RECONCILED_FINISHING_PLAN.md` §7 (Decisions) + §7.5
  (distribution-posture checklist).
- `docs/00_DOCS_INDEX.md` — taxonomy, the canonical "REMOVED features — do
  not reintroduce" list.
- `DORA_WORKLOG.md` last entry — handoff state.
- `DORA_FOLLOWUPS.md` `[OPEN]` items matching this prompt's surface.

Then the per-prompt list below.

---

## Wave A — Foundations

### A1 — Theme token-compliance
- **Surface:** app-wide styling
- **Charter principles:** P11 Fast (consistent visual baseline), P10
  Anti-creep (one token system not 15 hand-rolled palettes), P3 Honest
  (dark mode must actually work).
- **Feedback bullets:**
  - `§SPLASH` "page following system theme for background".
  - `§CANNOT CONNECT / INITIAL LOAD` "Same styling as login".
  - `§DASHBOARD` "Dark mode not working".
  - `§PRODUCT SEARCH` "search bar … white on white in dark mode";
    "loading area … not theme aware"; "bottom of the product card not
    theme aware"; "green chips in pesto … hard to read".
  - `§PRODUCT HISTORY` "hover bubble is not theme aware".
  - `§RECIPES OVERVIEW` "comparison chips not theme aware".
  - `§COOK MODE` "Timer component is not theme aware".
  - `§RECIPE DETAIL` "cookable now box of info is not theme aware".
  - `§MEAL PLANS` "elements not theme aware … day headers".
  - `§NO AREA / MISC` "404 page is not in theme"; "a lot of text isn't
    visible in either light/dark mode".
- **Related proposals:** none direct; this prompt produces
  `web_app/THEME_AUDIT.md` which A1b reads.
- **Related investigations:** none.
- **Original spec:** `00_original_spec/Feature Boards/User & Global
  Options.md` (where the theme picker first lived) — historical only.
- **Open follow-ups:** **FU-046** (A1 chunks D–F regressed); FU-010
  (late-game holistic theme review); FU-003 (other light themes
  `--text-muted` contrast); FU-004 (collapse `themeService.ts` THEMES
  dict into CSS-var reads); FU-002 (LoginPage `--lp-*` ladder).
- **Removed-features watchlist:** none adjacent (the theme work
  touches removed surfaces like substitute graph only via dead CSS).
- **Cross-prompt dependencies:** **must precede A1b, A2, A3, A5, A6,
  A7**; coordinate with B7 (toast styling) and B9 (404 re-skin uses
  tokens A1 establishes).

### A1b — Token value tuning
- **Surface:** app-wide styling (token files only)
- **Charter principles:** P11 Fast (legibility), P3 Honest (contrast),
  P10 Anti-creep (values only, no component churn).
- **Feedback bullets:**
  - `§NO AREA / MISC` "button colours in pesto for some buttons feel
    too bright … notice this particularly on the green ones".
  - `§PRODUCT SEARCH` "green chips in pesto … too hard to read".
  - `§RECIPE DETAIL` "cookable (green) is too bright … Well-stocked
    chip has same issue".
- **Related proposals:** none.
- **Related investigations:** none.
- **Original spec:** none material.
- **Open follow-ups:** **FU-046** (A1 regression scope informs which
  values matter); FU-010 (holistic review will likely revisit these).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** **depends on A1** completing first
  (every component on tokens). Independent of all B prompts.

### A2 — Standard button + toolbar + "create" placement
- **Surface:** app-wide chrome
- **Charter principles:** P11 Fast (consistent affordances), P10
  Anti-creep (one button standard, exceptions only with purpose).
- **Feedback bullets:**
  - `§STOCK OVERVIEW` "All buttons should be the same width and height
    … standard toolbar with a standard toolbar button".
  - `§MY PRODUCTS` "Bulk select button … should be part of the
    toolbar"; "Buttons aren't that many, can move to the card and
    remove ellipses".
  - `§RECIPES OVERVIEW` "Create recipe button in different placement
    … should be consistent across every page".
  - `§RECIPE DETAIL` "Buttons feel all over the place".
- **Related proposals:** `04_proposals/PROPOSAL_STOCK_OVERVIEW.md`
  (consumes the standard); `04_proposals/PROPOSAL_CART_BUTTON.md` (built
  *on* the base, not folded into it); `04_proposals/PROPOSAL_COOKBOOK.md`
  (toolbar lands here).
- **Related investigations:** none.
- **Original spec:** none material.
- **Open follow-ups:** **FU-006** (~289 `q-btn` still to migrate);
  FU-005 (`q-btn-dropdown` / split-button wrapper).
- **Removed-features watchlist:** none adjacent.
- **Cross-prompt dependencies:** depends on A1; precedes A7 (sticky
  footer uses the button) and every C-prompt that lands new toolbars.

### A3 — Standard modal behaviour
- **Surface:** dialogs app-wide
- **Charter principles:** P7 Preview/undo (no silent commits on
  backdrop click); P10 Anti-creep (one dialog standard).
- **Feedback bullets:**
  - `§RECIPES OVERVIEW` "Inconsistent with add stock item modal,
    cannot click out of it to cancel".
  - `§COOK MODE` "Finished cooking modal … clicking out does not
    cancel".
  - `§RECIPE DETAIL` "Unsaved changes modal … no 'cancel', also
    clicking out of the modal closes and navigates anyways".
  - `§RECIPE DETAIL` "Can't click out of the delete confirmation to
    cancel".
- **Related proposals:** none direct; every C-proposal assumes A3 lands.
- **Related investigations:** none.
- **Original spec:** none material.
- **Open follow-ups:** **FU-021** (confirm reported modal bug did NOT
  reproduce); **FU-007** (eyeball A3 modals in a real browser);
  FU-008 (unify dialog chrome via `BaseDialog` slots); FU-009 (fate
  of 3 specialised overlays vs BaseDialog).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** depends on A1 (tokens), helped by
  A2 (Cancel/Confirm buttons use the standard).

### A4 — Filter system standardisation + "empty = off" bug
- **Surface:** stock overview, product search, my products, recipes (Cookbook)
- **Charter principles:** P11 Fast (single shared filter UX); P3 Honest
  (empty filter must mean "off", not "exclude everything"); P10
  Anti-creep.
- **Feedback bullets:**
  - `§STOCK OVERVIEW` "Add a filter button that shows filters, hidden
    by default … Filter button changes based on filter state".
  - `§PRODUCT SEARCH` "filter labels … messy/hard to read"; "Empty
    should be the same as filter off"; "It's not obvious when a filter
    is applied".
  - `§MY PRODUCTS` "Filter clear button is different to other screens
    with its behaviour"; "should filter button be active by default on
    desktop, and hidden/disabled on mobile".
  - `§RECIPES OVERVIEW` "Filters should work the same here as on other
    pages … same filter issues … deleting input filters incorrectly".
- **Related proposals:** `04_proposals/PROPOSAL_STOCK_OVERVIEW.md` §
  filter behaviour; `04_proposals/PROPOSAL_COOKBOOK.md` § filters.
- **Related investigations:** none.
- **Original spec:** none material.
- **Open follow-ups:** **FU-022** (confirm reported filter bug did NOT
  reproduce); FU-012 (FilterBar panel has no visual container);
  FU-013 (multi-select control only partial); FU-011 (AuditLogSettings
  filtering not standardised).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** depends on A1, A2; precedes the C-1
  Stock Overview and C-4 Cookbook redesigns.

### A5 — One loading / skeleton component
- **Surface:** app-wide loading states
- **Charter principles:** P11 Fast (perceived speed via skeletons);
  P10 Anti-creep (one component); P3 Honest (no fake "Stock Item"
  placeholder text).
- **Feedback bullets:**
  - `§NO AREA / MISC` "Long loading areas are given a loading ghost
    effect … should replace things like stock item detail view showing
    'Stock Item' while it's still loading".
  - `§PRODUCT SEARCH` "Whatever icon is being used for the very first
    loading pulse … use that for every place there is loading".
- **Related proposals:** none direct.
- **Related investigations:** `05_investigations/STOCK_OVERVIEW_PERF.md`
  (DS4 changed *perceived* perf; skeletons reinforce that win).
- **Original spec:** none material.
- **Open follow-ups:** **FU-023** (A5 leftover: spinners not yet
  migrated on deferred surfaces).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** depends on A1.

### A6 — Text-size scale + global application
- **Surface:** typography app-wide
- **Charter principles:** P11 Fast (legibility); P3 Honest (the
  preference must actually do something); P8 Ownership (user pref
  honoured).
- **Feedback bullets:**
  - `§NO AREA / MISC` "Default text size in some areas feels way too
    small … change between small medium and large text size is also
    not much difference. I was expecting 75%, 100%, 150% scaling".
  - `§DORA BOT` "Some text does not change size as per the user
    settings".
- **Related proposals:** none direct.
- **Related investigations:** none.
- **Original spec:** none material.
- **Open follow-ups:** **FU-025** (eyeball A6 scale on dense screens).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** depends on A1.

### A7 — Componentised sticky footer for page counts
- **Surface:** stock overview, my products, recipes (Cookbook)
- **Charter principles:** P11 Fast (counts always visible without
  clutter); P10 Anti-creep.
- **Feedback bullets:**
  - `§STOCK OVERVIEW` "Counts should be minified and moved to the bottom
    of the page as a sticky footer".
  - `§MY PRODUCTS` "Info at the top of the page is so hidden and tiny
    … Move to be consistent with stock page design, as the sticky
    footer".
  - `§RECIPES OVERVIEW` "Same issue with page info at the top, should
    be a componentised sticky footer".
- **Related proposals:** `04_proposals/PROPOSAL_STOCK_OVERVIEW.md` § footer.
- **Related investigations:** none.
- **Original spec:** none material.
- **Open follow-ups:** **FU-024** (A7 leftovers: dead banner CSS +
  wider footer adoption).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** depends on A1, A2; consumed by C-1.

### A8 — Renames + remove refresh buttons + nav-state policy
- **Surface:** strings, nav chrome, list-page state
- **Charter principles:** P10 Anti-creep (kill refresh buttons); P11
  Fast (predictable nav state).
- **Feedback bullets:**
  - `§NO AREA / MISC` "Let's rename everywhere to Dashy Dora".
  - `§RECIPES OVERVIEW` "'Mark made' everywhere sounds odd... make it
    'Mark Cooked'"; "Should be called 'Cookbook' anywhere the page
    itself is mentioned".
  - `§DORA BOT` "Let's call Dorabot 'D.O.R.A.'".
  - `§DASHBOARD` / `§STOCKTAKE MODE` / `§MY PRODUCTS` "How useful is
    the refresh really?".
  - `§PRODUCT SEARCH` "The state of the page seems to be remembered
    after navigating away … assess and fix this for each screen".
- **Related proposals:** none direct; the rename lands the P8-01
  spirit ahead of P8-01 itself.
- **Related investigations:** none.
- **Original spec:** none material.
- **Open follow-ups:** **FU-031** (B9.3 stale "Recipes" labels after A8
  cookbook rename); **FU-015** (Onboarding tour "Alerts" card points at
  stock).
- **Removed-features watchlist:** none, but **be aware** the "Discount
  Dora" rename is itself a planned prompt P8-01 — A8 is the user-facing
  copy pass, code identifiers stay until P8-01.
- **Cross-prompt dependencies:** independent (do after naming decisions
  agreed).

---

## Wave B — Bug clusters

### B1 — Extra-forbid payloads (product save/link/quick-add/inactive)
- **Surface:** product API + product/my-products UI
- **Charter principles:** P7 Preview/undo (silent 422s are not honest);
  P10 Anti-creep.
- **Feedback bullets:**
  - `§PRODUCT SEARCH` "Cannot save products: Extra inputs are not
    permitted" (× several actions).
  - `§MY PRODUCTS` "Cannot mark products inactive: Extra inputs are
    not permitted"; "Link to a stock item same issue".
- **Related proposals:** `04_proposals/PROPOSAL_CART_BUTTON.md`
  (link-also-saves-product is a cart-button decision-tree branch).
- **Related investigations:** none.
- **Original spec:** `00_original_spec/Feature Boards/Products.md` —
  historical only.
- **Open follow-ups:** **FU-014** (B1: confirm `image` field
  round-trips for product create).
- **Removed-features watchlist:** **product/real-world barcodes for
  deal lookup** is removed (P6-02) — when fixing product create, do not
  re-add `StockItem.barcode` or deal-lookup paths.
- **Cross-prompt dependencies:** independent.

### B3 — PATCH semantics (can't save unless name changes)
- **Surface:** stock-item + recipe update handlers
- **Charter principles:** P7 Preview/undo; P3 Honest.
- **Feedback bullets:**
  - `§STOCK ITEM DETAIL` "Cannot edit unless I change the stock item
    name … it should be a PATCH, not a PUT".
  - `§RECIPE DETAIL` "Cannot save recipe for same reason cant save
    stock item".
- **Related proposals:** none direct.
- **Related investigations:** none.
- **Original spec:** none material.
- **Open follow-ups:** **FU-017** (B3 user re-test).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** independent.

### B4 — Delete stock item → FK constraint failed
- **Surface:** stock-item delete (backend + UI)
- **Charter principles:** P7 Preview/undo (preview consequences); P3
  Honest (accurate counts, not "dangling reference" hand-wave).
- **Feedback bullets:**
  - `§STOCK ITEM DETAIL` "Deleting stock item does not work. Server
    error. 'sqlalchemy.exc.IntegrityError: FOREIGN KEY constraint
    failed'".
- **Related proposals:** none direct.
- **Related investigations:** `05_investigations/ORPHANED_FIELDS_AUDIT.md`
  (maps fields/relationships that delete must respect).
- **Original spec:** none material.
- **Open follow-ups:** **FU-035** (overview hides items past page 1 —
  reproducing delete behaviour at scale needs this fixed too).
- **Removed-features watchlist:** **substitute graph** removed — do
  not expect its tables when mapping FK refs. **Stock map** removed.
- **Cross-prompt dependencies:** independent.

### B5 — Dead nav buttons (onboarding / dashboard / alerts → 404)
- **Surface:** onboarding wiring + dashboard banner + alerts nav
- **Charter principles:** P6 One-action (every UI lead → real
  destination); P3 Honest.
- **Feedback bullets:**
  - `§ONBOARDING` "Skip everything button does nothing"; "finish button
    does nothing"; "'Show me X' on all the cards … are non-functional".
  - `§DASHBOARD` "Skipped setup wizard … continue button does nothing".
  - `§DASHBOARD` "Alerts navigation is broken (goes to 404)".
- **Related proposals:** `04_proposals/PROPOSAL_ONBOARDING.md` (C-5 is
  the full redesign — B5 is just the stopgap wiring);
  `04_proposals/PROPOSAL_ALERTS.md` (alerts target).
- **Related investigations:** none.
- **Original spec:** none material.
- **Open follow-ups:** **FU-015** (Onboarding tour "Alerts" card points
  at stock, not `/alerts`); **FU-016** (audit other "frontend cache vs
  backend mutation" races — the onboarding dead button was one).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** independent; C-5 and C-9 will redo
  these surfaces but B5 keeps them usable in the meantime.

### B7 — Notification / toast defects
- **Surface:** toast layer, stocktake + meal-plans surfaces
- **Charter principles:** P3 Honest (no placeholder strings in
  production); P6 One-action (one accurate toast, not two contradictory).
- **Feedback bullets:**
  - `§MEAL PLANS` "'I'm a notification!' … I don't want to see anything
    like demo/example/placeholder stuff anywhere in the app".
  - `§STOCKTAKE MODE` "two toasts at the same time. '0 added, 1 already
    on list' and 'brazil nuts added to your primary list'".
- **Related proposals:** `04_proposals/PROPOSAL_CART_BUTTON.md` (the
  deeper "button should know list state" lives there).
- **Related investigations:** none.
- **Original spec:** none material.
- **Open follow-ups:** **FU-038** (cart button fires contradictory
  double-toast on already-on-list); **FU-018** (wider sweep for "store
  mutation + page toast" double-emits).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** independent.

### B8 — Recipe detail dead/wrong actions
- **Surface:** recipe detail page (post meals→recipes merge)
- **Charter principles:** P3 Honest (substitute swap must not silently
  mutate the saved recipe); P6 One-action; P10 Anti-creep (remove
  references to the removed substitutes graph).
- **Feedback bullets:**
  - `§RECIPE DETAIL` "Remove recipe from favourites does nothing";
    "Clicking recipes does not navigate correctly"; "None of the recipe
    actions do anything, except cook button"; "Why does selecting a
    substitute completely swap and edit the recipe?"; "Mentions the
    substitutes graph but this is a deleted feature".
- **Related proposals:** `04_proposals/PROPOSAL_COOKBOOK.md` (C-4 is
  the full redesign); `04_proposals/PROPOSAL_COOK_MODE.md` (cook-mode
  is the *correct* home for temporary substitute swaps).
- **Related investigations:** `05_investigations/SUBSTITUTE_SWAP_ASSESSMENT.md`
  (INV-8 — the list-level substitute swap fate).
- **Original spec:** `00_original_spec/Feature Boards/Recipes.md` —
  historical only.
- **Open follow-ups:** **FU-019** (B8 reported defects that did NOT
  reproduce); **FU-020** (recipe-detail substitute swap affordance —
  cook-mode-only for now?).
- **Removed-features watchlist:** **substitute graph** removed (the
  standalone `/substitutes` page / `SubstitutesGraph.vue`); the
  per-item substitutes list and cook-session swap survive — do not
  reintroduce the graph page.
- **Cross-prompt dependencies:** independent; pairs naturally with
  C-3/C-4.

### B9 — Misc global bugs
- **Surface:** shopping-list drag/drop, main menu, settings nav,
  ~~command palette~~ (retired 2026-06-12), undo stack, product
  history, logging, mobile Dora, 404 page.
- **Charter principles:** P3 Honest, P6 One-action, P11 Fast.
- **Feedback bullets:**
  - `§SHOPPING LIST DETAILS VIEW` "Drag and drop is an index off
    somehow".
  - `§NO AREA / MISC` "Main menu button hover (inactive) has double
    outline"; "Settings is shown in both main menu and the user
    dropdown"; "Undo cross-app seems off"; "Command palette (ctrl + k)
    doesnt work with some stuff like create stock item"; "404 page is
    not in theme"; "logs … 46539 lines long … not rolling properly".
  - `§PRODUCT HISTORY` "Can select products but no change occurs";
    "hover bubble is not theme aware"; "Price history graph does not
    extend to the edge".
- **Related proposals:** none direct.
- **Related investigations:** `05_investigations/LOGGING_AND_DATA_LAYOUT.md`
  (B9.7 log rotation).
- **Original spec:** none material.
- **Open follow-ups:** **FU-027** (B9.7 log-rotation decision); FU-028
  (B9.1 shopping-list drag-drop); ~~FU-029 (B9.4 command palette)~~
  (RESOLVED 2026-06-12 — palette retired); FU-030 (B9.9 404 page —
  RESOLVED 2026-06-12, redesigned); FU-026 (B9.5 undo behaves oddly).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** mostly independent; B9.5 (undo) ↔
  state-ownership scope (server-owned audit removes some client undo
  races).

---

## INV — Investigations

### INV-1 — Orphaned-field audit
- **Surface:** all domain entities + DTOs
- **Charter principles:** P10 Anti-creep (dead weight goes); P3 Honest.
- **Feedback bullets:** `§STOCK ITEM DETAIL` "What else in the app is
  like this? Field exists but no way to set it/interact with it";
  `§STOCK ITEM DETAIL` notes on stock groups, preferred merchant,
  notes.
- **Related proposals:** `04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md`
  (will own the surfaces that wire some orphaned fields).
- **Related investigations:** `05_investigations/ORPHANED_FIELDS_AUDIT.md`
  (this prompt's output).
- **Original spec:** all Feature Boards in `00_original_spec/Feature
  Boards/` may explain original intent of orphaned fields.
- **Open follow-ups:** **FU-033** (`StockItem.image`); **FU-034**
  (`StockItemSubstitute.notes`); **FU-039** (`Recipe.image`).
- **Removed-features watchlist:** confirm no dead **substitute graph
  / stock map / `StockItem.barcode`** fields are reintroduced — surface
  any survivors here for removal.
- **Cross-prompt dependencies:** independent; informs C-1, C-4, C-cross.

### INV-2 — Stock-overview perf + DS4 change
- **Surface:** stock overview load
- **Charter principles:** P11 Fast; P3 Honest (don't claim DS4 made it
  faster if it just felt that way).
- **Feedback bullets:** `§STOCK OVERVIEW` "Navigation to this page has
  a noticeable delay between 1 to 3 seconds … no longer feels laggy
  like it used to. What happened?".
- **Related proposals:** `04_proposals/STATE_OWNERSHIP_REFACTOR_PROPOSAL.md`
  (server aggregates remove per-row O(N) lookups).
- **Related investigations:** `05_investigations/STOCK_OVERVIEW_PERF.md`
  (this prompt's output).
- **Original spec:** none material.
- **Open follow-ups:** **FU-035** (overview silently shows only first 50
  items — found by this investigation).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** feeds C-1.

### INV-3 — Logging & .local folder layout
- **Surface:** logging + on-disk data layout
- **Charter principles:** P8 Ownership (user owns + can find data);
  P3 Honest (logs that don't roll lie about recency).
- **Feedback bullets:** `§NO AREA / MISC` ".local folder so messy …
  logs are in two different locations … 46539 lines long … wrong
  date".
- **Related proposals:** none direct.
- **Related investigations:** `05_investigations/LOGGING_AND_DATA_LAYOUT.md`.
- **Original spec:** none material.
- **Open follow-ups:** **FU-027** (B9.7 log-rotation model decision);
  **FU-037** (`.secret_key` hardcoded to `./data/`, ignores `DORA_DATA_DIR`).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** feeds B9.7.

### INV-4 — Forgot-password email wiring
- **Surface:** auth + email
- **Charter principles:** P8 Ownership; P10 Anti-creep (degrades
  gracefully when SMTP unset).
- **Feedback bullets:** `§LOGIN / REGISTRATION / FORGOT` "How does
  sending of the email for forgotten password work? … Implementation
  of this must be flexible".
- **Related proposals:** `04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md`
  (feature-flag panel home).
- **Related investigations:** `05_investigations/EMAIL_SETUP_FINDINGS.md`;
  `05_investigations/AUTH_ASSISTANT_SECURITY_FINDINGS.md` (CSRF / email
  change adjacent).
- **Original spec:** none material.
- **Open follow-ups:** none specific.
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** feeds C-5 (onboarding admin SMTP setup).

### INV-5 — Feature clarifications (QR vs barcode, relevancy, expiry↔open)
- **Surface:** stock detail QR/barcode, product search, expiry model
- **Charter principles:** P10 Anti-creep; P3 Honest.
- **Feedback bullets:** `§STOCK ITEM DETAIL` "How does show QR code
  and register barcode work? Are they different features?"; "Is there
  any relationship between expiry and open?"; `§PRODUCT SEARCH` "How
  does the relevancy filter work? Is it working well?".
- **Related proposals:** `04_proposals/PROPOSAL_BARCODE_SCANNING.md`
  (the canonical home for the QR/barcode answer; gated by
  `scanning_enabled`).
- **Related investigations:** `05_investigations/FEATURE_CLARIFICATIONS.md`.
- **Original spec:** `00_original_spec/Feature Boards/Stock Items.md` —
  may carry original QR intent.
- **Open follow-ups:** **FU-056** (P6-02 deferred register-against-product
  UI); **FU-057** (P6-02 browser-verify gated scanning).
- **Removed-features watchlist:** **real-world barcode deal lookup**
  removed (P6-02); `StockItem.barcode` column dropped. Do not advocate
  reintroduction.
- **Cross-prompt dependencies:** feeds C-1 (scan mode) and C-6/C-8
  companion (relevancy filter belongs there).

### INV-6 — Recipe-comparison worth
- **Surface:** Cookbook
- **Charter principles:** P10 Anti-creep (the canonical "keep/cut"
  test); P5 Loop.
- **Feedback bullets:** `§RECIPES OVERVIEW` "Recipe comparison tool in
  its current state feels useless. Is there any way to make this more
  useful?"; `§RECIPES OVERVIEW` "Recipe comparison chips are not theme
  aware".
- **Related proposals:** `04_proposals/PROPOSAL_COOKBOOK.md` (defers to
  INV-6 outcome).
- **Related investigations:** `05_investigations/RECIPE_COMPARISON_ASSESSMENT.md`.
- **Original spec:** `00_original_spec/Feature Boards/Recipes.md` —
  may explain original comparison intent.
- **Open follow-ups:** none specific (CUT decision propagated into C-4).
- **Removed-features watchlist:** **product comparison** is companion
  scope, not Dora-core — don't confuse the two.
- **Cross-prompt dependencies:** gates C-4 comparison decision.

### INV-7 — History tab worth
- **Surface:** stock item detail History tab
- **Charter principles:** P10 Anti-creep; P5 Loop.
- **Feedback bullets:** `§STOCK ITEM DETAIL` "the history tab as-is
  feels unuseful. Maybe if it had a bit more data/info … I'd need to
  be convinced".
- **Related proposals:** none direct.
- **Related investigations:** `05_investigations/HISTORY_TAB_ASSESSMENT.md`.
- **Original spec:** `00_original_spec/Feature Boards/Stock Items.md` —
  may explain original history intent.
- **Open follow-ups:** none specific.
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** feeds A-1 stock-item-detail Bucket-A
  brief if/when written.

### INV-8 — Substitute swap-into-list behaviour
- **Surface:** shopping list line · stock-item substitutes
- **Charter principles:** P10 Anti-creep; P5 Loop.
- **Feedback bullets:** `§STOCK ITEM DETAIL` "Swap into list for
  substitutes feels like a weird feature. Would it even get used?".
- **Related proposals:** `04_proposals/SHOPPING_LIST_REDESIGN_PROPOSAL.md`
  (the affordance lives in shopping-list detail); B8 makes cook-mode the
  *correct* substitute home.
- **Related investigations:** `05_investigations/SUBSTITUTE_SWAP_ASSESSMENT.md`.
- **Original spec:** none material.
- **Open follow-ups:** **FU-036** (confirm Shop Mode "Substitute" swaps
  offer-only — gates INV-8); **FU-020** (recipe-detail substitute
  affordance).
- **Removed-features watchlist:** **substitute graph** removed; the
  per-item substitutes list is kept.
- **Cross-prompt dependencies:** pairs with B8.

### ~~INV-9~~ — Command-palette worth — **SUPERSEDED / palette retired**
> **2026-06-12:** palette retired entirely (user decision after the
> SHRINK recommendation). FU-029 RESOLVED in the same move. The
> entry stays here as an audit-trail anchor; no future prompt
> should re-open it.
- **Surface:** ~~Ctrl-K palette~~ (no longer exists)
- **Charter principles:** P10 Anti-creep ✓ (cut won out over
  shrink).
- **Related investigations:** `05_investigations/COMMAND_PALETTE_ASSESSMENT.md`
  (OUTCOME banner at top of that file points back here).
- **Open follow-ups:** none — FU-029 RESOLVED.
- **Removed-features watchlist:** **command palette + `useCommands` +
  `useRecents`** — do not reintroduce. Keyboard-shortcut layer
  (`useShortcut`, `ShortcutsCheatsheet`) is **kept**.
- **Cross-prompt dependencies:** none.

### INV-10 — `essential` flag model
- **Surface:** stock-item flag + auto-generate shopping list
- **Charter principles:** P2 Coarse (is a boolean the right primitive
  vs derived "you buy every shop"?); P10 Anti-creep.
- **Feedback bullets:** `§STOCK ITEM DETAIL` "No way to set 'essential'
  that I can see. Might be missing it?".
- **Related proposals:** none direct.
- **Related investigations:** `05_investigations/ESSENTIAL_FLAG_FINDINGS.md`.
- **Original spec:** `00_original_spec/Feature Boards/Stock Items.md`.
- **Open follow-ups:** none specific.
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** feeds C-1 (stock overview filter set)
  and C-cross (whether "essential" is a user setting or derived).

---

## Wave C — Big-rock design briefs

### C-1 — Stock Overview redesign → `PROPOSAL_STOCK_OVERVIEW.md`
- **Surface:** stock overview page
- **Produces:** `04_proposals/PROPOSAL_STOCK_OVERVIEW.md`.
- **Charter principles:** P1 Effortless · P10 Anti-creep · P11 Fast.
- **Feedback bullets:** all of `§STOCK OVERVIEW` (top-area teardown,
  chip removal, row layout, scan mode, planned-meals metric, expiry
  buttons).
- **Related proposals:** `04_proposals/PROPOSAL_CART_BUTTON.md` (C-7);
  `04_proposals/PROPOSAL_BARCODE_SCANNING.md` (scan-mode gating);
  `04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md` (location-display zone
  policy); `04_proposals/PROPOSAL_MEAL_PLANS.md` (planned-meals
  metric).
- **Related investigations:** `05_investigations/STOCK_OVERVIEW_PERF.md`;
  `05_investigations/ORPHANED_FIELDS_AUDIT.md`;
  `05_investigations/ESSENTIAL_FLAG_FINDINGS.md`.
- **Original spec:** `00_original_spec/Feature Boards/Stock Items.md`.
- **Open follow-ups:** **FU-035** (only first 50 items); **FU-033**
  (`StockItem.image`); **FU-050** (broader "Out of Stock" name-match
  smell beyond cookability); **FU-052** (switch cookable surfaces to
  server query).
- **Removed-features watchlist:** **stock map** (locations is a simple
  tree — no spatial layout); **substitute graph** (per-item
  substitutes survive, the graph page does not); **`StockItem.barcode`**
  column dropped.
- **Cross-prompt dependencies:** consumes A2, A4, A7; depends on C-7
  cart-button design; informs A-1 stock-item-detail.

### C-2 — Meal Plans redesign → `PROPOSAL_MEAL_PLANS.md`
- **Surface:** meal plans page
- **Produces:** `04_proposals/PROPOSAL_MEAL_PLANS.md`.
- **Charter principles:** P1 Effortless · P5 Loop · P10 Anti-creep ·
  P11 Fast.
- **Feedback bullets:** all of `§MEAL PLANS` (templates, calendar
  widget, carousel, recurring, batch-vs-fresh, drag/tap, slot per
  entry, time-of-day taxonomy).
- **Related proposals:** `04_proposals/PROPOSAL_COOKBOOK.md`
  (recipes-with-amounts and the "available meals" pool);
  `04_proposals/PROPOSAL_COOK_MODE.md` (consumption closes the loop);
  `04_proposals/SHOPPING_LIST_REDESIGN_PROPOSAL.md` (generate-list
  step); `04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md` (money
  opt-in for budget; time-of-day taxonomy).
- **Related investigations:** none direct.
- **Original spec:** `00_original_spec/Feature Boards/Meals.md` (now
  merged into recipes); `Recipes.md`.
- **Open follow-ups:** **FU-032** (C-2 confirm B6 allocation works
  end-to-end in browser); FU-049 (RecipeDetailPage cookability
  reflects saved recipe).
- **Removed-features watchlist:** none direct, but note **meals as a
  page is gone** (merged into recipes) — do not rebuild a separate
  meals surface.
- **Cross-prompt dependencies:** depends on state-ownership impl
  (for allocation SSOT); pairs with C-4 (recipes are the unit), C-3,
  C-7.

### C-3 — Cook Mode redesign → `PROPOSAL_COOK_MODE.md`
- **Surface:** cook mode page
- **Produces:** `04_proposals/PROPOSAL_COOK_MODE.md`.
- **Charter principles:** P1 Effortless · P5 Loop (consumption is
  where the loop closes) · P3 Honest · P6 One-action.
- **Feedback bullets:** all of `§COOK MODE` (finish flow, headcount
  auto-adjust, grouping by location, tools, highlight vs tick, timer,
  voice "sous chef", celebration, "how many meals did you save?").
- **Related proposals:** `04_proposals/PROPOSAL_COOKBOOK.md` (tools,
  versions, structured steps — C-4 owns these);
  `04_proposals/PROPOSAL_ONBOARDING.md` (default headcount);
  `04_proposals/PROPOSAL_CART_BUTTON.md` (finish add-to-list);
  `04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md` (tools taxonomy).
- **Related investigations:** none direct.
- **Original spec:** `00_original_spec/Feature Boards/Recipes.md`.
- **Open follow-ups:** **FU-040** (C-4 should model structured recipe
  steps — C-3 depends on it).
- **Removed-features watchlist:** **substitute graph** removed
  (cook-session substitute swap stays — see B8).
- **Cross-prompt dependencies:** depends on C-4 structured steps; pairs
  with C-2.

### C-4 — Recipes / Cookbook redesign → `PROPOSAL_COOKBOOK.md`
- **Surface:** Cookbook (recipes overview + detail)
- **Produces:** `04_proposals/PROPOSAL_COOKBOOK.md`.
- **Charter principles:** P1 Effortless · P5 Loop · P10 Anti-creep
  (money/nutrition opt-in; comparison CUT).
- **Feedback bullets:** all of `§RECIPES OVERVIEW` + `§RECIPE DETAIL`
  (rename to Cookbook, tags, images, versions, multi-part, tools,
  source, URL import, cost, nutrition, comparison).
- **Related proposals:** `04_proposals/PROPOSAL_MEAL_PLANS.md` (C-2);
  `04_proposals/PROPOSAL_COOK_MODE.md` (C-3);
  `04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md` (money/nutrition opt-in;
  dietary/cuisine/category/tools taxonomies).
- **Related investigations:** `05_investigations/RECIPE_COMPARISON_ASSESSMENT.md`
  (INV-6 — comparison fate); `05_investigations/ORPHANED_FIELDS_AUDIT.md`
  (`Recipe.image`).
- **Original spec:** `00_original_spec/Feature Boards/Recipes.md`;
  `00_original_spec/Feature Boards/Meals.md`.
- **Open follow-ups:** **FU-039** (`Recipe.image`); **FU-040**
  (structured recipe steps).
- **Removed-features watchlist:** **product comparison** = companion
  scope (do not bring into Cookbook); recipe comparison = CUT per
  INV-6 — do not propose keeping it.
- **Cross-prompt dependencies:** gates C-3 (structured steps), pairs
  with C-2.

### C-5 — Onboarding redesign → `PROPOSAL_ONBOARDING.md`
- **Surface:** WelcomeWizard
- **Produces:** `04_proposals/PROPOSAL_ONBOARDING.md`.
- **Charter principles:** P1 Effortless (starter template = fastest
  path to value); P10 Anti-creep (no forced tour — C-help is the
  opt-in inverse); P8 Ownership.
- **Feedback bullets:** all of `§ONBOARDING`.
- **Related proposals:** `04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md`
  (first-login feature toggles mirror settings panel);
  `04_proposals/PROPOSAL_HELP_OVERLAY.md` (the opt-in inverse of a
  forced tour); `04_proposals/PROPOSAL_COOK_MODE.md` (default
  headcount feeds cook mode).
- **Related investigations:** `05_investigations/EMAIL_SETUP_FINDINGS.md`
  (admin SMTP setup).
- **Original spec:** all Feature Boards under `00_original_spec/Feature
  Boards/` — onboarding sells the whole product.
- **Open follow-ups:** **FU-041** ("you already have groups/locations"
  copy on first-run); **FU-015** (Onboarding tour Alerts card).
- **Removed-features watchlist:** none direct; the rename to "Dashy
  Dora" copy lives here ahead of P8-01 codebase rename.
- **Cross-prompt dependencies:** depends on C-cross (config + opt-ins
  + taxonomies); informs C-3 (headcount).

### C-6 — [COMPANION APP] Product Search perf & anti-blocking
- **Surface:** COMPANION APP — out of scope for Dora-core
- **Produces:** `PROPOSAL_SEARCH_PERF.md` in the companion repo (not
  this repo).
- **Charter principles:** P9 No-scrape (companion isolates the
  legally-risky scraping); P11 Fast.
- **Feedback bullets:** all of `§PRODUCT SEARCH` (companion home).
- **Related proposals:** `04_proposals/PROPOSAL_INGESTION_API.md`
  (C-10) — the seam C-6 targets back into Dora; this brief gates on
  C-10 landing.
- **Related investigations:** none in this repo.
- **Original spec:** `00_original_spec/Feature Boards/Products.md`.
- **Open follow-ups:** none in this repo's ledger (companion has its
  own).
- **Removed-features watchlist:** **central retailer scraping as a
  hosted service** is removed from Dora-core (P7-01) — survives only
  in the companion.
- **Cross-prompt dependencies:** gated by C-10; do not run in
  Dora-core.

### C-7 — Shopping-cart button → `PROPOSAL_CART_BUTTON.md`
- **Surface:** every "add to list" / cart control
- **Produces:** `04_proposals/PROPOSAL_CART_BUTTON.md` (already written).
- **Charter principles:** P1 Effortless (ask minimum questions); P6
  One-action; P10 Anti-creep; P11 Fast.
- **Feedback bullets:**
  `§STOCK OVERVIEW` cart-icon discussion;
  `§MY PRODUCTS` "Consider changes to shopping cart button … Can be
  componentised?"; `§MY PRODUCTS` standalone-product rule;
  `§RECIPE DETAIL` "shopping cart button on stock item row that could
  be componentised"; `§STOCKTAKE MODE` cart-button list-awareness;
  `§MEAL PLANS` "add individually, or add all in one go".
- **Related proposals:** `04_proposals/SHOPPING_LIST_REDESIGN_PROPOSAL.md`
  (target-list inference); `04_proposals/IMPL_PLAN_SHOPPING_LISTS.md`
  (when the contextual target lands).
- **Related investigations:** none direct.
- **Original spec:** `00_original_spec/Feature Boards/Shopping
  Lists.md`; `Products.md`.
- **Open follow-ups:** **FU-038** (cart button contradictory
  double-toast); FU-060 (Chunk 2 browser smoke — draft picker for
  cart).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** consumed by C-1, C-3, C-4 and B7/B8;
  depends on shopping-list status model (IMPL_PLAN_SHOPPING_LISTS).

### C-8 — [COMPANION APP] Merchant vs data-provider
- **Surface:** COMPANION APP
- **Produces:** `PROPOSAL_MERCHANT_PROVIDER.md` in the companion repo.
- **Charter principles:** P9 No-scrape; P3 Honest (label sources
  honestly into Dora via C-10's `source` field).
- **Feedback bullets:** `§PRODUCT SEARCH` "misunderstanding with
  merchants and merchant data providers".
- **Related proposals:** `04_proposals/PROPOSAL_INGESTION_API.md`
  (C-10) — the `source` label C-8 lands here.
- **Related investigations:** none in this repo.
- **Original spec:** `00_original_spec/Feature Boards/Products.md`.
- **Open follow-ups:** none in this repo's ledger.
- **Removed-features watchlist:** **central scraping as a hosted
  service** — companion-only.
- **Cross-prompt dependencies:** gated by C-10.

### C-9 — Alerts control centre → `PROPOSAL_ALERTS.md`
- **Surface:** alerts page + bell + dashboard alert card (contract only)
- **Produces:** `04_proposals/PROPOSAL_ALERTS.md`.
- **Charter principles:** P1 Effortless (as quiet as user wants); P6
  One-action; P10 Anti-creep.
- **Feedback bullets:** all of `§ALERTS`; `§DASHBOARD` alert card
  bullets; `§PRODUCT HISTORY` manage alerts button.
- **Related proposals:** `04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md`
  (per-type opt-in is a config editor).
- **Related investigations:** none direct.
- **Original spec:** `00_original_spec/Feature Boards/Alerts.md`.
- **Open follow-ups:** **FU-042** (Alerts bell count ≠ list count).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** B5 stopgaps the dead Alerts nav;
  this prompt removes the stopgap.

### C-10 — Ingestion-API contract → `PROPOSAL_INGESTION_API.md`
- **Surface:** Dora-core authenticated ingestion endpoint
- **Produces:** `04_proposals/PROPOSAL_INGESTION_API.md`.
- **Charter principles:** P9 No-scrape (Dora never calls out;
  sources call in); P4 Personal (feeds personal price history); P8
  Ownership; P12 No-invent.
- **Feedback bullets:** none directly (this is Dora-core architectural
  seam, not user-facing) — but enables `§PRODUCT SEARCH` work in the
  companion.
- **Related proposals:** `04_proposals/PROPOSAL_BARCODE_SCANNING.md`
  (P8-02 barcode-to-add via Open Food Facts also uses the seam shape).
- **Related investigations:** none direct.
- **Original spec:** `00_original_spec/Feature Boards/Products.md`.
- **Open follow-ups:** **FU-045** (Postgres migration); FU-053 (best
  deals card still fetches all products client-side — server seam
  needed).
- **Removed-features watchlist:** **central scraping** is the *reason*
  this seam exists — never reintroduce in-process scraping.
- **Cross-prompt dependencies:** **gates C-6 and C-8** (companion
  targets this contract); reused by P8-03 / P8-04.

### C-cross — Config, opt-ins & taxonomy settings → `PROPOSAL_CONFIG_AND_OPTINS.md`
- **Surface:** cross-cutting config layer (consumed by C-1/C-4/C-5/C-9)
- **Produces:** `04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md`.
- **Charter principles:** P10 Anti-creep (defaults off / hidden); P1
  Effortless; P8 Ownership.
- **Feedback bullets:**
  `§RECIPES OVERVIEW` cost-budget opt-in; tag taxonomy editors;
  `§RECIPE DETAIL` "Category should be like dietary tags";
  `§ONBOARDING` first-login feature enable/disable;
  `§STOCK OVERVIEW` location display "main zone, not 'right shelf'";
  `§ALERTS` per-type opt-in;
  `§RECIPE DETAIL` nutrition off/simple/complex.
- **Related proposals:** all five per-surface C-proposals defer to this
  one.
- **Related investigations:** `05_investigations/ESSENTIAL_FLAG_FINDINGS.md`
  (where "essential" UX setting lives).
- **Original spec:** `00_original_spec/Feature Boards/User & Global
  Options.md`.
- **Open follow-ups:** none specific (C-cross is the home for many
  config bullets).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** consumed by C-1, C-4, C-5, C-9;
  independent run otherwise.

### C-locale — Locale & international readiness → `PROPOSAL_LOCALE_I18N.md`
- **Surface:** currency, voice locale, AU-specific copy/seed
- **Produces:** `04_proposals/PROPOSAL_LOCALE_I18N.md`.
- **Charter principles:** P1 Effortless (currency-neutral); P10
  Anti-creep (full UI translation deferred); P8 Ownership.
- **Feedback bullets:** none directly (user-floated 2026-06-06) but
  intersects with `§PRODUCT SEARCH` (merchant logos) and
  `§DORA BOT` (voice locale default).
- **Related proposals:** `04_proposals/PROPOSAL_INGESTION_API.md`
  (whether C-10 price observations carry currency).
- **Related investigations:** none direct.
- **Original spec:** none material.
- **Open follow-ups:** **FU-043** (C-locale awaiting approval).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** independent; touches C-10.

### C-help — Opt-in contextual help overlay → `PROPOSAL_HELP_OVERLAY.md`
- **Surface:** cross-cutting help layer
- **Produces:** `04_proposals/PROPOSAL_HELP_OVERLAY.md`.
- **Charter principles:** P1 Effortless (opt-in, never forced); P10
  Anti-creep; P3 Honest (content rot prevention).
- **Feedback bullets:** none directly (user-floated 2026-06-06);
  intersects with `§HELP` content overhaul ask.
- **Related proposals:** `04_proposals/PROPOSAL_ONBOARDING.md` (C-5 is
  the inverse — C-help replaces the forced tour C-5 removed).
- **Related investigations:** none direct.
- **Original spec:** `00_original_spec/Feature Boards/Help, Guides &
  Assistant.md`.
- **Open follow-ups:** **FU-044** (C-help awaiting approval + per-surface
  hint rollout).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** lands content per-surface as
  C-1..C-9 ship.

---

## C-impl — Implementation-planning prompts

### IMPL — Shopping Lists → `IMPL_PLAN_SHOPPING_LISTS.md`
- **Surface:** shopping list status model + creation + shop mode +
  finish→restock
- **Produces:** `04_proposals/IMPL_PLAN_SHOPPING_LISTS.md`.
- **Charter principles:** P5 Loop · P3 Honest (server-owned audit;
  undo only where safe) · P7 Preview/undo.
- **Feedback bullets:** all of `§SHOPPING LISTS`, `§SHOPPING LIST
  DETAILS VIEW`, `§SHOPPING MODE`.
- **Related proposals:** source proposal
  `04_proposals/SHOPPING_LIST_REDESIGN_PROPOSAL.md`;
  `04_proposals/PROPOSAL_CART_BUTTON.md` (C-7 consumer of target
  inference); `04_proposals/IMPL_PLAN_STATE_OWNERSHIP.md` (lands
  before).
- **Related investigations:** none direct.
- **Original spec:** `00_original_spec/Feature Boards/Shopping
  Lists.md`.
- **Open follow-ups:** **FU-060** (Chunk 2 browser smoke); **FU-058**
  (resolved); **FU-059** (resolved — UUID-vs-str guard).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** depends on state-ownership impl
  landing first; consumed by C-7.

### IMPL — Cookbook → `IMPL_PLAN_COOKBOOK.md`
- **Surface:** recipe domain (overview filters, card, detail, versions,
  tools, images, source, structured steps, sections, cost, nutrition)
- **Produces:** `04_proposals/IMPL_PLAN_COOKBOOK.md`.
- **Charter principles:** P1 Effortless · P5 Loop (recipes = loop's hub) ·
  P10 Anti-creep (opt-in money/nutrition; comparison cut; substitute
  status skipped).
- **Feedback bullets:** all of `§RECIPES OVERVIEW` + `§RECIPE DETAIL`
  (L228-L315).
- **Related proposals:** source proposal `04_proposals/PROPOSAL_COOKBOOK.md`
  (decisions resolved §5a 2026-06-08); `04_proposals/PROPOSAL_COOK_MODE.md`
  (C-3 consumes Chunk 6 structured steps + Chunk 5 tools);
  `04_proposals/PROPOSAL_CART_BUTTON.md` (C-7 on ingredient rows L288);
  `04_proposals/IMPL_PLAN_STATE_OWNERSHIP.md` (cookability source-of-truth
  lands ahead).
- **Related investigations:** `05_investigations/RECIPE_COMPARISON_ASSESSMENT.md`
  (INV-6 — drives Chunk 1 comparison cut).
- **Original spec:** `00_original_spec/Feature Boards/Recipes.md`.
- **Open follow-ups:** **FU-039** (resolved by Chunk 5); **FU-040**
  (resolved 2026-06-08 — structured steps in Chunk 6); **FU-078**
  (resolved 2026-06-08 — this doc).
- **Removed-features watchlist:** **recipe comparison** (Chunk 1 cuts it,
  per INV-6).
- **Cross-prompt dependencies:** Chunk 6 **blocks** C-3 Chunk 5; Chunk 2
  + Chunk 5 + Chunk 9 depend on C-cross config surface (vocabularies +
  opt-ins); Chunks 4 + 7 consume A3 modal, A4 filter, A7 footer when they
  land.

### IMPL — Cook Mode → `IMPL_PLAN_COOK_MODE.md`
- **Surface:** cook mode page + recipe step model (C-4 ripple)
- **Produces:** `04_proposals/IMPL_PLAN_COOK_MODE.md`.
- **Charter principles:** P5 Loop (closes cook→consume) · P1 Effortless ·
  P6 One-action · P7 Preview/undo (finish dialog is preview→commit).
- **Feedback bullets:** all of `§COOK MODE` (L317-L338).
- **Related proposals:** source proposal
  `04_proposals/PROPOSAL_COOK_MODE.md` (decisions resolved §5a);
  `04_proposals/PROPOSAL_COOKBOOK.md` §2.6a (structured steps —
  co-sequenced as Chunk 4); `04_proposals/PROPOSAL_CART_BUTTON.md`
  (C-7 consumer at finish row).
- **Related investigations:** none direct.
- **Original spec:** `00_original_spec/Feature Boards/Recipes.md`.
- **Open follow-ups:** **FU-077** (resolved 2026-06-08 — this doc is
  what closes it).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** Chunk 5 blocked on Chunk 4 (C-4
  structured steps); Chunk 6 depends on C-5 onboarding headcount;
  Chunk 1 consumes C-7 cart button when available.

### IMPL — Cart Button → `IMPL_PLAN_CART_BUTTON.md`
- **Surface:** the unified add-to-list / cart control (every quick-add + bulk
  surface app-wide) + standalone-product shopping-list lines
- **Produces:** `04_proposals/IMPL_PLAN_CART_BUTTON.md`.
- **Charter principles:** P1 Effortless (minimum prompts) · P10 Anti-creep
  (one component, 13 → 1) · P11 Fast UX.
- **Feedback bullets:** the cart/add-to-list cluster — L83/L84/L108/L130/L154/
  L191/L195/L196/L288/L380/L381/L382.
- **Related proposals:** source proposal `04_proposals/PROPOSAL_CART_BUTTON.md`
  (decisions resolved §7a 2026-06-09); `04_proposals/SHOPPING_LIST_REDESIGN_PROPOSAL.md`
  + `IMPL_PLAN_SHOPPING_LISTS.md` (status model + draft inference — **landed**,
  powers Axis B); `IMPL_PLAN_STOCK_OVERVIEW.md` (C-1 row consumes this);
  `IMPL_PLAN_STATE_OWNERSHIP.md` (membership/`cartStateFor`).
- **Related investigations:** none direct.
- **Original spec:** `00_original_spec/Feature Boards/Shopping.md` (cart
  colour-on-add, quick-remove, swipe — proposal §9; swipe deferred).
- **Open follow-ups:** **FU-038** (cart double-toast — Chunk 1 closes it).
- **Removed-features watchlist:** no stored `is_primary` — draft inference only.
- **Cross-prompt dependencies:** Chunk 3 (standalone-product model) is the
  schema rock; consumed by C-1 (stock row), C-3 (cook-mode finish), recipe
  detail, My Products; couples L195 My-Products link affordance.

### IMPL — Stock Overview → `IMPL_PLAN_STOCK_OVERVIEW.md`
- **Surface:** stock overview (row, top area, filters, footer, detail nav,
  expiry, images, scan-mode, per-item metric)
- **Produces:** `04_proposals/IMPL_PLAN_STOCK_OVERVIEW.md`.
- **Charter principles:** P1 Effortless · P10 Anti-creep (kill the chip,
  net-less surface) · P11 Fast UX (most-used screen).
- **Feedback bullets:** all of `§STOCK OVERVIEW` (L63-L99).
- **Related proposals:** source proposal
  `04_proposals/PROPOSAL_STOCK_OVERVIEW.md` (decisions resolved §7a
  2026-06-09); `04_proposals/PROPOSAL_CART_BUTTON.md` (C-7 — row cart
  control, unbuilt); `04_proposals/IMPL_PLAN_STATE_OWNERSHIP.md`
  (server-owned status/counts); `04_proposals/IMPL_PLAN_COOKBOOK.md`
  Chunk 5 (image pattern reused for stock images / FU-033).
- **Related investigations:** `05_investigations/STOCK_OVERVIEW_PERF.md`
  (the 50-item-cap / virtualisation analysis — drives Chunk 1).
- **Original spec:** `00_original_spec/Feature Boards/Stock.md` (level
  button, footer summary, missing-picture placeholder — §6 of the proposal).
- **Open follow-ups:** **FU-035** (50-item cap — Chunk 1 closes it);
  **FU-033** (StockItem.image — folded into Chunk 6).
- **Removed-features watchlist:** stock map / spatial layout stays removed;
  scanning surface stays gated behind `scanning_enabled`.
- **Cross-prompt dependencies:** Chunk 3 hosts C-7 cart (placeholder until
  built); Chunk 6 needs FU-033; Chunk 8 (metric) gated on C-2 allocation;
  location display → C-cross.

### IMPL — Config & Opt-ins (C-cross) → `IMPL_PLAN_CONFIG_AND_OPTINS.md`
- **Surface:** cross-cutting config + per-user / install-wide opt-ins
  (money, nutrition, location-display, image-display, install feature
  flag panel). Taxonomy editors already shipped via C-4 Chunks 2 + 5
  (verify-only here).
- **Produces:** `04_proposals/IMPL_PLAN_CONFIG_AND_OPTINS.md` (drafted
  2026-06-10).
- **Charter principles:** P1 Effortless · P10 Anti-creep (defaults off
  for money/nutrition; defaults on for visual richness) · P8 Ownership
  (user picks visibility).
- **Feedback bullets:** the cross-cutting set from
  `PROPOSAL_CONFIG_AND_OPTINS.md §7` — L42 / L81 / L107 / L128 / L254
  / L262 / L263 / L287 / L321 / L441 plus the 2026-06-10 user ask
  (image-display opt-in).
- **Related proposals:** source proposal
  `04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md` (§4 decisions
  answered inline in the IMPL plan); the five per-surface
  C-proposals defer to this one.
- **Related investigations:** none direct.
- **Original spec:**
  `00_original_spec/Feature Boards/User & Global Options.md` (§6 of
  the proposal).
- **Open follow-ups:** **FU-090** folded into Chunk 5 (deferred-column
  fix for recipe-list image blobs); **FU-033** consumed as a no-op by
  Chunk 5's stock-image guard (no work pulled forward).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** **foundational** — consumed by
  C-4 Chunk 9 (money + nutrition gates), C-2 (plan budgets), C-1
  (location chip + stock images), C-5 (onboarding wizard feature
  step writes the install flags), C-9 (coarse alerts on/off may
  live here).

### IMPL — State ownership → `IMPL_PLAN_STATE_OWNERSHIP.md`
- **Surface:** server-owned domain facts (stock status, cookable,
  offer snapshots)
- **Produces:** `04_proposals/IMPL_PLAN_STATE_OWNERSHIP.md`.
- **Charter principles:** P3 Honest · P5 Loop · P12 No-invent (kill
  client recomputes that silently disagree).
- **Feedback bullets:** `§Technical Considerations` "I want to ensure
  there is single sources of truth for the front end data and
  operations".
- **Related proposals:** source proposal
  `04_proposals/STATE_OWNERSHIP_REFACTOR_PROPOSAL.md`;
  `04_proposals/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`
  (assistant deletes the *fourth* missing-ingredients copy);
  `04_proposals/IMPL_PLAN_SHOPPING_LISTS.md` (depends on this).
- **Related investigations:** `05_investigations/STOCK_OVERVIEW_PERF.md`
  (per-row O(N) lookups disappear with server aggregates).
- **Original spec:** none material.
- **Open follow-ups:** **FU-050** ("Out of Stock" name-match smell
  beyond cookability); **FU-052** (switch cookable surfaces to server
  query); **FU-051** (Chunks 3–5 not type-checked / browser-verified);
  **FU-049** (RecipeDetailPage cookability reflects saved recipe);
  **FU-047** (`confirm_actions._resolve_level` hardcoded names);
  **FU-048** (e2e suite pre-existing broken).
- **Removed-features watchlist:** none.
- **Cross-prompt dependencies:** lands *before* C-7, IMPL shopping
  lists, C-3, and the assistant refactor.

---

## Proposal → implementation cross-map

When implementing a proposal, read every doc in the right-hand column first.

| Proposal | Read-before list |
|---|---|
| `PROPOSAL_STOCK_OVERVIEW.md` | A2, A4, A7 prompts · `PROPOSAL_CART_BUTTON.md` · `PROPOSAL_BARCODE_SCANNING.md` · `PROPOSAL_CONFIG_AND_OPTINS.md` · `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` + `IMPL_PLAN_STATE_OWNERSHIP.md` · `STOCK_OVERVIEW_PERF.md` · `ORPHANED_FIELDS_AUDIT.md` · `ESSENTIAL_FLAG_FINDINGS.md` · FU-035, FU-033, FU-050 |
| `PROPOSAL_MEAL_PLANS.md` | `PROPOSAL_COOKBOOK.md` · `PROPOSAL_COOK_MODE.md` · `SHOPPING_LIST_REDESIGN_PROPOSAL.md` + `IMPL_PLAN_SHOPPING_LISTS.md` · `PROPOSAL_CONFIG_AND_OPTINS.md` · `IMPL_PLAN_STATE_OWNERSHIP.md` · FU-032, FU-049 |
| `PROPOSAL_COOK_MODE.md` | `PROPOSAL_COOKBOOK.md` (esp. §2.6a structured steps) · `PROPOSAL_ONBOARDING.md` · `PROPOSAL_CART_BUTTON.md` · `PROPOSAL_CONFIG_AND_OPTINS.md` · `IMPL_PLAN_COOK_MODE.md` (chunking + DEC resolutions) · FU-040 (RESOLVED — structured steps now in C-4) |
| `PROPOSAL_COOKBOOK.md` | `RECIPE_COMPARISON_ASSESSMENT.md` · `PROPOSAL_CONFIG_AND_OPTINS.md` · `PROPOSAL_MEAL_PLANS.md` · `PROPOSAL_COOK_MODE.md` · `IMPL_PLAN_COOKBOOK.md` (chunking + DEC resolutions) · `IMPL_PLAN_COOK_MODE.md` (Chunk 6 = C-4 §2.6a structured steps, must land before C-3 Chunk 5) · `ORPHANED_FIELDS_AUDIT.md` · FU-039 |
| `IMPL_PLAN_COOK_MODE.md` | `PROPOSAL_COOK_MODE.md` (§5a resolved decisions) · `PROPOSAL_COOKBOOK.md` §2.6a · `IMPL_PLAN_COOKBOOK.md` (Chunk 6 sequencing) · `PROPOSAL_CART_BUTTON.md` · `PROPOSAL_ONBOARDING.md` (Chunk 6 headcount default) · A1 theme tokens · A3 modal standard · B8 (substitute swaps kept) |
| `IMPL_PLAN_COOKBOOK.md` | `PROPOSAL_COOKBOOK.md` (§5a resolved decisions) · `IMPL_PLAN_COOK_MODE.md` (Chunk 6 of this plan blocks Chunk 5 of that one) · `RECIPE_COMPARISON_ASSESSMENT.md` (INV-6 drives Chunk 1) · `PROPOSAL_CART_BUTTON.md` (C-7 on ingredient rows) · `IMPL_PLAN_STATE_OWNERSHIP.md` (cookability) · A1/A3/A4/A7/A8 prompt outputs · B3 PATCH semantics · B8 substitute swaps · C-cross config surface |
| `IMPL_PLAN_STOCK_OVERVIEW.md` | `PROPOSAL_STOCK_OVERVIEW.md` (§7a resolved decisions) · `STOCK_OVERVIEW_PERF.md` (INV-2 — 50-cap/virtualisation drives Chunk 1) · `PROPOSAL_CART_BUTTON.md` (C-7 row cart, unbuilt) · `IMPL_PLAN_COOKBOOK.md` Chunk 5 (image pattern → FU-033) · `IMPL_PLAN_STATE_OWNERSHIP.md` (server-owned status/counts) · A1/A4/A7 prompt outputs · C-2 (planned-meals metric) · C-cross (location display) · FU-035, FU-033 |
| `IMPL_PLAN_CART_BUTTON.md` | `PROPOSAL_CART_BUTTON.md` (§7a resolved decisions) · `SHOPPING_LIST_REDESIGN_PROPOSAL.md` + `IMPL_PLAN_SHOPPING_LISTS.md` (status model + draft inference, landed → Axis B) · `IMPL_PLAN_STOCK_OVERVIEW.md` (C-1 row consumes it) · `IMPL_PLAN_COOK_MODE.md` (finish add-to-list reuses it) · `IMPL_PLAN_STATE_OWNERSHIP.md` (membership) · B1 (link/save errors, out of scope) · FU-038 |
| `PROPOSAL_ONBOARDING.md` | `PROPOSAL_CONFIG_AND_OPTINS.md` · `PROPOSAL_HELP_OVERLAY.md` · `PROPOSAL_COOK_MODE.md` · `EMAIL_SETUP_FINDINGS.md` · FU-041, FU-015 |
| `PROPOSAL_CART_BUTTON.md` | `SHOPPING_LIST_REDESIGN_PROPOSAL.md` + `IMPL_PLAN_SHOPPING_LISTS.md` · `IMPL_PLAN_STATE_OWNERSHIP.md` · A2 (BaseButton) · FU-038 |
| `PROPOSAL_ALERTS.md` | `PROPOSAL_CONFIG_AND_OPTINS.md` · `IMPL_PLAN_STATE_OWNERSHIP.md` · FU-042 |
| `PROPOSAL_INGESTION_API.md` | `RECONCILED_FINISHING_PLAN.md` §6.6 + §7 Decision 1 + §7.5 · `PROPOSAL_BARCODE_SCANNING.md` (P8-02 shape) · `IMPL_PLAN_STATE_OWNERSHIP.md` · FU-045 (Postgres) |
| `PROPOSAL_CONFIG_AND_OPTINS.md` | ADR-002 (feature-flag pattern) · all five per-surface C-proposals that consume it · `EMAIL_SETUP_FINDINGS.md` · `ESSENTIAL_FLAG_FINDINGS.md` |
| `PROPOSAL_LOCALE_I18N.md` | `PROPOSAL_INGESTION_API.md` (currency in observations) · `RECONCILED_FINISHING_PLAN.md` §7.5 · FU-043 |
| `PROPOSAL_HELP_OVERLAY.md` | `PROPOSAL_ONBOARDING.md` (inverse of forced tour) · FU-044 |
| `PROPOSAL_BARCODE_SCANNING.md` | `RECONCILED_FINISHING_PLAN.md` Decision 1 · `PROPOSAL_INGESTION_API.md` · ADR-002 · FU-056, FU-057 |
| `SHOPPING_LIST_REDESIGN_PROPOSAL.md` | `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` · `PROPOSAL_CART_BUTTON.md` · `IMPL_PLAN_STATE_OWNERSHIP.md` |
| `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` | `DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md` (the 4th client copy) · `STOCK_OVERVIEW_PERF.md` |
| `IMPL_PLAN_SHOPPING_LISTS.md` | `SHOPPING_LIST_REDESIGN_PROPOSAL.md` · `IMPL_PLAN_STATE_OWNERSHIP.md` · `PROPOSAL_CART_BUTTON.md` · ADR-003 (status `*_VALUES`) · FU-060 |
| `IMPL_PLAN_STATE_OWNERSHIP.md` | `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` · `DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md` · `STOCK_OVERVIEW_PERF.md` · FU-050, FU-052, FU-051, FU-047 |
| `DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md` | `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` + `IMPL_PLAN_STATE_OWNERSHIP.md` (sequence after) · `AUTH_ASSISTANT_SECURITY_FINDINGS.md` · ADR-002 (assistant gating) · FU-047 |

---

## Surface → docs index

Reverse lookup. For each app surface, every doc that touches it.

### Stock (overview + detail)
- **Prompts:** A2, A3, A4, A5, A7, A8 (rename pass), B3, B4, B9, INV-1,
  INV-2, INV-7, INV-10, C-1.
- **Proposals:** `PROPOSAL_STOCK_OVERVIEW.md` · `PROPOSAL_CART_BUTTON.md`
  · `PROPOSAL_BARCODE_SCANNING.md` · `PROPOSAL_CONFIG_AND_OPTINS.md`
  (location-display) · `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` ·
  `IMPL_PLAN_STATE_OWNERSHIP.md`.
- **Investigations:** `STOCK_OVERVIEW_PERF.md` · `ORPHANED_FIELDS_AUDIT.md`
  · `ESSENTIAL_FLAG_FINDINGS.md` · `HISTORY_TAB_ASSESSMENT.md` ·
  `SUBSTITUTE_SWAP_ASSESSMENT.md` (per-item substitutes anchor).
- **Original spec:** `Feature Boards/Stock Items.md`.
- **Open FUs:** FU-035, FU-033, FU-050, FU-052, FU-034.

### Recipes / Cookbook (overview + detail)
- **Prompts:** A2, A3, A4, A7, A8 (Cookbook rename / Mark cooked), B3,
  B8, INV-1, INV-6, INV-8 (substitute-swap), C-4.
- **Proposals:** `PROPOSAL_COOKBOOK.md` · `PROPOSAL_COOK_MODE.md` ·
  `PROPOSAL_MEAL_PLANS.md` · `PROPOSAL_CART_BUTTON.md` ·
  `PROPOSAL_CONFIG_AND_OPTINS.md`.
- **Investigations:** `RECIPE_COMPARISON_ASSESSMENT.md` ·
  `SUBSTITUTE_SWAP_ASSESSMENT.md` · `ORPHANED_FIELDS_AUDIT.md`.
- **Original spec:** `Feature Boards/Recipes.md` · `Meals.md`.
- **Open FUs:** FU-039, FU-040, FU-020, FU-031, FU-019, FU-049.

### Meal Plans
- **Prompts:** A4, A7, A8, B6 (folded into C-2), C-2.
- **Proposals:** `PROPOSAL_MEAL_PLANS.md` · `PROPOSAL_COOKBOOK.md` ·
  `PROPOSAL_COOK_MODE.md` · `PROPOSAL_CONFIG_AND_OPTINS.md`
  (money/time-of-day).
- **Investigations:** none direct.
- **Original spec:** `Feature Boards/Meals.md`.
- **Open FUs:** FU-032.

### Cook Mode
- **Prompts:** A1 (timer theming), A3 (finish modal), A6, B8
  (substitute swap), C-3.
- **Proposals:** `PROPOSAL_COOK_MODE.md` · `PROPOSAL_COOKBOOK.md` ·
  `PROPOSAL_CART_BUTTON.md` · `PROPOSAL_ONBOARDING.md` (headcount) ·
  `PROPOSAL_CONFIG_AND_OPTINS.md` (tools taxonomy).
- **Investigations:** none direct.
- **Original spec:** `Feature Boards/Recipes.md`.
- **Open FUs:** FU-040.

### Shopping Lists / Shop Mode
- **Prompts:** A2, A3, A4, A7, B9.1 (drag-drop), C-7, IMPL Shopping
  Lists.
- **Proposals:** `SHOPPING_LIST_REDESIGN_PROPOSAL.md` ·
  `IMPL_PLAN_SHOPPING_LISTS.md` · `PROPOSAL_CART_BUTTON.md` ·
  `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md`.
- **Investigations:** `SUBSTITUTE_SWAP_ASSESSMENT.md`.
- **Original spec:** `Feature Boards/Shopping Lists.md`.
- **Open FUs:** FU-060, FU-038, FU-036, FU-028.

### Alerts
- **Prompts:** B5 (nav stopgap), C-9.
- **Proposals:** `PROPOSAL_ALERTS.md` · `PROPOSAL_CONFIG_AND_OPTINS.md`.
- **Investigations:** none direct.
- **Original spec:** `Feature Boards/Alerts.md`.
- **Open FUs:** FU-042.

### Onboarding
- **Prompts:** A1, A8, B5 (skip/finish/show-me wiring), C-5.
- **Proposals:** `PROPOSAL_ONBOARDING.md` ·
  `PROPOSAL_CONFIG_AND_OPTINS.md` · `PROPOSAL_HELP_OVERLAY.md` ·
  `PROPOSAL_COOK_MODE.md` (headcount feeder).
- **Investigations:** `EMAIL_SETUP_FINDINGS.md`.
- **Original spec:** all Feature Boards (onboarding sells the
  product).
- **Open FUs:** FU-041, FU-015.

### Dashboard (DEFERRED but contracts land)
- **Prompts:** A1 (dark mode), B5 (Continue button + Alerts nav stopgap),
  B9 (Dora image off-centre), C-9 (alert-card contract).
- **Proposals:** `PROPOSAL_ALERTS.md` (dashboard alert card contract).
- **Investigations:** none direct.
- **Original spec:** `Feature Boards/Dashboard.md`.
- **Open FUs:** none specific (deferred surface).

### Dora Assistant
- **Prompts:** A6 (text size honouring), A8 (D.O.R.A. rename), INV
  (assistant indirectly).
- **Proposals:** `DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md` ·
  `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` (kills 4th missing-ingredients
  copy).
- **Investigations:** `AUTH_ASSISTANT_SECURITY_FINDINGS.md`.
- **Original spec:** `Feature Boards/Help, Guides & Assistant.md`.
- **Open FUs:** FU-047 (assistant `_resolve_level` hardcoded names).

### Ingestion API (Dora-core seam)
- **Prompts:** C-10 (writes it), C-6 + C-8 (companion targets it),
  C-locale (currency-carrying observations).
- **Proposals:** `PROPOSAL_INGESTION_API.md` ·
  `PROPOSAL_BARCODE_SCANNING.md` (P8-02 uses similar shape).
- **Investigations:** none direct.
- **Original spec:** `Feature Boards/Products.md`.
- **Open FUs:** FU-045 (Postgres), FU-053 (resolved — best deals
  client-side aggregation).

### Cart Button (cross-cutting)
- **Prompts:** B1, B7 (stop double-toast at button), C-7.
- **Proposals:** `PROPOSAL_CART_BUTTON.md` ·
  `SHOPPING_LIST_REDESIGN_PROPOSAL.md`.
- **Investigations:** none direct.
- **Original spec:** `Feature Boards/Shopping Lists.md` ·
  `Products.md`.
- **Open FUs:** FU-038.

### Help Overlay (cross-cutting)
- **Prompts:** C-help, every C-1..C-9 (per-surface hint rollout).
- **Proposals:** `PROPOSAL_HELP_OVERLAY.md`.
- **Investigations:** none direct.
- **Original spec:** `Feature Boards/Help, Guides & Assistant.md`.
- **Open FUs:** FU-044.

### Locale / i18n (cross-cutting)
- **Prompts:** A8 (rename pass touches AU copy), C-locale.
- **Proposals:** `PROPOSAL_LOCALE_I18N.md` ·
  `PROPOSAL_INGESTION_API.md` (currency).
- **Investigations:** none direct.
- **Original spec:** none material.
- **Open FUs:** FU-043.

### Config / Opt-ins (cross-cutting)
- **Prompts:** INV-4 (SMTP), INV-10 (essential flag), C-cross.
- **Proposals:** `PROPOSAL_CONFIG_AND_OPTINS.md` · ADR-002 pattern.
- **Investigations:** `EMAIL_SETUP_FINDINGS.md` ·
  `ESSENTIAL_FLAG_FINDINGS.md`.
- **Original spec:** `Feature Boards/User & Global Options.md`.
- **Open FUs:** none specific.

### Auth / Security (cross-cutting)
- **Prompts:** B9 (settings nav), INV-4.
- **Proposals:** none Dora-core specific yet.
- **Investigations:** `AUTH_ASSISTANT_SECURITY_FINDINGS.md` ·
  `MULTI_USER_READINESS.md`.
- **Original spec:** none material.
- **Open FUs:** FU-037 (`.secret_key` hardcoded path).

### Theming (cross-cutting)
- **Prompts:** A1, A1b, A6, B9 (404 + product-history tooltip).
- **Proposals:** none (consumed everywhere).
- **Investigations:** none direct.
- **Original spec:** `Feature Boards/User & Global Options.md`.
- **Open FUs:** FU-046, FU-010, FU-003, FU-004, FU-002.

### Filtering (cross-cutting)
- **Prompts:** A4, every list-page prompt.
- **Proposals:** consumed everywhere.
- **Investigations:** none direct.
- **Original spec:** none material.
- **Open FUs:** FU-022, FU-012, FU-013, FU-011.

### Notifications / Toasts (cross-cutting)
- **Prompts:** B7, C-7.
- **Proposals:** `PROPOSAL_CART_BUTTON.md` (list-state aware toast).
- **Investigations:** none direct.
- **Original spec:** none material.
- **Open FUs:** FU-038, FU-018.

### Data Layer / State Ownership (cross-cutting)
- **Prompts:** INV-2, INV-3, IMPL State Ownership.
- **Proposals:** `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` ·
  `IMPL_PLAN_STATE_OWNERSHIP.md` ·
  `DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`.
- **Investigations:** `STOCK_OVERVIEW_PERF.md` ·
  `LOGGING_AND_DATA_LAYOUT.md` · `ORPHANED_FIELDS_AUDIT.md`.
- **Original spec:** none material.
- **Open FUs:** FU-050, FU-051, FU-052, FU-049, FU-047, FU-048.

### Distribution / Tenancy / Deployment (cross-cutting)
- **Prompts:** INV-3, INV-4, C-10.
- **Proposals:** `PROPOSAL_INGESTION_API.md` ·
  `PROPOSAL_LOCALE_I18N.md`.
- **Investigations:** `MULTI_USER_READINESS.md` ·
  `Distribution Spec - Desktop App & Mobile Client.md` ·
  `LOGGING_AND_DATA_LAYOUT.md` · `COMMERCIALIZATION_REPORT.md`.
- **Original spec:** `00_original_spec/Distribution Spec - Desktop
  App & Mobile Client.md` (paired original).
- **Open FUs:** FU-045 (Postgres), FU-037, FU-027.

### Product Search & My Products (COMPANION SCOPE)
- **Prompts:** A4 (filter ripple in this repo's UI before migration), B1
  (forbid payloads — Dora-core API), B7 (product history toast), B9.6
  (product history graph), C-6 + C-8 (companion-scope), INV-5 (relevancy
  filter explained), INV-1 (orphaned fields incl. product fields).
- **Proposals:** `PROPOSAL_INGESTION_API.md` (the seam) ·
  `PROPOSAL_CART_BUTTON.md` (standalone-product rule).
- **Investigations:** none in this repo for the companion specifically.
- **Original spec:** `Feature Boards/Products.md`.
- **Open FUs:** FU-014 (image round-trip).

---

## Homeless follow-ups

Every currently-open `FU-NNN` in `DORA_FOLLOWUPS.md` is cited above
against at least one prompt or surface, with these placement notes:

- **FU-006** (~289 `q-btn` remaining) → A2 (the rule), opportunistic
  during any C-prompt that touches a toolbar.
- **FU-007** (eyeball A3 modals in browser) → A3.
- **FU-024** (A7 dead banner CSS + wider footer adoption) → A7.
- **FU-025** (eyeball A6 text scale) → A6.
- **FU-046** (A1 chunks D–F regressed) → A1.
- **FU-010** (late-game holistic theme review) → A1 (deferred final
  pass); not attached to any single C-prompt.
- **FU-016** (audit "frontend cache vs backend mutation" races) → B5
  (the index case), cross-cutting otherwise.
- **FU-026** (B9.5 undo behaves oddly) → B9 (partially resolved per
  ledger).
- **FU-027** (B9.7 log-rotation model decision) → INV-3 / B9.7.

No follow-up is currently without a home — if a new one is raised
without an obvious fit, list it under this heading.
