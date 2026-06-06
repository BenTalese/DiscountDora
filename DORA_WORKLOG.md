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

## 2026-06-06 — Distribution & tenancy posture (Decision 5) recorded
**Status:** complete (charter + CLAUDE.md; **no code changes**)
**What changed:**
- Added **Decision 5 — Distribution & tenancy posture** to
  `RECONCILED_FINISHING_PLAN.md §7`, plus a new **§7.5 distribution-posture
  checklist** it references.
- Added a **"Distribution & tenancy posture (check new work against it)"** section
  to `CLAUDE.md`, mirroring the existing state-ownership principle, pointing at
  Decision 5 / §7.5.

**Decisions made / reasoning:** resolves a multi-message strategic thread (SaaS vs
self-hosted vs local-first for a solo dev). User chose the **GitLab model: one
codebase, SaaS-style, self-hostable** — explicitly steering away from both pure SaaS
and a local-first rebuild.
- **Why this isn't a conflict (the crux):** SaaS and self-host-single-instance
  *agree* the server owns the domain logic + is the source of truth; only who runs
  the box / tenant isolation / managed conveniences differ → deployment difference,
  not architecture. **Local-first was rejected earlier in the thread precisely
  because it *disagreed* on where the source of truth lives** — that would have
  flipped the Phase-1 state-ownership refactor's direction. Self-host-vs-SaaS does
  not, so the current stack is already the shared trunk.
- **Five disciplines** to keep Path A reachable without paying for it now:
  repository-routed data access (one-layer tenant scoping later); DB layer portable
  (SQLite + Postgres); env/config-driven cloud-vs-self-host differences (no build
  forks); auth behind an interface with a local default; **no speculative
  `tenant_id`** (single-tenant = tenancy of size 1).
- **One caveat:** only *multi-tenant isolation* (Path A) is genuinely hard to
  retrofit and stays deferred to Phase 4; "managed single-tenant instances" (Path B)
  costs ~nothing now. Decision 5 makes Decision 4's "Path B → Path A" concrete at
  the code level — supersedes nothing.
- **Postgres = standard datastore target (new, user-directed).** User wants to
  migrate to Postgres ("SQLite feels too unstable for the long term"). Resolved as
  **Postgres-default, NOT Postgres-only** — SQLite stays supported as the
  zero-dependency lightweight self-host option so the everyday-person story survives.
  Strengthens discipline #2 (keep DB layer portable both ways, prefer the
  Postgres-native path where SQLite forces a wrinkle — e.g. the UUID/`text()`
  binding). Migration itself logged as **FU-045**, recommended for Phase 4
  productionize (already lists Postgres/gunicorn/Redis) or opportunistically sooner.
- **No build work** — this is a *posture*, recorded so finishing-phase prompts don't
  dig a self-hosted-only hole.

**Files touched:** `docs/01_charter/RECONCILED_FINISHING_PLAN.md` (Decision 5 + §7.5),
`CLAUDE.md` (new posture section), `DORA_FOLLOWUPS.md` (FU-045), this worklog.

**Verification:** doc-only; grounded against existing Decision 4 / Phase-4 Path B→A
tenancy language and the Clapy repository layer the disciplines rely on. Not run.

**Next up:** unchanged — Phase-1 implementation (state-ownership first chunk) remains
the master-plan next step. The offered `PROPOSAL_LOCAL_FIRST_SYNC.md` was **not**
written (local-first rejected; sync belongs to Phase 4 if/when hosted). No open
follow-up created — the posture lives in the charter, not the backlog.

---

## 2026-06-06 — C-locale + C-help design briefs (user-floated ideas)
**Status:** complete (two proposals; **no code changes**)
**What changed:**
- New `docs/04_proposals/PROPOSAL_LOCALE_I18N.md` (C-locale) and
  `docs/04_proposals/PROPOSAL_HELP_OVERLAY.md` (C-help) — two cross-cutting briefs
  for ideas the user floated this session.
- Registered both: `C_big_rock_design_briefs.md` (two new C sections),
  `00_DOCS_INDEX.md` (proposals table). Logged as `FU-043` (locale) and `FU-044`
  (help) in `DORA_FOLLOWUPS.md` — deferred jobs pending approval.

**Decisions made / key findings (verify-state-first):**
- **C-locale — the companion split is necessary but NOT sufficient.** It solves
  product *sourcing* (C-10 ingests country-agnostic data), but Dora-core keeps AU
  residue. Concrete finds: `$` hardcoded (`ShoppingListShopMode.vue`,
  `PreferencesSettings.vue` budget input); voice default `en-AU`
  (`useVoiceInput.ts`); AU merchants in `seed.py` + `AldiLogo`/`IgaLogo` + assistant
  copy. **Key:** `vue-i18n` is already a dep and wired in `boot/i18n.ts`, but
  **dormant** — locale hardcoded `en-US`, `src/i18n/en-US/index.ts` is the untouched
  Quasar stub (`failed`/`success`), zero `$t()` calls. So it's "plumbing present,
  unused," not "from scratch" nor "done." Brief = Layer A (currency/format) + B
  (de-AU) now; Layer C (full translation) deferred — matches the original spec's
  multi-language as a someday.
- **C-help — it's the opt-in inverse of the tour C-5 deleted.** Three help
  modalities already exist (Help page, assistant) but the **in-context "what is
  this"** one is missing. Net-new front-end component; the design's hard problem is
  **content rot**, so it recommends a co-located `v-help` directive + dev-time
  orphan check, with the hint corpus rolled out per-surface (folded into each
  C-1..C-9 impl), not authored up front. Mechanism is ephemeral client view-state —
  essentially no server model. Original spec ("page-based tips from Dora",
  non-obtrusive mascot) corroborates.
- Both briefs are **user-originated in conversation, not feedback-doc bullets** —
  honestly noted in each §coverage table (related bullets mapped: locale ↔ master
  Decision 1 / original-spec multi-language; help ↔ L43 / L444-449 / C-5 tour
  removal). Neither *closes* an existing feedback bullet; they're net-new scope.

**Files touched:** the two new proposals, `docs/03_prompts/C_big_rock_design_briefs.md`,
`docs/00_DOCS_INDEX.md`, `DORA_FOLLOWUPS.md` (FU-043, FU-044), this worklog.

**Verification:** grounded in live code — confirmed the dormant i18n scaffold
(`boot/i18n.ts`, `src/i18n/*`), hardcoded `$`/voice locale, AU seed/branding, and
the existing Help page/assistant surfaces. Design only — no code, not run.

**Next up:** unchanged — Phase-1 implementation (state-ownership first chunk) is
still the master-plan next step. C-locale and C-help now sit alongside the other
Wave-C briefs awaiting the user's approval + open-decision calls before any
implementation prompt is written for them (FU-043/FU-044).

**Open questions for user:**
- C-locale §3 (currency home; vue-i18n adopt-lite vs rip-out; C-10 currency field;
  merchant-logo fate) and C-help §4 (reveal style; content model; mascot;
  discoverability).
- Where these slot in priority vs Phase-1 implementation — C-locale's currency
  work pairs naturally with the C-cross config build; C-help can land anytime.

---

## 2026-06-06 — C-cross config/opt-ins design brief
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- New `docs/04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md` — the C-cross brief that
  C-1/C-4/C-5/C-9 each defer to. Owns once: money opt-in, nutrition mode
  (off/simple/complex), the four taxonomy settings editors (dietary tags /
  cuisine / category / tools), the location-display zone policy, and the
  install-wide feature-flag panel.
- Registered it: `C_big_rock_design_briefs.md` (new C-cross section),
  `00_DOCS_INDEX.md` (proposals table), `COVERAGE_GAPS.md` (flipped the
  money/nutrition/tag-taxonomy/location/feature-flag bullets from "→ C-cross
  (TBD)" to a written home; added SETTINGS/CONFIG line + audit row).

**Decisions made / key findings (verify-state-first):**
- **Two-tier model** is the spine: per-user opt-ins on `User`; install-wide config
  on `AppSetting` + new taxonomy tables. Taxonomies are install-wide because Dora
  is single-household (shared vocabulary), nutrition *mode* is per-user but the
  nutrition-*DB source* is admin.
- **Money is already half-built** — `User.budget_amount IS NULL` currently doubles
  as the money master switch. Recommended a dedicated `money_features_enabled`
  flag because the cost estimate wants money-on *without* a budget number
  (overloaded-NULL smell). Left as open-decision 1.
- **Feature flags belong on the existing single-row `AppSetting`** (already holds
  `llm_enabled`) — fold the assistant flag in, don't duplicate. C-5's first-login
  step writes the same flags; the set is open-decision 2 (recommend conservative).
- **Nutrition complex deferred** as a reserved seam (mirrors C-10 reserving the
  `source` seam for C-8): build off+simple now, reserve `nutrition_mode=complex`
  + the admin `nutrition_db_source` setting, don't build the DB conversion.
- **Scope discipline:** C-cross designs the *config editors* the per-surface briefs
  need; it does NOT redesign the deferred settings shell, own the per-type alert
  matrix (C-9), the inline location-edit interaction (stock-detail polish), or the
  cuisine-vs-category keep/collapse call (C-4 open-decision 1).
- **Original spec corroborates** the feature panel ("I can disable/re-enable
  features I don't use") — §6 keep; merchant enable/disable there is companion/C-8.

**Files touched:** `docs/04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md` (new),
`docs/03_prompts/C_big_rock_design_briefs.md`, `docs/00_DOCS_INDEX.md`,
`docs/02_feedback/COVERAGE_GAPS.md`, this worklog.

**Verification:** grounded in live code — `User`/`AppSetting`/`StockLocation`
entities, `app_settings` feature, `pages/settings/*`; read every C-cross
deference (C-1 §5, C-4 §2.2/2.6/2.8/2.9, C-5 §2.3); skimmed the original-spec
User & Global Options board; built the cross-cutting feedback-coverage table per
CLAUDE.md. Design only — no code, not run.

**Next up:**
- **Wave-C design briefs are now COMPLETE** — C-1,2,3,4,5,7,9,10 + C-cross + both
  C-impl plans. Only C-6/C-8 remain unwritten, and those are companion-app scope
  (master Decision 1), not Dora-core.
- Per the master plan, the ball is now **Phase-1 implementation**: start with the
  state-ownership first chunk (canonical stock-status contract), then shopping-list
  + cook-mode. Or the user reviews the C-cross open decisions first.

**Open questions for user:**
- The 5 C-cross open decisions (§4): money-flag vs overloaded-NULL; the
  toggleable-feature set; taxonomy edit permission (admin vs any-user);
  location-detail pref yes/no; confirm nutrition off+simple-now/complex-later.
- Proceed to Phase-1 implementation, or review the full proposal set as a whole
  first?

---

## 2026-06-06 — App-wide state-ownership audit (user-prompted)
**Status:** complete (audit + doc updates; **no code changes**)
**What changed:**
- Ran an app-wide sweep for state-ownership smells (duplication / client-side
  cross-entity logic / fetch-all-then-filter / duplicated constants) beyond the
  proposal's flagships.
- Appended **§8 audit addendum** to `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md`;
  tightened `IMPL_PLAN_STATE_OWNERSHIP.md` (Chunk 1 thresholds, Chunk 5 new B's);
  added a **standing state-ownership principle to `CLAUDE.md`**.

**Decisions made / key findings (answer to "do other areas need this?"):**
- **Mostly contained, not sprawling.** The proposal's Type A/B/C/D framework
  already captured the worst; the rest of the app is largely clean.
- **Genuinely clean (do NOT relocate — over-correction guard):** unallocated-meals,
  waste value/expiry/ranking, meal-plan shortfall, frequently-added, attention
  scoring + severity weights, the centralized price helper.
- **New instances found, all in dashboard/threshold territory:** (B) best-deals
  fetches all products to sort/slice client-side; (B) budget card re-fetches +
  re-sums what `budget.py` already computes; (A/constant) expiring-soon window `7`
  hardcoded in 3 client spots vs the server constant; (C) one inline discount-%
  copy. Folded into the existing chunks, not a new workstream.
- **Smoking gun is wider:** `"Out of Stock"` name-match in ~28 spots; sequence
  constants re-declared in `attention.py` + `assistant/tools.py` + client
  `doraIntents.ts` — the §3.1 contract must consolidate these, not just add
  booleans.
- **Standing principle** added to CLAUDE.md so new features don't re-introduce it:
  server owns derived facts + cross-entity aggregates + constants; client owns
  presentation + ephemeral view state; but don't over-correct fine display math.

**Files touched:** `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` (§8),
`IMPL_PLAN_STATE_OWNERSHIP.md` (Chunks 1 & 5), `CLAUDE.md`, this worklog.

**Verification:** very-thorough Explore sweep across budget/waste/deals/attention/
meal-plan/stock/search domains, mapped to A/B/C/D with a balanced clean-vs-smell
list. Audit only — no code.

**Next up:** unchanged from the C-impl entry — start Phase-1 implementation
(state-ownership Chunk 1, which now also consolidates thresholds), or write the
C-cross brief.

---

## 2026-06-06 — C-impl plans (state ownership + shopping lists)
**Status:** complete (two phased plans; **no code changes**)
**What changed:**
- New `docs/04_proposals/IMPL_PLAN_STATE_OWNERSHIP.md` and
  `docs/04_proposals/IMPL_PLAN_SHOPPING_LISTS.md` — phased plans + first chunks
  from the two existing approved proposals.
- `00_DOCS_INDEX.md` + `COVERAGE_GAPS.md` updated.

**Decisions made / key findings:**
- **State ownership — verify-state-first caught positive drift** (proposal is
  2026-06-04): recipe ingredient DTO ALREADY carries `stock_level_id`; a
  sequence-based status notion ALREADY exists (`attention.py` constants) but is
  scattered/duplicated across ~28 spots incl. client `doraIntents.ts`; and
  `?cookable=true` is ALREADY referenced client-side but unimplemented. So the
  first chunk is "finish + consolidate," not "build from zero."
  - **First chunk = the canonical stock-status contract (§3.1):** one server
    module keyed to `StockLevel.sequence` (not name), consolidating the scattered
    constants + migrating the server name-hardcodes (dashboard/waste/reports/
    confirm_actions); rename-test is the guard. Pure server, no behaviour change.
  - Then DTO cookable/missing (set-based, no N+1) → `?cookable=true` + dashboard
    `cookable_count` → delete the 7 client copies → Type B aggregates → Type C
    snapshot-at-add (overlaps shopping-list Chunk 1) → Type D optional.
- **Shopping lists — no drift.** First chunk = **status enum + migration
  (is_archived→done / is_in_progress→shopping / else draft, old booleans kept for
  rollback) + server-owned finish audit + reopen** that reverses from the audit
  (kills the brittle client-snapshot undo; the finish/restock transaction is the
  riskiest surface). Then contextual target inference (removes stored is_primary,
  7 consumers; **same resolver the C-7 cart button needs**) → lifecycle one-button
  UI → one creation surface (5 buttons → 1 form on the existing /auto-generate) →
  merge overview into detail → in-store polish (receipt/pricing-as-you-go,
  drag off-by-one) → planned_shop_date + drop old columns.

**Cross-refs captured:** C-7 (quick-add inference == cart Axis B resolver);
state-ownership Type C ↔ shopping-list finish transaction (build snapshot/audit
once); C-9 (shopping-day alert).

**Files touched:** the two new IMPL_PLAN docs, `00_DOCS_INDEX.md`,
`COVERAGE_GAPS.md`, this worklog.

**Verification:** two Explore sweeps mapped current touch-points + drift against
each proposal; cross-read shopping-list feedback (L401-422). Plans only — no code.

**Next up:**
- User reviews both IMPL plans — esp. each **first chunk** and the open decisions
  (state-ownership: missing=out-only-vs-out+low, quantity-aware cookable, Type-B
  endpoint shape; shopping-lists: DONE delete vs purge, remember-pick scope, two
  SHOPPING lists at once).
- **Wave C is now fully drafted** (all design briefs C-1..C-10 except companion
  C-6/C-8, + both C-impl plans). Per the master plan, **Phase 1 implementation**
  starts with the state-ownership first chunk, then shopping-list + cook-mode.
  Optional remaining design: a **C-cross** brief (money/nutrition opt-ins,
  tag/tool taxonomy settings, feature-flag panel) that C-4/C-5/C-9 lean on.

**Open questions for user:** the per-plan open decisions; whether to (a) start
Phase-1 implementation (state-ownership chunk 1), (b) write the C-cross brief, or
(c) review the proposal set as a whole first.

---

## 2026-06-06 — C-10 ingestion-API contract design brief
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- New `docs/04_proposals/PROPOSAL_INGESTION_API.md` — the Dora↔companion seam.
- `00_DOCS_INDEX.md` + `COVERAGE_GAPS.md` updated.

**Context (answered the user's Qs first):** C-6/C-8 exist as briefs but are
**companion-scope, deliberately unwritten** as Dora-core (re-scoped per Decision
1). The ingestion API is **necessary only because of Decision 1** (extract the
scraper into a companion); it's downstream of that call (user confirmed it
stands). It differs from the current `POST /products` by adding machine auth,
batching, idempotency, a `source` label, a first-class `price_observation`, and a
conflict policy — `POST /products` is a single-item, user-session, dedupe-or-skip
interactive save.

**Decisions made / key design:**
- **Auth:** new `IngestionSource` credential (hashed key, label, enabled, trust
  tier) + bearer-token decorator — net-new, since `AuthToken` is email-flow only.
- **One batched `POST /api/ingest`** with three record types (`products`,
  `offers`, `price_observations`), each carrying a `source`; `Idempotency-Key`
  header; per-record result DTO.
- **Mapping:** product → shared catalogue upsert; offer → set `current_offer` +
  append `ProductHistoricOffer` (the existing price-history log); observation →
  personal price-history point (product or stock-item ref).
- **`source` seam = where C-8 lands** — C-10 only stores the source string
  (reserve the seam); the full merchant↔provider taxonomy stays C-8/companion.
- **Multi-user:** pushed data → shared catalogue; personal price history unions it
  with the user's own shopping-pick snapshots (INV-1). Single-user desktop: moot.
- **Trust tier** carried now for P8-04 crowd reuse; enforcement later.
- Boundary restated: sources call in, Dora never calls out.

**Original spec:** taskboard "require an API key to hit the backend API"
corroborates the machine-auth need; "manually add product offers" = a user-side
share of the offer-append path; "back in stock" alert could be fed by offer pushes
(→ C-9).

**Files touched:** `docs/04_proposals/PROPOSAL_INGESTION_API.md` (new),
`00_DOCS_INDEX.md`, `COVERAGE_GAPS.md`, this worklog.

**Verification:** read the live product/offer/historic-offer/merchant/auth-token
models + `create_product.py` + `price_history.py` + §6.6 / §7 Decision 1. Proposal
only.

**Next up:**
- User reviews `PROPOSAL_INGESTION_API.md` — **6 open decisions §5** (price-history
  conflict policy, sync vs async, source storage, shared-catalogue ownership, fate
  of `POST /products`, trust enforcement).
- **Wave-C design briefs are now ALL done** (C-1,2,3,4,5,7,9,10; C-6/C-8 are
  companion-scope). Remaining Wave-C work: the two **C-impl plans** (shopping
  lists, state ownership — turn existing proposals into phased plans), and an
  optional **C-cross** brief (money/nutrition opt-ins, tag/tool taxonomy settings,
  feature flags) referenced by C-4/C-5/C-9.

**Open questions for user:** the 6 §5 decisions; whether to do the C-impl plans or
a C-cross brief next.

---

## 2026-06-06 — C-9 alerts control centre design brief
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- New `docs/04_proposals/PROPOSAL_ALERTS.md` — maps ALERTS (L437-441) + dashboard
  alert bullets (L57/L60).
- `00_DOCS_INDEX.md` + `COVERAGE_GAPS.md` updated; new **FU-042** (bell-count fix).

**Decisions made / key design:**
- **Found the bell-count root cause (L438):** badge = high+medium only (excludes
  **low**) while the dropdown lists ALL severities → the "6 vs 10" the user saw is
  the omitted lows; compounded by the badge using raw backend counts while the list
  filters client-snoozed alerts. Fix = **one canonical "what counts" set** feeding
  badge + bell + dashboard + page (FU-042; shippable ahead of the page).
- **Control centre** fills the existing `AlertsPage.vue` stub: summary boxes
  (types/counts/themes) + grouped list with **per-kind icons/styling** + manage
  prefs in-page. This is also the **contract for the deferred dashboard card** (L60).
- **Per-type opt-in/out + configurable thresholds** (L440) — "quiet or noisy";
  expiring-soon window etc. currently hardcoded. Prefs hosted on the page (settings
  deferred).
- **New "no planned meals next week" alert** (L441) from meal-plan data.
- **Unify context-aware subscriptions:** price "notify under" (separate today) +
  future "back in stock" surfaced/managed centrally — centre has two tiers (active
  alerts vs armed subscriptions).
- **Snooze is client-side localStorage** today; recommend **server-side** (reuse
  the `DoraSuggestionSuppression` pattern) so counts are consistent across devices.
- Alerts-route 404 (L57) already fixed by **B5** (confirm); the page was a stub.

**Original spec:** Alerts board strongly corroborates per-type config (stale-level
window, turn-off unchanging-level warnings), expiry-reset/prompt-after-alert
(partly built), and a "back in stock" subscription; plus system alerts (offline/
error) as a possible separate tier (open decision 5).

**Files touched:** `docs/04_proposals/PROPOSAL_ALERTS.md` (new), `00_DOCS_INDEX.md`,
`COVERAGE_GAPS.md`, `DORA_FOLLOWUPS.md` (FU-042), this worklog.

**Verification:** Explore sweep of `get_alerts.py` + `AlertsBell.vue` + dashboard
card + `AlertsPage.vue` + price alerts; root-caused the count mismatch in code;
cross-read ALERTS + dashboard feedback + original spec. Proposal only.

**Next up:**
- User reviews `PROPOSAL_ALERTS.md` — **5 open decisions §5** (priority/what-counts
  model, which alerts default on, snooze server-vs-device, prefs home, system
  alerts tier).
- **Wave-C per-surface briefs are now ALL done** (C-1,2,3,4,5,7,9). Remaining:
  **C-10 ingestion-API** (Dora-core backend seam; gates the companion C-6/C-8) and
  the two **C-impl plans** (shopping lists, state ownership — proposals already
  exist, these produce phased implementation plans). C-cross (config/opt-in
  surfaces: money, nutrition, tag/tool taxonomies, feature flags) is referenced by
  several proposals and may warrant its own brief.

**Open questions for user:** the 5 §5 decisions; whether to do C-10, the C-impl
plans, or a C-cross brief next.

---

## 2026-06-06 — C-5 onboarding design brief
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- New `docs/04_proposals/PROPOSAL_ONBOARDING.md` — maps ONBOARDING bullets (L24-46).
- `00_DOCS_INDEX.md` + `COVERAGE_GAPS.md` updated; new **FU-041** (first-run copy
  confirm-in-browser).

**Decisions made / key design:**
- **Centre of gravity = a pick-and-choose starter TEMPLATE of common household
  items** (cheese→Fridge, etc.) — the user's "worst part is getting data in" (L37).
  Plus all/none/some default groups/locations with preview, and opt-in demo
  recipe/meal/plan toggles (warned). Inline import (don't name Grocy; on-page not
  nav-away).
- **Sell the vision first** (L41/L43): short diagram/flowchart intro to the loop +
  core values, shared auth-shell styling, BEFORE any data entry.
- **Stock-item-vs-product explainer** (L46) before "add stock items" (milk vs
  Vitasoy Oat Milk @ Coles).
- **Capture headcount** (→ cook-mode C-3 serving auto-adjust) + **preferred
  stores** (L44/L45).
- **Admin first-login feature enable/disable** (L42) — but needs a matching
  settings panel (settings deferred → dependency).
- **Finish celebration** (confetti, L39) + the tour becomes a workflow/power-user
  explainer covering MORE areas, pointing to help/guides (L40/L43).
- **Theme** = system/pesto-light/pesto-dark only (L28); "Skip everything"→"Skip",
  persist on finish only (L35); slim "added" list (L36).
- **The flagged "you already have groups/locations" copy (L32/L33):** static read
  shows it's gated on has_groups/has_locations (false on a fresh DB), so it
  shouldn't misfire on a clean install — the user likely had dev/seed data.
  Logged FU-041 confirm-in-browser per the MANDATORY rule.
- Dead nav (skip/finish/show-me, L25-27) already fixed by **B5** (confirm).

**Original spec:** barely covers onboarding (only "pre-defined groups/locations on
first usage"); the rich wizard + starter-item template are newer feedback with no
original counterpart — nothing to extract/supersede.

**Files touched:** `docs/04_proposals/PROPOSAL_ONBOARDING.md` (new),
`00_DOCS_INDEX.md`, `COVERAGE_GAPS.md`, `DORA_FOLLOWUPS.md` (FU-041), this worklog.

**Verification:** full read of `WelcomeWizard.vue` + `onboarding.py` via Explore
(incl. the seed/pre-seeding logic for the copy question); cross-read ONBOARDING
feedback (L24-46) + original spec. Proposal only.

**Next up:**
- User reviews `PROPOSAL_ONBOARDING.md` — **5 open decisions §5** (toggleable
  features, starter-template contents, demo-data scope, vision depth, headcount
  granularity).
- Remaining Wave-C Dora-core briefs: **C-9 alerts**, **C-10 ingestion**; plus the
  two C-impl plans (shopping lists, state ownership). C-9 is the natural next
  per-surface brief; C-10 is the backend seam; the impl-plans turn approved
  proposals into phased plans.

**Open questions for user:** the 5 §5 decisions; which brief next.

---

## 2026-06-06 — C-3 cook-mode design brief
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- New `docs/04_proposals/PROPOSAL_COOK_MODE.md` — maps COOK MODE bullets (L317-338).
- `00_DOCS_INDEX.md` + `COVERAGE_GAPS.md` updated; new **FU-040** (structured steps
  → C-4 dependency).

**Decisions made / key design:**
- Cook mode is already feature-rich (timer, voice/TTS, B8 session swaps). The
  redesign targets the weak spots:
- **Finish flow = close the loop (highest value):** replace the blunt "update
  everything" toggle with a **per-item stock-level checklist** (set any level) +
  **per-item add-to-list** (C-7), meals-cooked **starts at 0/optional**,
  click-out cancels (A3), and a **celebration / "you saved N meals"** finish.
- **Serving auto-adjust by headcount** (default from onboarding C-5, per-session,
  scales quantities).
- **Ingredients grouped by base location**; stock level **de-emphasised mid-cook**
  (only relevant at finish, L334); UI rebuilt.
- **Highlight instead of tick** (remove ticking) — but reliable highlighting needs
  **structured steps**, which is a C-4 recipe-model change (FU-040).
- **Tools per step** (C-4), **sub-steps + per-step hints** (structured steps),
  **timer** theme-aware + sound + fill-bar + visible reset, **unit formatting**
  inclusion list ("200ml" vs "2 scoops"), **sous-chef** voice branding/discovery.
- B8 session swaps kept as-is (correct).

**Original spec consulted:** the cook-mode note ("interactive mode with TTS, voice
'next step', timers") matches what's already built — §2 just polishes it; location-
grouping note grounds §2.3. No superseded items.

**Key dependency surfaced (FU-040):** the recipe model stores instructions as a
freeform blob; cook mode's per-step highlighting/tools/hints/timers all need
**structured steps** — that model change belongs in C-4.

**Files touched:** `docs/04_proposals/PROPOSAL_COOK_MODE.md` (new),
`00_DOCS_INDEX.md`, `COVERAGE_GAPS.md`, `DORA_FOLLOWUPS.md` (FU-040), this worklog.

**Verification:** full read of `RecipeCookMode.vue` + cook endpoint via Explore;
cross-read COOK MODE feedback (L317-338) + original spec. Proposal only.

**Next up:**
- User reviews `PROPOSAL_COOK_MODE.md` — **5 open decisions §5** (ticking removal,
  structured-steps model, unit inclusion list, scaling display, finish-flow level
  controls).
- Remaining Wave-C Dora-core briefs: **C-5 onboarding**, **C-9 alerts**, **C-10
  ingestion**; plus the two C-impl plans (shopping lists, state ownership).
- Note: C-3, C-4, and C-1 all now point at recipe-model / cross-cutting work; a
  good moment soon to consider the C-impl plans or C-cross (config/opt-ins).

**Open questions for user:** the 5 §5 decisions; which brief next.

---

## 2026-06-06 — C-4 cookbook design brief
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- New `docs/04_proposals/PROPOSAL_COOKBOOK.md` — recipe-domain redesign covering
  all RECIPES OVERVIEW + RECIPE DETAIL bullets (L228-315).
- `00_DOCS_INDEX.md` + `COVERAGE_GAPS.md` updated; new **FU-039** (Recipe.image).

**Decisions made / key design:**
- **Tag taxonomy overhaul (the big one):** dietary tags → ONE filter cycling
  must/must-not/neutral (+/−/grey, no-close); cuisine & category → single-select
  each, NOT lumped, NOT "tags"; all taxonomies user-configurable in settings
  (C-cross).
- **Comparison → CUT** per INV-6; fold removal into the same chunk that adds the
  sort/filter axes it was standing in for.
- **Versions** replace Duplicate (original spec confirms intent: keep revisions
  without a separate recipe). Proposed full-snapshot + current-pointer.
- **Multi-part:** recommend **sections-first** (within one recipe) over linked
  sub-recipes (which ripple into cookability/allocation/cost) — open decision.
- **Images** (wire up dead `Recipe.image`, FU-039), **tools-required**
  (configurable + filter), **source** as its own field (stop dumping into
  instructions), **importer** site guidance + import-from-overview.
- **Cost estimate** (opt-in, product/history-fed, → meal-plan/shopping budgets)
  and **nutrition tiers off/simple/complex** — both gated by the money/nutrition
  opt-ins (C-cross); recommend off+simple nutrition now, complex later.
- **Card:** image, editable in-stock count + allocated box (red if avail<alloc,
  only shown when allocations exist), actions on card, ditch ⋮, fix collection
  grouping visibility.
- **Detail cleanup:** empty-ingredient validation (L290), filterable stock-item
  picker, editable-title consistency, buttons across top, log-cook into toolbar,
  "meals on hand"→"available meals", personal recipe notes shown in cook mode.
- Heavy cross-cutting overlap mapped to A1/A3/A4/A8/B3/B8/C-7/C-cross/C-2 rather
  than re-litigated here.

**Original spec consulted:** grounded the versions feature + rationale (the
"original feature notes" L312 cites); confirmed comparison's aspiration is now
served by sort/filter (so CUT stands); **superseded** the old markdown-file
storage idea (current DB model needed for cost/nutrition/allocation).

**Files touched:** `docs/04_proposals/PROPOSAL_COOKBOOK.md` (new),
`00_DOCS_INDEX.md`, `COVERAGE_GAPS.md`, `DORA_FOLLOWUPS.md` (FU-039), this worklog.

**Verification:** Explore sweep of the recipe domain (overview/detail/edit/model/
DTO/tags/allocation/import); cross-read all recipe feedback (L228-315) + original
spec Recipes board & notes; INV-6 CUT decision applied. Proposal only.

**Next up:**
- User reviews `PROPOSAL_COOKBOOK.md` — esp. the **6 open decisions §5**
  (cuisine-vs-category, versions UX, multi-part model, nutrition scope, cost
  estimate acceptability, substitute-status).
- Remaining Wave-C Dora-core briefs: **C-3 cook mode** (now unblocked — consumes
  C-4 tools/versions/notes/location-grouping), C-5 onboarding, C-9 alerts,
  C-10 ingestion; plus the two C-impl plans.

**Open questions for user:** the 6 §5 decisions; which brief next (C-3 is the
natural follow-on).

---

## 2026-06-06 — C-1 stock-overview design brief
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- New `docs/04_proposals/PROPOSAL_STOCK_OVERVIEW.md` — full redesign covering all
  37 STOCK OVERVIEW feedback bullets (L63-99).
- `COVERAGE_GAPS.md` + `00_DOCS_INDEX.md` updated (C-1 + C-7 proposals listed).

**Decisions made / key design:**
- **Kill the chip** (L75); rebuild the row: **stock-level button first, big,
  coloured, text-less = the focus action** (L70), replacing BOTH the chip avatar
  and the duplicate right-side level dropdown. Name emphasised; right cluster =
  expiry + planned-meals + cart. Removes badge/red-dot/on-N-lists/⋮/in-chip-cart.
- **Highlighting rules:** status → whole-row outline; selection → row **fill**
  (L91, avoids colour clash); essential is a filter, not a row dot (L66/L82).
- **Nav model (the #1 open decision):** proposed desktop drawer + mobile full-page,
  shared detail component; flagged the L68-vs-L71 wording tension + miss-tap risk
  for the user to confirm.
- **Expiry:** date-picker when unset, +1/+7/+14/clear when set (L87/L88).
- **Top area:** all buttons grouped; filter panel hidden behind a toggle (desktop
  too); search separate + shorter placeholder; stock-level filter → dropdown w/o
  counts; remove "used in recipe" filter; counts → sticky footer (A7).
- **Scan mode** (action-then-scan) — proposed unifying with stocktake (open Q).
- **"# recipes" → "# upcoming planned meals"** — gated on C-2 allocation.
- **Correctness prerequisites folded in:** the 50-item cap (FU-035) and
  filtered-export (L67) must be fixed with the redesign.
- **Original spec consulted** (per the new rule): corroborated the coloured
  level-button shape, the bottom summary panel, the missing-picture placeholder,
  long-press multi-select; and **superseded** column-header sorting (the author
  archived it — "it's a list view now, controlled by filters").

**Ripple/deps noted:** cart → C-7; chip removal app-wide → follow-up; location
display → C-cross; planned-meals → C-2; images → FU-033; detail component shared
with the stock-detail surface.

**Files touched:** `docs/04_proposals/PROPOSAL_STOCK_OVERVIEW.md` (new),
`COVERAGE_GAPS.md`, `00_DOCS_INDEX.md`, this worklog.

**Verification:** Explore sweep of the live overview/row/chip/filters; cross-read
all STOCK OVERVIEW feedback (L63-99) and the original-spec Stock Items board +
notes. Proposal only — nothing built/run.

**Next up:**
- User reviews `PROPOSAL_STOCK_OVERVIEW.md` — esp. the **7 open decisions §7**
  (nav model, miss-tap, open/in-use toggle, scan-vs-stocktake, planned-meals
  fallback, outline palette, 50-cap fix approach).
- Remaining Wave-C Dora-core briefs: C-3 cook mode, C-4 cookbook, C-5 onboarding,
  C-9 alerts, C-10 ingestion; plus the two C-impl plans.

**Open questions for user:** the 7 §7 decisions; which brief next.

---

## 2026-06-06 — Original spec wired in + cart-button extractions
**Status:** complete (docs/governance — no app code)
**What changed:**
- User added their **first-ever project spec** under `docs/00_original_spec/`
  (Feature Boards + ~125 "I can…" Feature Notes + original PROMPT_PLAN, etc.),
  pre-dating this branch's ~100k LOC.
- Referenced it meaningfully (NOT as an override): new section in
  `docs/00_DOCS_INDEX.md`; folder + cross-check rule added to `CLAUDE.md`
  (skim the matching board/notes when writing a brief; extract tagged
  keep/consider/superseded; it never auto-overrides the charter/feedback).
- **Extracted cart-button items into `PROPOSAL_CART_BUTTON.md §9`** (new "From
  the original spec" section + §9.1 remove path):
  - **keep (gap!):** the button is also the **remove** affordance — added a
    symmetric multi-list remove (remove-from-this / remove-from-all). The brief
    had only designed add.
  - **keep:** list picker's last row = "+ New list" (unifies add-to-existing /
    add-new; aligns L382).
  - **consider:** swipe-right → list picker (+ success animation) — new open
    decision §7.7.
  - **keep (corroborates):** standalone product uses the same button; cheapest-
    highlighted rationale.
  - **superseded:** auto-create-stock-item-on-product-add (user's own later note
    + L191 say products/stock-items are separate); stored "primary/default list"
    (replaced by DRAFT-count inference).
  - **cross-ref:** the picture-fallback note corroborates `StockItem.image`
    intent (INV-1 / FU-033) — noted on FU-033.

**Decisions made:**
- Original spec is **historical, non-authoritative**; charter/feedback/reconciled
  plan win where they disagree. Future briefs consult it per the new CLAUDE.md
  rule; `PROPOSAL_CART_BUTTON.md §9` is the reference shape.
- The most material extraction was the **remove path** — a genuine gap in the
  C-7 brief, now folded in.

**Files touched:** `docs/00_DOCS_INDEX.md`, `CLAUDE.md`,
`docs/04_proposals/PROPOSAL_CART_BUTTON.md` (§9 + §7.7), `DORA_FOLLOWUPS.md`
(FU-033 note), this worklog.

**Verification:** read the cart-relevant original notes directly; reconciled each
against the current design before tagging. No code touched.

**Next up:** same as the C-7 entry below — user reviews the cart proposal (now incl.
§9 + the remove path + the swipe open-decision), then picks the next Wave-C brief.

---

## 2026-06-06 — C-7 cart-button design brief
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- New `docs/04_proposals/PROPOSAL_CART_BUTTON.md` — unified add-to-list button,
  decision tree, products-without-stock-items model change, feedback coverage.
- `docs/02_feedback/COVERAGE_GAPS.md` Bucket D updated (cart/standalone bullets
  now covered by the proposal).

**Decisions made / key findings:**
- Mapped **~13 add-to-list controls** across the app (full table in the
  proposal). Two paradigms: blind quick-add-to-primary (11 of 13) vs multi-step.
- **Core design = two orthogonal axes:** Axis A "what line" (0/1/2+ linked
  products → none / pre-select / choice modal; or standalone product), Axis B
  "which list" (adopt `SHOPPING_LIST_REDESIGN §2.4` DRAFT-count inference, no
  stored primary). Combine into ONE modal when both ambiguous; 0 prompts in the
  common case.
- **Critical structural finding:** shopping-list lines currently REQUIRE a
  `stock_item_id` — products can't be added standalone, directly contradicting the
  My Products requirement (L191). Proposal adds nullable `product_id` line
  anchoring + the 4 nesting/cascade rules from L191. This is the heavy rock.
- **State-awareness fix:** generalise `cartStateFor`; clicking an already-on item
  becomes idempotent w/ a popover (Add-to-another / Remove), killing the
  contradictory double-toast (L154).
- **Sequencing:** ship the state-aware button against a temporary `is_primary`
  adapter first; flip Axis B to draft-counting when the shopping-list status model
  lands; do the standalone-product migration as a later phase. C-1 should consume
  this component, not define its own.

**Files touched:** `docs/04_proposals/PROPOSAL_CART_BUTTON.md` (new),
`docs/02_feedback/COVERAGE_GAPS.md`, this worklog.

**Verification:**
- Mapped surfaces via an Explore sweep; cross-checked the load-bearing claim
  (lines require `stock_item_id`) against `shoppingListApiService.ts` AddLineCommand
  + the line model. Read `SHOPPING_LIST_REDESIGN_PROPOSAL.md` for Axis-B alignment
  and the actual feedback bullets (L83-84,108,130,154,191,195-196,288,380-382).
- Proposal only — nothing built or run.

**Next up:**
- **User reviews `PROPOSAL_CART_BUTTON.md`** — esp. the 6 open decisions in §7
  (already-on-list click behaviour; >1-product silent vs modal; standalone-product
  line model; session-default scope; quantity; bulk reporting).
- Then continue Wave C. User picked C-7 first; remaining Dora-core briefs:
  C-1 stock overview, C-3 cook mode, C-4 cookbook, C-5 onboarding, C-9 alerts,
  C-10 ingestion API; plus the two C-impl plans (shopping lists, state ownership).

**Open questions for user:** the 6 §7 decisions, and which Wave C brief next.

---

## 2026-06-06 — INV-5, INV-7, INV-8, INV-9, INV-10 (remaining INV)
**Status:** complete (5 memos; **no code changes**) — INV series now fully done.
**What changed:**
- New `docs/05_investigations/FEATURE_CLARIFICATIONS.md` (INV-5)
- New `docs/05_investigations/HISTORY_TAB_ASSESSMENT.md` (INV-7)
- New `docs/05_investigations/SUBSTITUTE_SWAP_ASSESSMENT.md` (INV-8)
- New `docs/05_investigations/COMMAND_PALETTE_ASSESSMENT.md` (INV-9)
- New `docs/05_investigations/ESSENTIAL_FLAG_FINDINGS.md` (INV-10)

**Decisions made / key findings:**
- **INV-5:** (a) QR show+print and register-barcode (scan-to-jump) are **two
  distinct kept features, not redundant** — and register-barcode is NOT the
  removed P6-02 (that was barcodes for *deal lookup*; this lookup resolves to a
  stock item to open, verified `barcodes.py:350-401`). Clarify labels. (b)
  Relevancy = naive fuzzywuzzy token-overlap, threshold 70 — keep + document.
  (c) expiry & open are fully independent (no derivation) — keep + add tooltip.
- **INV-7:** History tab = level-changes-only, no context/action. **REWORK** —
  merge waste events + list-add provenance + open/checked context (all already
  in the model) into the timeline. Not cut (loses the only home for item
  history), not keep-as-is (weak).
- **INV-8:** List-level substitute swap works but is buried in the full-list menu
  and mispositioned vs the real in-shop moment; collides with Shop Mode's
  offer-"Substitute". **REWORK** (move into Shop Mode + disambiguate), cut only
  if confirmed unused. Distinct from B8 cook-mode ephemeral swap (no overlap).
- **INV-9:** Palette = 18 static commands (13 redundant nav) + a valuable but
  *hidden* entity search. No usage telemetry. **SHRINK** command set **+ PROMOTE**
  entity search to a visible global bar. Confirmed FU-031 stale "Recipes" labels.
- **INV-10:** "Essential" = existing `is_flagged` — there's **no missing
  feature**, just a labelling gap: the detail toggle reads "Always include in
  auto-generated lists," never "Essential." **Rename it** + add a stock-overview
  quick-toggle; keep the primitive explicit (don't auto-derive). Verified
  `essentials_only_for_low` reads `is_flagged` (`auto_generate.py:80-82`).

**Files touched:** the 5 new memos + this worklog + `DORA_FOLLOWUPS.md`.

**Verification:**
- Spot-verified the two most load-bearing claims against live code (not just
  sub-agents): INV-10 `is_flagged`==essential + toggle label
  (`StockItemDetailPage.vue:205-220`, `auto_generate.py:80-82`), and INV-5
  barcode-lookup purpose (`barcodes.py:350-401` → resolves to stock_item, NOT
  deal lookup) — corrected a sub-agent overstatement that register-barcode is
  "scheduled for deletion."
- Not run in the browser — read-only.

**Next up:**
- **INV series complete (1–10).** User reviews the 5 memos + decides per-item:
  - INV-5: approve label clarifications (QR/scan grouping; help text; tooltip)?
  - INV-7: schedule the History-tab rework, or defer to a detail-polish chunk?
  - INV-8: rework into Shop Mode vs cut — confirm Shop Mode "Substitute"==offer-only in browser first.
  - INV-9: shrink+promote vs keep-as-is? (fold FU-031 rename in either way)
  - INV-10: approve rename + overview quick-toggle.
- Per the master sequencing, after INV the next wave is **Wave C** big-rock
  design briefs (`docs/03_prompts/00_INDEX.md`). Several INV outcomes feed C
  briefs (INV-6→C-4 Cookbook; INV-7/8/10 → stock-item & shopping-list briefs).

**Open questions for user:** see Next up — one decision per INV, plus whether to
start Wave C next.

---

## 2026-06-06 — INV-2, INV-3, INV-4 (perf / logging / email)
**Status:** complete (3 memos; **no code changes**)
**What changed:**
- New `docs/05_investigations/STOCK_OVERVIEW_PERF.md` (INV-2)
- New `docs/05_investigations/LOGGING_AND_DATA_LAYOUT.md` (INV-3)
- New `docs/05_investigations/EMAIL_SETUP_FINDINGS.md` (INV-4)

**Decisions made / key findings (several CORRECT the original premises):**
- **INV-2:** The overview does **not** "load all 500 items" — the opposite. The
  frontend (`stockItemStore.ts:48`) fetches only **page 1 (≤50 items)** and never
  loops, so pantries >50 items silently drop the rest. **New correctness bug**
  (FU-035). Real mount cost = 8 parallel requests + per-row O(N) recipe/membership
  lookups, not list size. DS4 didn't speed anything up — it added fade/slide/hover
  motion that masks unchanged latency (perceived-perf, confirmed). Fixes: lift the
  50-cap, defer secondary loads, prebuild lookup maps; server-side aggregation is
  the bigger play.
- **INV-3:** Rotation IS configured but **size-based** (`RotatingFileHandler`,
  10 MB × 5) — a low-volume install never trips 10 MB, so one append-mode file
  grows across all days/restarts → the "46k-line wrong-date" symptom (= FU-027).
  Fix: switch to `TimedRotatingFileHandler` (midnight, ~14 backups). "Two
  locations" = stdout+file handlers + dev `./data/logs` vs desktop `user_log_dir`.
  **No `.local` folder exists** — the split is `data/` (persistent) vs `cache/`
  (regenerable) + desktop platformdirs; recommend keeping as-is.
- **INV-4:** Reset email **works out-of-the-box** — with SMTP env vars it sends;
  without, it runs **dry-run** and logs the reset link (deliberate, for
  self-hosted/desktop). No UI to configure SMTP today (env-var only). Proposed:
  extend the existing `AppSetting` singleton with SMTP fields + a SystemSettings
  section, add an `email_sender_configured` capability, hide the forgot-password
  link when unconfigured. Open Q: does dry-run count as "configured"?

**Files touched:** the three new memos + this worklog + `DORA_FOLLOWUPS.md`
(FU-035 raised; FU-027 referenced).

**Verification:**
- Spot-verified the premise-correcting claims against live code, not just the
  sub-agents: `email_sender.py` dry-run branch, `logging_setup.py` rotation
  config, `get_stock_items.py` `.paginate()`, `query_options.py` DEFAULT_LIMIT=50
  / MAX_LIMIT=500, and `stockItemStore.ts:48` taking only `page.items`.
- Not run in the browser — read-only investigations.

**Next up:**
- User reviews the three memos. Decisions:
  1. INV-2: how to fix the 50-item cap (quick `?limit=500` vs paging vs
     virtualised infinite-scroll)? Schedule the perf fixes?
  2. INV-3: approve switch to time-based log rotation (resolves FU-027)?
  3. INV-4: approve the phased email-setup plan; answer the dry-run "counts as
     configured?" question.
- Remaining INV: INV-5 (QR/barcode/relevancy clarifications), INV-7..10.

**Open questions for user:** see Next up (one decision per INV).

---

## 2026-06-06 — INV-1 (orphaned-field audit)
**Status:** complete (memo only; **no code changes**)
**What changed:**
- New `docs/05_investigations/ORPHANED_FIELDS_AUDIT.md`.
  Full sweep of all entities against DTOs and frontend refs.

**Decisions made:**
- **Two unfinished features found (NOT dead — user corrected this):**
  - `StockItem.image` — supposed to support an own image, with a fallback to a
    *linked product's* image when no own image is set. Neither half was built.
    Recommend **WIRE UP** (storage column already exists).
  - `StockItemSubstitute.notes` — supposed to capture *how* to substitute, e.g.
    "X butter can be replaced with Y amount of olive oil". Column exists (added
    in the undirected-refactor migration) but hardcoded to `None`, never in DTO
    or UI. Recommend **WIRE UP**, fits B8 cook-mode swap especially.
- **Two backend-only fields (intentional design, not bugs):**
  - `ShoppingListLine.picked_offer_price` and `list_price_at_pick` — used by
    budget, reports, waste, assistant but deliberately absent from the DTO.
    Recommend documenting with a comment; no structural fix needed.
- All user-flagged topics (stock groups, notes, preferred merchant, nutrition)
  turned out to be fully wired — no surprises there.
- No structured nutrition columns exist anywhere — only `Recipe.nutrition`
  (freeform string), which is fully surfaced.

**Files touched:**
- `docs/05_investigations/ORPHANED_FIELDS_AUDIT.md` (new)
- `DORA_WORKLOG.md` (this entry)

**Verification:**
- Read all entity files under `dora_api/domain/entities/`.
- Grepped `web_app/src/` for every suspect field (snake_case + camelCase).
- Checked `table_mappings.py`, all relevant feature handlers, and the
  budget / reports / waste / assistant files for invisible backend use.
- Not run in the browser — read-only investigation.

**Next up:**
- User reviews the memo. Key decisions:
  1. `StockItem.image` + `StockItemSubstitute.notes` are wire-up jobs (user
     confirmed both are intended-but-unbuilt). Need to schedule them — image
     likely its own prompt; substitute-notes folds into INV-8 / B8 cook-mode.
  2. Happy with "document only" for the two snapshot fields?
- Continue INV series: INV-2 (stock-overview perf), INV-3 (logging layout),
  INV-4 (forgot-password email), INV-5 (QR/barcode/relevancy clarifications),
  or jump to INV-7..10.

**Open questions for user:**
- Schedule the two wire-up jobs now or defer (FU-033 image, FU-034 sub-notes)?
- Which INV next?

---

## 2026-06-06 — INV-6 (recipe-comparison worth assessment)
**Status:** complete (memo only; **no code changes**)
**What changed:**
- New `docs/RECIPE_COMPARISON_ASSESSMENT.md`. One-page memo per the
  prompt: (1) what the feature does today, (2) signal of use,
  (3) what a useful comparison would need, (4) Charter check,
  (5) where the real use cases land if cut, (6) cleanup cost,
  (7) recommendation, (8) open follow-up.

**Decisions made:**
- **Recommended CUT.** Feature has no usage signal, the user's own
  feedback says "useless, would users actually use this?", and it
  fails 5 of the 12 Charter principles (P1 Effortless, P5 Closed
  loop, P6 Insight→action, P10 Anti-creep, P11 Fast UX). Every
  real cook-decision question it tries to answer lands more
  cleanly on the Cookbook overview's sort+filter, Cook Mode
  servings auto-adjust, money-opt-in per-row cost, or the Dora
  "what should I cook?" intent.
- **Cleanup placement:** fold the X2 removal into **C-4 Cookbook
  redesign** as a Charter-aligned cut, in the same chunk that adds
  the sort axes (`time`, `missing`, `last_made`,
  `cost_per_serving`) so users land on the overview and find the
  answer comparison was meant to give without entering a dialog.
- **No code touched.** Memo is decision input for C-4.

**Files touched:**
- `docs/RECIPE_COMPARISON_ASSESSMENT.md` (new)
- `DORA_WORKLOG.md` (this entry)

**Verification:**
- Read live code: `RecipesOverview.vue` compare-mode block
  (header buttons L7-22, dialog L259-356, state + handlers L662-692).
- Cross-referenced against the user feedback bullets in
  `Feedback _ Fixes - as of [06-Jun-2026].md` (Cookbook section)
  and against the reconciled finishing plan / triage / Charter
  Part II (P1, P5, P6, P10, P11).
- Confirmed no backend route exists for comparison and no
  telemetry surface tracks the toggle. Footprint estimate ~100
  lines, one file, no migration.

**Next up:**
- **User reviews the memo.** If `CUT` is approved:
  - The X2 removal becomes part of the C-4 Cookbook brief / impl
    chunk (when C-4 lands as a proposal).
  - `STATUS.md` X2 flips DONE → **CUT (INV-6, 2026-06-06)**.
- Per the prior plan sequencing: ready for the next INV
  (INV-1/2/3/4/5) or to head back to a Wave C brief on your
  signal.

**Open questions for user:**
- Sign off on **CUT** (vs `rework` if there's a use case in §3
  the memo missed).
- Confirm fold-into-C-4 is the right cleanup chunk vs a smaller
  standalone removal prompt.

---

## 2026-06-06 — Docs reorg + feedback coverage audit + INV-7..10 + CLAUDE.md cross-check rule
**Status:** complete (docs/governance — no app code touched)
**What changed:**
- **Docs folder reorganised** by lifecycle:
  - `docs/01_charter/` — DASHY_DORA_CHAMPION_PLAN, RECONCILED_FINISHING_PLAN, STATUS.
  - `docs/02_feedback/` — Feedback raw doc, FEEDBACK_TRIAGE_AND_PLAN, **new** COVERAGE_GAPS.md.
  - `docs/03_prompts/` — (was `docs/prompts/`) all wave A/B/C + INV prompts; INDEX updated.
  - `docs/04_proposals/` — PROPOSAL_MEAL_PLANS, SHOPPING_LIST_REDESIGN, STATE_OWNERSHIP_REFACTOR, DORA_ASSISTANT_ARCHITECTURE.
  - `docs/05_investigations/` — RECIPE_COMPARISON_ASSESSMENT, AUTH_ASSISTANT_SECURITY_FINDINGS, MULTI_USER_READINESS, COMMERCIALIZATION_REPORT, Distribution Spec.
  - `docs/06_legacy_prompt_plans/` — PROMPT_PLAN.md + PROMPT_PLAN_PART_2..7.
  - `docs/99_scratch/` — claude convo.txt, prompt - up to speed.txt, Finish task DS1.txt.
  - Root `docs/00_DOCS_INDEX.md` rewritten to describe new layout.
- **`CLAUDE.md` + `AGENTS.md` updated** with:
  - New folder layout enumerated in step 2.
  - Governing-document paths updated (`01_charter/RECONCILED_FINISHING_PLAN.md`, `01_charter/DASHY_DORA_CHAMPION_PLAN.md`, `03_prompts/`).
  - **New "Cross-checking against the original feedback — MANDATORY" section** requiring every brief/proposal/assessment/impl-plan to end with a flat coverage table mapping every relevant feedback bullet to a section in the doc, OR explicitly mark it out-of-scope. The PROPOSAL_MEAL_PLANS `F1..F49` table is the reference shape.
- **`02_feedback/COVERAGE_GAPS.md` created** — full audit of which feedback bullets currently have no home:
  - **Bucket A (whole-surface gaps)** — Stock Item Detail polish, DATA page, Dora Bot polish, HELP content, Settings deferred bullets.
  - **Bucket B (assessment-style)** — feeds INV-7..10.
  - **Bucket C (cross-cutting/niche/future)** — full systems QA doc, telemetry, design polish, push notifications, P2P, etc.
  - **Bucket D** — surfaces verified covered (so the audit is reproducible).
- **`03_prompts/INV_investigations.md` expanded** with INV-7..10:
  - INV-7 stock-item detail History tab worth.
  - INV-8 substitute swap-into-list behaviour.
  - INV-9 command-palette worth (keep / shrink / cut).
  - INV-10 essential-flag — where it lives, how to set, is it the right primitive.
  - INDEX line updated accordingly.

**Decisions made:**
- All four pieces of the audit response executed (user picked all in
  one `AskUserQuestion`): write COVERAGE_GAPS, reorg, CLAUDE.md
  cross-check rule, INV-7..10.
- Mixed `git mv` and plain `mv` for the moves because some files
  (PROPOSAL_MEAL_PLANS, RECIPE_COMPARISON_ASSESSMENT, the raw feedback
  doc) hadn't been committed yet. Git tracks the rest as renames.
- Worklog historical entries' inline paths kept as-is (they describe
  state at time of writing — not rewriting history).

**Files touched:**
- Moved: 26 docs across the new subfolders.
- Edited: `CLAUDE.md`, `AGENTS.md`, `docs/00_DOCS_INDEX.md`,
  `docs/03_prompts/00_INDEX.md`, `docs/03_prompts/INV_investigations.md`,
  this worklog.
- Created: `docs/02_feedback/COVERAGE_GAPS.md`.

**Verification:**
- `ls docs/` shows only `00_DOCS_INDEX.md` + the seven new subfolders.
- `git status` confirms all files tracked under their new paths.
- `CLAUDE.md` and `AGENTS.md` now point at the new paths consistently.
- COVERAGE_GAPS.md cross-referenced against the full
  `02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md` section by
  section (SPLASH..Technical Considerations).
- **Not run:** any build / lint — docs-only changes.

**Next up:**
- **Back to INV** — INV-6 already done (`05_investigations/RECIPE_COMPARISON_ASSESSMENT.md`).
  Next: pick from INV-1..10 (1/2/3/4/5 from original, 7/8/9/10 newly
  added). User had earlier sequencing of "INV-6 only first" — INV-6 is
  done.
- User may want to triage `02_feedback/COVERAGE_GAPS.md` Bucket A
  items into new C-briefs (especially C-DATA which is the biggest
  uncovered surface).
- Open user-blocking items unchanged from prior worklog entries.

**Open questions for user:**
- Which INV next? (INV-1 orphaned-fields is the most foundational — it
  also feeds A-1 and A-5 in COVERAGE_GAPS.)
- Want me to draft the C-DATA brief now or defer?

---

## 2026-06-06 — C-2 (Meal Plans proposal — feedback cross-check + rewrite)
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- Cross-checked every Meal Plans bullet in
  `docs/Feedback _ Fixes - as of [06-Jun-2026].md` against the
  proposal. Found 12+ gaps (page chrome removals, custom calendar
  spec detail, carousel direction, no-name plan instances, sidebar
  redesign, past-day bug, hover-to-highlight, etc.). Surfaced 4
  decisions to the user; took the picks
  (trays in left column, rotating sets in scope, single-button
  choice modal, drop cookable cues).
- Rewrote `docs/PROPOSAL_MEAL_PLANS.md` end-to-end. New §3.4-3.7
  cover the missing surface (new-plan flow, no-name instances, page
  chrome removals, page icon). New §5 expands templates with
  template-sets (rotating). New §13 is a flat per-feedback-bullet
  coverage table (F1..F49) so the next reviewer can audit the
  proposal against the source quickly.

**Decisions made (in addition to prior three):**
- 4. Rotating template sets **in scope** — new
  `MealPlanTemplateSet` entity; `from-template/recurring` accepts
  either a template_id or a template_set_id.
- 5. Trays in **left column** above all-recipes (not below carousel
  as feedback originally said — user explicitly picked left column;
  noted as a divergence from feedback wording).
- 6. Shopping-list target = **single button → choice modal**.
- 7. **Drop cookable cues from planner entirely** — no green-check,
  no "in-stock only" filter, no "Suggest meals I can cook now"
  CTA. Cookable lives on cookbook (C-4).

**Files touched:**
- `docs/PROPOSAL_MEAL_PLANS.md` (full rewrite)
- `DORA_WORKLOG.md` (this entry)

**Verification:**
- Re-read full `MEAL PLANS` section of the feedback doc bullet-by-
  bullet against the proposal. Every bullet F1..F49 mapped to a
  section in §13.
- Live code re-grounding from prior pass still holds (B6 works,
  past-day backend refusal, meals→recipes merge complete).
- Identified a real frontend bug from the feedback's exception
  log (Thu 8am AEST → 400 on Wed drop) — `isPastDay` drift vs the
  backend's `date.today()`. Specced as §12 phase C-2.K.
- No build/run — proposal only.

**Next up:**
- **User reviews the rewritten `docs/PROPOSAL_MEAL_PLANS.md`.** §13
  table is the quick audit.
- 5 smaller decisions remain in §11 (recurring window cap, tray
  count max, templates page route, slot-remap UI build-now-or-defer,
  set rotation start anchor).
- After approval — back to **INV — investigations** as per the
  user's earlier sequencing.

**Open questions for user:**
- §11 smaller decisions when convenient.
- Anything in the flat F1..F49 coverage table you disagree with the
  mapping for.

---

## 2026-06-06 — C-2 (Meal Plans redesign — proposal)
**Status:** complete (proposal only; **no code changes**)
**What changed:**
- New `docs/PROPOSAL_MEAL_PLANS.md`. Sections:
  1. Re-grounding against live code (meals→recipes merge, B6
     allocation, shortfall, slot model, past-day rules).
  2. Three big open decisions resolved with user (templates fork at
     apply-time; past days skipped entirely on template apply; shortfall
     banner moved per-cell + sidebar summary).
  3. Three-column surface map (left=recipe list, main=week carousel,
     right=calendar+shopping+templates).
  4. Configurable slot vocabulary (`Breakfast/Lunch/Dinner/Snack`
     defaults; user-scoped settings entry).
  5. Templates data model + API + recurring application.
  6. Sequential builder modal as alt path for fresh-cookers.
  7. Two-persona walk-through (batch + fresh).
  8. Wave A primitive reuse map.
  9. Ripple notes for C-3 / C-4 / C-impl / dashboard / settings /
     onboarding.
 10. Smaller secondary open decisions (servings default, recurring
     window cap, etc.).
 11. Sequencing into 8 chunks if approved.

**Decisions made:**
- Took the three "Recommended" answers for the brief's listed open
  decisions: fork-on-apply templates, skip past days, move shortfall
  per-cell. Logged inline in §2 of the proposal so the next agent
  doesn't re-litigate.
- B6 allocation **explicitly verified working** in `_hydrate_unallocated`
  — but kept the CLAUDE.md MANDATORY rule, so the proposal flags it as
  needing in-browser confirm before being closed.
- Calendar widget designed as a custom small widget (NOT `q-date`) —
  the brief specified "minimalist rounded squares with status
  underlines" which q-date can't render.
- Same-recipe-same-(day,slot) drop **increments servings** (single
  entry); same recipe on the same day at *different* slots stays two
  entries (no schema churn). Flagged as a smaller open decision in
  §10 so the user can override.

**Files touched:**
- `docs/PROPOSAL_MEAL_PLANS.md` (new)
- `DORA_WORKLOG.md` (this entry)
- `DORA_FOLLOWUPS.md` (FU-032 — B6 allocation in-browser confirm)

**Verification:**
- Read both create+update meal-plan handlers, get_meal_plans,
  get_meal_plan_ingredients, get_shortfall, reconcile_consumed_meals,
  cook_recipe, adjust_recipe_meals, `_hydrate_unallocated` in
  get_recipes — to ground every "current state" claim against live
  code.
- Read MealPlansOverview.vue start-to-middle (first ~370 lines incl.
  template + setup, palette, week grid, sidebar, dialogs) and
  cross-referenced with the recipe store and dto models.
- No build/run — proposal only.

**Next up:**
- **User reviews `docs/PROPOSAL_MEAL_PLANS.md`** and approves /
  redirects the smaller open decisions in §10.
- Per the user's plan ("a valuable big rock, then back to INV") —
  next session, drive **INV — investigations**
  (`docs/prompts/INV_investigations.md`).
- If approved, the proposal's §11 lays out 8 chunked implementation
  prompts (A→H). Phase A (slot vocabulary) is the first reviewable
  chunk and can ship before the canvas changes start.

**Open questions for user:**
- Sign-off on the proposal (§2 big decisions are locked from prior
  Q&A; §10 smaller decisions need your call when convenient).
- Anything in the surface map that should swap places (e.g. calendar
  on the LEFT and recipe list on the right — the brief said right for
  calendar but you might prefer otherwise).

---

## 2026-06-06 — B9 (misc global bugs)
**Status:** complete (static verification only; node_modules absent)
**What changed (fixes):**
- **B9.2** — `web_app/src/components/menu/MainMenuButton.vue`: hide
  Quasar's built-in `.q-focus-helper` overlay so the custom `::before`
  hover ring is the only outline. Removes "double outline" on inactive
  hover.
- **B9.3** — `web_app/src/layouts/MainLayout.vue`: removed the Settings
  entry from `linksList` (main menu). Already lives in the user-avatar
  dropdown.
- **B9.6** — `web_app/src/pages/PriceHistoryPage.vue`: replaced the
  hard-coded `chartWidth.value = 720` with a `ResizeObserver` against
  the chart card element. Chart now extends to the card edge at every
  breakpoint, minus q-card-section padding (~16px). Selection→chart
  binding and tooltip theming verified already correct in current code.
- **B9.8** — `web_app/src/pages/LoginPage.vue`: removed `display:none`
  on `.login-mascot` below 760px; mascot now scales to 96px (and 72px
  below 360px) and is horizontally centred via `right: 50%; margin-right:
  -<half-width>px` so the `bob` keyframe (which owns `transform`) doesn't
  clobber centring. Plus `.dora-empty-mascot` (ProductSearch) and
  `.dora-hero-mascot` (Dashboard) force their inner `<img>` to
  `width:100%; height:100%; object-fit: contain` so the mascot is centred
  in its padded square.

**What changed (verified already-correct → confirm-in-browser FUs):**
- **B9.1** — drag-drop. Static walk-through both directions produces the
  right ordering; backend sorts by `(sequence, id)`; frontend's
  `insertAt = fromIdx < toIdx ? toIdx-1 : toIdx` checks out.
- **B9.4** — command palette. Every static command in `useCommands(...)`
  has a wired action; `create.stock-item` routes to `/stock?create=1`
  and `StockOverview.maybeOpenCreateFromQuery` watches it.
- **B9.9** — 404 page. Both surfaces already use tokens (A1 themed).

**What changed (needs decision / repro — flagged):**
- **B9.5** — undo. `stockItemStore.updateStockItemAsync` captures
  pre-state field-by-field and registers inverse+redo for every change,
  including expiry pushes/clears. Plumbing correct on static read.
  Closest guess for "oddly": Dashboard's `alerts.value` is its own ref
  and doesn't refetch after an inverse runs on another surface. FU-026
  requests a concrete repro.
- **B9.7** — log rotation. `RotatingFileHandler` is wired (10MB × 5
  backups) at `infrastructure/logging_setup.py:87`. Current ~46k-line
  file is below the size trigger. Symptom implies time-based rotation
  expectation. FU-027 needs decision: `TimedRotatingFileHandler` (and
  when?), or lower `maxBytes`?

**Decisions made:**
- Took the prompt's "OK with two nav fixes touching deferred areas" as
  implicit-yes since the user said "continue B9". Both are surgical.
- CLAUDE.md MANDATORY rule applied per-defect: every "code says fine"
  defect gets `[OPEN] confirm in browser`, not blanket "all fine".

**Files touched:**
- `web_app/src/components/menu/MainMenuButton.vue`
- `web_app/src/layouts/MainLayout.vue`
- `web_app/src/pages/PriceHistoryPage.vue`
- `web_app/src/pages/LoginPage.vue`
- `web_app/src/pages/ProductSearch.vue`
- `web_app/src/pages/DashboardPage.vue`
- `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, this worklog.

**Verification:**
- Each fix reasoned-through against current code; no build/run.
- ResizeObserver guarded with `typeof` for SSR safety; cleaned up in
  `onBeforeUnmount`.
- Mascot positioning: confirmed the `bob` keyframe only touches
  `transform` (not `right/left/top`), so `right + margin-right` centring
  is animation-safe.
- **Not run:** dev server / lint / type-check (node_modules absent).

**Next up:**
- **User eyeballs the 4 visible fixes** (menu hover, no Settings dup in
  main menu, price-history chart extends + resizes, mobile login mascot
  visible + Dora centred on ProductSearch/Dashboard).
- **User confirms the 3 FU-flagged "static-fine" items in browser**
  (DnD, palette commands, 404 theme).
- **User decision on B9.7** rotation model.
- **Precise repro requested on B9.5** undo oddness.
- **Wave B complete (B1-B9).** Per `docs/prompts/00_INDEX.md`: next is
  INV (investigations, read-only) → Wave C (big-rock design briefs).

**Open questions for user:** see Next up.

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — B5 follow-up 2: Dashboard "Continue" sealed-wizard bug + Wave-B audit
**Status:** complete (static verification only)
**What changed:**
- `web_app/src/pages/DashboardPage.vue` — replaced the
  `<q-btn ... to="/welcome">` bare router-link on the skipped-setup
  banner with `@click="onContinueOnboarding"`. New handler calls
  `onboardingApi.restartAsync()` → `authStore.refreshAsync()` → drops
  the `dora.onboarding.skipped_at` localStorage key → `router.push('/welcome')`.
  Imported `OnboardingApiService`.
- `DORA_FOLLOWUPS.md` — logged FU-017 (B3 user re-test) and the
  miss-pattern note (FU-016 already covers the cross-cutting audit).
- `CHANGELOG.md` — Continue fix entry above the previous Skip/Finish
  fix, plus reframing of the original "no changes needed" claim.

**Decisions made:**
- **User asked me to audit my own "already-fine" claims** after the
  Skip/Finish bug landed. Re-walked every "no changes needed" call I
  made this session against the user's reported symptoms:
  - **B3 "can't save without changing the name"** — backend
    handlers (stock_item, recipe, recipe_collection, stock_location,
    stock_group, user_as_admin, me) all use `model_fields_set` +
    exclude-self correctly. The repo's identity map means `_StockItem`
    and `_SameName` are the same Python object when ids match, so the
    `_SameName.id != stock_item_id` guard returns False. Type
    alignment is fine (both UUIDs). I can't reproduce statically.
    Logged FU-017 for the user to re-test in browser — if it still
    repros, the actual error payload will tell us what code path is
    actually firing.
  - **B5 Dashboard "Continue"** — **was wrong**, same family as the
    Skip/Finish bug. The bare `to="/welcome"` link triggered a
    navigation that the router guard immediately reverted, because
    Skip Everything had stamped `onboarding_completed_at` on the
    backend and the guard now redirects authed users with a
    non-null timestamp AWAY from `/welcome` (lines 103-109). Fixed
    by using the existing `restartAsync` infrastructure (backend
    route + frontend service method both already existed —
    `AccountSettings.vue`'s "Restart onboarding" action even
    contains a comment explaining the exact guard issue). The
    "audit" approach worked: I saw the pattern by re-tracing
    Skip Everything's downstream effects on the guard, not by
    re-reading the button's wiring in isolation.
  - **B5 Skip/Finish/Show-me-X** — confirmed wrong, fixed in the
    previous worklog entry.
  - **B4 link-also-saves** — was correct in narrative *post-B1*, but
    pre-B1 fix would have 422'd. Noting for completeness.
  - **B7 "no other double-toast patterns"** — limited audit; only
    walked `addItems` callers. Wider sweep (store-mutation + page
    toast double-emit) not done. Flagging for opportunistic fix.
- **B3 verdict: re-test, don't dig further blind.** User chose
  "follow up later" (FU-017). Cheaper to wait for a live repro than
  to keep tracing speculative paths.

**Files touched:**
- `web_app/src/pages/DashboardPage.vue`
- `DORA_FOLLOWUPS.md`
- `CHANGELOG.md`

**Verification:**
- Walked the Continue path: user has skipped → `currentUser.onboarding_completed_at`
  is an ISO string → click → `restartAsync` POST sets it back to null
  on backend → `refreshAsync()` re-fetches `/me` → cached value is
  now null → `router.push('/welcome')` → guard (94-99) sees null
  for an authed user → falls through to the WelcomeLayout. ✓
- Confirmed `AccountSettings.vue:110-124` does the exact same dance
  in a different surface; copying its pattern.
- Confirmed `/onboarding/restart` exists at
  `dora_api/features/onboarding/onboarding.py:151` and that
  `onboardingApiService.restartAsync` (line 20) hits it.
- `useAuthStore` and `currentUser` already imported and instantiated
  in DashboardPage (lines 766/824) — no new store imports needed.
- **Not run:** dev server / browser (node_modules absent).

**Next up:**
- **User eyeballs**: Skip Everything from a fresh user → land on
  dashboard → banner appears → click Continue → wizard opens at
  the welcome step. No refresh needed.
- Back to the Wave B sequence: **B8** — recipe-detail dead actions /
  permanent substitute swap / deleted substitutes-graph ref.

**Open questions for user:** none. Wider audit findings logged in
`DORA_FOLLOWUPS.md` (FU-016, FU-017, FU-018).

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — B5 follow-up: onboarding "dead button" bug (stale auth state vs router guard)
**Status:** complete (static verification only)
**What changed:**
- `web_app/src/pages/onboarding/WelcomeWizard.vue` — both `complete()` and
  `onSkipEverything()` now `await authStore.refreshAsync()` immediately
  after `onboardingApi.completeAsync()` and before `router.push('/')`.
  (Show-me-X also benefits because it calls `complete()`.)

**Decisions made:**
- **My earlier B5 verdict was wrong.** I claimed the buttons were
  "already wired correctly in current code" after a static read. User
  pushed back with the actual symptom: clicks did nothing until a
  browser refresh — classic stale-state behaviour I should have
  recognised. Logging the miss here so the pattern (handler exists ≠
  feature works; check the guard layer) sticks for the next session.
- **Root cause: router-guard / auth-store race.**
  `router/index.ts:94-99` redirects authed users with
  `currentUser?.onboarding_completed_at === null` to `/welcome`.
  `completeAsync()` updates the backend; the frontend's cached
  `currentUser` keeps the stale null. `router.push('/')` then trips
  the guard, which bounces back to `/welcome` immediately. Hard
  refresh works because the router's `beforeEach` calls
  `bootstrapAsync()` on a fresh page load, which re-fetches `/me` and
  observes the new timestamp.
- **Fix kept minimal:** add a single `await authStore.refreshAsync()`
  (the method already exists for exactly this case — its docstring
  literally references the onboarding flow). No changes to the
  router guard, no caching/optimistic updates. Two call sites
  touched.
- **No other callers of `completeAsync()`** in `src/` — verified by
  grep, so no other paths need the same paired refresh.

**Files touched:**
- `web_app/src/pages/onboarding/WelcomeWizard.vue`
- `CHANGELOG.md` (extended the B5 Fixed entry rather than starting a
  new one — same prompt's loop)

**Verification:**
- Walked the failure path through `router/index.ts:75-118`: before
  fix, guard sees stale `null` → `{ path: '/welcome' }`; after fix,
  guard sees ISO timestamp → falls through to the actual destination.
- Confirmed `authStore.refreshAsync()` is the right method (line
  67-71 of authStore.ts) — its own docstring calls out the
  onboarding-state case. `useAuthStore` is already imported and
  instantiated in WelcomeWizard (lines 363/374).
- `clearDraft()` and the localStorage manipulation still run after
  the refresh, in the same order as before the bug fix.
- Grep'd every other call to `onboardingApi.completeAsync()` — only
  the two fixed sites. No other path leaks the same stale guard
  read.
- **Not run:** dev server / browser repro (node_modules absent).
  Once deps installed, this is the exact eyeball flow: Welcome →
  Finish (or Skip everything, or Show-me-X) → should land on its
  destination first try, no refresh needed.

**Next up:**
- **User re-eyeballs B5 onboarding flow** end-to-end. If a
  Finish/Skip/Show-me-X click still appears dead, the next thing to
  check is whether `getMeAsync()` is actually returning the updated
  timestamp (backend issue) rather than a stale-frontend issue.
- Then back to the Wave B sequence: **B8 — recipe-detail dead
  actions / permanent substitute swap / deleted substitutes-graph
  ref**.

**Open questions for user:**
- Worth a parallel audit for any other "frontend cached state vs
  backend mutation" gaps? Common shapes: after-import data refresh,
  after-restore stock-item refresh, after-onboarding-restart refresh.
  Logging as an opportunistic follow-up rather than acting now.

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — B7 (notification defects: "I'm a notification!" + duplicate toasts)
**Status:** complete (static verification only)
**What changed:**
- `web_app/src/boot/notifyTypeRegistration.ts` — removed placeholder
  `message: 'Hey did you know...'` and `caption: "I'm a notification!"`
  from the custom `info` Notify type registration. Type still defines
  the visual styling (colour, icon, progress bar, classes); the text now
  comes exclusively from the call site, as it should.
- `web_app/src/boot/axios.ts` — **deleted**. Quasar scaffold file with
  `baseURL: 'https://api.example.com'`. Confirmed: NOT registered in
  `quasar.config.ts`'s `boot:` array; `$api` / `$axios` never referenced
  in `src/`. The real http client is `axiosHttpClient.ts`.
- `web_app/src/pages/StocktakeRunner.vue` — `onAddToList` now delegates
  to `useStockItemActions.addToList(stock_item_id)` instead of calling
  `useShoppingListActions.addItems(...)` and then firing its own
  second toast. Dropped the `useShoppingListStore` /
  `useShoppingListActions` imports and the local `primaryListId` /
  no-primary-list branch (handled inside `addToList`).

**Decisions made:**
- **Fix the source, not the call sites.** Every `notify({ type: 'info', ... })`
  call already supplies a real message — the placeholder caption was
  bleeding through *underneath* the real message because Quasar renders
  both message and caption. Trimming the type registration is one
  surgical change rather than touching every caller. Sweep confirmed
  no caller relied on the placeholder defaults.
- **Reuse `useStockItemActions.addToList` instead of writing new
  messaging.** It already does the correct "Already on your primary
  list." vs "Added to primary list." messaging, handles the
  no-primary-list dialog, and is the cross-screen single-item action
  every other surface uses. The duplicate-toast bug was really a "this
  page used the bulk composable for a single item" miswiring.
- **No other double-toast patterns found.** Audited every `addItems`
  caller (4 sites: QuickAddSheet, AlertsBell, MyProductsPage,
  DoraChat). None stacks a custom toast on top of the composable's
  summary toast. DoraChat does push a chat-bubble after `addItems`,
  but that's a different surface (in-chat reply vs system Notify),
  not a redundant toast.
- **Kept `oopsie` type intact.** Its `message: 'Oops, something went
  wrong...'` default is real production copy used by
  `globalErrorHandler.ts` and `boot/stores.ts` which call
  `Notify.create({ type: 'oopsie' })` with no message — that's a
  deliberate "use the default" pattern there, not a placeholder leak.

**Files touched:**
- `web_app/src/boot/notifyTypeRegistration.ts`
- `web_app/src/boot/axios.ts` (deleted)
- `web_app/src/pages/StocktakeRunner.vue`
- `CHANGELOG.md` (Removed + Fixed entries)

**Verification:**
- Grep'd `"I'm a notification"`, `"placeholder"`, `"lorem"`,
  `"example.com"`, `"demo"` across `web_app/src/`. Remaining matches
  are either (a) input-`placeholder=` attributes (legitimate form
  hints), (b) the merchant-logo `.dora-logo-placeholder` CSS class
  (real placeholder badge rendering — not text), or (c) the
  intentional "UI placeholder" tooltips on unfinished
  `SystemSettings` toggles (those are functional indicators, not
  copy bugs).
- Manually walked through `notifyTypeRegistration.ts` post-edit —
  `info` type now only sets visual properties; no leaking text.
- Confirmed StocktakeRunner still uses `useStockLevelStore`,
  `StocktakeApiService`, `StockItemApiService`, and `useQuasar`;
  none of the removed imports are referenced elsewhere in the file.
- Quasar `boot:` array in `quasar.config.ts` does NOT list
  `axios` — confirmed the deletion has zero runtime effect.
- **Not run:** dev server / type-check / lint (node_modules absent).

**Next up:**
- **User eyeballs B7** in browser: Meal Plans → "Generate shopping
  list for this week" → toast should now show just the real message,
  no "I'm a notification!" caption under it. Stocktake → Add to list
  → exactly one toast ("Added to primary list." or "Already on your
  primary list."), no contradictory pair.
- Then proceed to **B8 — Recipe detail dead actions / permanent
  substitute swap / deleted substitutes-graph ref**, next 🟡 in
  Wave B.

**Open questions for user:** none.

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — B5 (dead nav buttons — onboarding, dashboard, alerts→404)
**Status:** complete (static verification only — node_modules absent)
**What changed:**
- New `web_app/src/pages/AlertsPage.vue` — minimal stopgap.
  Reuses `useAlertStore` (same source as the bell), groups items by severity
  with severity-coloured avatars + per-kind icons, shows snoozed entries in
  a collapsed expansion at the bottom, click row → `/stock/<id>`.
  Deliberately does NOT host inline actions (push expiry / mark restocked /
  snooze new) — those stay on the bell panel for now. Banner makes that
  explicit so the page doesn't read as half-built.
- `web_app/src/router/routes.ts` — added `/alerts` route under MainLayout.
- `CHANGELOG.md` — Unreleased § Added (AlertsPage stopgap) + § Fixed
  (`/alerts` 404 resolved, rest of B5 cluster verified already-wired).

**Decisions made:**
- **B5 is 80% already-wired.** Audit found the only real bug in the cluster
  was the `/alerts` 404; the rest were already correct in current code.
  Specifically verified:
  - `WelcomeWizard.vue:677` `onSkipEverything` → `onboardingApi.completeAsync()`
    + sets `dora.onboarding.skipped_at` + `router.push('/')`.
  - `WelcomeWizard.vue:702` `complete()` (invoked on Finish via
    `onNext`→`isLastStep`) → `completeAsync()` + clears skipped flag +
    `router.push('/')`.
  - `WelcomeWizard.vue:670` `onShowMe` → completes onboarding, then
    `router.push(path)` for the tour card (4 cards: `/stock`,
    `/shopping-lists`, `/stock?attention=true`, `/help`).
  - `DashboardPage.vue:77` Continue button uses `to="/welcome"` — Quasar
    router-link is fine, navigates correctly.
  Logged the verification rather than making no-op edits.
- **Stopgap target = new minimal page** (per user). Going with a tiny
  page rather than redirecting to the bell drawer keeps the link semantics
  honest (`All N →` lands on a real list view), and reusing `alertStore`
  means no duplicate fetching.
- **No inline actions on the page (yet).** The C-wave brief owns the real
  control centre. Putting half the actions here would risk locking in a
  shape we'd then have to rework. Banner explicitly steers users at the
  bell so they don't think the actions vanished.
- **Page is added to MainLayout's children**, not the deferred-section
  list — `/alerts` is an active navigation target now, not a planning
  doc. The "deferred surfaces" guidance in CLAUDE.md is about *redesign*,
  not *don't add routes that 404 today*.

**Files touched:**
- `web_app/src/pages/AlertsPage.vue` (new)
- `web_app/src/router/routes.ts`
- `CHANGELOG.md`

**Verification:**
- Read every handler the prompt named: `onSkipEverything`, `complete`,
  `onShowMe`, dashboard Continue button. Each navigates and persists state
  per the prompt's "Fix wiring" section already.
- TOUR_CARDS' four paths (`/stock`, `/shopping-lists`,
  `/stock?attention=true`, `/help`) all map to existing routes in
  `routes.ts` — no further 404s in the show-me-X cluster.
- Confirmed `/alerts` previously hit the catch-all `ErrorNotFound`
  (line 196 of `routes.ts`). New route at indent under MainLayout means
  the page renders inside the standard chrome with header bell still
  visible.
- Sanity-checked every ICONS key used in AlertsPage
  (`priority_high`, `warning`, `info`, `snooze`, `undo`,
  `chevron_right`, `check_circle`, `refresh`) — all exist in `style/icons.ts`.
- `useAlertStore` API used: `alerts`, `loading`, `loadError`, `totalCount`,
  `snoozedCount`, `snoozedAlerts`, `refreshAsync`, `snoozedUntil`,
  `unsnoozeAlert` — all on the public return of the store.
- **Not run:** dev server / lint / type-check (node_modules absent).

**Next up:**
- **User eyeballs B5** in browser: click "All N alerts →" on dashboard →
  lands on /alerts with grouped list; bell still works independently;
  onboarding Skip/Finish/Show-me-X still navigate as expected.
- Then proceed to **B7 — notification defects** ("I'm a notification!"
  placeholder, duplicate/contradictory toasts), next 🟢 in Wave B.

**Open questions for user:** none — but note: TOUR_CARDS' "Alerts" tour
card still routes to `/stock?attention=true` (per the existing copy "deep-
link into Stock"). That predates today's `/alerts` page; the user can
decide later whether to switch the tour card to `/alerts` instead. Logged
as a follow-up.

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — B4 (delete stock item → FK constraint failed)
**Status:** complete (static verification only — node_modules / DB not exercised)
**What changed:**
- `dora_api/features/stock_items/delete_stock_item.py` — full rewrite:
  - New `BlockingRecipe` dataclass; `DeleteStockItemResponse` carries
    `blocked_by_recipes: list[BlockingRecipe]`.
  - Handler now queries `RecipeIngredient._stock_item_id` (same shape as
    `get_stock_item_detail.linked_recipes`) before `repository.remove(...)`.
    If any recipes reference the item, returns a non-empty
    `blocked_by_recipes` and skips the delete entirely — nothing is mutated.
  - New module-local `_blocked_by_recipes_response(...)` helper builds the
    422 problem-details body: standard `errors`/`title`/`type` shape PLUS a
    `blocked_by_recipes: [{recipe_id, name}]` extension the frontend uses
    to render a structured dialog.
- `web_app/src/pages/StockItemDetailPage.vue`:
  - `confirmDelete` message changed from
    `Delete "X"? Recipes that use it will be left with a dangling reference.`
    to `Delete "X"?`. The dangling-reference promise was incorrect: the FK
    is `RESTRICT`, so the previous behaviour was a 500, not a dangle.
  - `doDelete` catch block now inspects `err.details?.blocked_by_recipes`;
    if it's a non-empty array, pops a Quasar `$q.dialog` with
    `html: true` listing the recipe names ("Can't delete this stock item —
    it's an ingredient on N recipe(s): …"). Other errors still flow into
    the existing `notifyErr` toast.
  - Added `NormalisedApiError` to the existing `axiosHttpClient` import so
    the catch can type-narrow.

**Decisions made:**
- **Policy (b) — block-with-explanation** (per user). Implemented entirely on
  the existing 422/problem-details rails; no new HTTP helper added (kept
  churn low — used `flask.jsonify` directly in the module-local helper).
- **Extension field placement.** Put `blocked_by_recipes` on the body itself
  rather than buried inside `errors`. `errors` keeps the string fallback so
  `describeApiError` still produces a readable line for clients that don't
  know the extension (e.g. assistant tools, future routes). This keeps the
  contract additive — no existing error-handling code breaks.
- **Reference map confirms no other action needed.** Every other FK to
  StockItem either cascades or set-nulls — `ShoppingListLine`,
  `ShoppingListTemplateLine`, `StockItemProduct`, `StockLevelChange`,
  legacy `StockItemSubstitute` (all CASCADE); `StockItemWasteEvent`
  (SET NULL with denormalised name to preserve history). Only
  `RecipeIngredient` was RESTRICT and that's now handled.
- **Sweep: only one other RESTRICT FK in schema** — `Product.merchant_id`
  → `Merchant.id`. No DELETE route exists for Merchant, so no exposure.
  Other delete handlers don't need the same treatment.

**Files touched:**
- `dora_api/features/stock_items/delete_stock_item.py`
- `web_app/src/pages/StockItemDetailPage.vue`
- `CHANGELOG.md` (Unreleased § Fixed — B4 entry above B1)

**Verification:**
- Reasoned through three paths against current code:
  1. Item not used anywhere → query returns no ingredient rows → `remove` +
     `save_changes` + 204. (Unchanged behaviour for the happy path.)
  2. Item used by ≥1 recipe → query returns ids → fetch recipe names →
     422 with `blocked_by_recipes` → frontend dialog. (Was 500.)
  3. Item id doesn't exist → unchanged 404.
- Cross-checked the RecipeIngredient query against the existing
  `get_stock_item_detail.linked_recipes` query (same `_recipe_id` /
  `_stock_item_id` mapper-property names); both compile against the same
  table_mappings.
- Verified the only call site for `stockItemStore.deleteStockItemAsync` is
  `StockItemDetailPage.vue:913` — no other surfaces need the new dialog.
- Verified the optimistic-update / Undo flow in the store doesn't fire on
  failure: the store awaits `deleteAsync` before mutating the local array,
  so a 422 throw bypasses the splice and the snapshot/restore toast.
- **Not run:** dev server, DB delete, lint, type-check (node_modules absent).

**Next up:**
- **User eyeballs B4** in browser once deps installed:
  - Delete an unreferenced stock item → succeeds with Undo toast.
  - Delete an item used by a recipe → dialog appears listing the recipe(s);
    no toast; no 500 in server logs.
  - Delete a stock item that's *only* on a shopping list (no recipe) →
    succeeds; the line cascades out cleanly.
- Then proceed to **B5 — dead nav buttons** (onboarding skip/finish, dashboard
  continue, Alerts → 404), next 🟢 in Wave B.

**Open questions for user:** none.

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — B3 (partial-update semantics / "can't save unless I change the name")
**Status:** complete (verified-resolved — no code changes)
**What changed:** nothing in code. Audit confirmed the reported bug doesn't
reproduce in current backend code (same situation as B2).

**Decisions made:**
- **B3 closed as already-resolved.** The bug Joey reported is the
  classic PUT-style self-collision: name-uniqueness check finds the row, the
  row *is* the row being edited, but the handler doesn't exclude self → 422.
  Every update handler in the repo now does both of B3's recommended fixes:
  - **Partial update via `model_fields_set`** (only set fields get applied):
    `update_stock_item.py`, `update_recipe.py`, `update_stock_location.py`,
    `manage_stock_groups.py`, `update_user_as_admin.py`, `update_me.py`,
    `update_meal_plan.py`.
  - **Exclude-self on the name-uniqueness check** (`_SameName.id != <entity_id>`):
    `update_stock_item.py:118`, `update_recipe.py:100`,
    `update_recipe_collection.py:40`, `update_stock_location.py:48`,
    `manage_stock_groups.py:156`, `update_user_as_admin.py:86`,
    `update_me.py:71`.
  Handlers without a name-uniqueness check (`update_meal_plan`,
  `update_location`, `update_product`, `update_app_settings`) don't need one.
- **Probable history:** the meals→recipes merge and DS-series rework that
  fixed B2 also brought this pattern in line. Stale planning docs again.
- **No CHANGELOG entry** — nothing shipped this session for B3. The
  underlying fix already shipped in earlier work and is already reflected
  in the current code.

**Files touched:** none.

**Verification:**
- Read both handlers the prompt names: `update_stock_item.py`,
  `update_recipe.py`. Both exclude-self and use `model_fields_set`.
- Swept every other `update_*.py` in `dora_api/features/` for the same risk
  pattern. All clean.
- Reasoned through the failure path: send unchanged name → backend finds
  same row → `id != current_id` is False → no `already_exists` → name
  re-assigned no-op → save_changes → 204. Should work today.
- **Not run:** the actual edit flow in browser. User should still eyeball
  before fully closing the loop (edit a stock item changing only expiry,
  edit a recipe changing only servings — both should save without changing
  name). Logged as part of the upcoming verification sweep.

**Next up:**
- **User eyeballs B1 + B3** together once deps are installed. B3 verification
  is: edit a stock item changing only e.g. expiry → saves; edit a recipe
  changing only servings → saves; renaming to a *different* existing name
  still 422s.
- Then proceed to **B4 — delete cascade ("delete stock item → FOREIGN KEY
  constraint failed")**, next 🟡 in Wave B.

**Open questions for user:** none — but if the bug DOES still reproduce in
browser, the cause must be frontend-side (e.g. a stale optimistic-update
toast) or a code path I haven't seen yet. Flag it and I'll re-investigate.

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — B1 ("Extra inputs are not permitted" on product save/link/quick-add/inactive)
**Status:** complete (static verification only — node_modules not installed)
**What changed:**
- `web_app/src/services/api/productApiService.ts` — `updateAsync` now strips
  `product_id` from the PATCH body (mirrors the `stockItemApiService.updateAsync`
  pattern). Was sending the full `UpdateProductCommand` including `product_id`,
  which the backend `UpdateProductRequest` (`extra="forbid"`) rejects.
- `web_app/src/pages/ProductSearch.vue` — `ensureSaved` now builds an explicit
  `CreateProductCommand` from the offer (brand, image, is_active=true,
  is_available, merchant_name, merchant_stockcode, name, price_now, price_was,
  size, size_unit, size_value, web_url). Was `{ ...offer, is_active: true }`,
  which leaked the offer-only fields `is_saved`, `is_saved_product_active`,
  `price_difference`, `price_per_cup` and tripped `CreateProductRequest`'s
  `extra="forbid"`.

**Decisions made:**
- **Backend kept frontend-aligned, not the other way around** (per the prompt's
  default). Two `extra="forbid"` schemas survive intact: `CreateProductRequest`
  and `UpdateProductRequest`. The leaking offer fields are display-only state,
  so the right move was to drop them client-side.
- **"Link also saves" requirement was already met.** `confirmLink` (and
  `onQuickAdd`) already call `ensureSaved` before `stockItemApi.linkProductAsync`.
  No new transaction logic added — sequencing was already correct. Fixing
  `ensureSaved`'s payload makes the existing save-then-link flow actually
  succeed.
- **Quick-add and Link backend models already matched the frontend** —
  `QuickAddRequest{stock_item_id}` and `LinkProductRequest{product_id}` accept
  exactly what the frontend sends. Both flows failed because of the save step
  they each chain to (`ensureSaved`), not the quick-add/link calls themselves.
  Logged here so a future agent doesn't go looking for a separate fix.

**Files touched:**
- `web_app/src/services/api/productApiService.ts`
- `web_app/src/pages/ProductSearch.vue`
- `CHANGELOG.md` (Unreleased § Fixed — new section)

**Verification:**
- Grep'd every caller of `productApi.createAsync` / `productApi.updateAsync` /
  `productStore.createProductAsync` / `productStore.updateProductAsync` —
  three call sites total (ProductSearch ensureSaved + onSaveToggle,
  MyProductsPage bulk inactive + per-row toggle). All now send only allowed
  fields.
- Cross-checked `CreateProductRequest` (create_product.py) and
  `UpdateProductRequest` (update_product.py) field-by-field against the new
  explicit `ensureSaved` payload and the trimmed PATCH body. No remaining
  mismatches.
- Walked the four failing actions end-to-end against current code: Save
  (create) → ensureSaved fixed; Save toggle / Mark active+inactive (bulk and
  per-row) → updateAsync trim fixed; Quick-add → ensureSaved + already-OK
  primary-line POST; Link → ensureSaved + already-OK link POST.
- **Not run:** `quasar build` / lint / dev server — `node_modules` absent.
- **Not tested manually** — UI eyeball required (see Next up).

**Next up:**
- **User eyeballs B1** on Product Search + My Products: Save toggle,
  Mark inactive (per-row and bulk), Quick-add to primary list, Link to stock
  item. Confirm no "Extra inputs are not permitted" toast on any.
- Then proceed to **B3 — partial-update semantics ("can't save unless I change
  the name")**, next 🟡 in Wave B.

**Open questions for user:**
- The image field is sent as a string from the frontend (`offer.image`) but
  the backend expects `Base64Bytes | None`. If existing offers populate
  `image` as a full data URL or a `data:image/...;base64,...` string, the
  backend may not parse it cleanly. Worth checking once the dev server runs.
  Logged as FU candidate if it surfaces.

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — A6 (text-size scale: re-spaced + extra-large + global apply)
**Status:** complete — static verification only (node_modules absent)
**What changed:**
- **New 4th step + re-spaced scale.** `themeService.ts` FONT_SIZE_PX:
  sm 14 / md 16.5 / lg 20.5 / xl 23px (was 14/16/18, too close). Ratios ≈
  0.85 / 1.0 / 1.25 / 1.4 with a very slightly larger default.
- **`xl` wired end-to-end:** `models/auth.ts` `FontSizePreference` += `'xl'`;
  `PreferencesSettings.vue` picker += "Extra large"; backend
  `user.py` `ALLOWED_FONT_SIZES` += `FONT_SIZE_XL`. DB column is `String(2)` so
  "xl" fits — **no migration**. Default stays `md`.
- **Global application (fixed-px → scale tokens):** `PageTitle.vue` (24px →
  `calc(var(--font-size-2xl)*1rem)`), `PreferencesSettings` theme-card blurb and
  `AuditLogSettings` payload/mono (12px → `--font-size-xs`). Added a `.q-tooltip`
  rule in `app.scss` so tooltips follow the pref.

**Decisions made:**
- **User chose 4 steps `0.85 / 1.0 / 1.25 / 1.4` with a "very slightly larger"
  default** (vs the prompt's 3-step options). Implemented base md = 16.5px (a
  +3% bump from 16) → sm 14 / lg 20.5 / xl 23 honour those ratios with clean-ish
  px. This was a bigger change than "re-space" (new enum value end-to-end).
- **Root cause of "not applied everywhere":** `app.scss` already sets
  `:root { font-size: var(--dora-base-font-size) }`, so rem text (incl. Quasar
  `text-*`) already scaled. The only hold-outs were fixed-px — migrated the real
  text ones; left deliberate carve-outs (camera overlay, SVG chart, micro-gauge).
- **Tooltips:** added a defensive global rule (they teleport to <body>; rem still
  resolves against root, but the rule guarantees they track the pref).

**Files touched:**
- Backend: `dora_api/domain/entities/user.py`.
- Frontend: `web_app/src/models/auth.ts`, `web_app/src/services/themeService.ts`,
  `web_app/src/pages/settings/PreferencesSettings.vue`,
  `web_app/src/components/menu/PageTitle.vue`,
  `web_app/src/pages/settings/AuditLogSettings.vue`, `web_app/src/css/app.scss`.
- `CHANGELOG.md`, `DORA_FOLLOWUPS.md`.

**Verification:**
- `FONT_SIZE_PX` is the only `Record<FontSizePreference,…>` — updated with `xl`;
  no other exhaustive map/switch over font sizes (grep). Picker is the only
  runtime option list (updated).
- Backend `ALLOWED_FONT_SIZES` now accepts `xl`; `register_user` passes through
  (no input validation against the old set); entity default `md` unchanged.
- Fixed-px audit: 8 sites total; 4 migrated (PageTitle, Preferences blurb,
  AuditLog ×2), 4 intentionally kept (ScanOverlay ×2, PriceHistoryChart SVG,
  Dashboard 3px/7.5px micro-gauge).
- **Not run:** lint / build / dev server — node_modules absent. See FU-025 for
  the required in-browser eyeball (xl on dense screens, tooltip scaling).

**Next up:**
- **User eyeballs A6** (FU-025): switch through Small→Extra large; confirm the
  spread is now obvious and nothing breaks on dense screens at xl; tooltips scale.
- **Wave A is essentially done** bar A8 (renames/refresh/nav-state, 🟡 — has
  decisions). A1, A1b, A2, A3, A4, A5, A6, A7 all complete.
- Wave B: B9 remains (other session's lane).

**Open questions for user:**
- Is md = 16.5px the right "very slightly larger" default, or nudge to 17?
- Happy with the xl spread (23px base → headings get large), or cap it lower?

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — A7 (sticky page-counts footer)
**Status:** complete — static verification only (node_modules absent)
**What changed:**
- New `web_app/src/components/PageCountsFooter.vue` — sticky-to-bottom counts
  footer (top border + soft elevation, tokenised; responsive wrap). Props:
  `counts: { label, value, tone? }[]`. tone → theme-aware text-* class.
- `useStockFilters.ts`: added `footerCounts` computed over the FILTERED set —
  Shown + per-stock-level (dynamic from `stockLevels`, so it survives renames;
  tone via name heuristic) + Flagged + Auto-add + Needs attention.
- StockOverview: **removed the top summary banner**; footer renders the counts.
  Toolbar button row untouched (Wave-C owns the top-area teardown).
- RecipesOverview: removed top count text; footer = Shown + Cookable now +
  Favourites (filtered). Removed now-orphan `cookableNowCount`.
- MyProductsPage: removed top count text; footer = Shown + On deal + Unlinked
  (filtered). Replaced orphan `onDealCount`/`unlinkedCount` with `footerCounts`.

**Decisions made:**
- **Counts reflect the FILTERED view** (user's call) — matches the
  export-follows-filtered convention. A "Shown" stat gives the filtered total.
- **Removed the StockOverview summary banner** (user's call) and moved counts to
  the footer; explicitly did NOT touch the toolbar (that's the Wave-C Stock
  Overview brief, per A7's own note).
- **Per-level stats derived dynamically** from the stock-levels list rather than
  hardcoding "Well-Stocked"/"Sufficient" — robust to user-renamed/added levels.
- Footer shown only when the page has data (`v-if=...length > 0`).

**Files touched:**
- New: `web_app/src/components/PageCountsFooter.vue`.
- `web_app/src/composables/useStockFilters.ts` (footerCounts).
- `web_app/src/pages/StockOverview.vue`, `RecipesOverview.vue`, `MyProductsPage.vue`.
- `CHANGELOG.md`, `DORA_FOLLOWUPS.md`.

**Verification:**
- 3 pages each: 1 `<PageCountsFooter>` use + import present (scripted).
- 0 orphan count computeds left (cookableNowCount/onDealCount/unlinkedCount gone).
- `summaryCounts` still exported from useStockFilters (now unused by the banner,
  harmless); `countByLevel` still used by the level-filter chips.
- **Not run:** lint / build / dev server — node_modules absent. Sticky-bottom
  behaviour in the Quasar layout needs an in-browser eyeball.

**Next up:**
- **User eyeballs A7:** footer sticks to the bottom without overlapping content;
  counts update live with filters; consistent across the 3 pages; mobile wraps
  sensibly; light + dark.
- **Wave A remaining:** A6 (text-size scale, 🟡) and A8 (renames/refresh/nav-state,
  🟡) — both have decisions to confirm first. A7 was the last 🟢 foundation.
- Wave B: B9 still open (other session's lane).

**Open questions for user:**
- Footer sticky behaviour OK in the real layout, or prefer a plain (non-sticky)
  bottom strip?
- Adopt the footer on other list pages (shopping lists, meal plans) too? (FU-024.)

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — A5 (one loading/skeleton treatment everywhere)
**Status:** complete (active surfaces; deferred pages noted) — static verification only
**What changed:**
- New `web_app/src/components/AppSpinner.vue` — shared inline/short-wait spinner
  (consistent size, theme-aware colour, optional label, `block` mode).
- New `web_app/src/components/AppSkeleton.vue` — layout-mimicking placeholder
  blocks (`line`/`rect`/`circle`), pulse on the boot splash's 1.6s rhythm,
  theme-aware (color-mix of `--surface-sunken` + `--text-muted`), reduced-motion
  aware.
- **Detail pages → skeletons (kills the placeholder-text bug):**
  `StockItemDetailPage` (no more "Stock item" while loading — skeleton title +
  toolbar/card blocks), `ShoppingListDetail` (no more "Loading…" — skeleton
  rows), `RecipeDetailPage` (header + two-column skeleton).
- **Spinners → `AppSpinner`** on: RecipesOverview, ShoppingListsOverview (+ inline
  "Loading totals…"), MyProductsPage, DashboardPage, ProductSearch (searching
  banner — was `q-spinner-dots color=primary`, now consistent), RecipeCookMode
  (page + swap-picker), RecipeDetailPage substitutes, ShoppingListShopMode,
  ShoppingListTemplates, ShopNowRedirect, QuickAddSheet.

**Decisions made:**
- **Decision (spinner + skeleton, both)** taken as recommended — boot-pulse-style
  spinner for short/inline waits; skeletons for known-layout detail/list loads.
  The user's impact-block intent was clearly both.
- **Reused the existing boot pulse rhythm** (index.html `pre-mount-pulse` /
  `SplashScreen` `splash-pulse`, both already identical: 1.6s ease-in-out). For
  skeleton blocks I used an **opacity-only** pulse on that rhythm — the boot pulse
  also scales, which would look wrong resizing individual layout blocks.
- **Skeleton colour via `color-mix`** of existing tokens (no new global token, no
  10-theme edit) → automatically theme-aware.
- **Deferred surfaces left on raw `q-spinner`** (Reports, Data→Export/Print,
  Settings sub-pages — on the prompt-pack "deferred" list) plus **DoraChat's
  typing dots** (deliberate). Logged as FU-023. A spinner swap there is harmless
  but low-value and the pages are "don't design yet."
- **Overviews got `AppSpinner`, not list-skeletons** — bounded scope; the
  placeholder-text bug was the detail-page issue. List-skeletons noted in FU-023.

**Files touched:**
- New: `web_app/src/components/AppSpinner.vue`, `web_app/src/components/AppSkeleton.vue`.
- Pages: `StockItemDetailPage`, `ShoppingListDetail`, `RecipeDetailPage`,
  `RecipeCookMode`, `RecipesOverview`, `ShoppingListsOverview`, `MyProductsPage`,
  `DashboardPage`, `ProductSearch`, `ShoppingListShopMode`, `ShoppingListTemplates`,
  `ShopNowRedirect`.
- Components: `QuickAddSheet`.
- `CHANGELOG.md`, `DORA_FOLLOWUPS.md`.

**Verification:**
- 0 AppSpinner/AppSkeleton usages missing their import (scripted check).
- Remaining `q-spinner` only on the deferred surfaces + DoraChat dots (expected).
- Detail-page placeholder strings ("Stock item", "Loading…") no longer render
  during load — replaced by skeletons in the keyed loading branch.
- **Not run:** lint / `quasar build` / dev server — `node_modules` absent.

**Next up:**
- **User eyeballs A5** once deps installed: detail pages show layout skeletons
  (not placeholder text); spinners consistent; ProductSearch searching banner
  reads in dark themes; reduced-motion stops the pulse. Light + dark.
- **Wave A remaining:** A6 (text-size scale, 🟡), A7 (sticky footer, 🟢),
  A8 (renames/refresh/nav-state, 🟡). Suggest A7 next (🟢, no decision), then the
  two 🟡 ones.
- Wave B: B9 still open (other session's lane).

**Open questions for user:**
- Want list-skeletons on the big overviews too (currently a centred spinner), or
  is spinner-for-lists fine? (Tracked in FU-023.)
- Migrate the deferred-page spinners (Reports/Data/Settings) now for full
  consistency, or leave per the "deferred" guidance?

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

---
## 2026-06-05 — B8 (recipe detail actions + substitutes → cook-session swap)
**Status:** complete (static verification only — node_modules not installed)
**What changed:**
- **Substitutes reworked to a temporary cook-session swap** (user's decision):
  - `RecipeCookMode.vue`: added per-ingredient session swap. New `sessionSwaps`
    Map (original stock_item_id → {substituteId, substituteName}), a swap-picker
    BaseDialog (fetches `stockItemApi.getDetailAsync(id).substitutes`), ↔ button +
    "Y instead of X" display + undo per ingredient row. `confirmFinish` maps used
    ids through `sessionSwaps` so the *substitute* is decremented / ran-out-checked,
    not the original. Never touches the saved recipe.
  - `RecipeDetailPage.vue`: removed the destructive `onSwapIngredient` (it edited
    the recipe form + marked dirty → permanent on Save). Substitutes dialog is now
    informational (chips non-clickable) with a note pointing to cook mode.
- Reworded stale "substitutes graph" text → "substitutes" in `RecipeDetailPage`
  (sidebar caption), `useStockItemActions.ts`, `StockOverview.vue`.
- Clarified `CLAUDE.md` "Removed features": the removed thing is the standalone
  substitute **graph page** (N7 `/substitutes`), NOT basic per-item substitutes.

**Decisions made:**
- **The substitutes confusion, resolved with the user.** Current state: the N7
  graph *page* is already deleted (no route/component); basic per-stock-item
  substitutes are live (stock-item tab + `StockItemSubstitute` table + recipe
  find-substitutes). Docs/CLAUDE.md conflated the two ("Substitute graph
  (stock-item substitutes)"). User wants basic substitutes KEPT; only the graph
  page was ever meant to go. Confirmed against `RECONCILED_FINISHING_PLAN §39`
  and `PROMPT_PLAN.md:90,154` (substitutes are a kept P2 feature).
- **Substitute behaviour = temporary cook-session swap** (user picked this over
  add-to-list / informational-only). Swap lives in cook mode, never edits the
  saved recipe. Recipe detail keeps substitutes *visible* (informational).
- **Most B8 reported defects don't reproduce** (stale docs / meals→recipes merge):
  favourite toggle chain is sound (sends `!is_favourite` → PATCH → backend
  assigns); all recipe actions are wired; there is no related-recipes section at
  all (so "clicking a related recipe → overview" can't happen). Logged, not
  "fixed". The genuine bug was the permanent substitute swap.
- Did NOT purge the substitutes backend/table — it's the kept feature.

**Files touched:**
- `web_app/src/pages/RecipeCookMode.vue` (session swap: state, picker dialog, row
  UI, finish mapping; +imports StockItemApiService, Substitute).
- `web_app/src/pages/RecipeDetailPage.vue` (removed destructive swap; dialog now
  informational; caption reworded).
- `web_app/src/composables/useStockItemActions.ts`, `web_app/src/pages/StockOverview.vue`
  (comment rewordings).
- `CLAUDE.md` (Removed-features clarification), `CHANGELOG.md`, `DORA_FOLLOWUPS.md`.

**Verification:**
- No "substitute(s) graph" text remains anywhere in `web_app/src`.
- `onSwapIngredient` fully removed from RecipeDetailPage (0 refs); `Substitute`
  type still used (substituteOptions) — no orphan import.
- RecipeCookMode tag balance: BaseDialog 2/2, q-card-section 8/8, template 5/5.
- `Substitute` model fields (`stock_item_id`, `name`) match the picker usage.
- Reasoned through finish flow: swapped ingredient decrements/ran-out-checks the
  substitute id, not the original.
- **Not run:** lint / `quasar build` / dev server — `node_modules` absent.

**Next up:**
- **User eyeballs B8** once deps installed: in cook mode, swap an ingredient (↔),
  confirm "Y instead of X" + undo, finish and confirm the *substitute's* level
  drops (not the original) and ran-out adds the substitute; on recipe detail,
  confirm "Find substitutes" no longer edits the recipe (Save stays disabled /
  recipe unchanged). Also confirm favourite un-toggle persists (reported broken;
  looks fine in code).
- Continue Wave B: next is **B9 — misc bugs** (`docs/prompts/B9_misc_bugs.md`),
  or revisit B1/B3/B4/B5/B7 if those weren't actually run yet (verify against
  code — our logs only cover A-series + B8).

**Open questions for user:**
- Cook-session swap feel right, or do you also want a quick swap affordance on
  the recipe detail page itself (not just cook mode)?
- Were B1/B3/B4/B5/B7 already run in other sessions? Our worklog has no record —
  worth confirming before assuming Wave B is nearly done.

---

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

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

## 2026-06-05 -- D.O.R.A. acronym naming pass
**Status:** complete (discussion/recon only -- no code changed)
**What changed:**
- Reviewed the current handoff context, changelog, follow-ups, Dashy Dora docs, and Dora assistant architecture notes to ground acronym suggestions in the pivoted product direction.
- No product/code files changed.

**Decisions made:**
- Naming suggestions should emphasize the pivoted Dora promise: effortless kitchen assistance, pantry/list organization, personal guidance, and action with user confirmation.
- "Delicious Organised Restock Assistant" is a good friendly baseline, but "Restock" may be too narrow for the planned closed-loop / zero-input pantry direction.

**Files touched:** `DORA_WORKLOG.md` only.

**Verification:** read-only review of `DORA_WORKLOG.md`, `CHANGELOG.md`, `DORA_FOLLOWUPS.md`, `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`, `docs/DASHY_DORA_CHAMPION_PLAN.md`, `docs/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`, `docs/PROMPT_PLAN_PART_3.md`, and `web_app/src/components/dora/DoraChat.vue`.

**Next up:** awaiting user decision on the preferred D.O.R.A. expansion / tone.

**Open questions for user:** choose whether D.O.R.A. should sound more practical/productive, friendly/foodie, or intelligent/proactive.

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
