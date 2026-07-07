# Dora Follow-ups Ledger — Open

Stateful backlog of **open follow-ups, deferred jobs, leftovers, and findings**
surfaced while running prompts — the stuff that's easy for the user to miss in a
long session summary. Distinct from the other logs:

- `CHANGELOG.md` = product/code changes that shipped.
- `DORA_WORKLOG.md` = per-session handoff narrative.
- `DORA_FOLLOWUPS.md` (this file) = **open loops** that outlive a single session.
- `DORA_FOLLOWUPS_RESOLVED.md` = the archive of items that have been resolved
  (kept for the trail — never delete).

## How to use this file

- **On session start:** scan for items here. Surface the ones whose *recommended
  resolution point* is "now" or matches the work about to start, and **ask the
  user** whether they want to review/resolve them now or defer.
- **On ending a work unit:** add any new follow-ups/leftovers/findings you
  generated. If you actually resolved an item, **move its entry from this file
  to `DORA_FOLLOWUPS_RESOLVED.md`**, flip the heading from `[OPEN]` to
  `[RESOLVED]`, and add a one-line state note on how. Do not leave resolved
  items in this file, and do not delete them either — the trail matters.
- **Reported defect that "doesn't reproduce" → still log it here** as `[OPEN]`
  type `finding`, resolution "confirm in browser". A static code read is not
  proof a user-reported bug is fixed. Track each reported item individually;
  never bury several as one "all fine" note.
- Keep the newest items at the top.

## Entry template

```
## [OPEN] FU-NNN — short title
- **Raised:** YYYY-MM-DD (prompt id / task)
- **Type:** follow-up | deferred job | leftover | finding
- **What:** one or two lines.
- **Why deferred:** the reason it wasn't done in-line.
- **Recommended resolution:** now | later during <Phase/Prompt X> | when <trigger> | opportunistic
```

---

## [OPEN] FU-NNN — short title
- **Raised:** YYYY-MM-DD (prompt id / task)
- **Type:** follow-up | deferred job | leftover | finding
- **What:** one or two lines.
- **Why deferred:** the reason it wasn't done in-line.
- **Recommended resolution:** now | later during <Phase/Prompt X> | when <trigger> | opportunistic
- **State note:** (filled in when resolved — date + how)
```

---

# Open


## [OPEN] FU-510 — Late-game sweep: hand-rolled code that should be a battle-tested library
- **Raised:** 2026-07-07 (user request).
- **Type:** deferred job (audit-first, then refactor).
- **What:** Full-codebase pass looking for **wheels we reinvented** — hand-rolled implementations of problems a well-known, well-maintained library solves better (correctness, security, ergonomics, performance). Focus areas to check (non-exhaustive):
  - **Security-adjacent:** custom CSRF double-submit vs Flask-WTF / Flask-SeaSurf, hand-rolled Fernet key handling vs `cryptography` recipes, the hand-rolled security headers (FU-459) vs Flask-Talisman, session/cookie hardening, password hashing choices.
  - **HTTP / API surface:** pagination + query-string parsing (`queryStringBuilder.ts`, `parse_query_options`) vs Flask-Smorest / API-spec libs; response envelope + error translation vs a marshalling lib; audit-retention + audit hooks.
  - **Data access:** the generic repository (`SqlAlchemyRepository`), `EntityField`, `include`/`then_include` chains — vs plain SQLAlchemy 2.0 selectinload/joinedload patterns. Is our wrapper carrying its weight or fighting the ORM?
  - **Domain infra:** unit conversion (`units.py`), locale display denominators, currency + locale formatting, timezone / calendar-day helpers (`household_today`), fuzzy matching (RapidFuzz already used, but check the wrappers around it).
  - **Frontend:** own drag-drop composables (`useDragDropList`) vs vue-draggable / dnd-kit; own toast/notify wrappers; own shortcut registry (`useShortcut`) vs a library; own offline queue (`useOfflineQueue`) vs Workbox background sync; own rollback registry vs a proper undo/redo stack lib.
  - **Ops:** log rotation (already time-based), scheduling (APScheduler in place), rate limiting (present? if hand-rolled, flag it), config layering (`ConfigurationManager`) vs pydantic-settings.
- **Method (two phases, do not skip Phase 1):**
  1. **Phase 1 — assessment only.** Produce `docs/05_investigations/HANDROLLED_VS_LIBRARIES.md` listing each hand-rolled site: what it is, what library would replace it, honest verdict `keep` / `replace` / `wrap-thin-adapter`, and rough effort/risk. **No code touched.** Verdict has to weigh Charter tie-breaks (Effortless + Anti-creep): sometimes the hand-rolled thing is right because it's smaller, has no supply-chain risk, and stays coupled to our domain. Do NOT default to "always prefer library."
  2. **Phase 2 — action.** For each `replace` verdict, open a per-item FU (or an implementation plan when the surface is broad, e.g. auth stack replacement). Sequence by risk + blast radius; ship one at a time with browser-verify per swap.
- **Why deferred:** late-game / pre-commercialization hardening. Not urgent while the app is still gaining new surfaces; do it when the feature surface has stabilised so a lib swap doesn't collide with in-flight redesigns. Doing it earlier risks churning code that's about to be reshaped anyway.
- **Recommended resolution:** **late-game / Phase 4 kick-off.** Pair with the pre-commercialization hardening pass ([[FU-412]] COMMERCIALIZATION_REPORT + [[FU-409]] auth security re-audit + [[FU-424]] senior-review Tier-2 delta) — same window, same "batten down the hatches before we ask anyone to trust this" mindset. Cross-check every existing `[Removed]` and `[Kept-because…]` verdict against ENGINEERING_STANDARDS on the way out so the assessment doc becomes source-of-truth for "here's why we didn't take the lib."

## [OPEN] FU-504 — Base-component adoption residuals (~54 raw `q-btn` uses across 16 files + one `BaseButton` variant gap)
- **Raised:** 2026-07-07 (FU-424 audit close-out).
- **Type:** finding + small design decision.
- **What:** SPA-wide grep for raw Quasar primitives where a Base* wrapper exists:
  - `q-btn`: **~54 raw uses across 16 files** — mostly straightforward migrations to `BaseButton variant="ghost"` / `"secondary"` / `"icon"`. Notable defensible cases: `HelpPage.vue:11-19` (uses the `accent` Quasar palette that no `BaseButton` variant exposes), `RecipeCard.vue:99-108` + `StocktakeRunner.vue:95-113` + `AddToListButton` inline chips (all "unelevated coloured icon buttons" — a shape `BaseButton variant="icon"` doesn't currently support).
  - `q-dialog`: **8 raw uses — all defensible** (panel/sheet patterns like `AlertsBell.vue` right-slide, `MealPlanPickerSheet.vue` bottom-sheet — `BaseDialog` deliberately assumes a centered modal). Verdict CLEAN.
  - `q-btn-toggle`: 1 defensible use in `AdminSystemStocktakeSettings.vue`. Verdict CLEAN.
  - `q-btn-dropdown`: only inside `BaseDropdown.vue` (the wrapper itself). Verdict CLEAN.
- **Design decision inside this FU:** does `BaseButton` gain an `unelevated` + `color` variant to cover the 3-4 icon-button carve-outs, or do those sites stay raw as a documented carve-out?
- **Why deferred:** not ship-blocking; audit-only for now. The 54 raw uses are cosmetic — no behaviour bug, no accessibility hole (they're all wrapping Quasar which handles a11y).
- **Recommended resolution:** **opportunistic per-touch** — when any file with a raw `q-btn` is edited for other reasons, migrate it in-pass. No dedicated sweep. The unelevated-coloured-icon-button variant decision is one design call the user needs to make before the last 3-4 offenders can migrate cleanly; deferring until then. ~150-200 LOC if a dedicated pass ever ran.
- **Cross-ref:** [[FU-424]] (audit that produced this) — resolved 2026-07-07.

## [OPEN] FU-500 — Apply R-029 (hide, don't nag) app-wide — inverse sweep of the retired FU-176
- **Raised:** 2026-07-06 (user directive walking back R-014 → new rule R-029 / ADR-025)
- **Type:** follow-up (cross-cutting presentation change)
- **What:** R-014 (reveal-and-disable) is retired. R-029 (respect the off-state — hide, don't nag) is the new rule: user- or household-disabled or install-unconfigured features are **hidden** (`v-if`) outside their own settings screen, not shown-disabled with a "Set up X" hint. Sweep the app for the pattern R-014 previously prescribed and flip each site to `v-if`:
  - **Meal-plan builder Email button (C-2.J)** — `useFeatureFlags().hasEmail` false → hide the button entirely (already respec'd in `IMPL_PLAN_MEAL_PLANS.md`; verify implementation when C-2.J is built or, if already built, revisit and flip disable → hide).
  - **`NotificationsSettings.vue`** — the C-9.7 alerts email digest row + C-9.8 push row are on the settings screen that *owns* the config, so they legitimately stay (R-029 carve-out). But if any *other* surface references those and shows a disabled affordance, hide it.
  - **`AssistantSettings.vue`, `VoiceSettings.vue`, `AdminSystemEmailSettings.vue`, `AdminSystemPushSettings.vue`** — all on their own settings screens; the disabled-when-unconfigured control is the R-029 carve-out and stays. Sweep only if any of these render R-014 patterns on *other* pages.
  - **`MainLayout.vue`** (product-search-URL unconfigured hint), **`models/auth.ts`** (SMTP-unconfigured control disabled), **`useFeatureFlags.ts`** helper comments, **`menuButtonProps.ts`** (`disabledWithTooltip`) — check each usage site: if it's the config surface, keep; if it's a workflow surface elsewhere, hide.
  - **`StockItemDetailPage.vue:796`** references the scanning flag with an R-014 comment; per the user's original example, the scanning button (and any related UI outside `AdminSystemScanningSettings`) should be **hidden** when `scanning_enabled=false`, restoring the original ADR-002 hide-when-off.
  - Empty-state usages (dashboard "all clear", meal-plan empty-week banner, `DoraScoreCard`, `YourPricesWidget`) are a **different pattern**; they stay unchanged. Their R-014 comment references can be re-labelled opportunistically (they were mislabelled — "calm empty state" isn't the same rule).
- **Why deferred:** cross-cutting presentation change touching ~10 files; better as a focused small pass than folded into other work.
- **Recommended resolution:** opportunistic / a focused sweep — pair with the next touch of each gated surface. Also update **ADR-002**'s stance in `ENGINEERING_STANDARDS.md:1149` to drop the "R-014 partially revisits it" implication (R-002's hide-when-off is now the whole story again).

## [OPEN] FU-457 — Boot-time resolved-route assertion for reflection-based wiring
- **Raised:** 2026-07-03 (FU-196 umbrella disassembly — item (c)).
- **Type:** finding / hardening.
- **What:** [`startup.py:135`](dora_api/startup.py) uses `get_attributes_ending_with('router', ...)` to auto-register blueprints; [`service_wiring.py:17`](dora_api/infrastructure/service_wiring.py) and [`decorators.py:13`](dora_api/infrastructure/decorators.py) also do reflection-based wiring. If a router file has a broken import or is renamed, the failure surfaces at the first request (opaque 404), not at boot. Add a boot-time assertion that (a) every discovered `*_ROUTER` was successfully registered on `app.url_map` (compare expected vs `app.url_map.iter_rules()`), (b) every `@has_request_body`-decorated handler has a registered URL rule. Fail-fast → operator sees the misconfiguration on `flask run`, not on the first 404.
- **Why deferred:** Tier-2 hardening; current failure mode is a 404 which is diagnosable, just not obvious.
- **Recommended resolution:** opportunistic — small (30-line assertion in `startup.py` after `register_routers()`), useful the first time a router silently breaks.

## [OPEN] FU-456 — Unit-of-work refactor for multi-commit handlers (starting with `create_recipe.py`)
- **Raised:** 2026-07-03 (FU-196 umbrella disassembly — item (b)).
- **Type:** deferred job / architecture.
- **What:** [`create_recipe.py`](dora_api/features/recipes/create_recipe.py) calls `self.repository.save_changes()` five times in one handler (L273/317/332/362/379) — no unit-of-work; a partial failure leaves committed rows plus dirty session state. FU-196's belt-and-braces `db.session.rollback()` in the global handler (shipped 2026-07-03) covers the *dirty-session* half; the *partial-commit* half needs the handler restructured to a single commit at the end. Sweep other multi-commit handlers when this pattern is decided (grep `save_changes` for count-per-file). Constraint: some handlers `add()` a parent → need its id → then `add()` children referencing that id, which currently uses an interstitial `save_changes()` to force a flush. Look at whether `db.session.flush()` (no commit) is enough for those cases so the whole handler stays one transaction.
- **Why deferred:** real refactor, not a one-liner; safer to do after the rollback safety net (done 2026-07-03) rather than before.
- **Recommended resolution:** later — Type-B aggregates pass, or the next serious cookbook-editor touch.

## [OPEN] FU-451 — P6-09 budget-defense swaps (the "negotiator" half) — DESIGN LOCKED, impl deferred
- **Raised:** 2026-07-02 (P6 legacy-plan cross-check).
- **Type:** deferred job (design locked 2026-07-07; awaiting chunked impl-plan).
- **Design brief:** [`docs/04_proposals/PROPOSAL_BUDGET_DEFENSE_SWAPS.md`](docs/04_proposals/PROPOSAL_BUDGET_DEFENSE_SWAPS.md) (2026-07-07). Covers this FU + [[FU-450]] in one plan. Locked decisions: brief-first-then-chunks; both FUs ship together; UI on meal-plan week + Dashboard budget card summary bullet; preview→confirm apply with a MealPlanSwapLedger row for undo; `cost_per_week` computed server-side on-the-fly (no new column); ranker filters out `fake_markdown=true` candidates; two-pass generator (recipe swaps + product swaps) with a closed reason-chip vocab.
- **What (original):** `PROMPT_PLAN_PART_6_POLISH.md:594` had two halves. **Shipped:** per-recipe cost estimate (Cookbook Chunk 9, uses `paid_price` via FU-216). **Missing:** the headline "negotiator" — `cost_per_week` on meal-plan weeks, and the budget-defense loop that, when a week is over budget, emits ranked swap suggestions with concrete dollar savings and one-tap apply — (a) PRODUCT swap (reuse `compare_prices`), (b) RECIPE swap. Must NOT use a stock-item substitute graph (that surface is retired). Depends on P6-03 deal-quality signal (see [[FU-450]]).
- **Why deferred:** design brief written; implementation is ~6 chunks (~1200-1500 LOC + one migration + one User column) and warrants a proper chunked impl-plan session rather than being folded into an unrelated turn.
- **Recommended resolution:** next Phase-1-mop-up session picks up chunks 1-6 in order (see brief §10). Chunks 1-3 (FU-450 upstream) can land independently; chunks 4-6 (FU-451 core + UI) depend on 1-3.

## [OPEN] FU-450 — P6-03 deal-quality (fake_markdown + good_deal alert) — DESIGN LOCKED, impl deferred
- **Raised:** 2026-07-02 (P6 legacy-plan cross-check).
- **Type:** deferred job (design locked 2026-07-07 as part of [[FU-451]]'s brief; awaiting impl).
- **Design brief:** [`docs/04_proposals/PROPOSAL_BUDGET_DEFENSE_SWAPS.md`](docs/04_proposals/PROPOSAL_BUDGET_DEFENSE_SWAPS.md) §4a-b + §10 chunks 1-3. Locked decisions: `DealQuality` is a pure function over offer-history + household paid-price history (FU-216); band-only enum (`poor/fair/good/great`), no 0-100 numeric score exposed; `fake_markdown` compares merchant claim against household median paid-price; `good_deal` alert throttled to 1 per (product, band) per 14 days, per-user threshold `good_deal_alert_threshold ∈ {"great", "good"}`; the surviving surface feeds the Buy Verdict card (existing P8-05, not a new UI) — no 0-100 score UI, no new PriceHistoryPage overlay.
- **What (original):** `PROMPT_PLAN_PART_6_POLISH.md:233` specified a pure-function scorer over per-product offer history + a `good_deal` alert. **Superseded framing:** P8-05 Buy Verdict shipped 2026-07-02. **Missing pieces still valuable and now designed:** (a) `fake_markdown` flag, (b) `good_deal` alert type.
- **Why deferred:** implementation is 3 chunks inside the FU-451 impl-plan — same session, same tests.
- **Recommended resolution:** ships as chunks 1-3 of the FU-451 impl-plan. Can land independently before chunks 4-6 (FU-451 core) if wanted.

## [OPEN] FU-447 — Security: AUTH_ASSISTANT findings (HIGH CSRF + MEDIUM email-change) still unfixed
- **Raised:** 2026-07-02 (surfaced by the full doc-register audit).
- **Type:** finding (security).
- **What:** `docs/05_investigations/AUTH_ASSISTANT_SECURITY_FINDINGS.md` (dated
  2026-06-04, "Draft for discussion") records a **HIGH-severity CSRF** flaw and a
  **MEDIUM email-change** flaw. No fix is logged in CHANGELOG/worklog; the report
  is still `[OPEN]` with the findings standing.
- **Why deferred:** The report was written but never actioned; it's orphaned from
  the "needs attention" view, so it silently aged.
- **Recommended resolution:** now — review the two findings and decide fix-vs-accept
  before more Phase-3 champion work. Now surfaced at the top of `PROJECT_STATE.md`.

## [OPEN] FU-445 — Stale "no code yet" status headers on ~15 shipped docs
- **Raised:** 2026-07-02 (doc-register audit).
- **Type:** finding.
- **What:** ~13 `IMPL_PLAN_*` (Alerts, Cart, Cookbook, Cook-Mode, Dashboard,
  Error-Handling, Ingestion, Meal-Plans, State-Ownership, Stock-Item-Detail,
  Stock-Overview, Waste) + 2 proposals (Auth-Shell, Buy-Verdict-Oracle) still carry
  a top "Status: … no code yet / Implementing" line despite the feature having fully
  shipped. Doc *bodies* are accurate design records — only the header lies. Full list
  in the `PROJECT_STATE.md` document register (marked "stale header").
- **Why deferred:** Purely cosmetic per-file edit; batch it rather than interleave.
- **Recommended resolution:** opportunistic — batch-flip each header to a
  done/record status (e.g. "✅ Shipped — see CHANGELOG"). The `PROJECT_STATE.md`
  register already carries the truth, so this is de-risked, not urgent.

## [OPEN] FU-432 — Recipe Detail residual polish: uncovered NO_HOME bullets
- **Raised:** 2026-07-01 (12-June feedback-audit delta).
- **Type:** deferred job (small residual cluster).
- **What:** Recipe Detail feedback had 33 bullets; Cookbook C-4 Chunks 1–10 shipped 17 and PROPOSED 11; **5 remain NO_HOME**. Named: **RD-11 ingredient-notes value** (open design question — do per-ingredient notes surface in cook mode / shopping list / just detail?); RD-18 substitutes-available status (already tracked by [[FU-407]]); plus ~3 other minor items (walk the audit doc for the current list).
- **Why deferred:** small enough that each didn't earn its own home; Cookbook C-4 finished without picking them up.
- **Recommended resolution:** next Cookbook touch — walk the audit's Recipe Detail table for `NO_HOME` rows, close each with a one-line call (kept / dropped / build). RD-11 is the only real design question; the rest are one-shot polish.

## [OPEN] FU-431 — Product History: deeper redesign brief (feature discoverability + desktop drawer pattern)
- **Raised:** 2026-07-01 (12-June feedback-audit delta).
- **Type:** deferred job.
- **What:** Product History has 10 bullets; B9.6 shipped 1 (chart-width fix); 7 are PROPOSED across A1/A6/B9/C-9. **2 remain NO_HOME:** **PH-1 "feature hidden away"** (surface-visibility redesign — how does a user land on Product History without knowing the URL?) and **PH-10 "drawer-style page on desktop"** (design open question). Deeper redesign has no brief. Overlaps with [[FU-227]] resolved "your prices" work but that closed the *stock-item* side, not the *product* side.
- **Why deferred:** briefs went to higher-priority surfaces; Product History is Products-layer, data-gated, so it only matters once real product data is ingested.
- **Recommended resolution:** discussion — decide whether a Product History redesign is worth its own brief (given the Products layer is data-presence-gated) or whether the "your prices" intel layer subsumes the user need. Wait until [[FU-214]] product-surface browser verify surfaces real usage patterns.


## [OPEN] FU-214 — Products-as-overlay Phase F tail: product-surface browser verify + L197/205/206/223/225 items
- **Raised:** 2026-06-22 (Phase F kickoff — reconstructed 2026-07-01 from `PRODUCTS_OVERLAY_RUNBOOK.md` + 8 worklog references; **the FU entry itself was missing from both ledgers**).
- **Type:** deferred job (multi-item Phase-F tail).
- **What:** Original scope was **product-surface browser verify + build the L205/206 bulk-select variants + decide L197 hard-delete**. Over time it accumulated:
  - **L197** — hard-delete decision for products (still not made).
  - **L205 / L206** — bulk-select variants on product surfaces (not built).
  - **L223** — Price-History hover-bubble dark-mode bug (added 2026-06-22 worklog).
  - **L225** — Price-History box-fit bug (redirected here from FU-227 scope, worklog).
  - Product-surface browser verify (My Products page, Price History page, stock-item Products tab) — waits on a running app.
- **Why deferred:** every item needs a running browser session; bulk-select is real UI work; L197 is a design call.
- **Recommended resolution:** when the next browser-verify session opens **and** the products layer has real data — knock out L223/L225 as bugs, do the browser-verify checklist, then split L197 (design call) and L205/206 (build) into their own FUs if this one gets too heavy. **This FU is the runbook's Phase F blocker** ([`PRODUCTS_OVERLAY_RUNBOOK.md`](docs/04_proposals/PRODUCTS_OVERLAY_RUNBOOK.md) §Status row F). Related: [[FU-227]] (resolved), [[FU-212]] (resolved), [[FU-210]] (resolved).

## [OPEN] FU-429 — DORA_ASSISTANT_ARCHITECTURE_PROPOSAL: not built + collision with in-flight SLM work
- **Raised:** 2026-07-01 (audit follow-up — file was missed on first pass because it lacks the `PROPOSAL_` prefix).
- **Type:** deferred job (design reconciliation + build).
- **What:** `docs/04_proposals/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md` proposes **one capability registry + two renderers** to collapse the three overlapping decision systems ([tools.py](dora_api/features/assistant/tools.py) server-side, [doraIntents.ts](web_app/src/services/doraIntents.ts) client rule engine, [doraContextualActions.ts](web_app/src/services/doraContextualActions.ts) client contextual chips) — none of which agree on what Dora can do. Proposal has been *augmented* multiple times (§2.2.1 mutation-confirmation model, §7 LLM-provider/connectivity) but **the structural refactor was never built** — all three systems still exist, no `CapabilityRegistry` exists anywhere, and `DoraChat.vue`'s missing-ingredients recompute (the Type-A duplication called out in §1) hasn't been deleted. **Collides with the in-flight SLM replacement** (memory `project_dora_slm_assistant`): the SLM direction may supersede parts of this proposal (rule-engine deletion becomes trivial once the SLM is always available), keep others (the capability registry is still the right shape for the SLM to call), or invalidate the whole thing. Nobody has reconciled the two directions.
- **Why deferred:** the SLM work was in-flight when the proposal was drafted; sequencing was never firmed up.
- **Recommended resolution:** **discussion first, not build** — a short session to reconcile: (a) which parts of the proposal survive the SLM pivot, (b) whether the capability registry lands before/after the SLM, (c) fate of the client-side rule engine (`doraIntents.ts`) once the SLM is the default. Outcome should either be a refreshed proposal or an explicit "superseded by SLM work, close" call. Tightly coupled to [[FU-390]] (P5-05 eval suite — tests whichever architecture wins) and [[FU-386]] (dangling client-only `doraContextualActions.ts` handle from the state-ownership plan).

## [OPEN] FU-422 — Search: display which products already link to a stock item
- **Raised:** 2026-07-01 (original-spec sweep).
- **Type:** deferred job (dropped intent from original spec).
- **What:** Original spec (`docs/00_original_spec/Unprocessed Ideas (from Google Docs).md`) asked that when searching for products, the UI should visibly mark ones **already linked to a stock item** so the user isn't tempted to re-link. Search now lives in the companion, but the *linkage-display* rule may still belong in Dora (the "Products" tab on a stock item) or become part of the companion's ingestion contract. Decide where it lives.
- **Why deferred:** search moved to companion mid-flight; the rule was never re-homed.
- **Recommended resolution:** during any companion↔Dora ingestion-boundary work — call whether Dora surfaces "already-linked" itself, or the companion queries a Dora endpoint. If the latter, add to the ingestion API's read-side.

## [OPEN] FU-413 — EMAIL_SETUP_FINDINGS: promote proposal to IMPL
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** deferred job.
- **What:** `docs/05_investigations/EMAIL_SETUP_FINDINGS.md` produced a §"Proposal" section for the forgot-password / email-wiring path. No IMPL plan; nothing shipped. This is the managed-convenience-that-degrades-gracefully case from §7.5 discipline #6.
- **Why deferred:** feature-absent when unconfigured is currently acceptable; only becomes a blocker at commercialization.
- **Recommended resolution:** before Phase 4 / any hosted deployment — draft `IMPL_PLAN_EMAIL_SETUP.md`, wire SMTP config through `AppSetting` with a "degrades to feature-absent" default.

## [OPEN] FU-412 — COMMERCIALIZATION_REPORT: dormant, not yet actioned
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** deferred job.
- **What:** `docs/05_investigations/COMMERCIALIZATION_REPORT.md` is a Phase 4 planning input. Not translated into a plan or prompts.
- **Why deferred:** Phase 4 territory.
- **Recommended resolution:** at Phase 4 kick-off — read the report top-to-bottom, spawn per-recommendation FUs / plans.

## [OPEN] FU-410 — MULTI_USER_READINESS §5 open questions
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** deferred job.
- **What:** `docs/05_investigations/MULTI_USER_READINESS.md §5` lists open questions gating Phase 4 tenancy work.
- **Why deferred:** Phase 4.
- **Recommended resolution:** at Phase 4 tenancy kick-off; part of P7-A1 / P7-A2 (see [[FU-406]] / [[FU-407]]).

## [OPEN] FU-409 — AUTH_ASSISTANT_SECURITY_FINDINGS: delta re-audit before commercialization
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** finding.
- **What:** `docs/05_investigations/AUTH_ASSISTANT_SECURITY_FINDINGS.md` originally listed CSRF / email-change / register-first-admin issues. Most were resolved (per resolved-FUs trail). A comprehensive item-by-item confirmation vs shipped code was not re-run.
- **Why deferred:** the delta itself is the work.
- **Recommended resolution:** before any public deployment — walk every finding, tick "fixed" or reopen. Overlaps with [[FU-424]] (senior-review credibility gaps).

## [OPEN] FU-408 — INV-8 substitute swap: cross-ref inside stock-item detail is stale
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** finding.
- **What:** `IMPL_PLAN_STOCK_ITEM_DETAIL.md` line ~83 cross-refs INV-8's swap rework as "not built here." INV-8's target surface (Shop Mode) no longer exists as a separate page — merged into ShoppingListDetail per UX v2. The cross-ref is stale until [[FU-407]] re-scopes the rework.
- **Why deferred:** blocked by [[FU-407]].
- **Recommended resolution:** update the cross-ref when [[FU-407]] resolves; same session.

## [OPEN] FU-407 — INV-8 substitute swap rework: re-scope for merged Shop Mode
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** finding (design call).
- **What:** `docs/05_investigations/SUBSTITUTE_SWAP_ASSESSMENT.md` recommended surfacing the stock-item substitute swap **inside Shop Mode + disambiguating the two "Substitute" labels** (line stock-item swap vs merchant-offer swap). Shop Mode has since been merged into ShoppingListDetail (UX v2); the recommendation is stale as written. Currently the only surface is a buried "Swap … with" line-menu action at [ShoppingListDetail.vue:1890](web_app/src/pages/ShoppingListDetail.vue:1890).
- **Why deferred:** the target surface changed mid-flight; nobody re-scoped the fix.
- **Recommended resolution:** short design brief — decide (a) do the rework against the merged surface (a shopping-mode-active affordance surfaced when a line is marked out-of-stock), or (b) cut the list-level swap outright and rely on cook-mode swaps + manual edit. Address the two-"Substitute" collision either way.

## [OPEN] FU-406 — P7-10 Launch readiness
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4 gate).
- **What:** `docs/06_legacy_prompt_plans/PROMPT_PLAN_PART_7_COMMERCIALIZATION.md §P7-10` — final launch-readiness checklist (marketing, legal, incident channels, escalation, on-call). Nothing done.
- **Why deferred:** last-mile.
- **Recommended resolution:** at Phase 4 finish.

## [OPEN] FU-405 — P7-09 Ops (observability, CI/CD deploy, staging, backups)
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-09 — production ops. CI is deliberately disabled in this repo (`.github/workflows/*.yml` commented out to preserve GH free-tier — see memory `feedback_ci_disabled_policy`). Observability, staging, backups all unplanned. **Do not silently re-enable CI as part of this** — separate call.
- **Why deferred:** Phase 4 + CI-cost policy.
- **Recommended resolution:** Phase 4 — pair with billing (P7-06) so ops cost lands with revenue.

## [OPEN] FU-404 — P7-08 Compliance (privacy policy, DSAR, deletion, security headers)
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-08 — full compliance surface. Partial: some security-headers work has landed; the privacy-policy hooks + full data-export/deletion (DSAR) contract not confirmed. Overlaps with [[FU-401]] (P5-02 Privacy).
- **Why deferred:** Phase 4.
- **Recommended resolution:** Phase 4 — merge P5-02 + P7-08 into one compliance work-unit.

## [OPEN] FU-403 — P7-07 Plan gating + usage limits
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-07 — feature/usage limits gated by plan tier once billing is in.
- **Why deferred:** Phase 4, gated by [[FU-402]] Stripe billing.
- **Recommended resolution:** immediately after Stripe lands.

## [OPEN] FU-402 — P7-06 Stripe billing
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-06 — Stripe integration for the SaaS Path A + managed Path B.
- **Why deferred:** Phase 4; only after tenancy ([[FU-400]] / [[FU-401]]).
- **Recommended resolution:** Phase 4.

## [OPEN] FU-401 — P7-A2 Repository-enforced tenant isolation + leak tests
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4, Path A).
- **What:** P7-A2 — tenant scoping enforced at the repository layer + cross-tenant leak tests. §7.5 discipline #1 keeps this a one-layer change when the time comes.
- **Why deferred:** Path A is Phase 4.
- **Recommended resolution:** with [[FU-400]] (Households-as-tenant) as one work-unit.

## [OPEN] FU-400 — P7-A1 Households-as-tenant + admin → owner / platform-admin split
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4, Path A).
- **What:** P7-A1 — introduce households as the tenancy boundary; split "admin" into household-owner and platform-admin. Gated by [[FU-410]] (MULTI_USER_READINESS §5).
- **Why deferred:** Phase 4.
- **Recommended resolution:** first Path-A work item once Phase 4 opens.

## [OPEN] FU-399 — P7-B1 Provisioning control plane
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4, Path B).
- **What:** P7-B1 — automated provisioning for managed single-tenant instances (Path B). Same artifact, different env per §7.5 discipline #3.
- **Why deferred:** Phase 4.
- **Recommended resolution:** first Path-B work item when Phase 4 opens; can precede Path-A work.

## [OPEN] FU-398 — P7-05 Redis + object storage for images
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-05 — Redis for sessions/cache/rate-limit + object storage (S3-ish) for uploaded images. Managed-convenience per §7.5 #6 — must degrade gracefully to "feature absent" (in-memory / local disk) on self-host.
- **Why deferred:** Phase 4.
- **Recommended resolution:** with P7-04 as the "production stack" work-unit.

## [OPEN] FU-397 — P7-04 Production WSGI + web/worker split
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-04 — replace dev server with gunicorn/uwsgi, split web vs worker. Env-driven per §7.5 discipline #3.
- **Why deferred:** Phase 4.
- **Recommended resolution:** paired with [[FU-398]] Redis + [[FU-405]] Ops as the production-stack work-unit.

## [OPEN] FU-395 — P5-11 Production readiness review
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4 gate).
- **What:** P5-11 — comprehensive pre-launch review sweep.
- **Why deferred:** Phase 4.
- **Recommended resolution:** at Phase 4 near-completion, before [[FU-406]] launch readiness.

## [OPEN] FU-394 — P5-10 Merchant data quality & support bundle: confirm companion-scope only
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** finding.
- **What:** P5-10 — merchant data quality is now companion-scope per Decision 1. Confirm nothing in the P5-10 spec landed in Dora-core, and formally mark the P5-10 prompt as "moved to companion project."
- **Why deferred:** scoping-only.
- **Recommended resolution:** doc edit — add a "moved to companion" banner to P5-10 in the legacy plan file; close.

## [OPEN] FU-393 — P5-08 Data-model sanity review sweep
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-08 — comprehensive data-model sanity sweep. `ORPHANED_FIELDS_AUDIT` covered one slice; nullability audit, FK-consistency, index coverage, dead columns — not done as a single pass.
- **Why deferred:** hasn't been forced.
- **Recommended resolution:** opportunistic sweeps as touched (partial credit for [[FU-416]]); a single dedicated pass would be a good pre-Phase-4 gate.

## [OPEN] FU-392 — P5-07 Demo & sellable showcase mode
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-07 — seed a "showcase" install with representative data + a toggleable demo mode for prospects. Seed system exists; showcase toggle + curated dataset don't.
- **Why deferred:** Phase 4-ish; needed for sales conversations.
- **Recommended resolution:** with commercialization prep (Phase 4 opening).

## [OPEN] FU-391 — P5-06 first-week experience (post-onboarding nudges)
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-06 — first-week experience: gentle nudges to complete profile, add first recipe, run first stocktake, etc. First-day onboarding shipped (C-5); first-week nudges not built. Overlaps with [[FU-352]] (P6-12 daily briefing card).
- **Why deferred:** waiting on the alerts/dashboard-card model to firm up.
- **Recommended resolution:** fold into the P8-08 Dora Score card brief when [[FU-352]] opens — the same launchpad-alerts model fits first-week nudges.

## [OPEN] FU-390 — P5-05 Dora AI reliability + eval suite
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-05 — reliability tests + evaluation suite for the assistant. Assistant is currently being replaced by a local SLM (per memory `project_dora_slm_assistant`). Eval suite needs to be built against the SLM rather than the rule-based intent path.
- **Why deferred:** SLM work in-flight; eval-first would test the wrong subject.
- **Recommended resolution:** as the SLM lands — the eval suite is the acceptance gate. Reference the SLM work when picked up.

## [OPEN] FU-389 — P5-04 Mobile / PWA field test
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-04 — real-device mobile / PWA testing pass. Overlaps with [[FU-411]] platform builds + P8-10 native.
- **Why deferred:** Phase 3-adjacent.
- **Recommended resolution:** fold into the P8-10 native-app brief; a device-lab pass is a natural gate before deciding native vs PWA-only.

## [OPEN] FU-388 — P5-03 Performance & scale pass
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-03 — comprehensive perf sweep (query N+1s, bundle size, load-tests). Only `STOCK_OVERVIEW_PERF` investigation touched a slice. No app-wide pass.
- **Why deferred:** hasn't been forced by user pain.
- **Recommended resolution:** pre-Phase-4 gate — do one comprehensive pass with real seed data at pantry size 500+ items, catch N+1s + big-query issues before they hit paying users.

## [OPEN] FU-387 — P5-01 Security & privacy hardening bundle sweep
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-01 — comprehensive security/privacy hardening sweep. Auth findings (CSRF, register-first-admin, email-change) resolved per resolved-FUs. The full P5-01 bundle (security headers, rate-limits, secrets management, dependency audit) not executed as a single sweep.
- **Why deferred:** slices landed opportunistically.
- **Recommended resolution:** pre-Phase-4 gate — one dedicated sweep before any public deploy. Overlaps with [[FU-409]] auth findings re-audit + [[FU-424]] senior-review Tier-2.

## [OPEN] FU-386 — IMPL_PLAN_STATE_OWNERSHIP: dangling client-only `doraContextualActions.ts`
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** finding.
- **What:** `IMPL_PLAN_STATE_OWNERSHIP.md:25` flags a client-side `doraContextualActions.ts` handle whose server-side counterpart was **not implemented** — a dangling contract. Either build the server side or delete the client handle.
- **Why deferred:** noted in the plan doc, never actioned.
- **Recommended resolution:** when the assistant/SLM work next touches contextual actions — decide direction + close.

## [OPEN] FU-385 — Dashboard: DashboardCard extraction + "new low" signal
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `IMPL_PLAN_DASHBOARD_REBUILD.md:263` — DashboardCard extraction was **not** done; zones ship via CSS instead of a shared card component. `:320` — the "new low" server-side signal was **not built** (needed for the dashboard's "just went low" surface).
- **Why deferred:** dashboard rebuild landed without them; not blocking.
- **Recommended resolution:** when Dashboard next opens for change — extract the shared card component (R-002 componentisation) and add the server-side new-low signal. Feeds into [[FU-352]] Dora Score card too.

## [OPEN] FU-384 — StockOverview collapse/expand button (deferred from C-cross)
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `IMPL_PLAN_CONFIG_AND_OPTINS.md:320` — the StockOverview collapse/expand button was explicitly **NOT built** in C-cross; row-geometry deferred to the next C-1 chunk which never happened.
- **Why deferred:** owned by C-1 not C-cross; C-1 didn't include it.
- **Recommended resolution:** next C-1 (Stock Overview) touch — decide keep/cut; if keep, build inline with any other row-geometry change.

## [OPEN] FU-383 — Onboarding: "preferred stores/merchants" step not built
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_ONBOARDING.md:268` — the preferred-merchants step was **not built** ("same uncertain bucket as preferred-*product* removal, FU-180"). Onboarding currently skips it.
- **Why deferred:** merchants layer is companion-scope and its onboarding value was unclear.
- **Recommended resolution:** discussion — decide whether the everyday user needs a "preferred store" concept for `usual_store_id` (which does exist server-side). If yes, small onboarding step + settings mirror; if no, close as decided.

## [OPEN] FU-382 — PROPOSAL_SHOPPING_LIST_UX_V2 §11 open questions
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** finding (unresolved decisions).
- **What:** V2 shipped but §11 open questions were not all closed in-doc. Read the section and either resolve each against the shipped behaviour or turn each into its own FU.
- **Why deferred:** end-of-implementation admin miss.
- **Recommended resolution:** doc-only pass — walk §11, mark each RESOLVED (with the shipped behaviour) or spawn a per-question FU.

## [OPEN] FU-381 — PROPOSAL_COOK_MODE §5 open decisions
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_COOK_MODE.md:166` — open decisions: ticking removal, sub-step model, quantity-unit inclusion list. Cook mode C-3 shipped but the doc's open-decision block was not closed.
- **Why deferred:** built without fully resolving the doc's open calls.
- **Recommended resolution:** doc-only walk — mark each against shipped behaviour or spawn per-question FUs.

## [OPEN] FU-380 — PROPOSAL_CART_BUTTON §7 open decisions + swipe-right + success animation
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_CART_BUTTON.md:220` (§7 open decisions), plus §7.7 swipe-right affordance and success animation added as new open decisions. Cart button C-7 shipped; not all open decisions closed.
- **Why deferred:** built without fully resolving.
- **Recommended resolution:** walk §7 + §7.7 vs shipped, close or spawn.

## [OPEN] FU-379 — PROPOSAL_ALERTS §7 open decisions + still-open deferred cluster
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_ALERTS.md:326` §7 open decisions + `:341` "still open (deferred to their phase, not blocking)" cluster. C-9 Phase A shipped; the deferred cluster survives.
- **Why deferred:** flagged not-blocking.
- **Recommended resolution:** revisit when alerts next opens (or fold into [[FU-352]] Dora Score card if the alerts-as-launchpads reframing subsumes them).

## [OPEN] FU-378 — PROPOSAL_STOCK_OVERVIEW §2.3 detail navigation model + §7 open decisions
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job (design call).
- **What:** `PROPOSAL_STOCK_OVERVIEW.md:84` — §2.3 is flagged as **"the #1 open decision"** (detail navigation model — desktop drawer vs mobile full-page, row-tap vs button-tap miss risk, L68/L71). §7 has additional open decisions. C-1 shipped but this call was not closed.
- **Why deferred:** shipped without resolving the top-of-doc open decision.
- **Recommended resolution:** discussion — resolve §2.3 vs shipped behaviour + user preference, then walk §7. Prerequisite for [[FU-384]].

## [OPEN] FU-377 — PROPOSAL_COOKBOOK open decisions (cuisine-vs-category, versions UX, multi-part model)
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_COOKBOOK.md` has three named open decisions: cuisine-vs-category fate, versions UX (full snapshot vs branchable), multi-part model A vs B. C-4 shipped chunks 1–10; these calls were not all closed.
- **Why deferred:** shipped what was clear, deferred what wasn't.
- **Recommended resolution:** doc walk vs shipped state; the cuisine-vs-category call cascades into [[FU-XXX]] C-cross taxonomy editors ([[FU-372]]).

## [OPEN] FU-376 — PROPOSAL_PRODUCTS_AS_OVERLAY §7 open decisions + GAP bucket
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_PRODUCTS_AS_OVERLAY.md:262` §7 build-time open decisions + `:391` "GAP = small, not yet built" bucket. IMPL landed but these residual bits were not swept.
- **Why deferred:** small-slice residuals.
- **Recommended resolution:** doc walk vs shipped; each GAP either becomes its own FU or gets closed with a state note.

## [OPEN] FU-375 — PROPOSAL_MEAL_PLANS §11 smaller secondary open decisions
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_MEAL_PLANS.md:494` — §11 "smaller secondary open decisions" cluster. Meal-plans rebuild has an active IMPL (`IMPL_PLAN_MEAL_PLANS_REBUILD.md`); §11 not fully resolved.
- **Why deferred:** secondary, not blocking the rebuild.
- **Recommended resolution:** roll into the meal-plans rebuild close-gate — walk §11 vs shipped, close each.

## [OPEN] FU-374 — PROPOSAL_SIMPLE_MODE: sweep non-spine parts (spine superseded)
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** finding (doc drift).
- **What:** `PROPOSAL_SIMPLE_MODE.md` marked spine-superseded 2026-06-17 by PRODUCTS_AS_OVERLAY. The doc's non-spine parts (money opt-in framing, some UI notes) were not confirmed re-homed elsewhere.
- **Why deferred:** doc admin.
- **Recommended resolution:** doc walk — mark every non-spine section either "re-homed at X" or "dropped by pivot"; close.

## [OPEN] FU-373 — PROPOSAL_BARCODE_SCANNING deferred slices (register-against-product + scan-unknown)
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_BARCODE_SCANNING.md` cleanup slice landed; **register-against-product UI + scan-unknown rework** deferred to Phase 2 (ingestion). Ingestion has landed but these barcode slices did not follow through. §6 "Scan tab under QR codes placement" also open.
- **Why deferred:** waited on ingestion; ingestion landed without pulling these along.
- **Recommended resolution:** next barcode-touch — build the register-against-product UI (unknown EAN → offer to link to an existing Product) + scan-unknown rework. Resolve §6 placement while there.

## [OPEN] FU-372 — PROPOSAL_COOKBOOK_CARD_REVISION: not built
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** Design-only sequel to Cookbook §2.10. Two open-decision sections (§3, §5). No IMPL plan.
- **Why deferred:** Cookbook C-4 shipped without this revision.
- **Recommended resolution:** when Cookbook next opens for change — resolve open decisions + spawn `IMPL_PLAN_COOKBOOK_CARD_REVISION.md` if kept.

## [OPEN] FU-371 — PROPOSAL_TEST_SUITE_IMPROVEMENTS: not built
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** Draft proposal, no IMPL, nothing shipped.
- **Why deferred:** infra investment; hasn't been forced.
- **Recommended resolution:** pre-Phase-4 gate; better test suite is a commercialization prerequisite for confident refactors.

## [OPEN] FU-370 — PROPOSAL_SUPPORT_CHANNEL: not built
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** Draft proposal for a user support channel; no IMPL, nothing shipped.
- **Why deferred:** commercialization-adjacent; no users to support.
- **Recommended resolution:** Phase 4 alongside [[FU-402]] Stripe + [[FU-404]] compliance.

## [OPEN] FU-369 — PROPOSAL_RECIPE_IMAGE_STEPS: not built (draft for co-design)
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** Draft 2026-06-25 with 3 open decisions (peer switch across payload types §5.1; vertical vs swipe carousel §5.2; client-side resize target + image cap §5.3). No IMPL.
- **Why deferred:** waiting on co-design.
- **Recommended resolution:** 30-minute co-design session on the 3 open decisions, then `IMPL_PLAN_RECIPE_IMAGE_STEPS.md`.

## [OPEN] FU-368 — PROPOSAL_LOCALE_I18N: not built
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** Draft proposal; §4 open decisions (`:140`); no IMPL. Currency + locale currently AUD-hardcoded in places.
- **Why deferred:** single-locale is fine while personal-use.
- **Recommended resolution:** before commercialization (Phase 4-adjacent) — many customers won't be AU-based. Overlaps with [[FU-402]] Stripe (multi-currency).

## [OPEN] FU-366 — Deferred surfaces: Reports, Settings shell, Mobile view
- **Raised:** 2026-07-01 (Wave-C audit).
- **Type:** deferred job.
- **What:** `C_big_rock_design_briefs.md` "do not redesign yet" list. Dashboard has been pulled forward and shipped. **Reports, Settings shell, Mobile view** remain officially deferred — no briefs. Feedback for Reports is empty; Settings has some deferred bullets (see [[FU-365]] A-5); Mobile view has no direct feedback.
- **Why deferred:** deliberately parked.
- **Recommended resolution:** discussion at some future point — decide whether each stays parked forever or gets a brief. Not on a critical path.

## [OPEN] FU-365 — INV-10 Essential flag: row-level quick-toggle in Stock Overview
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** deferred job.
- **What:** `ESSENTIAL_FLAG_FINDINGS.md` rec #1 (rename to "Essential") is done in detail. **Rec #2 (row-level quick-toggle in stock-overview row context menu or multi-select) is NOT built.** Only Reports has bulk `markAllEssential`.
- **Why deferred:** rec #1 alone resolved the "can't find it" complaint; #2 dropped off.
- **Recommended resolution:** next C-1 (Stock Overview) touch — add "Mark essential" to the row three-dot menu + the multi-select bulk action bar. Small change.

## [OPEN] FU-364 — Wave-C briefs: unresolved open-decision blocks across shipped proposals
- **Raised:** 2026-07-01 (proposals audit meta-item).
- **Type:** finding (meta).
- **What:** Multiple Wave-C proposals shipped without closing their in-doc "Open decisions" sections. Individual FUs exist for each ([[FU-378]] Stock Overview, [[FU-377]] Cookbook, [[FU-379]] Alerts, [[FU-375]] Meal Plans §11, [[FU-380]] Cart Button, [[FU-381]] Cook Mode, [[FU-382]] Shopping List V2). This meta-FU exists so the pattern is visible: **going forward, add an "open decisions closed / spawned as FUs" step to every proposal close-gate**.
- **Why deferred:** process gap surfaced only in aggregate.
- **Recommended resolution:** adopt the close-gate step in CLAUDE.md's "on ending a work unit" section next time it's edited. Meanwhile, individual per-proposal FUs (above) carry the actual delta work.

## [OPEN] FU-363 — Cross-cutting / niche feedback (Bucket C in COVERAGE_GAPS)
- **Raised:** 2026-07-01 (COVERAGE_GAPS sweep).
- **Type:** deferred job (bundle — 8 sub-items).
- **What:** `COVERAGE_GAPS.md` Bucket C cross-cutting items with no per-surface home:
  1. Full systems QA test doc (final regression walkthrough of every feature). User wants done LAST to capture the final product.
  2. Usage analytics / telemetry — "I'd like to know how people are using my app." Privacy-conscious (Charter P8).
  3. UI uniqueness / polish design pass — "looks just okay, not polished/unique."
  4. Push notifications between users (share a shopping list via notify).
  5. Kivy P2P sync branch — decide whether the user's prior experiment has a home here.
  6. Main menu bottom border — micro polish.
  7. Real ALDI / IGA logos — asset request.
  8. General UI consistency — cross-cutting.
- **Why deferred:** no per-surface home; several are Phase 3/4-timed or design-only.
- **Recommended resolution:** split into per-item FUs *only when picked up*. Items 1 (QA test doc) and 3 (polish pass) are natural Phase 4 gates; item 2 (telemetry) is a Charter P8 decision + build; item 4 (push notifications) is a Phase 3-ish feature; items 5–8 are one-shots.

## [OPEN] FU-362 — A-5 Settings: theme *type* separated from theme *identity*
- **Raised:** 2026-07-01 (COVERAGE_GAPS sweep).
- **Type:** deferred job.
- **What:** `COVERAGE_GAPS.md` A-5 — theme **type** (system / light / dark) should be separated from theme **identity** (pesto, lemon, …) — two dropdowns, not coloured light/dark buttons on each theme card.
- **Why deferred:** Settings shell is a deferred surface ([[FU-366]]).
- **Recommended resolution:** fold into any Settings polish pass — small self-contained change; can precede the full Settings shell redesign.

## [OPEN] FU-361 — A-4 Help content overhaul
- **Raised:** 2026-07-01 (COVERAGE_GAPS sweep).
- **Type:** deferred job (content task).
- **What:** `COVERAGE_GAPS.md` A-4 — 5 feedback bullets all about **content**: detailed per-feature help, guides, FAQ, easy navigability, UI screenshots / diagrams. No brief.
- **Why deferred:** content task typically deferred to post-launch.
- **Recommended resolution:** discussion — decide whether it lives as a dedicated `HELP_CONTENT_PLAN.md` proposal or folds into the existing HelpPage work. The overlay-shell counterpart (FU-367) was retired in favour of the shipped `(?)` help chips, so this content work no longer has an overlay to render into — it lives on HelpPage / DoraBot.

## [OPEN] FU-360 — A-3 DORA BOT (assistant chat) polish
- **Raised:** 2026-07-01 (COVERAGE_GAPS sweep).
- **Type:** deferred job (bundle — 6 sub-items).
- **What:** `COVERAGE_GAPS.md` A-3 open bullets:
  1. Text size not honouring user settings (bug).
  2. Basic/AI chip squished/small.
  3. Make basic/AI chip a toggle slider (slanted thick, glow on slide).
  4. DS4 animation flashing on hover — regression to investigate.
  5. Don't show "Hi I'm Dora, click me…" every login (once-per-user acknowledge).
  6. Turn the bot off completely in settings.
- **Why deferred:** scattered across owners; no bundle owner.
- **Recommended resolution:** fold into the DORA_ASSISTANT_ARCHITECTURE polish appendix or a small Wave-C brief. Bug items (1, 4) are triage-first — can fix inline.

## [OPEN] FU-359 — A-2 DATA page redesign
- **Raised:** 2026-07-01 (COVERAGE_GAPS sweep).
- **Type:** deferred job (bundle — 7 sub-items).
- **What:** `COVERAGE_GAPS.md` A-2 open bullets. No dedicated brief. Items: (1) move under Settings → "My Data" (not top-level); (2) multiple export formats (json, csv, …); (3) page formatting overhaul — margins, alignment, headings, font/type; (4) card + checkbox layout; (5) drop the breadcrumb fluff; (6) schema-driven import templates (partially addressed by FU-343/344 but still open); (7) Export & Print tab utility — drop or rework; plus decide whether the optional/collapsed section should be the main view. Barcode-tab items are already covered.
- **Why deferred:** no owner brief.
- **Recommended resolution:** new Wave-C brief `C-DATA — Data Management redesign`. Sequence early if Settings shell ([[FU-366]]) is also opened, since #1 depends on it.

## [OPEN] FU-356 — Gamification: revisit the "someday-list" verdict as a discussion task
- **Raised:** 2026-07-01 (§7 decisions audit).
- **Type:** deferred job (discussion / re-decision — not an implementation).
- **What:** `RECONCILED_FINISHING_PLAN.md` §7 Decision 3c parked **gamification** (rewards / streaks / notify-users) on the someday-list — "captured, not built during finishing." That was a 2026-06-04 call made before P8-08 Dora Score and the C-waste de-emphasis. Worth a fresh discussion pass to decide whether any gamification element (streaks on the Score card, "N shops on budget in a row", waste-free week, first-time badges) is actually free-standing content once the P8-08 card exists — or whether it stays parked. Do NOT design or build off this FU; the deliverable is a **decision** (keep-parked / promote a specific slice into a brief / kill outright).
- **Why deferred:** the original call is defensible but was made without knowing what the Score card would look like; re-checking is cheap.
- **Recommended resolution:** later, during the P8-08 / FU-352 combined Dora Score brief — take 10 minutes at the top of that session to co-decide gamification's fate against the just-designed card, then update `RECONCILED_FINISHING_PLAN.md` §7 Decision 3c accordingly (either "still someday" with a date, or "promoted, see brief §X"). If P8-08 slips, the discussion can happen standalone whenever the user wants — it's not on a critical path. Related: [[FU-352]].

## [OPEN] FU-355 — Wire `clearAllListState()` into sign-out
- **Raised:** 2026-07-01 (A8 §3 landing).
- **Type:** leftover (nice-to-have on top of R-026).
- **What:** `useListState`'s module-level Map persists across sign-out
  because `authStore.signOut` currently does a soft router push rather
  than a full reload. On a shared device the next user could inherit
  the previous session's filter shape on any migrated list page. The
  fallout is minor (filters are per-page UI knobs, not sensitive
  data), but the honest close is to call `clearAllListState()` in the
  sign-out handler (or force a `window.location.reload()`, which some
  auth flows already do).
- **Why deferred:** cross-cutting hook into the auth store — not part
  of the A8 §3 shape and worth its own tiny prompt.
- **Recommended resolution:** opportunistic — bundle with the next
  auth-store touch, or when a shared-device concern surfaces.

## [OPEN] FU-354 — Migrate remaining list pages to `useListState` (R-026 rollout)
- **Raised:** 2026-07-01 (A8 §3 landing).
- **Type:** deferred job.
- **What:** R-026 (nav-state via `useListState`) was applied to
  `StockOverview` (via `useStockFilters`), `RecipesOverview`, and
  `MyProductsPage` as the canonical pattern. Remaining list surfaces
  still lose their filter/search/sort/scroll on navigate-back:
  `MealPlansOverview.vue`, `MealPlanTemplatesPage.vue`,
  `ShoppingListsOverview.vue`, `ShoppingListDetail.vue` (line
  filters + sort), `StocktakePage.vue` (if it grows filters),
  `settings/UsersAdminSettings.vue`, `settings/StoresSettings.vue`,
  `settings/ApiAccessSettings.vue`, and any surface added since. Each
  is a small wrap-in-`useListState` edit; nothing structural.
- **Why deferred:** scope discipline — Phase 0 closed the policy +
  the primitive + three canonical pages, not a repo-wide sweep.
- **Recommended resolution:** opportunistic — migrate a page the
  next time you're editing it for another reason. New list pages
  land with `useListState` from the outset (R-026 violation signal).

## [OPEN] FU-353 — Rename local checkout dir + GitHub repo to `DashyDora`
- **Raised:** 2026-07-01 (P8-01 landing).
- **Type:** leftover (external identifier).
- **What:** P8-01 renamed every in-repo identifier from
  Discount Dora / DiscountDora → Dashy Dora / DashyDora (UI copy,
  package name `dashy-dora`, PWA `appId`, container name
  `dashy_dora`, User-Agents, README + docs, docstrings, badges,
  release-check URL). Two external identifiers can't be flipped
  from inside the repo:
  1. The GitHub repository itself — still `BenTalese/DiscountDora`.
     Until the user renames it, the README badges (shields.io
     endpoints), `_GITHUB_RELEASE_URL` in
     [`dora_api/features/help/get_version.py`](dora_api/features/help/get_version.py),
     and the clone URL in the README all point at
     `BenTalese/DashyDora` and will 404. GitHub auto-redirects the
     old name for a while after rename, so flipping first is safe.
  2. The local checkout directory (`~/Repos/DiscountDora/`) —
     cosmetic; agent CLAUDE.md paths, Codex session paths, and
     shell muscle memory all still work but read wrong.
- **Why deferred:** the user has to run `gh repo rename` (or the web
  UI) and `mv ~/Repos/DiscountDora ~/Repos/DashyDora` — not
  something the agent should do unprompted.
- **Recommended resolution:** now (opportunistic — do it whenever
  the user has 30 seconds). After the GitHub rename, hit the Help
  → About panel in the SPA to confirm the release check resolves
  and the "newer version" banner logic still works. Once done,
  flip this to `[RESOLVED]`.

## [OPEN] FU-352 — P6-12 daily briefing → fold into a "Dora Score" dashboard card (with P8-07/P8-08)
- **Raised:** 2026-07-01 (Phase 1/2 audit vs code — nothing built for P6-12).
- **Type:** deferred job (Phase 1 loop item, un-started).
- **What:** The legacy plan's **P6-12 (proactive daily briefing + alerts-as-launchpads)** has no code — no briefing module server-side, no dashboard section, no follow-up trail. Rather than build it as its own surface, **combine it with the Phase 3 "Dora Score" (P8-08)** and roll both into a single dashboard card: the score is the headline number, the briefing bullets underneath are the "why" (top alerts, likely-due items, over-budget flag, no-planned-meals-next-week, etc.), each bullet is a launchpad link into the relevant surface. One card, one card only — replaces (does not add to) whatever alerts/summary blocks the dashboard has today.
- **Why deferred:** cross-phase design call — the sensible framing didn't exist until P8-08 was on the table.
- **Update 2026-07-04:** **P8-08 partially covered.** The Dora Score card shipped today with a per-component "why" model — every one of the five signals renders its own server-authored reason sentence + a launchpad link to the remediating feature (waste tab, budget prefs, expiring stock, shopping lists, stocktake). That's *the score portion* of this FU. What's still open: the *briefing bullets beyond the 5 signals* (no-planned-meals-next-week, top-active-alerts summary, likely-due items) and the "replaces the existing attention card" framing — my P8-08 sits alongside the existing "Needs your attention" card rather than replacing it. Decide separately whether to (a) leave alerts + Dora Score as two coexisting surfaces, or (b) fold alerts into Dora Score as further "briefing rows" beneath the 5 signals.
- **Recommended resolution:** **when Dashboard next opens** — reassess whether the coexisting-card model feels right in real use. If not, spin a follow-up FU to fold alerts into a "Briefing rows" section on the Dora Score card. Feeder data (suggestions, alerts, budget) is all wired; the composition is presentation-only.

## [OPEN] FU-351 — P6-10 "self-drafting weekly shop": plumbing is built, one-click entry point is missing
- **Raised:** 2026-07-01 (Phase 1/2 audit vs code).
- **Type:** deferred job (partial coverage — needs the shell on top).
- **What:** The multi-source builder [`auto_generate.py`](dora_api/features/shopping_lists/auto_generate.py) already dedupes across `auto_recipe > auto_meal_plan > auto_flagged > auto_essential > auto_low_stock > auto_frequently_added` — that **is** the self-drafting engine P6-10 called for. What's missing is the P6-10 UX framing: a prominent "Draft my shop" one-click entry point that pre-selects sensible defaults (probably meal-plan-for-the-week + low-stock + flagged), shows the reason chip per line ("usually rebuy ~every 12 days"), and lands the user in a DRAFT list ready to edit before starting shopping. Legacy prompt in `docs/06_legacy_prompt_plans/PROMPT_PLAN_PART_6_POLISH.md:646`.
- **Why deferred:** shipping X5 (`auto_generate`) satisfied the mechanics; the one-click "Draft my shop" surface was never built and no one flagged the gap.
- **Recommended resolution:** later, during Phase 1 mop-up before Phase 3 opens (P8-07 Zero-Input Pantry directly depends on P6-10 per §5). Small design brief first — decide entry-point location (Dashboard? Shopping Lists overview? both?), default source set, and whether the reason chip is new UI or reuses the existing `added_via` chip. Then a bounded implementation prompt on top of `auto_generate.py`.

## [OPEN] FU-350 — Import templates: example row is positional, silently drifts on schema change
- **Raised:** 2026-07-01 (post-FU-343 self-review).
- **Type:** finding (drift risk).
- **What:** In
  [`import_spreadsheet.py`](dora_api/features/data/import_spreadsheet.py)
  the `ImportTemplate.example` field is a positional `tuple[str, ...]`
  hand-crafted to match `TARGET_FIELDS`. Add a seventh target field and
  the CSV emits 7 headers + 6 example cells — misaligned in a very
  confusing way (`expiry`'s example lands under `is_essential`, etc.).
  Nothing fails; nothing warns.
- **Why deferred:** wasn't in scope for FU-343 shipping; noticed during
  the "is this future-proof?" review after the fact.
- **Recommended resolution:** change `example` to
  `dict[str, str]` keyed by field name. Reordering `TARGET_FIELDS` then
  becomes safe (the CSV column order is driven by `headers`; example
  values follow the key). Add module-load assertions:
  `assert set(t.example.keys()) <= set(t.headers)` and
  `assert set(t.headers) == set(TARGET_FIELDS)` so drift fails at
  boot instead of at user download time. Should also add an assertion
  that every ImportTemplate section is a registered target the commit
  handler actually knows how to process (today: single section, so
  trivially true — but wire the check now so future sections can't
  silently ship broken templates). Small (~30-line change).

## [OPEN] FU-349 — Import templates: example values reference seed-data strings, not the install's actual reference data
- **Raised:** 2026-07-01 (post-FU-343 self-review).
- **Type:** finding (correctness on customised installs).
- **What:** The stock_items template's example row is
  `("Rice", "In stock", "Pantry", "Grains", "2027-01-01", "no")`.
  `"In stock"`, `"Pantry"`, `"Grains"` are the names of the
  **default seeded** StockLevel / StockLocation / StockGroup rows. An
  install that renamed those (which is perfectly legal — the whole
  point of the taxonomy editors under Settings → Kitchen setup) gets
  an example CSV that would fail row-level validation on commit. The
  template is honest about the *schema* but not about *this install's
  actual reference data*.
- **Why deferred:** worth its own thinking — the fix isn't obvious and
  changes the endpoint's shape.
- **Recommended resolution:** decide between:
  - **(a)** Add an inline `# example values are illustrative; use your
    own level/location/group names` comment on the CSV as a third
    row starting with `#`, and rely on the user to overwrite. Cheap;
    doesn't require a DB read; still ships broken defaults.
  - **(b)** Have the template endpoint read the install's actual
    seeded StockLevel/StockLocation/StockGroup names and inject the
    first of each into the example row. Correct for every install
    but makes the template dynamic — the frontend cache-once
    pattern would need a nudge (or accept staleness across a rename,
    which is fine).
  - **(c)** Drop the example row entirely — just emit the header row.
    Cleanest schema story; loses a bit of "here's what a filled-in
    row looks like" hand-holding.
  My lean: **(b)**. Adds ~20 lines of backend, no UI change, and the
  template is now truly install-shaped. But (c) is defensible if we
  want the endpoint to stay stateless.

## [OPEN] FU-348 — Import templates: registry has no "every importable section has a template" symmetry check
- **Raised:** 2026-07-01 (post-FU-343 self-review).
- **Type:** finding (latent bug when a second importable section lands).
- **What:** The `IMPORT_TEMPLATES` tuple is manually curated. Today
  that's fine (`stock_items` is the only shape the importer supports)
  — but when a second importable section lands (recipes, shopping
  lists), someone has to remember to add an `ImportTemplate` entry
  or the "Download template" button silently misses that section.
  The commit handler and the templates registry don't share a
  registry-of-registries; nothing enforces symmetry.
- **Why deferred:** trivially true today; only bites when a second
  section lands.
- **Recommended resolution:** when a second importable section is
  planned, introduce an `IMPORTABLE_SECTIONS` registry that both the
  commit handler and the templates endpoint consume — one entry per
  section with `{name, target_fields, synonyms, example, commit_fn}`.
  Or, simpler: at module load, assert that every section the commit
  path recognises has a matching `ImportTemplate`. The exact shape
  falls out naturally when the second section is designed; don't
  pre-design it. **Recommended resolution point:** when the second
  importable section is designed.

## [OPEN] FU-346 — Admin settings feel hidden — pick a better host / entry point
- **Raised:** 2026-07-01 (settings-scroll fix session).
- **Type:** design decision.
- **What:** User noted the Admin · global group inside `/settings/*`
  "feels a little hidden". The settings shell (see
  [`SettingsShell.vue`](web_app/src/pages/SettingsShell.vue)) puts it
  as the third sidebar group under Account + Kitchen setup, admin-
  gated. User floated "maybe as a separate option in the profile
  dropdown" but the header dropdown was retired 2026-07-01 (the
  avatar now goes straight to `/settings/account`), so there's no
  obvious host.
- **Why deferred:** Ambiguous design call — could stay put (with a
  visibility polish, e.g. a divider or shield-badge affordance),
  become a peer header icon for admins only (like the retired Help
  button pattern), get its own top-level `/admin` route, or land in
  a small avatar-tooltip menu. Each has trade-offs against the
  charter's Effortless + Anti-creep tiebreak and against the recent
  header-simplification work. Needs a user call, not a silent
  reshuffle.
- **Recommended resolution:** now — user asked the question; needs a
  short back-and-forth on direction before any code moves.

---

## [OPEN] FU-337 — Platform deliverables docs reference artifacts that don't actually ship
- **Raised:** 2026-06-30 (FU-327 audit — `docs/05_investigations/PLATFORM_BUILDS_AUDIT.md`).
- **Type:** finding / leftover.
- **What:** README + the FU-333 Bucket D copy reference AppImage *and*
  `.exe` *and* `.dmg` as if all three exist today. Only the AppImage
  actually does. A user reading the current docs would expect a
  Windows / macOS installer link in a release and find none. Either
  build the other two (paired with [[FU-327]]) or correct the docs
  to set expectations.
- **Why deferred:** docs-only sweep that's only worth doing once the
  build-script decision is made — the right copy depends on which
  targets actually ship.
- **Recommended resolution:** pair with [[FU-327]]. If FU-327 ships
  Windows + macOS scripts, the docs already-write themselves. If
  FU-327 defers further, this FU does the doc-correction pass so the
  README stops over-promising.

## [OPEN] FU-336 — PWA build mode never actually selected — Workbox/manifest config emits nothing
- **Raised:** 2026-06-30 (FU-327 audit — `docs/05_investigations/PLATFORM_BUILDS_AUDIT.md`).
- **Type:** finding (config wired, build step skips it).
- **What:** `web_app/quasar.config.ts` lines ~226–347 define a
  complete PWA: Workbox `GenerateSW`, manifest with 4 app shortcuts
  (primary list, shop-now, scan, add-item), NetworkFirst on `/api/`,
  CacheFirst on stock/merchant images, offline.html fallback.
  Client-side lifecycle + push subscription wiring are already
  shipped ([usePwaLifecycle.ts](web_app/src/composables/usePwaLifecycle.ts),
  [usePushSubscription.ts](web_app/src/composables/usePushSubscription.ts)),
  and the backend has Web Push end-to-end
  ([push_sender.py](dora_api/infrastructure/push_sender.py)). But
  `npm run build` runs `quasar build` (SPA mode), **not**
  `quasar build -m pwa`. The SW + manifest + offline.html therefore
  never land in shipped artifacts. The same is true of the
  PyInstaller bundle (it consumes whatever `web_app/dist/spa/`
  contains — which today is the SPA-mode build).
- **Why deferred:** out of scope of the audit prompt; the audit was
  recon-only.
- **Recommended resolution:** ~1 hour fix. Two options:
  1. Change `web_app/package.json`'s `build` script to
     `quasar build -m pwa`, or
  2. Add a sibling `build:pwa` script and update consumers
     (`packaging/build-linux.sh`, `Dockerfile`) accordingly.
  Then verify the manifest + SW are present in `dist/pwa/` (or
  `dist/spa/`, depending on what Quasar v2 emits today) and that
  the PyInstaller spec's `("web_app/dist/spa", "web_app/dist/spa")`
  data tuple still points at the right output path. **Highest-ROI
  platform move in the audit** — install-to-home-screen on every
  modern mobile + desktop with zero new code. Tagged "now" for the
  next platform-targeted session.

---
## [OPEN] FU-320 — Document every auto-behaviour in the in-app help and point at the setting that controls it
- **Raised:** 2026-06-28 (FU-092 magic-behaviour audit close-out).
- **Type:** documentation / discoverability.
- **What:** For every auto-behaviour catalogued in
  `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md`, write a plain-
  English entry in the relevant in-app help section (Settings help,
  feature-specific help cards, onboarding tooltips — whichever
  surface owns the feature). Each entry:
  1. Names the behaviour ("When you mark an item Low, Dora may add
     it to your shopping list automatically").
  2. States the trigger and what changes ("…when you turn on
     *Auto-add when low* on the item, and you have exactly one
     draft list").
  3. **Links to the setting / toggle that controls it** so the user
     can turn it off, switch it, or read more — never just "the app
     does this" with no escape hatch.
  All 18 findings get coverage (including the (a)-keep-silent ones —
  the doc is the receipt that proves they're not hidden, even if no
  per-event surface fires). Audit table → help-section map should be
  spelled out in this FU's eventual implementation chunk.
- **Gate (HARD):** **do NOT start until all related FUs are
  resolved.** The related set is:
  - [[FU-315]] auto-add toast/chip verify
  - [[FU-316]] remembered-list toast + "always ask" setting
  - [[FU-317]] manual meal-plan reconcile proposal **and** its
    implementation chunks (the F5 area is the one where the help
    copy would change most after the new feature lands)
  - [[FU-318]] cheapest-pick chip
  - [[FU-319]] inline-create pantry toast
  Starting this work earlier than that means the help copy goes
  stale the moment one of those follow-ups lands (new toast wording,
  new setting toggle, new manual-reconcile surface to point at).
- **Why deferred:** documentation that describes a moving target is
  worse than no documentation. Wait for the surface decisions to
  settle.
- **Recommended resolution:** focused doc-writing pass once the gate
  clears — own its own prompt under `docs/03_prompts/`.
- **Cross-ref:** `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` (the
  source-of-truth catalogue this FU documents into help).

## [OPEN] FU-318 — "Cheapest" chip on shopping-list lines using the auto-picked offer (F7)
- **Raised:** 2026-06-28 (FU-092 magic-audit verdict on F7 — (b)).
- **Type:** UX / cleanup.
- **What:** When a line has no `selected_product_id`, the displayed
  price / store comes from `chosenOfferFor(line)` falling back to
  `offers[0]` (server pre-sorted cheapest-first). Render a small
  `cheapest` chip on those lines so the user can see *why* the price is
  what it is — removes the only "did I really pick that store?" surprise
  on the list. Don't render the chip when `selected_product_id` is set
  (user picked) or when the user has typed an `actual_unit_price`
  override (the price-source label takes precedence).
- **Where:** `web_app/src/pages/ShoppingListDetail.vue` line render +
  `web_app/src/models/shoppingList.ts:172` (`chosenOfferFor`); confirm
  the same fallback shape at
  `dora_api/features/shopping_lists/get_shopping_list_detail.py:108-110`.
- **Recommended resolution:** opportunistic — fold into the next
  shopping-list-detail polish pass. ~10 LOC.
- **Cross-ref:** `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` F7.

## [OPEN] FU-317 — Proposal: manual meal-plan reconcile feature ("stocktake-mode for meals") + opt-in for auto-drain (F5)
- **Raised:** 2026-06-28 (FU-092 magic-audit verdict on F5 — plan-first).
- **Type:** proposal / design (no code yet).
- **What:** `reconcile_consumed_meals` is currently the heaviest implicit
  behaviour in the app — every dashboard / meal-plan / recipe read
  silently marks past-day plan entries as consumed and decrements the
  `Recipe.available_meals` pool. No receipt, no undo, no "did you
  actually cook this?" check.
  User wants this thought through before any code touches the
  reconcile path. The desired shape:
  1. **Per-user setting**, default **on**, for "auto-drain past-day
     plans". When off, past-day entries stay unconsumed until the user
     explicitly confirms them.
  2. **A new manual-reconcile feature** modelled on stocktake mode —
     its own page, its own surfacing (alert / dashboard chip), and a
     UX that **shows the user what *should* have been consumed** since
     they last reconciled, so they can confirm / amend per-entry
     before the pool decrements.
  3. Decide what happens to existing alerts (`no_planned_meals`, etc.)
     when manual-reconcile is overdue — does an "unreconciled meals"
     alert fire? At what severity?
  4. Decide whether auto-drain and manual-reconcile coexist (auto-drain
     decrements; manual-reconcile lets the user dispute / amend after
     the fact) or are mutually exclusive (off-by-default users never
     auto-drain; on-by-default users never reconcile).
- **Where to write:** new `docs/04_proposals/PROPOSAL_MEAL_RECONCILE.md`.
  Cross-cut feedback table at the end per the CLAUDE.md mandate.
- **Why deferred:** Charter-level UX call; needs a designed surface
  (page + alert + dashboard chip) before the implementation chunks make
  sense. The audit itself is FU-092's scope; the *feature* is not.
- **Recommended resolution:** focused design session — own its own
  prompt under `docs/03_prompts/`. Before any code touches
  `reconcile_consumed_meals.py` or the `before_request` hook in
  `startup.py:150`.
- **Cross-ref:** `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` F5 (+
  F6, which rides this decision).

## [OPEN] FU-304 — Meal planner rebuild: build both layouts (A + B) behind a toggle
- **Raised:** 2026-06-25 (`/design-critique` on the meal planner →
  `docs/04_proposals/IMPL_PLAN_MEAL_PLANS_REBUILD.md`).
- **Type:** deferred job.
- **What:** the brief diagnoses the planner's emergent sprawl (all-slots ×
  all-days + vertical carousel + non-sticky columns + centre-weighted grid).
  **Q1 RESOLVED (2026-06-25):** build **both** directions and keep them live
  behind a **temp desktop toggle** — upgrade the existing page to **Direction A**
  (de-sprawled carousel) and add a **separate page** for **Direction B** (desktop
  week grid). Shared state/logic; pick a winner later, then delete the loser +
  toggle. Canonical phasing is **§12** of the brief.
- **Progress (2026-06-25 PM):**
  - **R-Phase 0 closed** — Q2 (used-slots default), Q3 (gate behind batch
    posture), Q4 (bottom-sheet picker), Q5 (slot-as-tag, B page only),
    Q6 (server-enrich `MealPlanEntryDto`) all locked with the recommended
    option. Brief §11 updated to reflect resolutions. FU-179 still left to
    user (browser-verify).
  - **R-Phase 1 landed** — extracted `useMealPlanner()` composable +
    `MealPlanRecipePicker.vue` + `MealPlanWeekDayCard.vue` +
    `MealPlanShoppingSummary.vue`. `MealPlansOverview.vue` shrinks
    1,222 → 304 lines, behaviour-preserving. vue-tsc + eslint clean on the
    five changed files.
  - **R-Phase 2 landed (2026-06-25 PM, same session)** — Direction A
    upgrade: de-sprawled per-day slots (Q2) with calm "+ add a meal" +
    show-all toggle, sticky context columns, new
    `MealPlanWeekStatus.vue` strip, `MealPlanFirstRun.vue` hero,
    empty-week "Plan this week" banner, U7 destructive-button fix. Seven
    files changed/added; vue-tsc + eslint clean. Browser walk folded into
    FU-305.
  - **R-Phase 3 landed (2026-06-25 PM, same session)** — Direction B
    page + A/B toggle. Q6 server-enriched `MealPlanEntryDto` (4 new
    display fields + bulk-hydrated `has_image`).
    `MealPlanRichCard.vue` (slot-as-tag per Q5), `MealPlanWeekBoard.vue`
    (7-day grid with day-major default + group-by-slot alt view),
    `MealPlansBoardPage.vue` (top strip + sticky consequences bar +
    pinnable picker drawer + calendar-as-popover), and the
    `useMealPlannerView` persistence helper. New route
    `/meal-plans/board`. List/Grid toggle on both pages (desktop-only).
    13 files touched; vue-tsc + eslint + AST-parse clean. Browser walk
    folded into FU-305.
  - **R-Phase 4 landed (2026-06-25 PM, same session)** — shared mobile
    single-day focus. `MealPlanMobileFocus.vue` (day-strip + focused-day
    cards + collapsible week status) and `MealPlanPickerSheet.vue`
    (bottom-sheet picker). Both pages render the same focus at `lt.md`;
    A/B toggle gated to desktop only. Slot-as-tag rich card reused on
    mobile. Drag is force-disabled at the picker level on mobile (H7).
    vue-tsc + eslint clean.
  - **R-Phase 5 landed (2026-06-25 PM, same session)** — three cleanups:
    (a) Q3 batch posture gate end-to-end (User column + migration +
    `useBatchEnabled` + Settings → Preferences toggle + 5 component
    gates); (b) sequential builder rebuilt onto the shared picker
    (multi-select mode) + dead Email button hidden + build decoupled
    from generate-list; (c) `MealPlanTemplatesDrawer.vue` apply/manage
    drawer wired into both pages. 14 files touched + new Alembic
    migration `e4c7a2f9b5d3`. vue-tsc + eslint + AST-parse clean.
    The migration needs to run on the user's DB before the next
    backend boot.
  - **R-Phase 6 landed (2026-06-26)** — hierarchy + a11y + skeletons.
    Calmer status accents on entry chip + rich card (border + icon +
    aria-label, not saturated fill). Slot rows / day columns / week
    rows / calendar weeks promoted to real `<button>` with combined
    accessible labels. Global ArrowUp/Down nav scoped via
    `closest('button,a,select,…')` so it doesn't steal focus keys.
    New `MealPlanSkeleton.vue` (list / grid / mobile variants) +
    `useMealPlanner.isInitialLoading` ref render layout-shaped
    placeholders during the ~10 parallel mount loads. Calendar status
    text alternatives via `title` + aria-label close 1.4.1.
    9 files touched; vue-tsc + eslint clean.
- **Sequencing (resolved):** extraction-first — **R-Phase 1** pulls a
  `useMealPlanner()` composable + leaf components out of the current page
  (behaviour-preserving R-001) **before** the B page is created, to avoid a
  1,222-line duplicate that double-maintains mutation logic. **Done.**
- **Recommended resolution:** next session — **"pick a winner" cleanup**
  (live with both layouts; once A or B wins, delete the loser page +
  `useMealPlannerView` + the A/B toggle + any leaf components unused by
  the survivor). After that FU-304 itself closes.

## [OPEN] FU-308 — Fold the /meal-plans/templates manager into the drawer (or retire it)
- **Raised:** 2026-06-25 (R-Phase 5 of the meal planner rebuild).
- **Type:** follow-up.
- **What:** R-Phase 5's templates drawer covers the daily Apply / Rename /
  Delete / Save flow. The dedicated `/meal-plans/templates` page still
  exists and is reachable via direct URL — it shipped before the drawer
  and overlaps with the drawer for the basic CRUD. Once browser-verified,
  either (a) fold any unique-to-page features (e.g. bulk reorder, full
  description editing) into the drawer and retire the route, or (b) keep
  the page as the "heavy management" screen and add a clearer entry
  point on the planner pages (right now neither the A page templates
  card nor the B page Templates button links to it).
- **Why deferred:** R-Phase 5 explicitly scoped to the drawer (§9-E);
  reworking the dedicated page is its own assessment.
- **Recommended resolution:** opportunistic — at the "pick a winner"
  cleanup, decide if the manager page survives.

## [OPEN] FU-309 — Run the batch-posture migration before next backend boot
- **Raised:** 2026-06-25 (R-Phase 5 of the meal planner rebuild).
- **Type:** finding (operational debt — built static; no Python
  interpreter on this host).
- **What:** R-Phase 5 adds `User.batch_features_enabled` as a non-null
  column (migration `e4c7a2f9b5d3_20260625_user_batch_optin.py`). The
  GET `/api/users/me` handler reads it through `from_entity`, so a
  backend boot against an unmigrated DB will 500 on every
  authenticated call. Run `flask db upgrade` (or your equivalent) on
  local DBs before restarting the API. Existing users default to
  False ("fresh"), matching the Charter P10 Anti-creep choice.
- **Why deferred:** no Python interpreter on the session host;
  migration is static.
- **Recommended resolution:** **now**, before the next backend boot
  on any environment.

## [OPEN] FU-307 — Per-entry cookability on the Direction-B meal card
- **Raised:** 2026-06-25 (R-Phase 3 of the meal planner rebuild).
- **Type:** follow-up (enhancement).
- **What:** the rich meal card on Direction B currently colours the left
  accent amber when the **recipe is in the cook-shortfall set** (the same
  signal the existing chip uses). It does **not** yet show "missing 3
  ingredients" / "ready to cook now" per entry. To do that the meal-plan
  query would need to include `MealPlanEntry.recipe.ingredients`
  (selectin-loaded), and the entry DTO would fold `missing_count_for(...)`
  + `cookable` through. The query expansion is modest but not free.
- **Why deferred:** §6.5 calls for status accent + tag, which the existing
  shortfall signal already drives; per-entry "what's missing" is the next
  precision step rather than a critical part of the card.
- **Recommended resolution:** opportunistic — when Direction B is named the
  winner and the cookability detail is wanted on the card. The same enrichment
  can flow into the A-page chip too (`MealPlanEntryChip.vue`).

## [OPEN] FU-306 — Persist "Show all slots" toggle across reload
- **Raised:** 2026-06-25 (R-Phase 2 of the meal planner rebuild).
- **Type:** follow-up (enhancement).
- **What:** the new "Show all slots" toggle above the meal-plan carousel is
  currently a session-local `ref` — refreshing the page reverts to the
  used-slots default. For a household that *does* plan all five slots a day,
  re-flicking the toggle every visit is friction.
- **Why deferred:** the default (used-slots) covers the dominant case
  cleanly. A genuine multi-slot household will tell us; pre-emptively
  wiring a household preference is small but not free (settings UI + a new
  pref column).
- **Recommended resolution:** opportunistic — when adding the next batch of
  household preferences, lift `showAllSlots` into the household
  `Preference` table (or a small local-storage cache if the call is "this
  is purely a per-device view choice").

## [OPEN] FU-357 — Cross-app undo off after dashboard "push expiry"
- **Raised:** 2026-06-23 (Dashboard `/design-critique` pass).
- **Type:** finding.
- **What:** feedback L480 — "Undo cross-app seems off, e.g. dashboard push
  expiry, then go to stock item and clear its expiry." An undo/toast initiated
  on the dashboard alert action doesn't behave correctly once you navigate to
  the stock item and mutate the same field. Marked **out-of-scope** in
  `IMPL_PLAN_DASHBOARD_REBUILD.md` §5 — it's an undo/toast-ownership defect, not
  a dashboard-design item.
- **Why deferred:** belongs to whoever owns the cross-app undo/toast mechanism,
  not the dashboard rebuild scope (R-007).
- **Recommended resolution:** confirm in browser, then route to the undo/toast
  owner (likely the global notify/undo layer).

## [OPEN] FU-224 — App-wide colour-usage assessment (primary vs secondary vs accent)
- **Raised:** 2026-06-18 (Stock-pages feedback pass)
- **Type:** deferred job
- **What:** During the feedback pass the user noted that the open / in-use button on the
  Stock Overview row was using `secondary` and was hard to see in Pesto dark — that fix
  landed by promoting to `primary`, but the user flagged that the broader pattern
  ("majority primary usage; not sure where secondary actually pulls weight") may need a
  separate audit. Walk the app, list every place `color="secondary"` (and other lower-used
  semantics like `info`, `accent`) appears, decide which deserve to stay vs. which should
  consolidate to `primary` or theme tokens for visual hierarchy reasons. Likely outputs:
  a short proposal under `docs/04_proposals/` + targeted fixes.
- **Why deferred:** intentionally out of scope for the feedback pass (R-007). The user
  explicitly called it out as a separate task to think about.
- **Recommended resolution:** opportunistic — fold in next time a theming/styling pass
  comes around, or after FU-046 (theme-token compliance) gets another round.

## [OPEN] FU-169 — Implement the test-suite improvements proposal
- **Raised:** 2026-06-13 (post-FU-166 proposal)
- **Type:** deferred job
- **⚠️ CI policy (2026-06-30):** the entire contents of
  `.github/workflows/ci.yml` and `release.yml` are intentionally
  commented out to preserve the user's GitHub Actions free-tier
  allowance during rapid Claude-driven development. **They must stay
  disabled while that cadence continues.** Do not un-comment them as
  part of any other prompt without an explicit user decision; the cost
  is per-push minutes on a free-tier account. When the user is ready
  to spend the minutes, this FU is the natural home for the revival —
  see also [[FU-327]] which depends on CI for its Windows/macOS matrix.
- **What:** `docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md` — phased
  plan to make the suite a trustworthy net: **Phase 1 (P0)** CI runs all tests
  (not just `tests/e2e/dora_api`) + pytest config (`xfail_strict`,
  `filterwarnings`, markers) + `pytest-cov` + shared `assert_problem`/
  `assert_envelope` matchers + one naming convention; **Phase 2** per-test DB
  rollback (isolation → kills order coupling, enables `xdist`) + data
  factories + parametrize; **Phase 3** close the 24 untested API surfaces +
  domain/repository/contract tests; **Phase 4** frontend Vitest +
  `merchant_api`/`emailer` fixture tests + Hypothesis + Postgres CI.
- **Why deferred:** sizeable; needs user prioritisation. Each phase ships
  independently green.
- **Recommended resolution:** start **Phase 1** opportunistically (half-day,
  no-regret); sequence the rest per the proposal. Relates to FU-045 (Postgres
  CI, Phase 4) and FU-161 (Aldi scraper — Phase 4 gives it a net).
- **Update 2026-06-29 — Phase 1 partially landed (no-deps slice).** Done in
  this session:
  - **`pytest.ini`** at repo root: `testpaths = tests` (so bare `pytest`
    collects unit + e2e), `xfail_strict = true`, `addopts = -ra`, the
    `unit`/`e2e`/`slow`/`scraper` marker registry, and `filterwarnings`
    silencing the fuzzywuzzy and pytest-asyncio noise the proposal §3.9
    flagged.
  - **Shared response matchers in `tests/support.py`** — `assert_problem(resp,
    status, *, field=None, detail=None, title=None)` and
    `assert_envelope(resp, *, expect_total=None)`. Returns the parsed body /
    items so callers can drill deeper without re-parsing.
  - **Naming convention codified** as R-023 + ADR-019 in ENGINEERING_STANDARDS:
    `test__<unit>__<condition>__<result>`, per-edit migration policy (don't
    open a rename-all PR).
  - Suite still 538/541 green (3 failures are FU-328 pre-existing; the
    flaky 4th from earlier passed under this run's ordering).
- **Still owed for Phase 1** (each needs a user decision):
  1. **`pytest-cov` reporting** — adds a pip dep and slows runs ~10-20%;
     proposal says "no gate yet" so it's report-only. Want me to add it?
  2. **Un-comment `.github/workflows/ci.yml`** — the entire workflow has
     been commented out since `20176e8` ("Comment out github workflows
     temporarily") and CI hasn't run since. Phase 1's "CI runs the whole
     suite" can't land without first un-commenting, then changing
     `pytest tests/e2e/dora_api` → `pytest`. This is the bigger ask.
  3. **Retrofit ~40 inline problem-detail assertions** to use
     `assert_problem` — R-023 explicitly says "per-edit migration, don't
     open a rename-all PR", so this is intentionally not done as a sweep.
     The matchers are available for any new test or any old one that gets
     touched.

## [OPEN] FU-161 — Shopping list drag-and-drop "index off" (feedback L414) — confirm in browser
- **Raised:** 2026-06-12 (shopping-list UX design session; original report L414, 06-Jun feedback)
- **Type:** finding (reported defect, not reproduced in static read)
- **What:** "Drag and drop is an index off somehow (wrong items being swapped)."
  *2026-06-12 update:* a deeper read found the fix **already shipped in P6-01
  Chunk 6** — `onLineDrop` carries a comment explicitly correcting the
  "subtract 1 when dragging down" off-by-one, and UX v2 preserved that logic
  verbatim. Per the reported-defect rule it stays open until verified in the
  running app (now part of the FU-165 checklist).
- **Recommended resolution:** confirm in browser (FU-165).

## [OPEN] FU-358 — Check / upgrade the Aldi scraper (site appears updated)
- **Raised:** 2026-06-12 (user note during Phase 1 wrap-up)
- **Type:** deferred job
- **What:** User flagged that Aldi's website appears to have
  changed; the existing Aldi scraper in the companion / merchant
  scraping module likely needs revisiting. Concrete steps when
  picked up:
  1. Hit a representative Aldi product page in a browser, compare
     the live DOM to what the scraper's selectors expect.
  2. Run the scraper against a known SKU and inspect the result
     (price, size, on-special detection) — note any fields that
     come back null / wrong / missing.
  3. Decide whether it's a selector tweak or a structural
     rewrite. Aldi historically uses a different layout from
     Coles/Woolworths, so changes there can ripple more than a
     simple class rename.
  4. If structural: cross-check the merchant scraping posture
     (`RECONCILED_FINISHING_PLAN.md` Decision 1 — scraper is the
     companion-app-only path; the core repo doesn't ship live
     scrape).
- **Why deferred:** out of scope of the current finishing-pass
  stream; needs live URLs + the companion app to investigate
  properly.
- **Recommended resolution:** opportunistic — when the user
  next needs Aldi pricing data, or as a focused session in the
  companion repo.

## [OPEN] FU-108 — Reorder Cookbook overview filters by usefulness
- **Raised:** 2026-06-10 (FU-083 follow-up; user, after the bug pass)
- **Type:** finding / UX polish
- **What:** The filter bar in `RecipesOverview.vue` lays controls out
  in the order they were added, not in the order users reach for
  them. The chip cluster (Favourites / Cookable now / Have meals in
  pool / Planned), the numeric inputs, the single-select dropdowns
  (Collection / Cuisine / Category), and the multi-select pickers
  (Uses ingredients / Doesn't use / Dietary / Tools) should be
  ordered by how often users actually flip them — most-used first,
  long-tail later. Pure template reorder, no logic changes.
- **What "useful" means here (open):** the user reads this. A
  reasonable starting cut: **(1) Favourites, Cookable now,
  Planned, Have meals in pool** (the quick-pick chips stay first
  because they're zero-effort); **(2) Cuisine, Category** (single-
  select, common during "what should I cook tonight?"); **(3) Uses
  ingredients / Doesn't use** (when fridge-clearing); **(4) Dietary
  + Tools** (occasional); **(5) Meals ≥ / Missing ingredients ≤**
  (numeric refinement); **(6) Collection** (visual grouping, almost
  set-and-forget). Confirm before moving — the actual answer is the
  user's, not the data's.
- **Recommended resolution:** opportunistic — fold into the next
  pass that touches this template. 10-minute job.

## [OPEN] FU-025 — A6 text scale: many surfaces still don't respond (likely needs its own sweep)
- **Raised:** 2026-06-05 (A6); user-verified gap 2026-06-12
- **Type:** finding (real, app-wide)
- **What:** Initial A6 in-browser check (2026-06-12) confirmed the scale
  steps themselves are working at the page level, BUT user observed that
  **a lot of secondary text still doesn't change size** when the scale is
  changed — e.g. **button labels, input text, toggle labels**, and likely
  other component-internal text. These almost certainly use Quasar's
  component CSS (`font-size` declared inside `.q-btn__content`,
  `.q-field__native`, `.q-toggle__label`, etc.) which doesn't inherit from
  the page-level rem-scaling tokens A6 set up. Fixing this is broader than
  any single page — likely a Wave-A-style "global pass" prompt that
  overrides the component-internal font-sizes to track the text-scale
  variable (or replaces hard-coded px with the same `rem`/var the body
  text already uses).
- **Why deferred:** out of FU-025's verify scope; needs its own sweep.
- **Recommended resolution:** now-ish — promote into a small Wave-A-shaped
  prompt ("A6b: text-scale follow-through into component-internal text").
  Audit method: grep `font-size` in `web_app/src/css/quasar.variables.scss`
  / overrides, plus a runtime walk through Stock Overview + a form-heavy
  page (Recipe edit, Stock-item detail) at Small vs Extra-large; list each
  surface that doesn't visibly change and convert its `px` to the same
  text-scale var. Deliberately-fixed-px carve-outs (ScanOverlay camera UI,
  PriceHistoryChart SVG labels, Dashboard 3px/7.5px micro-gauge) stay.


## [OPEN] FU-010 — Late-game holistic theme / colour / overall-look review
- **Raised:** 2026-06-05 (user request)
- **Type:** finding / deferred job
- **What:** A dedicated end-to-end pass over all themes, colours, and the overall
  visual feel of the app — viewed as a whole, in the browser, across the full
  theme set — rather than the per-chunk token work done piecemeal in A1/A1b.
- **Known input — Pesto looks over-dulled:** the user believes Pesto was dulled
  *too far*. Likely cause: the brightness tuning in A1b happened while a theme-logic
  bug was overriding the new values (the `themeService.ts` `THEMES` dict clobbering
  `themes.scss` via `setCssVar` — see the 2026-06-04 A1b round-2 worklog entry and
  the structural fix tracked in [[FU-004]]). So the dulling may have over-corrected
  against values that weren't actually rendering. Now that Pesto/Pesto Dark were
  synced, the *final* dulled value should be re-judged from scratch.
- **Also feed in:** the structural dual-source collapse ([[FU-004]]) so the review
  isn't fighting a moving target. (Note: FU-003 — the Pesto-only `--text-muted`
  42% bump — was reverted 2026-07-06; all light themes are back on the original
  50% baseline, so this holistic review starts from parity across the family.)
- **Why deferred:** look-and-feel polish is best judged late, in one sitting, on a
  near-final app — not litigated token-by-token mid-build.
- **Recommended resolution:** later — a dedicated pass during **Phase 3 (champion
  polish)** or just before **Phase 4 (commercialize)**, once the app is feature-
  complete enough to eyeball holistically. Requires the app actually running
  (deps installed) and ideally a side-by-side across all themes.

