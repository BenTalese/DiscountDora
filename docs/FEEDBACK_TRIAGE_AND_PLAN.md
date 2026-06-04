# Feedback Triage & Action Plan

**Status:** Processing pass — for your confirmation before any code changes
**Date:** 2026-06-04
**Source:** `Feedback / Fixes (MASTER).md` (~250 items across ~25 areas)

> Your instructions were: analyse and generate prompts, but **check impacts with me before acting**, flag where I think you've **misunderstood** the current app, and tell you if you've **missed reviewing any Dora features**. This document does the analysis and sets up the work. It does **not** change code. Nothing here is actioned until you confirm.

---

## Corrections after your review (2026-06-04)

Your answers changed several things in this doc. Captured here so the rest stays accurate:

- **My code copy is stale; yours is newer.** Biggest drift: **meals have been merged into recipes** — the meals page is gone, the **meal planner now takes recipes with amounts**, and recipes track a pool of available (batch-cooked) portions. Treat anything I derived from the old meals/recipes/meal-plan code as needing re-grounding against your live code.
  - **Consequence: Bug B2 below is already fixed in your version.** My files showed the planner endpoint demanding `meal_id`; you moved it to recipes, which is why your UI correctly sends `recipe_id`. Struck through below.
- **Delivery model = portable prompts, not direct edits.** Since my files lag yours, I won't edit them. Each work-unit becomes a self-contained prompt (that re-reads your current code) you run against the live repo — matching your "generate prompts" instruction.
- **Sequencing chosen: Foundations first (Wave A).**
- **Areas you're deferring (do not design, but track ripple into them):** dashboard, reports, waste, settings, mobile view. The app is highly interconnected, so I'll flag when other work impacts these.
- **C1 "dark mode" is an audit, not a build.** Confirmed a mature token system exists (`tokens.scss`, `themes.scss` — 5 families × light/dark, font-size scale wired to prefs). The bugs are components **bypassing** the tokens with hardcoded colours. The fix is a token-compliance sweep.

> **Superseded for sequencing & strategy by `RECONCILED_FINISHING_PLAN.md` (the master).** This doc remains the *feedback → work mapping* (the what/why). For *order* and *decisions*, defer to the master. Key consequences:
> - **Scraper extraction:** product-search work — §2's "Product search performance" and "Merchant vs data-provider" rocks, and prompt-pack C-6/C-8 — is **companion-app scope, not Dora-core** (master §7 Decision 1).
> - **Wave → Phase:** Wave A + B + INV = **Phase 0**; Wave C = **Phases 1–3** (master §5). The §8 ordering below is folded into the master's phased plan.
> - **Charter cuts resolved:** product comparison → companion; recipe comparison → **INV-6** (assess first); gamification → someday-list; nutrition → off + simple kcal.

---

## 0. How to read this

Your feedback was written page-by-page, in isolation ("I reviewed page by page in isolation half the time"). The single most useful thing I can do is collapse that back into **cross-cutting work** — because ~40% of the list is the *same handful of problems* repeated on every screen. Fixing those once, centrally, is far better than fixing them 15 times per-page (and is exactly how you avoid the inconsistency you keep flagging).

So this is organised by **type of work**, not by page:

1. Cross-cutting themes (do once, apply everywhere)
2. Big rocks (large redesigns with wide ripple — most already have proposals)
3. Bugs (grouped by shared root cause)
4. Questions you asked me (answered where I can; flagged where I must investigate)
5. Likely misunderstandings to confirm
6. Coverage gaps — what you haven't reviewed yet (incl. Dora)
7. How this maps to the 6 proposals already written
8. Proposed working process

---

## 1. Cross-cutting themes (do once, centrally)

Each of these recurs across many pages. Treating each as **one** work-stream with a shared component/rule is the fix for the "Consistency!" and "componentise!" notes that appear throughout.

| # | Theme | Where it recurs | Nature |
|---|---|---|---|
| C1 | **Theme-awareness / dark mode is systemically broken** | splash, login, onboarding, dashboard ("dark mode not working"), product search (white-on-white search bar, loading area, card bottom), pesto-dark chips unreadable, hover bubbles, tab buttons, timer, comparison chips, cook-mode boxes, recipe cookable box, meal-plan cards/headers, 404 page, "a lot of text isn't visible in dark mode" | One root cause: components hardcode colours instead of theme tokens. **This is a single theming audit**, not 15 fixes. |
| C2 | **Filter system is inconsistent and has a real bug** | stock, product search, my products, recipes | "Empty input filters everything out" (should = filter off) is a **bug** on every screen. Plus: shown/hidden/active states, clear-button styling when active, multi-select pattern. One shared filter component + rule. |
| C3 | **Toolbar / buttons not standardised** | "app-wide", stock, my products, recipes, recipe detail, "create X" button placement varies per page | One standard toolbar + standard button (size/height/width), standard "create" placement, standard filter button. Exceptions (glow) by purpose only. |
| C4 | **Page header counts → sticky footer** | stock, my products, recipes | One componentised sticky footer for page-level counts/info. |
| C5 | **Modals must close on click-outside + have Cancel** | add-stock vs new-recipe inconsistency, recipe delete, cook-mode finish, unsaved-changes modal | One modal standard. Several are **bugs** (click-out navigates anyway). |
| C6 | **The "stock item chip" should be removed** | stock overview + everywhere it's reused (stock detail, recipes, substitutes) | Keep only: stock-level indicator + row outline highlighting. Removing it touches every screen that renders it. |
| C7 | **Shopping-cart button — standardise + define behaviour** | stock overview, stock detail, recipe detail, my products | You flagged this as having "many branching paths" (no products → list logic; products → choice modal; multiple lists; etc.). **Needs a decision-tree design + one component.** High ripple. |
| C8 | **Stock-level quick-change button** | stock overview, stocktake, stock detail | Big coloured no-text button, consistent everywhere, shows colours (stocktake currently text-only). |
| C9 | **Location should display main zone, not sub-shelf** | stock overview, add-stock modal, stock detail, cook-mode grouping | "Left shelf" means nothing alone. Display/data decision applied everywhere. |
| C10 | **Money/budget features must be opt-in & hideable** | recipe cost, meal-plan budget, "all budget/money features outside basic product search" | One global setting gates all money UI. |
| C11 | **Nutrition must be opt-in (off / simple / complex)** | new-recipe modal, recipe detail | One setting + a tiered model. |
| C12 | **User-configurable taxonomies in Settings** | recipe tags, dietary tags, cuisine/category, "tools required", meal-plan times-of-day, nutrition DB | Pattern: seed defaults, let user add/edit/remove in settings. One generic "managed lookup list" mechanism, reused. |
| C13 | **Drag/drop + tap/click alternative everywhere** | meal plans, "anywhere you can drag/drop", card reorder on dashboard | Drag = power-user; always offer a tap menu; disable drag on mobile. |
| C14 | **Loading skeletons / one loading animation** | "use the first-load pulse everywhere", stock detail "Stock Item" placeholder, product search | One loading component, used everywhere. |
| C15 | **Text-size system** | "not applied everywhere", "expected 75/100/150%", many small-text complaints | Fix the scale + apply the token globally. |
| C16 | **Remove "refresh" buttons** | dashboard, my products, stocktake | You see no value anywhere; remove unless justified. |
| C17 | **Page-state on navigation — decide per app** | product search (partial state kept), "assess for each screen" | One rule: what persists vs resets on nav. |
| C18 | **Rename pass** | Discount Dora → **Dashy Dora** (app-wide); "Mark made" → **"Mark cooked"** (app-wide); Recipes page → **"Cookbook"**; Dorabot → **D.O.R.A.** | Mechanical but must be consistent + complete. |
| C19 | **Splash / cannot-connect / login / onboarding shared styling** | those four screens | One shared auth-shell style (keep the Dora animation/placement). |

> **Recommendation:** the cross-cutting themes should be built/fixed *first*, because almost every per-page note then resolves for free. Doing pages first guarantees re-work.

---

## 2. Big rocks (large redesigns — wide ripple)

These are not tweaks; each is a feature redesign with knock-on effects. Several already have proposals (see §7).

| Rock | Scope | Ripple warning | Proposal? |
|---|---|---|---|
| **Meal Plans redesign** | template-based plans, calendar week-picker widget, scrolling carousel, recurring plans, batch-vs-fresh UX, slot-per-meal (not always "Dinner"), favourites/"haven't had in a while" trays, Dora-assisted planning | Touches recipes, meals, shopping-list generation, the meal/recipe data model (see Bug B-MP1), and budgets. The **biggest** item in the doc. | Partial — needs its own |
| **Shopping Lists merge + primary rethink** | merge overview into detail, planned-shop-day, shop-mode-as-receipt, finish→restock-all loop, undo review | You independently re-derived my proposal. | ✅ `SHOPPING_LIST_REDESIGN_PROPOSAL.md` |
| **Stock Overview overhaul** | top-area teardown, chip removal (C6), cart button (C7), scan mode, detail-view-only-on-mobile nav model | Detail-view-on-mobile-only is a **navigation-model change** (deep links, desktop drawer) — confirm carefully. | Needs one |
| **Onboarding overhaul** | starter-template data (pick-and-choose common items), feature toggles, core-values/vision explainer, stock-item-vs-product explainer first, demo-data toggles, celebration | Ties to settings (feature flags), seed system, and the "empty DB" question (M2). | Needs one |
| **Recipe Cookbook overhaul** | cost estimate, versions, multi-part recipes, tools-required, images, tag system | Ties to budget (C10), taxonomies (C12), meal plans. | Partial |
| **Cook Mode overhaul** | serving auto-adjust by headcount, ingredient grouping by location, finish→restock checklist, tools section, celebration | Ties to onboarding headcount, location model (C9), shopping list. | Needs one |
| **Theme system split** | type (system/light/dark) × theme (pesto/lemon) as separate axes; fix dark mode (C1) | Settings redesign + the systemic theming audit. | Needs one |
| **Single source of truth (backend-owned logic)** | "more in the backend the better" (your line 511) | **This is exactly the state-ownership refactor.** | ✅ `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` |
| **Product search performance & anti-blocking** | 20-30s searches, concurrent users, scraping-block risk | **→ COMPANION APP** (master Decision 1). Dora-core owes only the ingestion API (C-10). | Companion |
| **Multi-user / sharing / notify / P2P** | share lists, notify users, kivy P2P sync | All the latent single-tenant landmines. | ✅ `MULTI_USER_READINESS.md` |
| **Merchant vs data-provider model** | they're conflated; a merchant (ALDI) ≠ a data provider | **→ COMPANION APP**; its source-label informs Dora's ingestion API (C-10). | Companion |
| **Alerts control centre** | dedicated alerts page, opt-in/out per type, bell-count fix, smarter priority | Recurs in dashboard, price history, alerts. | Needs one |
| **Dashboard redesign** | alert summary card, fortnight calendar widget, card reorder, welcome-message system | Kitchen-sink home screen. | ✅ `DASHBOARD` (in state-ownership scan; could expand) |

---

## 3. Bugs (grouped by shared root cause)

Several "different" bugs are the **same** backend issue. Fixing the root fixes the cluster.

### B1 — `extra="forbid"` request models reject frontend payloads
**Symptom:** "Extra inputs are not permitted" on: save product, quick-add product, link product, mark product inactive (Product Search + My Products).
**Root cause:** request schemas use `ConfigDict(extra="forbid")` (confirmed in `create_product.py`, `update_product.py`); the frontend sends extra/computed fields the schema rejects.
**Fix shape:** align the frontend payloads to the request contracts (or relax specific schemas) — but **do it deliberately**, since `extra="forbid"` is a good guardrail you don't want to blanket-remove.

### B2 — ~~Meal-plan update expects `meal_id`, frontend sends `recipe_id`~~ — RESOLVED in your version
~~Dragging a meal onto a day → 400.~~ **Superseded by your meals→recipes merge:** the planner now takes recipes-with-amounts, so the `recipe_id` payload is correct against your current schema. This was an artifact of my stale `meal_id` code. No action — but the 400 in your log predates the merge, so confirm it no longer reproduces. The broader design question (recipes carry the available-meals pool; batch-vs-fresh) is now settled in your code and just needs re-grounding when we reach the Meal Plans rock.

### B3 — PATCH-that-is-really-PUT collides on unique name
**Symptom:** can't save a stock item / recipe unless you change the name → "a stock item with name X already exists." (Stock Detail, Recipe Detail.)
**Root cause:** update sends *all* fields incl. unchanged name; the handler re-validates uniqueness against itself.
**Fix shape:** true PATCH semantics (only changed fields) **or** exclude-self from the uniqueness check. You flagged "be careful with this" — agreed; it needs the partial-update pattern done right, app-wide.

### B4 — Delete stock item → FK constraint failure
**Symptom:** `IntegrityError: FOREIGN KEY constraint failed`.
**Root cause:** the item is referenced (recipe ingredients, shopping-list lines, products, etc.) and cascade/cleanup isn't configured.
**Fix shape:** decide cascade vs. block-with-explanation vs. soft-delete. Ties to your "dangling reference" warning copy on Stock Detail.

### B5 — Navigation / dead buttons (onboarding & dashboard)
Skip-everything, finish, "Show me X" cards, dashboard "Continue", **Alerts → 404**. Cluster of missing routes/handlers.

### B6 — Allocation (meals ↔ meal plans) appears non-functional
Recurs: Recipes Overview ("allocation logic seems not working"), Recipe Detail, Meal Plans ("allocating a meal does not affect x unallocated of x on hand"). Likely one broken feature. Needs investigation — and overlaps B2's meal/recipe question.

### B7 — Notification/toast defects
Placeholder "I'm a notification!" subtitle (Meal Plans) — unprofessional, must be purged app-wide. Stocktake double/contradictory toast ("0 added, 1 already" + "added to primary").

### B8 — Recipe Detail dead/wrong actions
Remove-from-favourites does nothing; clicking recipes nav fails → overview; recipe actions inert except Cook; **substitute permanently swaps/edits the recipe** (should be temporary); references the **deleted substitutes-graph** feature.

### B9 — Misc concrete bugs
Unlink-product → exception (Stock Detail); shopping-list-detail drag-drop **off-by-one** (wrong items swapped); product-history selection does nothing + graph clipped + hover bubble not themed; command palette (ctrl+k) doesn't fire create-stock-item; undo cross-app inconsistent (push-expiry then clear-expiry); main-menu hover double outline; settings duplicated in menu + dropdown; logs not rolling (46k-line file, wrong date span); floating Dora vanishes on mobile login; Dora image off-centre (search + dashboard).

---

## 4. Questions you asked me

**I can answer / investigate from the code:**
- *Forgot-password email sending* — it's SMTP-based and likely unconfigured by default; your instinct (admin sets up a sending account in onboarding; hide the button if unset) is the right model. I can confirm the current wiring.
- *Stock overview 1-3s delay / "what changed after DS4?"* — needs a perf investigation + a look at the DS4 animation commit. I can do this.
- *"What else is like stock groups — field exists, no UI to set it?"* — I can **audit** the whole data model for orphaned fields (this is a concrete, valuable pass).
- *QR vs register-barcode; show-QR vs print-QR* — I can map what each actually does and whether they're redundant.
- *Allocation logic working?* — see B6; needs investigation.
- *Relevancy filter (product search)* — I can trace how it ranks.

**Genuinely open design questions (your call, I'll advise):** expiry↔open relationship; value of stock groups / notes / preferred-merchant / history-tab / recipe-comparison / command-palette / substitutes-swap-into-list. These are "keep, rework, or cut" calls — I'll give a recommendation on each when we get to that area.

---

## 5. Likely misunderstandings to confirm (per your instruction)

1. **"You already have groups/locations set up" on first-run onboarding.** You read this as dev data leaking. More likely it's *defensive copy* that always shows, regardless of DB state. The fix could be cosmetic (detect true first-run, change wording) **or** there genuinely is non-system seed data — I need to check which. Don't assume it's leaked data yet.
2. **"Detail view only on mobile."** This removes the desktop drawer/standalone split and makes row-click the only nav. That's a real navigation-model change (deep-linking, the 50%-splitter notes elsewhere contradict it). Confirm you mean *drawer on desktop, full-page on mobile*, not "no detail on desktop."
3. **Cookable "remove from meal planner."** Agreed it doesn't belong on the planner — but note cookable is currently computed client-side (Type A in the state doc). The clean fix routes through the backend-owned field, so this small note is coupled to a bigger refactor.
4. **Meal plans hold recipes or meals?** (B2.) Your feedback treats them interchangeably ("drag a meal", but the log sends `recipe_id`). The whole Meal-Plans redesign hinges on settling this. **This is the most important single decision in the document.**
5. **Single-source-of-truth (line 511).** I'm reading this as explicit sign-off to proceed with the state-ownership refactor. Confirm.

---

## 6. Coverage gaps — what you haven't reviewed yet

You asked me to flag if you missed features — especially Dora. You did.

**Areas with no / empty feedback:**
- **Reports** (you wrote "?") and **Waste** ("?") — not reviewed.
- **Mobile view** — empty section.
- ~~**Stock Map**~~ — **removed feature**, not unreviewed; ignore (my earlier flag read stale code).
- **Locations management pages** — only the location *chip* was reviewed, not the Locations Overview / Detail pages.
- **Settings sub-pages** — Audit Log, Users Admin, Merchants (only touched via "providers" conflation), Backup/Restore (partly under DATA).
- **Stock Groups** — flagged as "forgotten"; needs a keep/cut decision, not just a note.

**Dora assistant — you reviewed the *chrome*, not the *capabilities*.** Your "DORA BOT" section covers the chip, animation, speech bubble, on/off toggle, and rename. But you gave **no** feedback on what Dora can actually *do*:
- the ~25 data tools + 8 action tools (search, suggest recipes, conversions, price stats, expiry-rescue, add-to-list, update-stock, push-expiry…),
- the **confirmation flow** when it takes an action (this is well-built — worth your eyes),
- the **suggestion panel** and the **contextual quick-action chips**,
- the **capability gap between "Basic" and "AI" modes** (Basic does a fraction of what AI does — users won't know why),
- **voice input/output**.

👉 **Request:** please do a focused review pass of Dora's *capabilities* (open the chat, try asking it to do things, watch the confirmation cards and suggestions). I've written `DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md` describing the current behaviour — reviewing against that would close the gap. Also worth a pass: **Reports and Waste** (since deferred by you). Stock Map is removed — skip.

---

## 7. This validates the proposals already written

Strikingly, your independent page-by-page feedback re-derived the conclusions of the six docs from earlier sessions:

- *"Single source of truth, more in the backend"* (line 511) ↔ **STATE_OWNERSHIP_REFACTOR_PROPOSAL**
- *"Primary list feels not quite right"* + shop-mode-as-receipt + restock loop + undo review ↔ **SHOPPING_LIST_REDESIGN_PROPOSAL**
- share lists / notify users / P2P sync ↔ **MULTI_USER_READINESS**
- Dora basic/AI toggle + on/off + rename ↔ **DORA_ASSISTANT_ARCHITECTURE_PROPOSAL** (the basic/AI capability cliff)
- dashboard alert-summary + calendar widget + card reorder ↔ the **dashboard** findings
- forgot-password / email setup / CSRF-adjacent ↔ **AUTH_ASSISTANT_SECURITY_FINDINGS**

That's strong corroboration that those refactors are the right backbone — the per-page polish hangs off them.

---

## 8. Proposed working process

Generating 250 prompts now would violate your "check impacts first" rule. Instead:

1. **Settle the 5 decisions in §5** (especially #4, recipes-vs-meals). These unblock everything downstream.
2. **Coverage reviews (§6)** — Dora capabilities, Reports, Waste: now **deferred** by you (revisit later). Stock Map: removed, skip.
3. **Sequence the work**, recommended order:
   - **Wave A — cross-cutting foundations** (C1 theming, C2 filters, C3 toolbar, C5 modals, C14 loading, C18 renames, C15 text-size). Highest leverage; resolves most per-page notes for free.
   - **Wave B — bug clusters** (B1–B9). Mostly independent; can run alongside A.
   - **Wave C — big rocks**, each gated by its own impact check: state-ownership → shopping lists → stock overview → meal plans → recipes/cook → onboarding → dashboard → alerts → merchants → product-search-perf.
4. **Per work-unit ritual** (honouring your instruction): before any code, I give you a short **impact brief** — what changes, what else it touches, what you might not have realised — and you confirm. Only then do I generate + run the implementation prompt.

I'll track the whole thing as a living backlog so nothing is lost.

---

## 9. What I need from you now

- Answers to the **§5 decisions** (recipes-vs-meals is the big one).
- A yes/no on doing the **§6 coverage reviews** before we design those areas.
- Agreement on the **§8 sequencing** (Wave A first), or your preferred order.
- Anything in §1/§2 where my grouping doesn't match your intent.
