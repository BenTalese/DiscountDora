# Wave C — Big-rock design briefs

**Type:** 🔵 design briefs — each produces a **proposal doc, changes NO code.** You approve the proposal, *then* we write implementation prompts.

**Why briefs, not implementation:** these areas have heavy open design questions in your feedback ("help me design this", "thoughts?") and several sit in code that drifted from my copy (esp. recipes/meals). One-shotting them would be reckless. Each brief tells the agent to read the live code, then propose.

**Global rule for every brief below:** read the relevant current code FIRST; treat the deferred areas (dashboard, reports, waste, settings, mobile) as *do-not-redesign* but *note ripple into them*; honour the cross-cutting standards from Wave A (tokens, standard button/modal/filter); output a single proposal markdown file; list open decisions for me.

---

## C-1 — Stock Overview redesign → `PROPOSAL_STOCK_OVERVIEW.md`
Read the current stock overview. Propose a redesign covering: top-area teardown (all action buttons grouped; filters behind a toggle; counts → sticky footer via A7); **remove the stock-item "chip"** keeping only stock-level indicator + row-outline highlight; **stock-level quick-change button** first in row (big coloured, no text — the focus action); row click → detail (desktop drawer / mobile full-page — confirm the nav model); mobile long-press → multi-select (Google-Drive style); optional **scan mode** (pick an action applied to scanned items); show/hide images (saved pref); taller rows + emphasised name; expiry button moved right (date-picker if unset; +1/+7/+14/clear if set); replace "# recipes" with "# upcoming planned meals". **Open decisions:** the row-click vs button-tap miss risk; exact footer counts; how scan-mode relates to stocktake. Defer the **shopping-cart button** to C-7. Note ripple to the cart button, location display (C-cross), and the planned-meals metric (needs meal-plan allocation, C-2).

## C-2 — Meal Plans redesign → `PROPOSAL_MEAL_PLANS.md`
**Re-ground first:** meals are merged into recipes; the planner takes recipes-with-amounts; recipes hold an available-meals pool. Verify current behaviour. Then propose the redesign you described: template-based plans (save/apply templates, recurring/rotating); a sequential builder (pick meals → required stock → build shopping list from what's missing → email/print); a custom **calendar week-picker** widget (week selection, status underlines, current-day marker, minimalist rounded squares) on the right above shopping info; a **scrolling carousel** main area (prev/next week with animation); a filterable vertical recipe list (hundreds of items) on the left; favourites + "haven't had in a while" trays; **tap/click add** alongside drag (drag disabled on mobile); slot per entry (not always "Dinner"); same recipe dropped twice increments count; configurable times-of-day. **Critical UX requirement:** must serve BOTH batch-cookers (store meals) and fresh-cookers (cook same day) without feeling overbearing. **Folds in B6** (allocation: allocating should affect "x unallocated of x on hand" — verify/repair). **Open decisions:** recurring×editing coexistence; how applying a template handles past days (read-only?); shortfall banner — keep or redundant?

## C-3 — Cook Mode redesign → `PROPOSAL_COOK_MODE.md`
Read current cook mode. Propose: **finish-cooking flow that closes the loop** — per-item stock-level update checklist (choose levels) + quick add-to-shopping-list, replacing the blunt "update everything" toggle; **serving auto-adjust** by headcount (default from onboarding, adjustable per session, zero friction); ingredients **grouped by base location** (fridge/pantry); a **tools section** (if recipe has tools) highlighted per step like ingredients; **highlight** ingredients used per step instead of ticking (assess removing ticking entirely); theme-aware **timer** with sound + fill-bar; unit formatting (space rules, "2 scoops" not "2scoops"); clearer **voice ("sous chef")** affordance; a finish **celebration**; "how many meals did you save?" framing for batch cookers; sub-steps/hints handling. **Open decisions:** ticking removal; sub-step model; quantity-unit inclusion list. Note ripple to recipes (tools/versions), onboarding (headcount), shopping list.

## C-4 — Recipes / Cookbook redesign → `PROPOSAL_COOKBOOK.md`
Read current recipes (post-merge). Propose: rename page "Cookbook"; recipe **images**; **versions** ("new version"/"manage versions"); **multi-part recipes** (sections and/or linked sub-recipes — compare approaches); **tools-required** (configurable list); recipe **source** as its own field; URL **import** (with which-sites-likely-work guidance); recipe **cost estimate** (opt-in, from linked-product/history data; feeds meal-plan budgets) — gated by the money opt-in (C-cross); **nutrition** tiers off/simple/complex (opt-in); tag system overhaul — dietary tags as a single toggle filter (must/must-not/neutral), cuisine & category as single-select and **not** lumped together, all tag taxonomies user-configurable in settings (C-cross); editable in-stock count + allocated-meals box on cards; useful filters (planned-in, last-made, meal-count, in-stock); **recipe-comparison fate is decided by INV-6** (assess worth → rework or cut) — don't re-litigate here; if INV-6 says keep, fold its redesign in. **Open decisions:** multi-part model; versions UX; cuisine-vs-category fate. Heavy ripple to meal plans, cook mode, shopping list, budget.

## C-5 — Onboarding redesign → `PROPOSAL_ONBOARDING.md`
Read current onboarding. Propose: shared auth-shell styling; explain **Dora's vision/core values & core workflows** with diagrams/flowcharts (sell it) before asking for data; **stock-item-vs-product explainer** BEFORE "add stock items" (milk = stock item; "Vitasoy Oat Milky @ Coles" = product); a **starter template** of common household stock items with sensible locations, pick-and-choose on/off (fastest path to value); demo recipe/meal/plan toggles (warn they need demo data); theme step = system/light/dark only (maps to pesto variants); first-login admin **feature enable/disable** (mirrored in admin settings) + "invite other users later" wording; headcount ("how many do you cook for") feeding cook-mode auto-adjust; preferred stores; **finish celebration** (confetti); fix the "you already have groups/locations" copy (see INV — confirm whether it's wrong wording on a truly-empty DB or real seed data). **Open decisions:** which features are toggleable at first-login; starter-template contents. Ripple to settings (feature flags — deferred, note it), seed system, cook mode.

## C-6 — [COMPANION APP] Product Search performance & anti-blocking → `PROPOSAL_SEARCH_PERF.md`
**Scope: the standalone companion app, NOT Dora-core** (master Decision 1 — scraping leaves Dora; the companion pushes data in via C-10's ingestion API). Read the search path (frontend + merchant_api/scraping) *in the companion*. Investigate & propose for: 20–30s searches with all merchants enabled → **concurrent provider search** and/or **streaming results as they arrive**; and **scraping-block risk** (rate/identity/concurrency across multiple users) → how to avoid being blocked. Report current architecture, bottlenecks, and a concrete plan (concurrency model, progressive rendering, backoff/throttling, caching). Also fold in the **merchant-vs-provider** terminology fix only if it touches search wiring (full model is C-8). **Open decisions:** acceptable latency target; how aggressive to fetch vs block-safety. This one is part-investigation, part-design.

## C-7 — Shopping-cart button (the multi-path component) → `PROPOSAL_CART_BUTTON.md`
You flagged this as deeply branching. Read every place a cart/add-to-list control appears (stock overview, stock detail, recipe detail, my products, meal plans). Propose **one componentised button** with a defined decision tree: no products linked → add by list logic; one product → add it; multiple products → choice modal; multiple lists → which-list resolution; awareness of the item's current list state (already on list, ticked, etc.). Incorporate the **products-without-stock-items** rule from My Products feedback (product can be on a list standalone; nesting under a stock item when linked; removal cascades/asks). **Open decisions:** the full state×action matrix (I'll co-design). This underpins C-1, recipe detail, my products — sequence it early among the rocks. Aligns with `SHOPPING_LIST_REDESIGN_PROPOSAL.md`.

## C-8 — [COMPANION APP] Merchant vs data-provider model → `PROPOSAL_MERCHANT_PROVIDER.md`
**Scope: the companion app** (the merchant/provider model lives there); its output **source label** is what Dora's ingestion API (C-10) records. You clarified: a **merchant** is a company/stores (ALDI, Coles); a **data provider** is a source of product data (often the merchant's site, but also third parties). They're conflated (visible on manage-merchants). Read the merchant/product/offer model. Propose a clean separation (merchant ↔ provider(s); offers reference a merchant, sourced via a provider), the migration, and the manage-merchants UI change. **Open decisions:** can one merchant have multiple providers / one provider serve multiple merchants (many-to-many?). Ripple to product search, offers, price history.

## C-9 — Alerts control centre → `PROPOSAL_ALERTS.md`
Read current alert generation + the bell + dashboard alert card. Propose a dedicated **alerts page** (nice display: summary section — types/counts/themes — plus a top-N preview + "see all"); **per-type opt-in/out** ("as quiet or noisy as they want"); smarter priority/what-counts; per-type unique icons/styling; fix the **bell-count mismatch** (number bubble ≠ count when opened); new alert type "**no planned meals next week**"; central management that also covers the context-aware alerts (e.g. price-history "notify under"). **Open decisions:** priority model; which alerts default on. Note: the dashboard alert *card* redesign is deferred (dashboard) but this defines what it'll show.

## C-10 — Ingestion-API contract (Dora-core seam) → `PROPOSAL_INGESTION_API.md`
**Dora-core, NOT the companion.** Design the authenticated endpoint Dora exposes for external price/product data to be pushed in — used by the scraper companion (C-6/C-8) and later P8-03 (email) and P8-04 (crowd). Read the current product/offer/price-history models. Propose: accepted payloads (`product`, `offer`, `price_observation`; batched + idempotent; each carrying a `source` label), how Dora dedups/maps them into the product catalog + personal price history (feeds P6-01/P6-03), the auth model, and the explicit boundary (Dora never calls out; sources call in). **Open decisions:** conflict/overwrite policy for price history; sync vs async. **Gates C-6/C-8** (the companion targets this contract). See master plan §6.6.

## C-cross — Config, opt-ins & taxonomy settings → `PROPOSAL_CONFIG_AND_OPTINS.md`
The cross-cutting config layer that C-1/C-4/C-5/C-9 each defer to. Owns, once:
the **money opt-in** (gates recipe cost C-4 §2.8 + meal-plan budgets C-2, leaves
basic product-search prices alone); the **nutrition mode** off/simple/complex
(C-4 §2.9 — build off+simple, reserve the nutrition-DB seam); the four
**taxonomy settings editors** (dietary tags / cuisine / category / tools — seeded
defaults + add/edit/remove, delete-safe; C-4 defines the vocabulary, this builds
the editor); the **location-display policy** (show the zone, not "right shelf";
breadcrumb on demand — C-1 §2.5, C-3 grouping); and the **feature-flag panel**
(install-wide enable/disable, the settings mirror of C-5's first-login step).
Two tiers: per-user opt-ins on `User`, install-wide config on `AppSetting` + new
taxonomy tables. **Does NOT** redesign the settings shell (deferred), build the
nutrition-DB integration (reserved seam), own the per-type alert matrix (C-9), or
the cuisine-vs-category keep/collapse call (C-4 open-decision 1). **Open
decisions:** money-flag vs overloaded-NULL; the toggleable-feature set; taxonomy
edit permission; whether to add a per-user location-detail pref. Written
2026-06-06.

## C-locale — Locale & international readiness → `PROPOSAL_LOCALE_I18N.md`
User-floated (2026-06-06): make Dora usable outside Australia. The companion split
(Decision 1) solves *product sourcing* (products can be from anywhere via C-10),
but Dora-core still carries AU residue: hardcoded `$` currency, `en-AU` voice
default, AU merchant branding/copy/seed in core, and a **dormant vue-i18n scaffold**
(plumbed in `boot/i18n.ts` but unused — stub messages, zero `$t()`). Three layers:
**A. currency/number-format neutrality (do now), B. de-AU the core (do now),
C. full UI translation (deferred big rock).** **Open decisions:** currency home
(install-wide vs per-user); vue-i18n adopt-lite-for-formatting vs rip-out; whether
C-10 price observations carry a currency; merchant-logo fate. Written 2026-06-06.

## C-waste — Waste minimisation → `PROPOSAL_WASTE_MINIMISATION.md`
User-floated (2026-06-24) after the `WASTE_PAGE_ASSESSMENT_2026-06-24.md` scratch read. The
`/waste` page is dissolved into smaller surfaces: row-level `Mark as wasted` under the
existing expiry dropdown (tile-grid modal, reason only, no value/note/freeze/out-of-stock,
Undo toast); a new `Expires soonest` sort on StockOverview (replacing the misimplemented
`Stalest first`); a new `Uses expiring ingredients (14d)` filter on Cookbook (recipes ordered
by count of expiring ingredients used; per-card badge only when the filter is active); the
dashboard `Use soon` card removed (`Needs your attention` absorbs); the `/waste` route
deleted (no redirect, pre-release). Backend: `StockItemWasteEvent` schema slimmed (drop
`quantity`/`estimated_value`/`note`); `waste_insights` Dora tool simplified to "most/recently
wasted"; `expiry_rescue` unchanged; `frequent_waster` suggestion deep-link re-pointed to
StockItemDetail. **All decisions resolved in-session — see PROPOSAL §2.** Charter pillar of
the future Dora Score is preserved as a *signal* (events still logged + queryable) but the
de-emphasis of waste as a UI feature spawns **FU-302** (Dora Score reassessment, deferred
pre-Phase 3). Written 2026-06-24.

## C-help — Opt-in contextual help overlay → `PROPOSAL_HELP_OVERLAY.md`
User-floated (2026-06-06): a persistent **"?" toggle** that overlays dismissible
"what does this do" bubbles on the current page's controls — the **opt-in inverse**
of the forced first-run tour C-5 removed. Complements (not replaces) the existing
Help page + assistant; fills the missing *in-context* help modality. The mechanism
is cheap client view-state; the real cost is **content** (a hint per element kept
from rotting), so the design favours a co-located `v-help` directive + a dev-time
orphan check, with hints rolled out per-surface as each C-1..C-9 lands. **Open
decisions:** reveal-all vs hover-to-reveal; co-located vs central content model;
mascot-fronted vs plain; discoverability. Written 2026-06-06.

---

## C-impl — Implementation-planning prompts (proposals already exist)

### Shopping Lists → `IMPL_PLAN_SHOPPING_LISTS.md`
Read `SHOPPING_LIST_REDESIGN_PROPOSAL.md` (if present) and the current shopping-list code. Produce a **phased implementation plan**: the `DRAFT→SHOPPING→DONE` status model + migration; remove stored "primary" → contextual target inference; merge overview into detail; planned-shop-day + alert; shop-mode-as-receipt + finish→restock-all; review-undo rework. Sequence with risk notes and a first reviewable chunk. No code yet — plan + chunk list.

### State ownership (single source of truth) → `IMPL_PLAN_STATE_OWNERSHIP.md`
Your line 511 ("single source of truth, more in the backend") = this. Read `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` (if present) + current code. Produce a phased plan for: server-owned stock-status contract (kill duplicated "Out of Stock" string), `cookable`/`missing_count` on recipe DTOs + `?cookable=true` + dashboard `cookable_count`, then delete the client copies; Type-B server aggregates; Type-C offer-snapshot-at-add fix. Sequence + first chunk. No code yet.
