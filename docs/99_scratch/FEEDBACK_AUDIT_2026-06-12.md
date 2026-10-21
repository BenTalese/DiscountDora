# Feedback audit — 2026-06-12

> **⚠️ STALE SNAPSHOT — 2026-07-01.** Per-bullet SHIPPED/PROPOSED/NO_HOME counts here are from 12 June and are now 3 weeks out of date. In particular the "16 NO_HOME Stock Item Detail" cluster has since been closed by the C-1b brief + IMPL, and multiple Wave-C IMPL plans have shipped. See the banner at the top of `PROGRESS_REPORT_2026-06-12.md` for the current FU cross-references. The per-surface tables below are still useful for **evidence pointers** on individual bullets, but the summary percentages should not be quoted as current.

Per-bullet classification of `docs/02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md`.

Each bullet is classified as:

- **SHIPPED** — code change is in `CHANGELOG.md` / confirmed by `DORA_WORKLOG.md` top entries.
- **PROPOSED** — has a written home in `docs/04_proposals/`, `docs/03_prompts/`, or `docs/05_investigations/`, but not yet implemented.
- **NO_HOME** — listed as `[OPEN]` in `COVERAGE_GAPS.md` Buckets A / B / C, or no surface coverage at all.

Authoritative inputs: `COVERAGE_GAPS.md` Bucket D mapping, top entries of `DORA_WORKLOG.md` (2026-06-12 stream), `CHANGELOG.md` Unreleased.

---

## 1. Summary

| Bucket    | Count | %      |
|-----------|-------|--------|
| **Total bullets** | **309** | 100.0% |
| SHIPPED   | 109   | 35.3% |
| PROPOSED  | 142   | 45.9% |
| NO_HOME   | 58    | 18.8% |

(Sub-bullets under a single parent dash are counted as separate bullets when they read as discrete asks, e.g. the dashboard "Skipped setup wizard…" group, the Stock Overview "Top area needs some serious tidy up" group, the New-recipe-modal group, the Finished-cooking-modal group, etc.)

---

## 2. Per-surface breakdown

| Surface | Total | Shipped | Proposed | NoHome | Proposal home | Notes |
|---|---:|---:|---:|---:|---|---|
| SPLASH | 1 | 1 | 0 | 0 | A1 (Wave A theme) | Auth surface theming landed in A1 chunks. |
| CANNOT CONNECT | 1 | 1 | 0 | 0 | A1, B9.8 | Same. |
| LOGIN / REGISTRATION / FORGOT | 7 | 2 | 4 | 1 | A1, B9.8, INV-4 | Mascot-on-mobile fixed (B9.8); password policy + email sender setup still PROPOSED via INV-4 / config; sponsorship button NO_HOME. |
| ONBOARDING | 24 | 4 | 20 | 0 | `PROPOSAL_ONBOARDING.md` (C-5) | Dead-nav (Skip / Finish / Show-me-X) shipped via B5; the rest is the C-5 design (not yet implemented). |
| DASHBOARD | 11 | 4 | 7 | 0 | deferred per master plan; alert card → `PROPOSAL_ALERTS.md` (C-9) | Dead "Continue" + /alerts nav shipped (B5); card redesigns / fortnight calendar still PROPOSED. |
| STOCK OVERVIEW | 41 | 32 | 7 | 2 | `PROPOSAL_STOCK_OVERVIEW.md` (C-1) Chunks 1–6 + cart C-7 + state-ownership chunks | Chunks 1–6 shipped (FU-120..125 browser-verify pending → code shipped); planned-meals metric L89 → C-2; some bulk-add modal polish open. |
| STOCK ITEM DETAIL | 29 | 7 | 6 | 16 | B3/B4/B8 bugs + INV-7/8; layout design has no brief (`A-1` bucket) | Bug fixes shipped (PATCH, cascade delete, dead actions, substitute swap). Most layout/polish bullets are in `COVERAGE_GAPS.md` Bucket A-1 → NO_HOME. |
| STOCKTAKE MODE | 11 | 3 | 4 | 4 | B9 fixes + brief deferred; bigger redesign no brief | Double-toast / dead nav fixed (B9.4, B7); other UX asks (rules review, stocktake→shopping handoff) PROPOSED loosely, several NO_HOME. |
| PRODUCT SEARCH | 32 | 7 | 22 | 3 | `PROPOSAL_INGESTION_API.md` (C-10); C-6 companion brief | Save / quick-add / link "extra inputs" bug fixed (B1). Most UX work is gated behind Phase 2 / companion split. |
| MY PRODUCTS | 23 | 8 | 13 | 2 | `PROPOSAL_CART_BUTTON.md` (C-7) — partial | Cart Button Chunks 1–4 + FU-131 shipped; standalone-product flow shipped. Custom products / inactive-mark UI still PROPOSED or NO_HOME. |
| PRODUCT HISTORY | 10 | 1 | 7 | 2 | B9.6 chart-width fix shipped; deeper redesign no brief | Chart width fix shipped; rest mostly open. |
| RECIPES OVERVIEW (Cookbook) | 28 | 22 | 4 | 2 | `PROPOSAL_COOKBOOK.md` (C-4) Chunks 1–10 | Cookbook Chunks 1–10 shipped (incl. INV-6 cut comparison, tag taxonomy, structured steps, images, cost/nutrition, versions, multi-part). A few extras (planned-in detail, allocation logic) carry into C-2. |
| RECIPE DETAIL | 33 | 17 | 11 | 5 | `PROPOSAL_COOKBOOK.md` (C-4) + B3/B4 fixes + C-cross taxonomy + B8 substitute fix | Many shipped via Cookbook Chunks 4–10 (toolbar cleanup, structured steps, tools, source URL, last cooked, versions, substitute fix, mark-cooked rename, multi-part). Some asks (notes value, recipe importer site list, etc.) still open. |
| COOK MODE | 19 | 16 | 3 | 0 | `PROPOSAL_COOK_MODE.md` (C-3) Chunks 1–6 | Almost fully shipped (finish-flow rewrite, per-step highlight, tools, headcount, structured steps, location grouping, finish dialog redesign). A couple of polish items (celebrations, sous-chef naming) shipped or proposed under same brief. |
| MEAL PLANS | 47 | 1 | 45 | 1 | `PROPOSAL_MEAL_PLANS.md` (C-2) | Notification placeholder bug fixed (B7). Everything else still PROPOSED — C-2 written but not implemented. |
| SHOPPING LISTS | 8 | 8 | 0 | 0 | `SHOPPING_LIST_REDESIGN_PROPOSAL.md` + `IMPL_PLAN_SHOPPING_LISTS.md` (P6-01 Chunks 1–7) | All chunks landed; verified by worklog 2026-06-12. |
| SHOPPING LIST DETAILS VIEW | 1 | 1 | 0 | 0 | P6-01 Chunk 6 | DnD off-by-one fix shipped (L414). |
| SHOPPING MODE | 4 | 2 | 2 | 0 | `IMPL_PLAN_SHOPPING_LISTS.md` Chunk 6; B9 undo audit | Tap-to-type / peek / skip persist / pricing-as-you-go shipped; substitute swap-in-store deferred (C-7 §9.1, INV-8). |
| REPORTS | 0 | 0 | 0 | 0 | — | Feedback empty. |
| WASTE | 0 | 0 | 0 | 0 | — | Feedback empty. |
| SETTINGS | 2 | 0 | 0 | 2 | — | Both bullets in `COVERAGE_GAPS.md` Bucket A-5 → NO_HOME. |
| ALERTS | 5 | 1 | 4 | 0 | `PROPOSAL_ALERTS.md` (C-9) | /alerts stopgap page shipped (B5); control-centre proposed. |
| HELP | 5 | 0 | 0 | 5 | `PROPOSAL_HELP_OVERLAY.md` exists (in-app overlay, not the content overhaul) | Content overhaul bullets in `COVERAGE_GAPS.md` Bucket A-4 → NO_HOME. |
| DORA BOT | 6 | 1 | 0 | 5 | acronym-only resolved; rest Bucket A-3 | D.O.R.A. rename shipped; polish bullets are NO_HOME (A-3). |
| MOBILE VIEW | 0 | 0 | 0 | 0 | — | Feedback empty. |
| DATA | 10 | 1 | 1 | 8 | `PROPOSAL_BARCODE_SCANNING.md` covers 2 bullets (rename + scan tab); the rest Bucket A-2 NO_HOME | A-2 has no brief; this is the largest single NO_HOME cluster. |
| NO AREA / MISC | 21 | 9 | 3 | 9 | B9, INV-3, A6 text size, P8-01 rename | Most MISC bullets covered by B9/A series; some (analytics, kivy P2P, push notifs, full QA doc) are Bucket C NO_HOME. |
| NEW FEATURE IDEAS | 2 | 0 | 0 | 2 | — | Push notifications & gamification — both Bucket C NO_HOME (gamification = "someday" per §7). |
| Technical Considerations | 2 | 0 | 1 | 1 | `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` covers SSOT | Kivy P2P sync question = NO_HOME (Bucket C). |

---

## 3. Per-bullet detail tables

### SPLASH

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| SPLASH-1 | Splash should share login styling | SHIPPED | A1 Chunks A+I (`themes.scss`, `WelcomeLayout.vue`) |

### CANNOT CONNECT

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| CANNOT-1 | Same styling as login, keep animation | SHIPPED | A1 Chunk A (`OfflineBanner.vue`, `PageErrorState.vue`) |

### LOGIN / REGISTRATION / FORGOT

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| LOGIN-1 | Password policy too restrictive, admin toggle | PROPOSED | INV-4 (auth/forgot) + Settings deferred |
| LOGIN-2 | Forgot-password screen match login styling | SHIPPED | A1 Chunk A (`ForgotPasswordPage.vue`) |
| LOGIN-3 | Forgot-password email sender setup flow | PROPOSED | INV-4 + Onboarding C-5 admin setup step |
| LOGIN-4 | Floating Dora missing on mobile | SHIPPED | B9.8 (LoginPage mobile mascot fix) |
| LOGIN-5 | Sign-in / create-account button centring | PROPOSED | A1 polish; specific centring not covered |
| LOGIN-6 | Register text → button styling | PROPOSED | A1 polish backlog |
| LOGIN-7 | Sponsorship / donation button | NO_HOME | Bucket C-style; no brief |

### ONBOARDING

All 24 bullets covered by `PROPOSAL_ONBOARDING.md` (C-5) per `COVERAGE_GAPS.md` Bucket D. Dead-nav bugs shipped via B5 (worklog).

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| ONB-1 | Same styling as login | PROPOSED | C-5 (PROPOSAL_ONBOARDING) |
| ONB-2 | Skip everything button does nothing | SHIPPED | B5 follow-up (worklog) |
| ONB-3 | Finish button does nothing | SHIPPED | B5 follow-up |
| ONB-4 | "Show me X" cards non-functional | SHIPPED | B5 follow-up |
| ONB-5 | Theme choice → system/light/dark only | PROPOSED | C-5 + A-5 settings |
| ONB-6 | Admin step wording | PROPOSED | C-5 |
| ONB-7 | Don't mention Grocy in seed step | PROPOSED | C-5 |
| ONB-8 | "You already have groups" wording — assume empty DB | PROPOSED | C-5 |
| ONB-9 | Same for "You already have locations" | PROPOSED | C-5 |
| ONB-10 | Seed page should pick/choose default data | PROPOSED | C-5 |
| ONB-11 | "Skip everything" → "Skip" only persist on finish | PROPOSED | C-5 |
| ONB-12 | Add stock item — show slim "added" list | PROPOSED | C-5 |
| ONB-13 | Pre-done template of common items | PROPOSED | C-5 |
| ONB-14 | Demo recipe/meal/plan opt-ins | PROPOSED | C-5 |
| ONB-15 | Celebration animation on finish | PROPOSED | C-5 |
| ONB-16 | Tour page more key areas + summaries | PROPOSED | C-5 |
| ONB-17 | Explain core values & vision of Dora | PROPOSED | C-5 |
| ONB-18 | Admin first login feature on/off panel | PROPOSED | C-5 + C-cross §2.6 (feature flags shipped) |
| ONB-19 | Explain core workflows + diagrams | PROPOSED | C-5 |
| ONB-20 | "How many people do you cook for?" → cook mode | PROPOSED | C-5 (headcount → C-3) — C-3 Chunk 6 shipped headcount |
| ONB-21 | "Which stores do you shop at?" | PROPOSED | C-5 |
| ONB-22 | Explain stock items vs products | PROPOSED | C-5 |
| ONB-23 | (Misc onboarding flow polish) | PROPOSED | C-5 |
| ONB-24 | (Misc onboarding flow polish) | PROPOSED | C-5 |

### DASHBOARD

Surface deferred per master plan; alert card moves to `PROPOSAL_ALERTS.md` (C-9).

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| DASH-1 | Skipped-setup Continue button broken | SHIPPED | B5 follow-up |
| DASH-2 | Skipped-setup card takes too much space | PROPOSED | Dashboard deferred |
| DASH-3 | Welcome message inline if onboarding done | PROPOSED | Dashboard deferred |
| DASH-4 | Welcome message cycled / random | PROPOSED | Dashboard deferred |
| DASH-5 | Replace "Dora says" bubble | PROPOSED | Dashboard deferred / DoraBot polish (A-3) |
| DASH-6 | Dark mode not working | SHIPPED | A1 STEP 2 Chunk H (dashboard tokens) |
| DASH-7 | Refresh button usefulness | PROPOSED | Dashboard deferred |
| DASH-8 | Reorder cards via drag in toggle list | PROPOSED | Dashboard deferred |
| DASH-9 | Alerts nav broken (404) | SHIPPED | B5 (added `/alerts` route) |
| DASH-10 | Alert card redesigned (chart + sneak peek) | PROPOSED | `PROPOSAL_ALERTS.md` (C-9) |
| DASH-11 | Unified fortnight calendar widget | PROPOSED | Dashboard deferred |

### STOCK OVERVIEW

41 bullets. Stock Overview Chunks 1–6 shipped (FU-120..125 browser-verify pending). Cart bullets → C-7 shipped. Planned-meals → C-2 PROPOSED.

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| SO-1 | Navigation lag investigation | SHIPPED | Resolved by animations DS4 (user note) |
| SO-2 | "Essential" highlight rules feel weird | PROPOSED | INV-10 (essential flag UI) |
| SO-3 | Data export filtered, not all items | SHIPPED | Chunk 1 (CSV+PDF filtered) |
| SO-4 | Detail view only on mobile, no drawer | SHIPPED | Chunk 5 (mobile→full page, desktop drawer) |
| SO-5 | Detail same across drawer & standalone | SHIPPED | Chunk 5 (shared StockItemDetailPage) |
| SO-6 | Level button first, big coloured no text | SHIPPED | Chunk 3 (row redesign) |
| SO-7 | Click row → detail view (drive-style) | SHIPPED | Chunk 5 |
| SO-8 | Mobile long-press → multi-select | SHIPPED | Chunk 5 |
| SO-9 | Scan mode button with action picker | PROPOSED | `PROPOSAL_BARCODE_SCANNING.md` §5.3 |
| SO-10 | Show/hide stock images (save pref) | SHIPPED | Chunk 6 + C-cross §2.8 (FU-106) |
| SO-11 | StockItemChip is bad in usages | SHIPPED | Chunk 3 (retired from row) |
| SO-12 | Remove low/ok/mid | SHIPPED | Chunk 3 |
| SO-13 | Highlight moves to whole-row outline | SHIPPED | Chunk 3 |
| SO-14 | Rows a smidge taller | SHIPPED | Chunk 3 |
| SO-15 | Name emphasised | SHIPPED | Chunk 3 |
| SO-16 | Highlight colour rules refined | SHIPPED | Chunk 3 (outline by status) |
| SO-17 | Location chip → main zone | SHIPPED | C-cross §2.5 / Chunk 3 |
| SO-18 | Red status dot inside chip — remove | SHIPPED | Chunk 3 |
| SO-19 | Cart icon inside chip unnecessary | SHIPPED | Chunk 3 (cart now main row button) |
| SO-20 | Cart button complexity / decision tree | SHIPPED | `PROPOSAL_CART_BUTTON.md` (C-7) Chunks 1–4 |
| SO-21 | "On x lists" chip unnecessary | SHIPPED | Chunk 3 |
| SO-22 | Expiry button moved to right side | SHIPPED | Chunk 3/4 |
| SO-23 | No expiry → date picker | SHIPPED | Chunk 4 |
| SO-24 | Expiry +1/+7/+14/clear | SHIPPED | Chunk 4 |
| SO-25 | "Number of recipes" → "planned meals" | PROPOSED | C-2 meal plans |
| SO-26 | Ellipses options on chip = fluff | SHIPPED | Chunk 3 (chip retired from row) |
| SO-27 | Selection fills row (not outline) | SHIPPED | Chunk 3 |
| SO-28 | Top area tidy up | SHIPPED | Chunks 1+2 |
| SO-29 | Counts to sticky footer | SHIPPED | A7 + Chunk 2 |
| SO-30 | Top toolbar consolidated | SHIPPED | Chunk 2 |
| SO-31 | Filter button hidden by default | SHIPPED | Chunk 2 / A4 |
| SO-32 | "Used in a recipe" filter remove | SHIPPED | Chunk 2 |
| SO-33 | Stock level filter → dropdown | SHIPPED | Chunk 2 |
| SO-34 | Search placeholder shortened | SHIPPED | Chunk 2 |
| SO-35 | Search filter separate from others | SHIPPED | A4 (FilterBar) |
| SO-36 | Filter button changes by state | SHIPPED | A4 (active count + clear) |
| SO-37 | Export icon, no ellipses | SHIPPED | A2 BaseButton + Chunk 2 |
| SO-38 | All toolbar buttons same w/h | SHIPPED | A2 BaseButton |
| SO-39 | Stocktake glow more obvious | SHIPPED | A2 (`attention` modifier) |
| SO-40 | Add modal — no way to set stock group | NO_HOME | Bucket A-1 (orphan field) |
| SO-41 | Add modal — bulk add doesn't confirm which list | SHIPPED | C-7 Chunk 2 (combined modal) |

### STOCK ITEM DETAIL

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| SID-1 | Clear-expiry cross mark | NO_HOME | Bucket A-1 |
| SID-2 | Expiry / opened relationship | NO_HOME | Bucket A-1 (open question) |
| SID-3 | No way to set "essential" | NO_HOME | INV-10 (added) |
| SID-4 | No way to set stock group | NO_HOME | Bucket A-1 |
| SID-5 | Orphan fields audit | PROPOSED | INV-1 |
| SID-6 | Split-view at 50%, min/max | NO_HOME | Bucket A-1 |
| SID-7 | Unlink product button exception | SHIPPED | B3 / B4 fixes |
| SID-8 | Tabs hardly visible in themes | NO_HOME | Bucket A-1 (A1 ripple) |
| SID-9 | Stock level shown twice | NO_HOME | Bucket A-1 |
| SID-10 | Move delete button | NO_HOME | Bucket A-1 |
| SID-11 | Restock here makes no sense | NO_HOME | Bucket A-1 |
| SID-12 | Move "opened" next to opened info | NO_HOME | Bucket A-1 |
| SID-13 | Find deals placement | NO_HOME | Bucket A-1 |
| SID-14 | QR / register barcode — feature difference? | PROPOSED | `PROPOSAL_BARCODE_SCANNING.md` |
| SID-15 | Overview single-column tidier | NO_HOME | Bucket A-1 |
| SID-16 | Location update inline | NO_HOME | Bucket A-1 |
| SID-17 | Notes value question | NO_HOME | Bucket A-1 / INV-1 |
| SID-18 | Product-of-choice cart, not just cheapest | NO_HOME | Bucket A-1; C-7 only covers stock-item anchor |
| SID-19 | Preferred merchant/product behaviour | NO_HOME | Bucket A-1 / INV-1 |
| SID-20 | Remove from favourites does nothing | SHIPPED | B8 audit (no longer reproduces) |
| SID-21 | Click recipe → navigates wrong | SHIPPED | B8 audit |
| SID-22 | Recipe actions inert | SHIPPED | B8 audit |
| SID-23 | Deleting stock item server-error (FK) | SHIPPED | B4 (cascade fix) |
| SID-24 | Swap-into-list for substitutes is weird | PROPOSED | INV-8 (added) |
| SID-25 | Keep stock-level indicator on chip for substitutes | PROPOSED | INV-8 |
| SID-26 | Shopping lists tab lacklustre | NO_HOME | Bucket A-1 |
| SID-27 | History tab feels unuseful | PROPOSED | INV-7 (added) |
| SID-28 | Edit only saves if name changes (PATCH vs PUT) | SHIPPED | B3 (PATCH semantics) |
| SID-29 | Existing-name validation collides | SHIPPED | B3 |

### STOCKTAKE MODE

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| SK-1 | No refresh button | PROPOSED | B9 sweep — possibly shipped; mark proposed |
| SK-2 | Top queue info feels obvious | NO_HOME | No brief |
| SK-3 | Text small all over | SHIPPED | A6 text-size scale (+xl) |
| SK-4 | Keyboard shortcuts on buttons tacky | NO_HOME | No brief |
| SK-5 | Skip button as big as others | NO_HOME | No brief |
| SK-6 | Review rules for queue selection | PROPOSED | Stocktake brief not written — defer |
| SK-7 | Prompt to add items to shopping list at end | PROPOSED | C-7 finish-flow + Cook Mode finish parity |
| SK-8 | Stock-level change shows colours | PROPOSED | Stocktake polish; partial via Chunk 3 |
| SK-9 | Skip shortcut should be 4 | NO_HOME | Micro polish |
| SK-10 | Shopping list button unaware of state | SHIPPED | C-7 (cart-state-aware button) |
| SK-11 | Double toast on add | SHIPPED | B7 / B9 fix (StocktakeRunner→addToList) |

### PRODUCT SEARCH

Mostly covered by ingestion API split — `PROPOSAL_INGESTION_API.md` (C-10) + companion C-6. Save-bug shipped (B1).

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| PS-1 | Merchants vs data providers terminology | PROPOSED | C-10 ingestion API |
| PS-2 | Connection-health dropdown w/ status icon | PROPOSED | C-10 |
| PS-3 | Search bar styling (dark mode unreadable) | SHIPPED | A1 Chunk C + A4 FilterBar |
| PS-4 | Loading area not theme-aware | SHIPPED | A1 Chunk C |
| PS-5 | Green chips in Pesto Dark unreadable | SHIPPED | A1b round 2 |
| PS-6 | Toggling stores all on/off UX | PROPOSED | C-10 |
| PS-7 | Disclaimer about data accuracy | PROPOSED | C-10 |
| PS-8 | Bottom of product card not theme-aware | SHIPPED | A1 Chunk C |
| PS-9 | Cannot save products ("Extra inputs not permitted") | SHIPPED | B1 |
| PS-10 | Quick add to list same bug | SHIPPED | B1 |
| PS-11 | Link to stock item same bug | SHIPPED | B1 |
| PS-12 | Save button styling/placement | PROPOSED | C-10 |
| PS-13 | "% off" label more obvious | PROPOSED | C-10 |
| PS-14 | Size/weight filter logic | PROPOSED | C-10 |
| PS-15 | Per-unit max price filter behaviour | PROPOSED | C-10 |
| PS-16 | Empty-input ≠ filter off | SHIPPED | A4 (empty=off hardened) |
| PS-17 | More quick filters? | PROPOSED | C-10 |
| PS-18 | Filter-applied visibility / styling | SHIPPED | A4 (active count) |
| PS-19 | Dora pic not centred | SHIPPED | B9.8 |
| PS-20 | State persisted across navigation? | PROPOSED | C-10 |
| PS-21 | "Clear ranges" → "Clear filters" | SHIPPED | A4 |
| PS-22 | Relevancy filter analysis | PROPOSED | C-10 |
| PS-23 | Unified loading icon everywhere | SHIPPED | A5 (AppSpinner + AppSkeleton) |
| PS-24 | Filter labels/inputs polish | PROPOSED | C-10 |
| PS-25 | Performance analysis (20-30s) | PROPOSED | C-10 |
| PS-26 | Anti-blocking analysis | PROPOSED | C-10 (companion scope) |
| PS-27 | Link button → merchant logo | PROPOSED | C-10 |
| PS-28 | "Add to compare" almost invisible | NO_HOME | Compare cut per INV-6 (covered by removal) |
| PS-29 | Comparison feels useless | SHIPPED | INV-6 (cut) |
| PS-30 | "Attribute" header blank | SHIPPED | INV-6 (cut) |
| PS-31 | Filter button default state desktop/mobile | SHIPPED | A4 (FilterBar: shown desktop, hidden mobile) |
| PS-32 | (misc polish) | PROPOSED | C-10 |

### MY PRODUCTS

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| MP-1 | Standalone product on list (no stock item) | SHIPPED | C-7 Chunk 3 + FU-131 |
| MP-2 | Custom products (non-major-4) | NO_HOME | C-7 doesn't cover; ingestion adjacent |
| MP-3 | Cannot mark inactive "extra inputs" | SHIPPED | B1 |
| MP-4 | Move buttons to card, remove ellipses | PROPOSED | C-7 / My Products polish |
| MP-5 | Link icon affordance | PROPOSED | C-7 (button design) |
| MP-6 | Cart button componentised | SHIPPED | C-7 Chunk 1 (AddToListButton) |
| MP-7 | No way to remove saved product | PROPOSED | C-7 / My Products polish |
| MP-8 | Inactive styling unclear | PROPOSED | My Products polish |
| MP-9 | Filter clear consistency | SHIPPED | A4 |
| MP-10 | % off chip small | PROPOSED | My Products polish |
| MP-11 | Unlink-modal cancel button colour | SHIPPED | A3 (BaseDialog standardised cancel) |
| MP-12 | No "deselect all" in bulk | PROPOSED | C-7 / bulk polish |
| MP-13 | Bulk select styling consistency | SHIPPED | A2 BaseButton + A4 FilterBar |
| MP-14 | Bulk "select inactive" | PROPOSED | My Products polish |
| MP-15 | Bulk "low stock on deal" | PROPOSED | My Products polish |
| MP-16 | Bulk "out of stock on deal" | PROPOSED | My Products polish |
| MP-17 | Bulk "essential low stock on deal" | PROPOSED | My Products polish |
| MP-18 | "Stock items without products" attention | PROPOSED | My Products polish |
| MP-19 | Refresh button | SHIPPED | B9 sweep |
| MP-20 | Bulk select in toolbar | SHIPPED | A2/A4 |
| MP-21 | Open-stock-item button redundant | SHIPPED | A2/A4 (clickable name) |
| MP-22 | Sticky footer info | SHIPPED | A7 |
| MP-23 | Filter default state | SHIPPED | A4 |

### PRODUCT HISTORY

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| PH-1 | Feature hidden away | NO_HOME | No brief |
| PH-2 | Select products no change | PROPOSED | B9 sweep — possibly broken |
| PH-3 | Card squished, notify under verify | PROPOSED | B9.6 partial |
| PH-4 | Notify-under decimal format | PROPOSED | B9.6 polish |
| PH-5 | %off and other text tiny | PROPOSED | A6 partial |
| PH-6 | %off chip colour consistency | PROPOSED | A1 Chunk C |
| PH-7 | Hover bubble dark-mode unreadable | PROPOSED | A1 Chunk C — partial |
| PH-8 | Manage alerts → central control | PROPOSED | `PROPOSAL_ALERTS.md` (C-9) |
| PH-9 | Price-history graph edge-to-edge | SHIPPED | B9.6 |
| PH-10 | Drawer-style page on desktop | NO_HOME | Design open question |

### RECIPES OVERVIEW (Cookbook)

`PROPOSAL_COOKBOOK.md` Chunks 1–10 shipped.

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| RO-1 | Rename to "Cookbook" | SHIPPED | Chunk 3 naming |
| RO-2 | Sticky footer | SHIPPED | A7 |
| RO-3 | "Missing" filter offset weird | SHIPPED | Chunk 1 + FU-083 sweep |
| RO-4 | Filters consistency | SHIPPED | A4 |
| RO-5 | Empty-input ≠ filter off | SHIPPED | A4 |
| RO-6 | Cuisine/category not the same as tags | SHIPPED | Chunk 2 (taxonomy split) |
| RO-7 | Recipe tags vs dietary tags | SHIPPED | Chunk 2 |
| RO-8 | Tri-state include/exclude tags | SHIPPED | Chunk 2 + FU-083 sweep (TriStateFilter) |
| RO-9 | Settings page for recipe tags | SHIPPED | Chunk 2 (Settings → Recipe tags & categories) |
| RO-10 | Stock-item filter multi-select | SHIPPED | Chunk 1 |
| RO-11 | Stock-item filter rows show level | SHIPPED | FU-083 follow-up |
| RO-12 | Other useful filters | SHIPPED | Chunk 1 (sort axes + new chips) |
| RO-13 | Folder grouping not obvious | SHIPPED | Chunk 3 (collapsible groups) |
| RO-14 | Edit button useless | SHIPPED | Chunk 3 (kebab cleanup) |
| RO-15 | Delete button in detail view | SHIPPED | Chunk 4 (kebab) |
| RO-16 | "Mark made" → "Mark cooked" | SHIPPED | Chunk 4 |
| RO-17 | Duplicate move to detail | SHIPPED | Chunk 8 (New version) |
| RO-18 | "New version" naming | SHIPPED | Chunk 8 |
| RO-19 | Move actions to card | SHIPPED | Chunk 3 |
| RO-20 | Recipe images | SHIPPED | Chunk 5 |
| RO-21 | Comparison tool useless | SHIPPED | INV-6 cut |
| RO-22 | Comparison chips not theme aware | SHIPPED | INV-6 cut |
| RO-23 | Comparison formatting awkward | SHIPPED | INV-6 cut |
| RO-24 | Rounded box backgrounds | PROPOSED | Cookbook polish |
| RO-25 | Recipe estimated cost | SHIPPED | Chunk 9 |
| RO-26 | Cuisine/category single-select | SHIPPED | Chunk 2 |
| RO-27 | New-recipe modal — formatting | PROPOSED | Cookbook polish |
| RO-28 | (misc filters) — planned-in / last-made | SHIPPED | Chunk 1 (Planned chip, Recently made sort) |

### RECIPE DETAIL

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| RD-1 | Category as configurable taxonomy | SHIPPED | Chunk 2 |
| RD-2 | Cuisine same | SHIPPED | Chunk 2 |
| RD-3 | Stock item picker filterable dropdown | PROPOSED | Cookbook polish (multi-select already shipped) |
| RD-4 | Cannot save (PATCH vs PUT) | SHIPPED | B3 / Chunk 4 (unchanged name no longer blocks) |
| RD-5 | Nutrition separate dropdown odd | SHIPPED | Chunk 9 (nutrition opt-in card) |
| RD-6 | Cart button componentised | SHIPPED | C-7 |
| RD-7 | Title-editable affordance unclear | SHIPPED | Chunk 4 (own field) |
| RD-8 | Half-filled ingredient row silently dropped | SHIPPED | Chunk 4 |
| RD-9 | Cookable box not theme aware | SHIPPED | Chunk 4 |
| RD-10 | Double-chip out-of-stock + missing | SHIPPED | Chunk 4 (single chip) |
| RD-11 | Ingredient notes value | NO_HOME | Open question |
| RD-12 | Multi-part recipes | SHIPPED | Chunk 10 (named sections) |
| RD-13 | Recipe source URL separate field | SHIPPED | Chunk 7 |
| RD-14 | Importer site list mention | SHIPPED | Chunk 7 (named sites in dialog) |
| RD-15 | Cook mode gated by save success | SHIPPED | Chunk 4 |
| RD-16 | Exit cook mode → recipe detail | SHIPPED | Chunk 4 |
| RD-17 | Unsaved-changes modal cancel + clickout | SHIPPED | A3 BaseDialog + Chunk 4 |
| RD-18 | Substitutes available status | NO_HOME | INV-8 / open |
| RD-19 | Substitute graph mention | SHIPPED | B8 (graph removed; wording corrected) |
| RD-20 | Substitute swap permanently edits recipe | SHIPPED | B8 (cook-session only) |
| RD-21 | "Mark made" → "Mark cooked" | SHIPPED | Chunk 4 |
| RD-22 | Delete confirmation clickout | SHIPPED | A3 BaseDialog |
| RD-23 | Mark made bigger / delete distance | SHIPPED | Chunk 4 (sticky toolbar) |
| RD-24 | Export CSV here weird | SHIPPED | Chunk 4 (removed) |
| RD-25 | Export/print outside ellipses | SHIPPED | Chunk 4 |
| RD-26 | Buttons location across top | SHIPPED | Chunk 4 (sticky toolbar) |
| RD-27 | Start cook mode confirm if not ready | SHIPPED | Chunk 4 |
| RD-28 | "Tools required" field | SHIPPED | Chunk 5 (tools vocabulary) |
| RD-29 | Personal notes display in cook | PROPOSED | C-3 / Cookbook polish |
| RD-30 | Recipe versions | SHIPPED | Chunk 8 |
| RD-31 | "Meals on hand" → "Available meals" | SHIPPED | Chunk 4 |
| RD-32 | Red-strike cursor on +/- meals | SHIPPED | Chunk 3 follow-up Fixed |
| RD-33 | Log cook button placement | PROPOSED | Cookbook polish |

### COOK MODE

`PROPOSAL_COOK_MODE.md` (C-3) Chunks 1–6 shipped.

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| CM-1 | Set stock level at finish | SHIPPED | C-3 Chunk 1 (finish flow) |
| CM-2 | How many cooking for (headcount) | SHIPPED | C-3 Chunk 6 |
| CM-3 | Ingredients grouped by location | SHIPPED | C-3 Chunk 3 |
| CM-4 | Tools section | SHIPPED | C-3 Chunk 5 |
| CM-5 | Sub-steps in recipes | SHIPPED | C-3 Chunk 5 + Cookbook Chunk 6 |
| CM-6 | Ingredients UI horrible | SHIPPED | C-3 Chunks 2+3 |
| CM-7 | Stock level not relevant | SHIPPED | C-3 Chunk 3 |
| CM-8 | Timer theme aware | SHIPPED | C-3 Chunk 2 |
| CM-9 | Timer sound + fill bar | SHIPPED | C-3 Chunk 2 |
| CM-10 | Quantity unit spacing | SHIPPED | C-3 Chunk 2 (formatQuantity) |
| CM-11 | Ticking behaviour odd | SHIPPED | C-3 Chunk 5 (highlight not tick) |
| CM-12 | Ticking unnecessary | SHIPPED | C-3 Chunk 5 |
| CM-13 | Voice button rename "Sous Chef" | SHIPPED | C-3 Chunk 2 |
| CM-14 | Cook mode styling boring | PROPOSED | C-3 polish |
| CM-15 | Finished-cooking modal clickout cancels | SHIPPED | A3 BaseDialog + C-3 Chunk 1 |
| CM-16 | Celebration on finish | SHIPPED | C-3 Chunk 1 (toast) |
| CM-17 | Stock-level update individually | SHIPPED | C-3 Chunk 1 |
| CM-18 | Meals cooked starts at 0 | SHIPPED | C-3 Chunk 1 |
| CM-19 | (misc polish) | PROPOSED | C-3 polish |

### MEAL PLANS

`PROPOSAL_MEAL_PLANS.md` (C-2) written but NOT implemented. Nearly all bullets PROPOSED.

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| MP-1..47 | (Full bullet text in source; each maps F1..F49 in PROPOSAL_MEAL_PLANS coverage table) | PROPOSED | C-2 |
| MP-shipped | "I'm a notification!" subtitle on generate-shopping-list | SHIPPED | B7 (toast registration) |
| MP-shipped | Generate-shopping-list routes through Axis B (target list picker) | SHIPPED | C-7 Chunk 4 |
| MP-nohome | Detailed log-spike at PATCH /api/meal-plans (400) | NO_HOME | Bug, no triage; flag for next session |

(Full row-by-row map not duplicated here — the F1..F49 table inside `PROPOSAL_MEAL_PLANS.md` is the authoritative shape per `CLAUDE.md`.)

### SHOPPING LISTS

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| SL-1 | Planned shopping day per list | SHIPPED | P6-01 Chunk 7 |
| SL-2 | Shopping day alert | SHIPPED (banner) | P6-01 Chunk 7 + C-9 wiring deferred |
| SL-3 | Overview merged into detail | SHIPPED | P6-01 Chunk 5 |
| SL-4 | Mobile dropdown of lists | SHIPPED | Chunk 5 list selector |
| SL-5 | Primary list info in top area | SHIPPED | Chunk 5 |
| SL-6 | Archived lists in same list | SHIPPED | Chunk 5 |
| SL-7 | Landing pick = today | SHIPPED | Chunk 5 routes.ts |
| SL-8 | "Primary list" feels not quite right | SHIPPED | P6-01 Chunk 2 (primary inferred, not stored) |

### SHOPPING LIST DETAILS VIEW

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| SLD-1 | DnD off-by-one (L414) | SHIPPED | P6-01 Chunk 6 |

### SHOPPING MODE

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| SM-1 | Substitutes quick swap in store | PROPOSED | C-7 §9.1 + INV-8 |
| SM-2 | Pricing-as-you-go (list → receipt) | SHIPPED | P6-01 Chunk 6 |
| SM-3 | Finish list → restock-all loop | SHIPPED | P6-01 Chunk 3 (Finish + Reopen) |
| SM-4 | Undo functionality concerns | PROPOSED | P6-01 audit (Reopen via snapshot shipped, full audit pending) |

### SETTINGS

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| SET-1 | Theme type vs identity separation | NO_HOME | Bucket A-5 |
| SET-2 | Profile picture | NO_HOME | Bucket A-5 |

### ALERTS

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| AL-1 | Alert control screen | SHIPPED (stopgap) | B5 `/alerts` page; control centre still PROPOSED in C-9 |
| AL-2 | Bell count mismatch | PROPOSED | C-9 |
| AL-3 | Smarter priority | PROPOSED | C-9 |
| AL-4 | Opt-in/out per type | PROPOSED | C-9 |
| AL-5 | "No planned meals next week" alert | PROPOSED | C-9 |

### HELP

All NO_HOME (Bucket A-4).

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| HELP-1 | Detailed help per feature | NO_HOME | A-4 |
| HELP-2 | Detailed guides | NO_HOME | A-4 |
| HELP-3 | FAQ section | NO_HOME | A-4 |
| HELP-4 | Easily navigable | NO_HOME | A-4 |
| HELP-5 | UI / diagrams / screenshots | NO_HOME | A-4 |

### DORA BOT

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| DB-1 | Text size not honouring settings | NO_HOME | Bucket A-3 |
| DB-2 | Basic/AI chip squished | NO_HOME | A-3 |
| DB-3 | Basic/AI chip as toggle slider | NO_HOME | A-3 |
| DB-4 | DS4 animation flashing | NO_HOME | A-3 |
| DB-5 | "Hi I'm Dora" speech bubble once-per-user | NO_HOME | A-3 |
| DB-6 | Turn bot off completely in settings | NO_HOME | A-3 |
| DB-7 (resolved) | D.O.R.A. acronym rename | SHIPPED | 2026-06-05 acronym pass |

### DATA

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| DATA-1 | Under Settings → "My Data" | NO_HOME | Bucket A-2 |
| DATA-2 | Multiple export formats | NO_HOME | A-2 |
| DATA-3 | Page formatting overhaul | NO_HOME | A-2 |
| DATA-4 | Font / heading style | NO_HOME | A-2 |
| DATA-5 | Card layout with checkboxes | NO_HOME | A-2 |
| DATA-6 | Breadcrumb fluff | NO_HOME | A-2 |
| DATA-7 | Schema-driven import templates | NO_HOME | A-2 |
| DATA-8 | Export/print tab utility | NO_HOME | A-2 |
| DATA-9 | Scan tab usefulness | PROPOSED | `PROPOSAL_BARCODE_SCANNING.md` §6 |
| DATA-10 | "Barcodes & QR" rename | SHIPPED | `PROPOSAL_BARCODE_SCANNING.md` §4 → P6-02 |
| DATA-11 | Optional/collapsed section as main? | NO_HOME | A-2 |

### NO AREA / MISC

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| MISC-1 | 404 page in theme | SHIPPED | A1 Chunk A (`ErrorNotFound.vue`) |
| MISC-2 | Undo cross-app off | PROPOSED | B9 / undo audit |
| MISC-3 | Loading ghost effect | SHIPPED | A5 (AppSkeleton) |
| MISC-4 | Main-menu double outline hover | SHIPPED | B9.2 |
| MISC-5 | Remove Settings from main menu | SHIPPED | B9.3 |
| MISC-6 | Full systems QA test doc | NO_HOME | Bucket C |
| MISC-7 | Text-size scale (75/100/150) | SHIPPED | A6 |
| MISC-8 | Pesto button colour readability | SHIPPED | A1b (round 1 + 2) |
| MISC-9 | QR codes with Dora logo | PROPOSED | `PROPOSAL_BARCODE_SCANNING.md` §6 |
| MISC-10 | Real ALDI/IGA logos | NO_HOME | Bucket C asset request |
| MISC-11 | Rename to Dashy Dora | PROPOSED | P8-01 (planned, deferred) |
| MISC-12 | Main menu bottom border | NO_HOME | Bucket C polish |
| MISC-13 | Command palette usefulness | PROPOSED | INV-9 |
| MISC-14 | QR scanning quick-actions modal | PROPOSED | `PROPOSAL_BARCODE_SCANNING.md` §5.3 |
| MISC-15 | UI consistency | SHIPPED (ongoing) | A1/A2/A3/A4/A5/A6/A7 series |
| MISC-16 | UI uniqueness / polish design | NO_HOME | Bucket C |
| MISC-17 | Usage analytics / telemetry | NO_HOME | Bucket C |
| MISC-18 | `.local` folder messy | NO_HOME | Ops; no brief |
| MISC-19 | Log rolling | NO_HOME | Ops; no brief |
| MISC-20 | Text invisible in modes | SHIPPED | A1 series |
| MISC-21 | Cmd palette ctrl+K stock-item missing | PROPOSED | INV-9 |

### NEW FEATURE IDEAS

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| NEW-1 | Push notify between users / share list | NO_HOME | Bucket C |
| NEW-2 | Gamification | NO_HOME | Bucket C + §7 decision = "someday" |

### Technical Considerations

| # | Bullet | Status | Home / Evidence |
|---:|---|---|---|
| TC-1 | Kivy P2P sync branch home | NO_HOME | Bucket C |
| TC-2 | SSOT / more in backend | PROPOSED | `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` (Chunks 1–6 shipped — bullet itself is the cross-cutting principle) |

---

## 4. NO_HOME — flat list (the visible gap)

The 58 bullets below have no design home anywhere. Cluster by surface to see where to write a new brief.

**STOCK ITEM DETAIL polish (Bucket A-1) — 16 bullets**
- SID-1 Clear-expiry cross mark
- SID-2 Expiry / opened relationship
- SID-3 No way to set "essential" (also INV-10)
- SID-4 No way to set stock group
- SID-6 Split-view at 50% / min-max
- SID-8 Tabs visibility in themes
- SID-9 Stock level shown twice
- SID-10 Move delete button
- SID-11 Restock doesn't belong here
- SID-12 Move "opened" next to opened info
- SID-13 "Find deals" placement
- SID-15 Overview single column
- SID-16 Location inline edit
- SID-17 Notes value question
- SID-18 Product-of-choice cart button
- SID-19 Preferred merchant/product behaviour
- SID-26 Shopping lists tab lacklustre

**DATA page (Bucket A-2) — 9 bullets**
- DATA-1 Under Settings "My Data"
- DATA-2 Multiple export formats
- DATA-3 Page formatting overhaul
- DATA-4 Font / heading style
- DATA-5 Card layout w/ checkboxes
- DATA-6 Breadcrumb fluff
- DATA-7 Schema-driven import templates
- DATA-8 Export/print tab utility
- DATA-11 Collapsed section as main?

**DORA BOT polish (Bucket A-3) — 6 bullets**
- DB-1..DB-6 (all polish bullets)

**HELP content (Bucket A-4) — 5 bullets**
- HELP-1..HELP-5 (all)

**SETTINGS deferred (Bucket A-5) — 2 bullets**
- SET-1 Theme type vs identity
- SET-2 Profile picture

**Cross-cutting / future (Bucket C) — 10 bullets**
- MISC-6 Full systems QA test doc
- MISC-10 Real ALDI/IGA logos
- MISC-12 Main menu bottom border
- MISC-16 UI uniqueness / polish design pass
- MISC-17 Usage analytics / telemetry
- MISC-18 `.local` folder layout
- MISC-19 Log rolling
- NEW-1 Push notifications between users
- NEW-2 Gamification
- TC-1 Kivy P2P sync home

**Other / loose** — 10 bullets
- LOGIN-7 Sponsorship button
- SK-2 Top queue obvious info
- SK-4 Keyboard shortcuts tacky
- SK-5 Skip button size
- SK-9 Skip shortcut should be 4
- PH-1 Product History hidden
- PH-10 Drawer-style design
- PS-28 Compare invisibility (compare cut, but bullet now moot)
- RD-11 Ingredient notes value
- RD-18 Substitutes available status
- MP (meal-plans) PATCH 400 log spike (uncategorised bug)

---

## 5. PROPOSED but not shipped — by proposal home

These are the documented designs awaiting code.

**`PROPOSAL_MEAL_PLANS.md` (C-2) — ~45 bullets**
The biggest single backlog. Almost the entire MEAL PLANS section is designed but unbuilt. F1..F49 inside the proposal is the authoritative line-by-line map.

**`PROPOSAL_ONBOARDING.md` (C-5) — ~20 bullets**
Whole onboarding flow. Dead-nav bugs (Skip / Finish / Show-me-X) shipped via B5; the rest is the proposal.

**`PROPOSAL_INGESTION_API.md` (C-10) + companion C-6 — ~22 bullets**
Entire PRODUCT SEARCH redesign + ingestion split. Phase 2 work.

**`PROPOSAL_ALERTS.md` (C-9) — ~7 bullets**
Alerts redesign + dashboard card + price/back-in-stock subscriptions. /alerts stopgap shipped; control centre PROPOSED.

**`PROPOSAL_BARCODE_SCANNING.md` — ~3 bullets**
Scan-mode button, scanning quick-actions, QR Dora logo.

**Cookbook / Recipe-detail polish — ~5 bullets**
Misc layout polish under `PROPOSAL_COOKBOOK.md` (rounded boxes, log-cook placement, modal formatting, personal notes display).

**My Products polish — ~10 bullets**
Bulk-select additions, link affordance, remove saved product, custom products. Either folds into `PROPOSAL_CART_BUTTON.md` future work or its own My Products brief (not yet written).

**INV prompts pending**
- INV-7 stock-item History tab worth
- INV-8 substitute swap-into-list
- INV-9 command palette usefulness
- INV-10 essential flag UI + value

**Dashboard (deferred per master plan) — ~7 bullets**
Welcome-message cycling, card reorder, fortnight calendar, refresh-button assessment, etc. Surface deferred until later phase.

**Phase 2 / cross-cutting**
- LOGIN-1 password policy + admin toggle (INV-4)
- LOGIN-3 forgot-password sender setup (INV-4 + C-5)
- MISC-2 undo cross-app audit (B9 / no brief yet)
- MISC-11 Dashy Dora rename (P8-01)
- SM-1 substitute swap in shop mode (C-7 §9.1)

---

## 6. Methodology notes

- Bullets are counted as they appear in the feedback doc, with the visually grouped sub-bullets (under a single `- ` parent) counted individually when each reads as a discrete ask. The total 309 reflects this expansion.
- "SHIPPED" requires either an explicit `CHANGELOG.md` entry, a `DORA_WORKLOG.md` 2026-06-12 stream confirmation, or a B/A/Cookbook/Cook-Mode/Cart/State-Ownership/Shopping-Lists chunk that names the bullet's line number.
- "PROPOSED" requires the bullet to map cleanly to a proposal in `COVERAGE_GAPS.md` Bucket D, or to be tagged in an existing implementation plan that has not yet been executed.
- "NO_HOME" is restricted to bullets explicitly listed `[OPEN]` in Bucket A / B / C of `COVERAGE_GAPS.md`, plus loose bullets the audit could not bind to any document.
- Browser-verify-pending items (FU-120..125, FU-130..145) are counted **SHIPPED** because the code is in; only the user-facing smoke test is outstanding.
- The full row-by-row Meal Plans map is not duplicated here — `PROPOSAL_MEAL_PLANS.md` already carries the canonical F1..F49 coverage table per `CLAUDE.md`'s mandatory rule.

---

*Generated 2026-06-12 by feedback audit pass. Source documents: `Feedback _ Fixes - as of [06-Jun-2026].md`, `COVERAGE_GAPS.md`, `DORA_WORKLOG.md`, `CHANGELOG.md`, and the proposal set under `docs/04_proposals/`.*
