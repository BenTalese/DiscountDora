# Dashy Dora — Project State

**Last reviewed: 2026-08-23.** Milestone-progress front door — phase board,
workstreams, and what needs your attention. This is *not* a changelog;
shipped-work history lives in `CHANGELOG.md` + `DORA_WORKLOG.md`.

This is the single front door: where every phase and workstream is up
to, and what needs your attention. For *where things stand* this doc
wins; for *how/why* a decision was made, follow the linked planning
doc. Regenerated after each substantive close-gate (see
`CLAUDE.md → Regenerating PROJECT_STATE.md`); if it looks out of date,
the last session skipped its close-gate — trust `DORA_WORKLOG.md` +
`CHANGELOG.md` over it.

Status key: ✅ done-clean · ➗ done-with-carve-outs · 🟡 active/in-progress ·
🔵 designed-not-built · ⚪ not-started · 🔴 needs-a-decision · 🕸 stale ·
📦 superseded · 🗄 historical.

---

## Where we are right now

Phases **0** and **2** are effectively done (foundations; ingestion API +
standalone companion, both backend-green), **Phase 1** sits at ~95% with only
browser-verify and the meal-reconcile Chunk 6 tail left, and **Phase 3
(champion) is fully built** at ~95% — four surfaces (P8-07/08/09/10) still need
a real-device walk. The work has been a sustained **owner-feedback polish
stream** across stock overview, stock-item detail, cookbook and the recipe page:
the stock-signal consolidation is code-complete across all six chunks, the
redesigned recipe page won its comparison and its feature gaps are closed, and
the 2026-08-22 batch put the stock row's expiry menu, uncertainty ring and **six
new bulk endpoints** in (one request per bulk action instead of N). Both suites
are green as of 2026-08-23 — backend **1947 passed** / 1 skipped / 1 xfailed,
frontend **494 vitest passed**, `vue-tsc` clean. The dominant debt is no longer
building: it is that **a large, stacked body of shipped UI has never been seen
in a browser** — stock overview, stocktake, recipe, cookbook, inference
surfaces, offline sync and the whole champion sequence all sit in
`DORA_VERIFY.md` unwalked. **Phase 4 (open-source release) remains at ~0%** and
needs an owner call on scope and timing.

---

## Phase board

| Phase | Scope | Status | Remaining |
|---|---|---|---|
| **0 — Foundations** | Theme/buttons/modals/filters/text-size/renames + bug clusters + config/opt-ins | ✅ ~99% | Residual polish only. Live token debt: FU-674 (`--text-on-primary` fails D-002 in three themes), FU-709 (dark themes' `--surface-page` never paints). |
| **1 — Close the loop** | Shopping lists, cook mode, stock overview, cookbook, suggestions, costing, stocktake | ➗ ~95% | All P6 tail items resolved; **nothing left to build except meal-reconcile Chunk 6** (settings row/copy). Everything else is browser-verify: stock overview (three feedback batches, 2026-08-20/21/22), stocktake's three-phase runner, cookbook batch 3, the recipe page. |
| **2 — Ingestion API + companion** | `/api/ingest` seam; standalone companion; Merchant→Store rename | ✅ done (backend-green) | Phase-F tail only: product-surface browser-verify (FU-214), L197 hard-delete decision, L205/206 bulk-select unbuilt. |
| **3 — Champion** | Zero-Input Pantry, buy/wait oracles, barcode-add, Dora Score, culinary memory, native app | ➗ ~95% (verify pending) | P8-01..P8-10 fully built. Browser/device-verify of P8-07/08/09/10 remains; native FCM push parked until SaaS (FU-465). |
| **4 — Open-source release** (was Commercialize) | README/showcase + release process + support channel (Postgres done) | ⚪ ~0% | **Not sold — donation/OSS/MIT, all free.** FU-406 (README+release), FU-608 (donation/OSS infra), FU-557 (support channel). Ops/CI (FU-405) gates FU-520/FU-404. SaaS parked. |

---

## Major workstreams

| Workstream | Status | Where it's at | Governing doc |
|---|---|---|---|
| **Shopping lists (three-face redesign)** | ➗ | **All three faces built.** *Plan*: trip card + "Where you'll spend it" store card, four ordering modes with Unsorted fallback and auto-disable, thumb-friendly reorder arrows, slimmed toolbar. *Run* (2026-08-23): whole-row tap target, undo toast on tick, cleared sections collapsing to "all N picked", bottom-sheet price capture, rail moved to More, every curation affordance stripped. *Receipt* (2026-08-23): read-only itemised receipt + past-tense store split + "Didn't buy" tail, corrections behind an announced **Amend** that also rewrites the harvested price observation (FU-726 closed). Underneath it all, price comes from **what you last paid**, resolved server-side with its provenance (R-053/ADR-049), so totals work with no product data; offers are a separate *"Online offer:"* chip feeding no total. Promoted to **R-054/ADR-050**. Only a real-device walk is owed (FU-729) | worklog 2026-08-23 + `DORA_VERIFY` → Shopping list |
| Stock Overview | ➗ | Signal consolidation **code-complete, all six chunks**; the row went 9 visual channels → 4, attention is one server-owned rule (`stock_attention.py`) read by outline/count/chip/bell, and the list opens on what needs you. Three owner feedback batches since (2026-08-20/21/22): filter-panel auto-open, urgency-ordered Needs-attention sort, "Needs check" chip retired to Stocktake, and 2026-08-22's expiry-menu date header, uncertainty ring moved off the box edge, and **six bulk endpoints** replacing per-item request loops. **None of it walked in a browser** | [IMPL_PLAN](docs/04_proposals/IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md) + `PROPOSAL_STOCK_OVERVIEW` |
| Stocktake Mode | ✅ | Three-phase runner (Review Dora's confident set → Walk → Sweep what dropped out), queue ordered least-certain-first, install-wide on/off switch. Verify owed; FU-700 (switch not gated on dashboard/help copy) open | [PROPOSAL](docs/04_proposals/PROPOSAL_STOCKTAKE_MODE.md) |
| Stock-item detail | ➗ | 2026-08-21 batch: 10 of 12 items shipped (buy-verdict card unified with "Dora thinks", clickable expiry, Barcodes own tab, peek-panel verdict follows the item, named 404 errors). Two left as install-state findings — FU-648 (QR dialog, never reproduced, now instrumented) and FU-710 (barcode register 404). Phone-verify owed | `DORA_VERIFY` → Stock-item detail |
| Cookbook | ➗ | Chunks 1–10 plus three feedback batches. Batch 3 (2026-08-20) re-ordered the filter row to reported use, added `Serves ≥`, removed `Missing ≤`, ran a one-glyph-one-meaning icon pass, and deleted meal-slot names from the Category vocabulary (migration `c8b3e5f0a712`). Desktop branch + Quasar dropdowns unverified (agent pane pins `$q.screen` to `xs`). Open: FU-691 (off-token stylesheet), FU-692 (`ICONS.restaurant` overloaded), FU-693 (row names off D-003) | [PROPOSAL](docs/04_proposals/PROPOSAL_COOKBOOK.md) |
| Recipe page | 🟡 | The redesign (`RecipeDetailNext.vue`) **won the owner comparison**, its gaps are closed (substitutes chip, `time_of_day`, per-ingredient optional/notes, explicit Save + route guard — ADR-045/R-049), and the **2026-08-23 feedback batch (17 items)** reworked how it edits: two **block-level pencils** replacing every per-field popup (R-055/ADR-051), the "Organise ingredients" disclosure deleted into an ingredients edit mode whose ↑/↓ also move rows between sections, a shared unit dropdown, and three real bugs fixed — the masthead photo rendering at 0×0, free text unreachable when the pantry matched nothing, the title wrapping early. **Blocked on one owner call (FU-688)**: masthead vs shared `PageToolbar` — which this batch effectively answers in the masthead's favour — gating the swap pass (delete the 2,727-line old page) | [PROPOSAL](docs/04_proposals/PROPOSAL_COOKBOOK.md) |
| Products-as-overlay | ➗ | Phases 0–E code-complete; Phase-F tail is FU-214 browser-verify + L197 hard-delete decision + L205/206 bulk-select | [RUNBOOK](docs/04_proposals/PRODUCTS_OVERLAY_RUNBOOK.md) |
| Prices surface | 🔴 | Investigation done and it confirms the owner's own diagnosis: all price *reading* capability (compare 5, ranges, alerts) sits on the product axis at `/price-history`, which has **no nav entry**, while the everyday user's own data gets a single-item modal with no range and no compare. Placement settled (price lens on Stock overview + trend section in Reports; alerts advanced-only); the keep/cut call itself is **FU-703** and gates FU-708 | [ASSESSMENT](docs/05_investigations/PRICES_SURFACE_UX_ASSESSMENT.md) |
| ⭐ Zero-Input Pantry (P8-07) | 🟡 | Built end-to-end and extended (FU-653) to recipes, shopping lists and the meal planner, each behind its own off-by-default opt-in, purely additive. Server verified live; **all three client renders and the original P8-07 walk unseen** | [PROPOSAL](docs/04_proposals/PROPOSAL_ZERO_INPUT_PANTRY.md) + [INFERENCE_SURFACES](docs/04_proposals/PROPOSAL_INFERENCE_SURFACES.md) |
| Meal Plans | ➗ | Build-my-week auto-planner, cook batches, per-day calories, lighter-option swaps all shipped + verified. Evening brief (one 19:00 opt-in digest, silent when there's nothing to say) shipped; device-verify owed. Per-slot reminders + `MealSlot.starts_at` are **won't-do** | [PROPOSAL](docs/04_proposals/PROPOSAL_MEAL_PLANS.md) |
| Meal reconcile | ➗ | Chunks 1–5 shipped; **Chunk 6 (settings row/copy) is the last unbuilt Phase-1 item** | [IMPL_PLAN](docs/04_proposals/IMPL_PLAN_MEAL_RECONCILE.md) |
| Alerts control centre | ✅ | Nine alert kinds cut to six, severity is the only importance scale, email digest deleted whole (migration `e4b1c7a95d20`). Open: FU-702 (expiring-soon chip coupled to notifications), FU-701 (wording overlap with "Needs attention") | [PROPOSAL](docs/04_proposals/PROPOSAL_ALERTS.md) |
| Nutrition (complex mode) | ➗ | Built end to end: install-wide mode, USDA + OFF import, 15 micronutrients (migration `b6e04c9a2f18`), server-rendered panel table, recipe rollup, cookbook badge, per-day calories, auto-suggest matching screen. Open: FU-643 (no synonym layer), FU-645 (rows blank until re-import), FU-646 (rollup still sums four), FU-657 (OFF scale factors unverified) | [FU-635 (resolved)](DORA_FOLLOWUPS_RESOLVED.md) |
| Settings & config polish | 🟡 | Active owner-driven stream: nav regrouped, Admin split into five flat groups (nav sub-headers deleted app-wide, D-021), Users page rebuilt with direct password-set + deactivate-not-delete (`is_active`, migration `a7f3c9d15e82`), Region & locale rebuilt preview-first, stocktake install switch. Several DORA_VERIFY walks queued | `CHANGELOG [Unreleased]` |
| Assistant surface | ✅ | Per-user rate limits, SLM default path, multi-provider config (`UserLlmProvider`), chat-window feedback batch. Browser-verify owed; FU-663 (24px tap target) folds into FU-641 | `ask_assistant.py`, `AssistantSettings.vue` |
| Offline / resilience (F3) | ➗ | Found broken end-to-end 2026-08-17 (replay never attached the CSRF header, so every drain 403'd and was silently discarded while the UI said "Synced everything") and fixed, R-047/ADR-043. **Live round-trip verify owed** — a mocked transport cannot reproduce the failure. Open: FU-660/661/662 | `useOfflineQueue.ts` |
| Design remediation (DR) | 🟡 | DR-1/1b/2/3/4/5/6/7/8/9/10/11/14/15 done or done-with-carve-outs; **DR-12 (alerts order + calendars), DR-13 (history grouping), DR-16 (onboarding activation — owner call) remain**. Brand-secondary rethink spun out as FU-621/622 | [DESIGN_REMEDIATION_PLAN](docs/04_proposals/DESIGN_REMEDIATION_PLAN.md) · [FU-578](DORA_FOLLOWUPS.md) |
| Postgres datastore | ✅ | Implemented + default (SQLite fallback via `DORA_DB_PATH`); suite green on PG. CI wiring remains, blocked on FU-405 | `configuration_manager.py` |
| Test suite | ✅ | Green 2026-08-23: backend **1947 passed** / 1 skipped / 1 xfailed, frontend **494 passed**. Note for this machine: bare `pytest` throws ~56 spurious setup errors — pass `--basetemp=<real dir>`. Remnant: Postgres CI (FU-520, waits on FU-405) | [PROPOSAL](docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md) |
| Open-source release (P7) | ⚪ | Not sold — donation/OSS/all-free. README/showcase, release process, support channel (FU-406/557/608) | [PLAN §5](docs/01_charter/RECONCILED_FINISHING_PLAN.md) |
| Finalisation sweep | 🔵 | Designed, not started — 20 chunks, two-stage, single-maintainer north-star | [PLAN](docs/01_charter/FINALISATION_PLAN.md) + [COVERAGE](docs/01_charter/FINALISATION_COVERAGE.md) |

---

## ⚠️ Needs your attention now

**Total open backlog is 102 items in `DORA_FOLLOWUPS.md`** (counted 2026-08-23).
These are the ones wanting a decision or a running-app check, most important
first.

1. **🟡 One character in `deploy-dora.sh` (FU-717, cause found).** The deploy
   rsyncs with `--exclude='data'`, which matches the **basename at any depth** —
   so it deleted `dora_api/features/data/` (15 files) off the server every
   deploy, and all of `/api/data/*` 404'd. Change it to `--exclude='/data'` and
   redeploy. The script also holds your SSH password in plaintext at mode 0664;
   worth a key + rotation. Follow-ups: **FU-720** (nothing verifies the deployed
   route map — the app booted clean while serving 404s) and **FU-719**.
2. **🔴 Decide the fate of the product price axis (FU-703).** You named the cause
   yourself: products got demoted to a push-your-own-data niche while the stock
   item was upgraded to carry everyday price functionality, and the half-built
   surface got torn the other way. The investigation confirms it — all the price
   *reading* capability lives at `/price-history`, which has no nav entry, while
   *"which of my items got more expensive?"* has no surface at all. Placement is
   already settled (a price lens on Stock overview + a trend section in Reports,
   no new nav slot; alerts advanced-only). The keep/cut call is yours and **gates
   FU-708**. FU-704/705/706/707 (mobile form, chart touch, observation edit,
   signal tone) are independent and can start whenever.
3. **🔴 Say the word on the recipe masthead (FU-688).** You picked the redesigned
   page, its feature gaps are closed, and the 2026-08-23 feedback batch has now
   *reworked* that masthead to your notes — which reads as an answer in the
   masthead's favour, but it's still your call against the shared `PageToolbar`
   every other detail page uses. The **swap pass waits on it**, because it's a
   one-way door — route re-point, delete `RecipeDetailPage.vue` (2,727 lines),
   both hatch buttons, the duplicate form model. Then walk `DORA_VERIFY.md` →
   "⚠️ Recipe page (new layout)": the two new edit pencils, the ingredients edit
   mode and the free-text ingredient flow all need real pointer input (the
   preview pane wouldn't paint for the build session — FU-733).
4. **Walk the 2026-08-22 stock-overview batch — the bulk-bar network check is the
   one that matters.** Six new bulk endpoints replaced per-item request loops on
   log-waste (and Undo), add-to-list, add-to-chosen-list, mark-restocked,
   remove-from-list and move. Open devtools Network: **if any bulk action still
   fires N requests, a call site was missed.** Also here: the expiry menu now
   shows the item's date and deliberately stays open as you push days, and the
   uncertainty marker sits as a dashed ring just outside the level box. None of it
   was seen in a browser — port 5170 was held by another session's pre-change
   backend. `DORA_VERIFY.md` → "Stock overview: expiry menu, uncertainty ring,
   bulk endpoints (2026-08-22)".
5. **Walk the whole stock + stocktake surface — it's all built and none of it has
   been seen (FU-683).** Six chunks, nothing waiting on you, Chunks 3–6 never run
   in front of a human. The row went from nine visual channels to four; the
   highlighting and the "Needs attention" count are finally the same rule; nothing
   pulses or rings; the list opens on what needs you. The stocktake queue is
   least-certain-first, and the runner is three phases. Two things to *confirm*
   rather than check: an overdue shopping day now counts on the bell badge (a side
   effect of tier deriving from severity — a one-line reversal), and the Review
   phase **legitimately won't appear** until Dora has ~3 logged purchases for
   something.
6. **Confirm the "Needs attention" chip in a browser after a bulk action
   (FU-715).** You reported it broken, then said it seemed fine — logged rather
   than dropped. The static read found the chip now does a bare
   `needs_attention === true` with no client fallback, so it matches nothing if
   the server field is ever absent, plus two live gaps that would look
   intermittent: optimistic/offline-queued mutations don't recompute attention
   until a refetch, and the rule honours mutes but not snooze/dismiss, so **the
   chip and the bell disagree on a real install**.
7. **🔴 Two install-state bugs that only reproduce on your box.** FU-710 — the
   barcode register POSTs 404 on your install (same module as the QR 404, so
   likely one cause). FU-648 — the QR dialog failure has never reproduced in three
   attempts, but the error now names status + ref, so the next report closes it.
   Both need a phone or a non-localhost host.
8. **🔴 Pick a lever for `--text-on-primary` (FU-674).** Three themes (pesto 3.88,
   blueberry 4.21, midnight 2.86) fail D-002's 4.5:1 floor **app-wide**. Either
   darken those themes' ink (changes every primary button in three themes) or
   darken their `--brand-primary` (changes the brand colour). One decision, then
   mechanical.
9. **🔴 Dark themes never paint their authored page colour (FU-709).** Every dark
   theme declares a `--surface-page` that nothing renders. A colour decision, not
   a bug fix.
10. **🔴 Small decisions that clear the stock row (FU-685, FU-686).** The row's
   expiry button still colours off a hardcoded 7 days while its outline reads your
   configured window — a 14-day setting can outline a row whose expiry pill is
   still green (~5 lines either way once you pick). And `PantryBeliefChip.vue` is
   orphaned while three comments still call it the live row form.
11. **Walk the new inference surfaces (FU-653).** Recipes / shopping lists / meal
    planner, each toggled separately, all off by default. Server side verified;
    the three client renders have never been seen, and the seed carries two
    "Belief demo:" recipes that make it a 30-second check.
12. **Round-trip the offline sync in a browser.** It queued changes and lost every
    one of them while reporting success. Fixed and Vitest-pinned, but the failure
    mode is exactly what a mocked transport can't reproduce — go offline, change
    something, come back, **and reload to confirm the server kept it**.
13. **Walk the nutrition surfaces against a real USDA import.** Auto-suggest was
    agent-verified on a 20-food scratch catalogue; what's unknown is **match
    quality on your own pantry at ~7,800 rows** and whether the matching page
    loads at that size. That walk is what should decide **FU-643** (the missing
    AU/US synonym layer). The recipe nutrition card hasn't been seen with real
    data either.
14. **Products-overlay Phase-F verify + hard-delete call (FU-214).** Product
    surfaces need a running-app walk with real data; L197 hard-delete is undecided
    and L205/206 bulk-select is unbuilt — the runbook's Phase-F blocker.
15. **⭐ Verify the champion sequence (P8-07/08/09/10).** Four surfaces stacked and
    untested — Zero-Input Pantry, Kitchen health, Memory reports, plus the native
    Android APK build + device walk. Pairs naturally with FU-389 (mobile/PWA field
    test) and the queued Settings-rework verify sections.
16. **Phase-4 release readiness needs your steer on scope and timing.** FU-406
    (README/showcase + GitHub Releases process), FU-608 (make the repo public,
    stand up Sponsors / BMC / PayPal, then one placeholder-swap pass), FU-557
    (support channel — a one-line config change lights up Help / error-report /
    DoraBot once picked). FU-405 (ops/CI/observability — and CI must **not** be
    silently re-enabled) gates FU-520 and FU-404.

**Also owner-judgement, lower urgency:** FU-678 + FU-675 (every `.dora-btn` is
36px against D-004's 44px floor, and ~64 `q-select`s still lack the shared
wrapper — one pass on a real phone), FU-621/622 (brand-secondary rethink + the
visual options board), FU-010 / FU-224 (holistic theme + colour-usage review,
needs eyes on the running app), FU-713/714 (the bulk work's honest leftovers —
commits-per-item, and `addItems` still loops at ~16 other call sites), remaining
DR units DR-12/13/16.

**Trigger-gated, not urgent:** FU-520 (Postgres CI — waits on FU-405), FU-404
(compliance — only when hosting user data), FU-576 (uploads spec — needs a
bundled-Chromium run), FU-579 (quasar-dev checker overlay), FU-575 (name
uniqueness — opportunistic), FU-358 (Aldi scraper — when Aldi data is next
needed).

> **Cleared at the previous reviews:** every item that earlier revisions of this
> section listed is now in `DORA_FOLLOWUPS_RESOLVED.md` — the red frontend suite
> (FU-666/FU-634) and the order-dependent seed-pollution blocker (FU-676), FU-595
> (planner freeze), the whole security thread (FU-447/515/197), FU-620
> (email-change removal), FU-612/609/346/353/606/085/429/025/549/464/355/383, and
> the P6 loop tail FU-450/451/452. Do not reintroduce them as live.

---

## Where the detail lives

- **`DORA_WORKLOG.md`** — per-session handoff narrative (what ran, decisions, what's next).
- **`CHANGELOG.md`** — product/code changes that shipped.
- **`DORA_FOLLOWUPS.md`** — the full 18-item open backlog (this dashboard shows only the top).
- **`DORA_VERIFY.md`** — your browser-verify checklist (walk + delete as you confirm).
- **The full per-doc register is below** — every planning doc's verified state.
- **Charter / how & why:** `docs/01_charter/` (vision, standards, master plan).
- **To refresh this doc:** see the regeneration routine in `CLAUDE.md`.

**Do not trust as current** (kept for history only): the old `STATUS.md`
(retired to `06_legacy_prompt_plans/`), `99_scratch/PROGRESS_REPORT_2026-06-12.md`
and `FEEDBACK_AUDIT_2026-06-12.md` (June snapshots — say Phase 2/3 = 0%, both wrong
now), `docs/00_DOC_GRAPH.md` (stale stub, FU-428), and `00_original_spec/` (historical,
pre-dates the current codebase).

---

# Document register

Complete per-doc state map — every active planning doc opened, classified, and
cross-checked against `DORA_WORKLOG.md` + `CHANGELOG.md` + code reality (verified
2026-08-12 via a 5-agent fan-out). This is the "everything accounted for" backing
for the dashboard above; the dashboard is the rollup, this is the per-doc truth.
**You don't need to read this** — it's the audit trail. **127 active docs** across 8
folders; the 157 `docs/00_original_spec/` files are charter-designated historical
(one bucket, see end).

State key: ✅ done-clean · ➗ done-with-carve-outs · 🟡 active · 🔵 designed-not-built ·
⚪ not-started · 🕸 stale · 📦 superseded (successor named) · 🗄 historical.
Investigations: ✅ closed-actioned · 🟡 open · 🔵 informational · 🕸 stale.

## Systemic findings (from the 2026-08-12 re-audit)

17. **✅ Security thread closed.** `AUTH_ASSISTANT_SECURITY_FINDINGS` is now a triaged standing register — the HIGH CSRF + MEDIUM email-change were fixed under FU-197 (2026-06-30); the 8 residual Medium/Low findings went to FU-515 (resolved); the orphan audit-follow-up FU-447 was reconciled + closed. A.5/A.6/A.7 are accepted risks (A.6 → Phase-4). Nothing open.
18. **🕸 Stale "no code yet" / "designed-not-built" headers on ~15 shipped docs (FU-445).** Bodies are accurate records; only the top status line lies (e.g. IMPL_PLAN_ALERTS, IMPL_PLAN_MEAL_RECONCILE). Judge by this register, not the header.
19. **🕸 `docs/00_DOC_GRAPH.md` is a retired stub (FU-428).** Superseded by this doc + the CLAUDE.md anti-drift rule.
20. **Backlog right-sized.** The old dashboard cited "~60 open items"; the ledger actually holds **17**. Most of the prior attention list had long since moved to `_RESOLVED`.

## 01_charter — governance (6)

| Doc | Type | State | Purpose | Evidence |
|---|---|---|---|---|
| DASHY_DORA_CHAMPION_PLAN.md | Charter / vision | 🟢 authoritative | Part 8 vision + 12-principle Decision Charter + operating procedure | Governing rubric cited across CLAUDE.md |
| RECONCILED_FINISHING_PLAN.md | Master plan | 🟢 authoritative | Phases 0–4, resolved decisions §7, scope arbiter | "Active — all decisions resolved"; owns order/scope |
| ENGINEERING_STANDARDS.md | Rules / ADR log | 🟢 authoritative | R-001..R-040 code rubric + ADR log, checked every task | Living; R-039/040 + ADR-035/036 (dialog noCaps + dialog-gated mutations) added 2026-08-12 |
| DESIGN_STYLE_GUIDE.md | Design spec | 🟢 authoritative | Prescriptive D-rules token/component spec, enforced via R-035 | Authoritative since 2026-07-18; D-020 (indicator tokens) + **D-021 (nav is one flat level)** added 2026-08-16/17 |
| FINALISATION_PLAN.md | Late-game plan | 🔵 designed-not-built | Two-stage code-walk sweep (FST/Help/Review/Tests) | Self-labelled "designed, not started"; verify campaign has since covered similar ground ad hoc |
| FINALISATION_COVERAGE.md | Coverage register | 🔵 designed-not-built | Per-chunk × per-track status matrix for the sweep | All 20 chunk rows ⬜ |

## 02_feedback — inputs (3)

| Doc | State | Purpose | Evidence |
|---|---|---|---|
| Feedback _ Fixes - as of [06-Jun-2026].md | 🟢 authoritative | Raw user feedback — source of truth for coverage tables | Named SoT in CLAUDE.md |
| COVERAGE_GAPS.md | 🟡 active-living | Tracker: feedback bullets lacking a brief/proposal home | Living; entries flip gap→covered as briefs land |
| FEEDBACK_TRIAGE_AND_PLAN.md | 📦 superseded (RECONCILED_FINISHING_PLAN) | Feedback→work map | Superseded for sequencing/strategy; retains what/why map |

## docs/ root — navigation & guides (2)

| Doc | State | Purpose | Notes |
|---|---|---|---|
| 00_DOC_GRAPH.md | 📦 superseded → stub | Former per-prompt required-reading map | Retired (FU-428); CLAUDE.md calls it a legacy stub |
| INGESTION_GUIDE.md | ✅ done-clean | Power-user guide: sourcing data via `POST /api/ingest` | Matches shipped ingestion API (C-10.5) |

## 03_prompts — executable prompts (19)

The whole pack is a historical execution map — live state lives here in
PROJECT_STATE.md. Index banner (verified 2026-07-02): all Wave-A + Wave-B
prompts shipped; every Wave-C brief produced its proposal (most now built via
IMPL_PLAN_*); INV prompts produced their reports.

| Doc | State | Evidence |
|---|---|---|
| 00_INDEX.md | 🗄 historical (banner added) | "Status column is stale… read as historical execution map" |
| A1 / A1b / A2 / A3 / A4 / A5 / A6 / A7 / A8 | 🗄 historical | Wave-A foundation sweeps (tokens, button/modal/filter, skeletons, text-scale, footer, renames) — all shipped |
| B1 / B3 / B4 / B5 / B7 / B8 / B9 | 🗄 historical | Wave-B bug clusters — all shipped (B2/B6 folded); B9 item 4 (command palette) cancelled |
| C_big_rock_design_briefs.md | 🗄 historical | Big-rock briefs → proposals → IMPL_PLANs; C-6/C-8 companion-scope |
| INV_investigations.md | 🗄 historical | INV-1..10 → reports; INV-9 (palette) superseded |

## 04_proposals — designs, impl-plans, runbook (64)

**IMPL plans & runbook (A–M):**

| Doc | Type | State | Purpose | Evidence |
|---|---|---|---|---|
| DESIGN_REMEDIATION_PLAN | Design backlog | 🟡 active | Action the 2026-07-18 UX/design audit (DR-1…16) | DR-1/1b/2/3/4/5/6/8/10/11 done (10=owner leave-as-is), DR-7 ➗ (FU-624), DR-9 ➗ (FU-631), DR-14 ➗ (FU-632), DR-15 ➗ (FU-694); remaining: DR-12/13/16 |
| DORA_ASSISTANT_ARCHITECTURE_PROPOSAL | Proposal | ➗ carve-outs | Unify assistant capability model + LLM config | §2.2 registry deliberately not built; §7 multi-provider shipped |
| IMPL_PLAN_ALERTS | Impl plan | ✅ done | Alerts control-centre (C-9) | Digest+push+prefs shipped; header stale |
| IMPL_PLAN_AUTH_SHELL | Impl plan | ✅ done | Extract shared AuthShell + AuthButton (C-19) | `AuthShell.vue`/`AuthButton.vue` exist |
| IMPL_PLAN_CART_BUTTON | Impl plan | ✅ done | Unify add-to-list into one cart control (C-7) | `AddToListButton` in use |
| IMPL_PLAN_CONFIG_AND_OPTINS | Impl plan | ✅ done | Feature-flag/opt-in spine (C-cross) | `useFeatureFlags`/health flags shipped |
| IMPL_PLAN_COOKBOOK | Impl plan | ✅ done | Recipe domain rebuild (C-4) | Structured steps/tags shipped |
| IMPL_PLAN_COOK_MODE | Impl plan | ✅ done | Cook-mode rebuild (C-3) | `RecipeCookMode.vue` live |
| IMPL_PLAN_DASHBOARD_REBUILD | Rebuild brief | ✅ done | Rebuild DashboardPage around savings | `DashboardPage.vue` rebuilt |
| IMPL_PLAN_ENV_TO_APPSETTING | Impl plan | ✅ done | Promote 12 env vars to AppSetting (FU-333B) | Header "SHIPPED 2026-07-05/06" |
| IMPL_PLAN_ERROR_HANDLING | Impl plan | ➗ carve-outs | App-wide error-message polish (FU-099) | `apiErrorHandler.ts` live; full 166-catch sweep unconfirmed |
| IMPL_PLAN_HELP_CHIPS | Impl plan | ✅ done | Add (?) hover-help chips (FU-044) | `help_outline` tooltip pattern across pages |
| IMPL_PLAN_INGESTION_API | Impl plan | ➗ carve-outs | Ingestion `/api/ingest` + Your-Prices (C-10) | Built; browser-verify pending |
| IMPL_PLAN_MEAL_PLANS | Impl plan | ✅ done | Build meal-plans surface (C-2) | Rebuild doc: all F1–F49 shipped |
| IMPL_PLAN_MEAL_PLANS_REBUILD | Critique+rebuild | ✅ done | Re-critique + rebuild the C-2 result | `useMealPlanner.ts` + components exist |
| IMPL_PLAN_MEAL_RECONCILE | Impl plan | 🟡 in-progress | Manual meal-plan reconcile (FU-317) | Chunks 1–5 shipped; Chunk 6 pending; header stale |
| IMPL_PLAN_ONBOARDING | Impl plan | ✅ done | Onboarding redesign + de-persona (C-5/FU-210) | Onboarding pages live |
| IMPL_PLAN_PRODUCTS_AS_OVERLAY | Impl plan | ➗ carve-outs | Chunk detail for products overlay | Phases 0–E done; Phase-F tail open |
| IMPL_PLAN_RECIPE_IMPORTER | Impl plan | ✅ done | Paste-based recipe importer (FU-104/199/396) | Importer machinery present |
| IMPL_PLAN_SETTINGS_REBUILD | Rebuild brief | ✅ done | Rebuild settings shell + sections | "COMPLETE (Phases 1–5 landed)"; reworked since |
| IMPL_PLAN_SHOPPING_LISTS | Impl plan | ✅ done | Shopping-list status-model rebuild (P6-01) | Cited "landed" across surfaces |
| IMPL_PLAN_SHOPPING_LIST_RECEIPTS | Impl plan | ✅ done | Attach receipt photos (FU-334) | "Built 2026-06-30" |
| IMPL_PLAN_STATE_OWNERSHIP | Impl plan | ✅ done | Server-owned derived facts refactor | cookable/missing/allocation SSOT landed |
| IMPL_PLAN_STOCK_ITEM_DETAIL | Impl plan | ✅ done | Stock-item detail polish (C-1b) | Detail page live |
| IMPL_PLAN_STOCK_OVERVIEW | Impl plan | ✅ done | Stock overview redesign (C-1) | `StockOverview.vue`/`StockItemRow.vue` |
| IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION | Impl plan | 🟡 active | Collapse the stock row's 9 competing signals → 4; one attention rule, one cadence engine | Written 2026-08-19; **Chunks 1–4 landed** — C1: one cadence engine, D-11 belief→verdict, bulk verdicts endpoint, + the FU-684 bug that made the verdict inert; C2: verdict off the row (D-10), `buy_verdict_enabled` AppSetting→User (D-12/B7, migration `d9f4b2c7e803`), shopping list on the bulk endpoint (B6), all three walked live; C3: Step-0 cuts (3 alert kinds + the digest lane, migration `e4b1c7a95d20`) and one server-owned attention rule; C4: sort + row treatments, 9 channels → 4. **Chunks 5–6 open** (queue ranking, runner rebuild), neither blocked; FU-683 |
| IMPL_PLAN_WASTE_MINIMISATION | Impl plan | ✅ done | Waste-minimisation cluster (C-waste) | `wasteApiService.ts` + mark-as-wasted |
| IMPL_PLAN_YOUR_PRICES | Impl plan | ➗ done-with-carve-outs | "Your prices" intelligence (Phase F) | All 8 chunks landed (FU-227/425) — but the **reading** side never grew a stock-item twin: PRICES_SURFACE_UX_ASSESSMENT (2026-08-21) found compare/range/alerts still product-only; FU-703 |
| OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT | Option doc | 🔵 deferred | Parked multi-tenant SaaS / managed-host option | Deferred 2026-07-14; kept parked post-pivot |
| PLAY_STORE_LISTING | Listing draft | 🔵 designed | Play Store copy + screenshot plan | "Draft copy; no submission yet" |
| PRODUCTS_OVERLAY_RUNBOOK | Runbook/status | 🟡 active | Drive products-overlay end-to-end | Phases 0–E done, Phase F in progress |

**Proposals (N–Z):**

| Doc | Type | State | Purpose | Evidence |
|---|---|---|---|---|
| PROPOSAL_ALERTS | Proposal (C-9) | ✅ done | Design the alerts control-centre | Realized by IMPL_PLAN_ALERTS |
| PROPOSAL_AUTH_SHELL | Design brief (C-19) | ➗ carve-outs | Shared AuthShell for pre-auth pages | Built; header "no code" stale |
| PROPOSAL_BARCODE_SCANNING | Proposal (P6-02) | ➗ carve-outs | Fix scan data model, gate off-by-default | Implemented; §5.2 ingestion auto-populate deferred |
| PROPOSAL_BUDGET_AWARE_LISTS | Proposal (P2-05 tail) | 🔵 designed | Budget-aware auto shopping-list optimizer | Header "Draft"; no budget logic in `auto_generate.py` |
| PROPOSAL_BUDGET_DEFENSE_SWAPS | Design brief (FU-451/450) | ➗ carve-outs | Over-budget swaps + deal-quality signal | `swap_suggestions.py`/`deal_quality.py` shipped; good_deal alert + product swaps CUT |
| PROPOSAL_BUY_VERDICT_ORACLE | Proposal (P8-05) | ✅ done | In-aisle "should I buy this?" verdict | Leaned on as shipped by adjacent docs |
| PROPOSAL_CART_BUTTON | Proposal (C-7) | ✅ done | Unify all add-to-list controls | `IMPL_PLAN_CART_BUTTON.md` |
| PROPOSAL_CONFIG_AND_OPTINS | Design brief (C-cross) | ➗ carve-outs | Cross-cutting config/opt-in editors | Chunks shipped; chunk 6 verify-only |
| PROPOSAL_COOKBOOK | Proposal (C-4) | ✅ done | Recipe/cookbook domain redesign | `IMPL_PLAN_COOKBOOK.md`; comparison cut per INV-6 |
| PROPOSAL_COOKBOOK_CARD_REVISION | Proposal (FU-088) | ✅ done | Recipe card redesign + optional ingredients | "BUILT — A+B+C shipped" |
| PROPOSAL_COOK_MODE | Proposal (C-3) | ✅ done | Cook mode / finish-loop redesign | `IMPL_PLAN_COOK_MODE.md` |
| PROPOSAL_HELP_OVERLAY | Design brief (C-help) | 📦 superseded (IMPL_PLAN_HELP_CHIPS) | Opt-in contextual help overlay | Superseded 2026-07-06 → help chips |
| PROPOSAL_INGESTION_API | Proposal (C-10) | ➗ carve-outs | Inbound ingest endpoint + "your prices" | Built; register-against-product deferred Phase 2 |
| PROPOSAL_LOCALE_I18N | Design brief (C-locale) | ➗ carve-outs | De-AU currency/format neutrality | Region/currency shipped; full translation out-of-scope |
| PROPOSAL_MEAL_PLANS | Proposal (C-2) | ✅ done | Meal-plan surface redesign | `IMPL_PLAN_MEAL_PLANS(_REBUILD).md` |
| PROPOSAL_MEAL_PLANS_PART_2 | Proposal (FU-617) | ✅ built | Cook batches (one cook, several days) | CHANGELOG "cook batches" 2026-08-11 |
| PROPOSAL_MEAL_RECONCILE | Proposal | ✅ done | Manual meal-plan reconcile | `MealReconcilePage.vue`; header stale |
| PROPOSAL_ONBOARDING | Proposal (C-5) | ✅ done | First-run on-ramp redesign | `IMPL_PLAN_ONBOARDING.md`; personas cut |
| PROPOSAL_PRODUCTS_AS_OVERLAY | Proposal | 🟡 active | Products as data-presence-gated overlay | Runbook-tracked; Phase-F tail |
| PROPOSAL_RECIPE_IMAGE_STEPS | Proposal (C-4 add-on) | ✅ done | Photo-based recipe steps mode | "BUILT 2026-06-25" |
| PROPOSAL_SHOPPING_LIST_UX_V2 | Proposal | ➗ superseded in part | Single-page shopping experience | "BUILT 2026-06-12"; the rail + status enum survive, but its toolbar, header cluster and row anatomy are replaced by the 2026-08-23 three-face redesign (worklog) |
| PROPOSAL_SIMPLE_MODE | Proposal | 📦 superseded (PRODUCTS_AS_OVERLAY) | Minimal-user workflow / pricing substrate | Spine superseded; substrate shipped |
| PROPOSAL_STOCKTAKE_MODE | Proposal (FU-430) | ✅ done | Walk-the-pantry stocktake redesign | Decisions locked + shipped end-to-end |
| PROPOSAL_STOCK_ITEM_DETAIL | Proposal (C-1b) | ✅ done | Stock-item detail polish/timeline | `IMPL_PLAN_STOCK_ITEM_DETAIL.md` |
| PROPOSAL_STOCK_OVERVIEW | Proposal (C-1) | ✅ done | Stock overview redesign | Reconciled against shipped reality |
| PROPOSAL_SUPPORT_CHANNEL | Action plan | ➗ built (dormant) | In-app support/feedback channel | Built off-by-default (FU-370); admin-editor half won't-build; stand-up = FU-557 |
| PROPOSAL_TEST_SUITE_IMPROVEMENTS | Engineering proposal | ➗ carve-outs | Test coverage/quality/cleanup | Built across ~8 sessions; Postgres CI carve-out open (FU-405) |
| PROPOSAL_USAGE_TELEMETRY | Proposal | 📦 superseded (OPTIONAL_SAAS) | Privacy-first usage analytics | Parked hosted-only; self-host won't-do |
| PROPOSAL_WASTE_MINIMISATION | Proposal (C-waste) | ✅ done | Dissolve waste page, keep signal | `IMPL_PLAN_WASTE_MINIMISATION.md` |
| PROPOSAL_ZERO_INPUT_PANTRY | Proposal (P8-07) | ✅ built (verify pending) | Inferred inventory / confidence beliefs | "Built 2026-07-03 server+SPA" |
| SELF_HOST_COMMERCIALIZATION_PLAN | Plan | 📦 superseded | Sequence to sell self-hosted Dora | Reversed 2026-07-31 → donation/OSS (FU-562/567 won't-do) |
| SHOPPING_LIST_REDESIGN_PROPOSAL | Proposal (v1) | 📦 superseded (SHOPPING_LIST_UX_V2) | Shopping-list lifecycle redesign | Structural work shipped as P6-01 |
| STATE_OWNERSHIP_REFACTOR_PROPOSAL | Proposal | ➗ carve-outs | Server-vs-client state ownership refactor | `IMPL_PLAN_STATE_OWNERSHIP.md`; §8 addendum binding |

## 05_investigations — reports (21)

| Doc | Type | State | Purpose/Notes | Evidence |
|---|---|---|---|---|
| DATA_MODEL_SANITY_SWEEP_FU393 | Schema sweep | ✅ closed-actioned | Whole-schema sanity; remediation spawned FU-563/564/565 | Fully remediated 2026-07-15; schema-match test enforces (R-034) |
| PERF_SCALE_SWEEP_FU388 | Perf sweep | ✅ closed-clean | Query-scale at 500/2000 items — no N+1s | "DB/query-scale pass done (clean)" |
| AUTH_ASSISTANT_SECURITY_FINDINGS | Security audit | ➗ closed-with-carve-outs | Auth+assistant register; re-audited 2026-07-13 | HIGH/MED fixed (FU-197/442/515); A.5/A.6/A.7 accepted |
| EMAIL_SETUP_FINDINGS (INV-4) | INV memo | ✅ closed-actioned | Password-reset flow + admin email-setup | Shipped via R-030/FU-413 |
| LOGGING_AND_DATA_LAYOUT (INV-3) | INV memo | ✅ closed-actioned | Time-based rotation + data/cache split | `logging_setup.py` uses TimedRotatingFileHandler (FU-027) |
| ESSENTIAL_FLAG_FINDINGS (INV-10) | INV memo | ✅ closed-actioned | `is_flagged`→`is_essential` wire-up + rename | CHANGELOG 2026-08-08 (migration `f4a2c7e9b1d3`) |
| RECIPE_COMPARISON_ASSESSMENT (INV-6) | INV memo | ✅ closed-actioned | Compare tool — verdict CUT | Comparison UI gone from RecipesOverview; §4 cut |
| COMMAND_PALETTE_ASSESSMENT (INV-9) | INV memo | ✅ closed-actioned | Ctrl-K palette — SHRINK→CUT | Palette/registry/recents removed (FU-029) |
| CROWD_PRICES_ASSESSMENT (INV-11) | INV memo | ✅ closed-actioned | P8-04 crowd price graph — verdict CUT | RECONCILED §7 Decision 6; unblocked FU-438 |
| PRICES_SURFACE_UX_ASSESSMENT | INV memo | 🔴 needs-a-decision | "My prices" + price-history UX; the product/stock axis split | 2026-08-21; D2/D3/D4 answered, D1 open as FU-703; defects FU-704..708 |
| MAGIC_BEHAVIOUR_AUDIT (FU-092) | Audit | ✅ closed-actioned | All implicit "magic" behaviours; spun FU-315..319 | "Complete; verdicts gathered 2026-06-28" |
| ORPHANED_FIELDS_AUDIT (INV-1) | Audit | ➗ closed-with-carve-outs | Fields set-but-unread; delta-checked FU-416 | Feeds DATA_MODEL_SANITY_SWEEP |
| STOCK_OVERVIEW_PERF (INV-2) | INV memo | ➗ closed-with-carve-outs | Mount cost + latent page-1-only fetch bug (logged FU) | Broader scale cleared by FU-388 |
| PLATFORM_BUILDS_AUDIT (FU-327) | Report | ➗ closed-with-carve-outs | Delivery-target audit; real blocker = dead CI | Report-only; gaps spun as FUs; FU-327 scoped-open |
| UX_DESIGN_CRITIQUE_2026-07-18 | Design critique | ➗ closed-with-carve-outs | Synthesis of FU-578 UX passes; system-vs-screens gap | Feeds DESIGN_STYLE_GUIDE + DESIGN_REMEDIATION_PLAN |
| FEATURE_CLARIFICATIONS (INV-5) | INV memo | 🔵 informational | QR vs register-barcode, product-search, expiry↔open | Partly superseded by barcode-on-Product (FU-373) |
| HISTORY_TAB_ASSESSMENT (INV-7) | INV memo | 🟡 open | Stock-item History tab weak → REWORK | No matching CHANGELOG entry found |
| SUBSTITUTE_SWAP_ASSESSMENT (INV-8) | INV memo | 🟡 open | List-level substitute swap → REWORK (move to Shop Mode) | Swap still lives in list ⋮ menu |
| FU_512_UNIT_OF_WORK_SWEEP_RUNBOOK | Runbook | 🟡 open (analysis-only) | Mechanical UoW refactor guide (10 handlers) | "Analysis-only, no code changes yet" |
| Distribution Spec - Desktop & Mobile Client | Spec/plan | 🔵 designed (partial) | Desktop (PyInstaller) + mobile packaging plan | Desktop/gunicorn shipped (FU-397); mobile Capacitor scaffolded |
| MULTI_USER_READINESS | Pre-flight checklist | 🔵 informational | Single-tenant assumptions to dismantle before multi-user | "Draft for discussion"; Phase-4; ties FU-045 |
| COMMERCIALIZATION_REPORT | Strategy report | 🗄 historical / 📦 partly superseded | Monetization analysis; selling reversed 2026-07-31 | Productionization findings (§3–4) shipped; monetization thread historical |

## 06_legacy_prompt_plans — historical (9)

All 🗄 historical — the original pre-charter plan library, retired 2026-06-12;
superseded by `docs/03_prompts/` (active prompts) and, for state, `CHANGELOG.md`
+ `DORA_WORKLOG.md`. Files: `PROMPT_PLAN.md`, `PROMPT_PLAN_PART_2..4.md`,
`PROMPT_PLAN_PART_5_OPTIONAL.md`, `PROMPT_PLAN_PART_6_POLISH.md`,
`PROMPT_PLAN_PART_7_COMMERCIALIZATION.md`, `STATUS.md` (🕸 stale, last regen
2026-05-27, self-labelled non-authoritative), and
`PRICING_SYSTEM_REASSESSMENT_HANDOFF.md` (✅ fully executed via
IMPL_PLAN_YOUR_PRICES — FU-227, delta-checked FU-425).

## 99_scratch — raw notes (4)

| Doc | State | Recommendation |
|---|---|---|
| MINIMAL_USER_PRODUCTS_OFF_FRICTION | 🗒 untriaged | Fuss-free (products-off) talk-time audit; promote or keep (FU-181) |
| SENIOR_REVIEW_2026-06-16 | 🗄 historical | "Is it sellable?" static review; findings already spun to FUs; LOC metrics dated |
| PROGRESS_REPORT_2026-06-12 | 🕸 stale / 🗄 historical | Point-in-time snapshot; superseded by this doc — safe to delete |
| FEEDBACK_AUDIT_2026-06-12 | 🕸 stale / 🗄 historical | 309-bullet snapshot, stale as of 2026-07-01; evidence pointers only |

## docs/00_original_spec — historical bucket (157 files)

The author's first spec (Feature Boards + ~125 "I can …" notes + original plan).
Charter-designated **historical / non-authoritative** — pre-dates the current
codebase; overridden by charter/plan/feedback. Mined opportunistically when writing
a brief. Treat the whole folder as 🗄 historical; not verified per-file.
