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
- **Note (2026-07-09, FU-387 audit):** when CI is re-enabled at Phase 4, wire in dependency scanning as part of this FU — a scheduled `pip-audit -r requirements.txt` + `npm audit --prefix web_app` job that opens an issue on new advisories. FU-387 shipped a manual `scripts/security-audit.sh` runner as the interim; promoting it to CI belongs here, not in a fresh FU. See [SECURITY_REVIEW.md](docs/security/SECURITY_REVIEW.md) §6 for the current baseline the CI job should measure against.

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
- **What:** P5-06 — first-week experience: gentle nudges to complete profile, add first recipe, run first stocktake, etc. First-day onboarding shipped (C-5); first-week nudges not built.
- **Why deferred:** waiting on the alerts/dashboard-card model to firm up. *(2026-07-07: [[FU-352]] resolved with "keep Attention + Kitchen Health coexisting", so the launchpad-alerts fold-in path for these nudges is gone; they need their own venue.)*
- **Recommended resolution:** treat as a small standalone brief when picked up — likely a nudges list on the Attention card *or* first-week-only overlay chips, not a Score-card row. Deliberately not folded into any existing dashboard card; keep the first-week experience honest as a first-week experience, not a permanent gauge.

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
- **Recommended resolution:** revisit when alerts next opens. *(The FU-352 "fold alerts into the Dora Score card" fallback path was closed 2026-07-07 as won't-do — Attention + Kitchen Health stay as coexisting cards — so this FU no longer has that shortcut. Resolve on the Alerts surface itself when it's next touched.)*

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

## [OPEN] FU-360 — A-3 DORA BOT (assistant chat) polish — code-complete, 2 browser verifies remain
- **Raised:** 2026-07-01 (COVERAGE_GAPS sweep).
- **Type:** deferred job (bundle — was 6 sub-items; all code work now landed).
- **Shipped 2026-07-08:**
  - **#5 greeting once-per-user** — the "Hi! I'm Dora" hint key in `DoraBubble.vue` is now keyed by user id (`dora.helpHintDismissed.<userId>`) instead of one browser-wide key, so each household account gets exactly one acknowledge.
  - **#6 turn the bot off** — new per-user `show_assistant` preference (User column + migration `c7d1a9e3f2b6` + `PATCH /auth/me` + DTO). Toggle at Settings → Assistant ("Show Dora on every page"); `MainLayout` gates the bubble on it. e2e round-trip test added.
  - **#2 chip squished/small** — dropped `dense`, added a `.dora-mode-chip` style (rem-based font so it follows the text-size pref, padding, icon spacing). Superseded 2026-07-09 by #3's slider replacement.
- **Shipped 2026-07-09:**
  - **#3 Basic/AI chip → toggle slider** — new `DoraModeSlider.vue` (two-position pill, skewed thick knob that slides between Basic/AI with a brand-primary glow on the AI side). Replaces the read-only `q-chip` in the chat header. Slider represents the user's `llm_enabled` preference (source of truth); tapping it flips the preference via `authStore.updateMeAsync` and re-probes `/assistant/status`. Disabled state (with tooltip explaining why) when: install-wide `master_llm_enabled=false`, or the user hasn't finished configuring a provider (mirrors AssistantSettings `canEnable` guard). AI-unavailable banner logic untouched (still driven by `aiActive` from the status probe, so a "preference on but currently unreachable" state still surfaces the banner).
- **Still open (browser verify only, in DORA_VERIFY.md):**
  - **#1 text size not honouring settings** & **#4 DS4 animation flashing on hover** — both live in `DORA_VERIFY.md` (Dashboard/Cross-cutting → Dora bot). #1 *appears already fixed* by the A6 rem migration; #4 is a hover-animation regression that can only be reproduced/fixed with the app running.
- **Recommended resolution:** confirm the new slider behaves as intended in-browser (Basic ↔ AI flip + PATCH round-trip + disabled state when unconfigured), then walk #1/#4 during the next browser-verify session. Close this FU once all three verifies pass.



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
  - ~~[[FU-317]] manual meal-plan reconcile proposal~~ (proposal
    done 2026-07-09 → `PROPOSAL_MEAL_RECONCILE.md`) **and its
    implementation chunks** (the F5 area is the one where the help
    copy would change most after the new feature lands; impl-plan
    still pending)
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

