# Dashy Dora — Project State

**Last reviewed: 2026-08-19 (stock-signal consolidation design session).** Milestone-progress front door — phase board, workstreams, and what needs your attention. This is *not* a changelog; shipped-work history lives in `CHANGELOG.md` + `DORA_WORKLOG.md`.

This is the single front door: where every phase and workstream is up
to, and what needs your attention. For *where things stand* this doc
wins; for *how/why* a decision was made, follow the linked planning
doc. Regenerated after each substantive close-gate (see
`CLAUDE.md → Regenerating PROJECT_STATE.md`); if it looks out of date,
the last session skipped its close-gate — trust `DORA_WORKLOG.md` +
`CHANGELOG.md` over it.

Status key: ✅ done · ➗ done, with skipped/deferred items · 🟡 in progress ·
🔵 designed, not built · ⚪ not started · 🔴 needs your decision · 🕸 stale doc.

---

## Where we are right now

Phases **0** and **2** are effectively done (foundations; ingestion API +
standalone companion, both backend-green). **Phase 1** is now in good shape —
the stocktake-mode redesign shipped end-to-end and the P6 loop tail closed out
(FU-450 deal-quality, FU-451 budget-defense swaps, FU-452 put-away all
**resolved**), and the planner-freeze blocker **FU-595 is fixed**. **Phase 3
(champion) sits at ~95%, fully built** — nothing champion is left to construct;
four surfaces (P8-07 Zero-Input Pantry, P8-08 Kitchen health, P8-09 Memory
reports, P8-10 native Android APK) still need a real-device / browser walk.
Recent work has been a steady **Settings/UX polish stream** (household budget,
AI master-switch removal, Region & locale merge, Account/Kitchen-setup
redesigns, cook-batches meal planner, Build-my-week auto-planner) plus test-infra
hardening. The whole security thread (CSRF + email-change + the residual
assistant findings) is **closed** — FU-447/515/197/620 all resolved.
Both test suites are **green** as of 2026-08-19 (backend 1858/0, frontend 469/469) — the long-standing `stockLevelDot` red pair and a same-day handoff blocker were both cleared. The polish stream has since moved onto **cookbook UX**, now on its second feedback batch.
**Next up:** either a **browser-verify sweep** of the four unverified
champion/native surfaces, or **Phase 4 open-source release readiness**
(README/showcase + release process + donation/support stand-up —
FU-406/608/557); the largest live design backlog is triaging the **FU-578
UX/UI review** into fix units.

---

## Phase board

| Phase | Scope | Status | Remaining |
|---|---|---|---|
| **0 — Foundations** | Theme/buttons/modals/filters/text-size/renames + bug clusters + config/opt-ins | ✅ ~99% | Residual polish only; FU-025/346/609 etc. now closed. |
| **1 — Close the loop** | Shopping lists, cook mode, stock overview, cookbook, suggestions, costing, stocktake | ➗ ~95% | Stocktake redesign shipped; **P6 tail FU-450/451/452 all resolved**; **FU-595 planner-freeze fixed**. Residual browser-verify only. Meal-reconcile Chunk 6 (settings row/copy) pending. Cookbook UX is on its second feedback batch (2026-08-19) — filter row now runs off shared `BaseFilterField`/`FilterRow`; verify pending. |
| **2 — Ingestion API + companion** | `/api/ingest` seam; standalone companion; Merchant→Store rename | ✅ done (backend-green) | Product-surface browser-verify pending (FU-214). |
| **3 — Champion** | Zero-Input Pantry, buy/wait oracles, barcode-add, Dora Score, culinary memory, native app | ➗ ~95% (verify pending) | Sequence P8-01..P8-10 **fully built**. Only browser/device-verify of P8-07/08/09/10 remains; native FCM push deferred (FU-465). |
| **4 — Open-source release** (was Commercialize) | README/showcase + release process + support channel (Postgres done) | ⚪ ~0% | **Not sold — donation/OSS/MIT, all free** (billing/tenancy won't-do). Remaining: FU-406 (README+release), FU-608 (donation/OSS infra), FU-557 (support channel). SaaS/hosted parked (OPTIONAL_SAAS). |

---

## Major workstreams

| Workstream | Status | Where it's at | Governing doc |
|---|---|---|---|
| Products-as-overlay | ➗ | Phases 0–E code-complete; Phase-F tail (FU-214 browser-verify + L197 hard-delete decision + L205/206 bulk-select) pending | [RUNBOOK](docs/04_proposals/PRODUCTS_OVERLAY_RUNBOOK.md) |
| Ingestion API | ✅ | Backend green, bearer-auth lane, admin keys page | [PROPOSAL](docs/04_proposals/PROPOSAL_INGESTION_API.md) |
| Standalone companion | ✅ | Runs standalone (`../dora-companion`); round-trip tests pass | RUNBOOK Phase C |
| Merchant→Store rename | ✅ | `usual_store_id` + Stores page shipped | RUNBOOK Phase E |
| Shopping Lists | ✅ | 8/8 bullets; DRAFT→SHOPPING→DONE loop | [PROPOSAL](docs/04_proposals/SHOPPING_LIST_REDESIGN_PROPOSAL.md) |
| Cook Mode | ✅ | Chunks 1–6 shipped | `C_big_rock_design_briefs.md` |
| Cookbook | ➗ | Chunks 1–10 shipped; recipe-detail residuals; complex-mode nutrition on the card + kcal filter/sort in both modes (FU-637 done). **2026-08-17 feedback batch:** the toolbar is now the Stock Overview toolbar (order, secondary Import, phone icon-only + two-row wrap), the filter panel split into stock's two sideways-scrolling rows, and a **compact one-row-per-recipe view** landed with the choice remembered per device (`useListViewMode`) — the card/row split forced the display-derivation duplication out into a shared `useRecipeDisplay` (R-003). Verified live at 375px; **desktop shape owed** (`$q.screen` reads 0 in the agent pane, so only mobile branches render there). **FU-638 still open** but now evidenced as an rAF-wedge pane artifact. **2026-08-17:** recipe pages now mark *which* ingredient is at risk (server-derived `is_expiring` / `is_expired` on the ingredient DTO, sharing the filter's horizon by construction) — read view only for now, see FU-670. **2026-08-17 fix:** the page was only ever loading the first 50 recipes and filtering client-side over them, so anything past the cut was invisible to the list, search, filters and counts (owner hit it at 68 recipes); the store now pages until exhausted, as stock has since FU-035. Browser walk owed; **FU-668** sweeps the remaining list stores for the same trap. **2026-08-19 recipe-view batch (14 items):** the recipe page collapsed its three header rows onto the shared `PageToolbar` (name inline with the back arrow, no breadcrumb, no `⋮` — New version / Delete / Favourite / Import promoted to buttons, phone icon-only); **Mark cooked + Log cook deleted** — cooking is now implicit via cook mode only (owner call); the estimated-cost card expands to a per-ingredient breakdown; image-Remove un-gated from the photos *display* preference; Available meals gated on `batchEnabled`. Two real bugs fixed with it: the **$1590 estimate** (quantity × price with no unit reconciliation — reproduced from the seed on paper, fixed live) and the **Print 404** (an un-swept R-045 `window.open(apiUrl)`; the mechanic is now shared in `printView.ts`, **FU-682** carries the three remaining violations). Layout half is **unseen** — the recipe page never leaves its loading skeleton in the agent pane (**FU-681**) | [PROPOSAL](docs/04_proposals/PROPOSAL_COOKBOOK.md) |
| Stock Overview | ✅ | 3-band StockLevel, buy-verdict badge, Needs-check filter, overdue pulse. **2026-08-17:** the Essential row marker is now a tapered tab hooked around the row's top/bottom edges rather than a straight left-edge bar (browser-verify owed — virtualised rows don't paint in the agent pane) | `PROPOSAL_STOCK_OVERVIEW` |
| Stock-item detail | ➗ | 2026-08-16 batch, then a **2026-08-17 batch**: QR "Print one" **root-caused and fixed** (the ADR-041 fix had moved `window.open` after the `await`, so browsers blocked it — mobile unconditionally; now R-046/ADR-042), server half pinned by 7 new e2e tests + proven live cross-origin; nutrition **micronutrient block** (15 nutrients, migration `b6e04c9a2f18`) with the panel table now server-rendered from one authority; stock-take caption, expiry "Set" label, "Track again" and the verdict's "across N trips" all removed. **FU-648 stays open but is now instrumented** — the dialog failure has never reproduced in 3 attempts, and the error message now names status + ref, so the next report closes it. Phone-verify owed (the pop-up bug is only observable there) | `DORA_VERIFY` → Stock-item detail (2026-08-17) |
| Stocktake Mode redesign | ✅ | Built end-to-end (Chunks 1–3 + housekeeping); SK-1..11 resolved. **2026-08-17:** the locked Skip decision was revised on owner feedback — Skip resolves the item for the run instead of re-queuing it (the old behaviour grew the run's own denominator, so a run couldn't be finished by skipping); proposal §5 updated in place | [PROPOSAL](docs/04_proposals/PROPOSAL_STOCKTAKE_MODE.md) |
| ⭐ Zero-Input Pantry (P8-07) | 🟡 | Built end-to-end; **extended 2026-08-17 (FU-653)** — the belief now also surfaces on recipes, shopping lists and the meal planner, each behind its own opt-in (all off by default) and purely additive (cookability, filters, list contents unchanged). Server verified live; **client renders + the original P8-07 browser-verify pending** | [PROPOSAL](docs/04_proposals/PROPOSAL_ZERO_INPUT_PANTRY.md) + [INFERENCE_SURFACES](docs/04_proposals/PROPOSAL_INFERENCE_SURFACES.md) |
| Buy-verdict oracle (P8-05/06) | ✅ | Row + line badges + `BuyVerdictCard`; wait-hints; one-tap actions | [PROPOSAL](docs/04_proposals/PROPOSAL_BUY_VERDICT_ORACLE.md) |
| Barcode-to-add (P8-02) | ✅ | OFF lookup for unknown EANs, gated by `scanning_enabled`; real-barcode register shipped (FU-373) | [PROPOSAL](docs/04_proposals/PROPOSAL_BARCODE_SCANNING.md) |
| Native mobile app (P8-10) | 🟡 | Capacitor 8 wraps SPA; Android/iOS scaffolded; **final APK build + on-device verify pending** | [BUILD_NATIVE.md](packaging/BUILD_NATIVE.md) |
| Onboarding | ➗ | Per-name picks + paste-rows; slimmer bar + dark look; preferred-stores step done (FU-383); **verify pending** | [PROPOSAL](docs/04_proposals/PROPOSAL_ONBOARDING.md) |
| Meal Plans | ➗ | **Evening brief shipped 2026-08-17 (later 10)** — one opt-in push at 19:00 household time with tomorrow's meals + any shopping day due, silent when there's nothing to say (`daily_brief.py` + `send_daily_brief.py`, migration `f2a9c4e18b73`, 19 tests). Owner reframed the original per-slot reminder ask (≤35 notifications/wk) into a digest; **`MealSlot.starts_at` and the just-in-time nudge are won't-do**, not deferred. Device-verify owed. Also built end-to-end **+ extended**: Build-my-week auto-planner, day/meal toggles, week-duplicate, cook batches (Part 2), per-day calories, kcal in the recipe picker, and "find a lighter option" swaps (FU-637) — all shipped + verified live | [PROPOSAL](docs/04_proposals/PROPOSAL_MEAL_PLANS.md) + `IMPL_PLAN_MEAL_PLANS_REBUILD.md` |
| Meal reconcile | ➗ | "Stocktake for meals" — Chunks 1–5 shipped; Chunk 6 (settings row/copy polish) pending | [IMPL_PLAN](docs/04_proposals/IMPL_PLAN_MEAL_RECONCILE.md) |
| Alerts control centre | ✅ | `/alerts` hub, ALERT_ROUTER, price-watch + email-digest + push; shared `resolve_overdue_map` | [PROPOSAL](docs/04_proposals/PROPOSAL_ALERTS.md) |
| Assistant surface | ✅ | Per-user rate limits; SLM default AI path; Basic-mode `add_to_list` verb; AI master-switch removed (per-user only); **multi-provider config + Mode-dropdown settings redesign** (`UserLlmProvider` table; browser-verify owed). **Chat-window feedback batch 2026-08-17 (later 8)** — first-time hint no longer resurfaces on a slow `/me` hydration; the D.O.R.A. tooltip is scoped to the wordmark instead of the whole header row; the launcher is anchored to the dynamic viewport (Firefox-Android address-bar drift) and its `:hover` states are gated to real pointers (sticky-hover on touch); the un-configurable Basic/AI slider is now **tappable and routes to Settings → Assistant** rather than explaining itself in a hover-only tooltip. New: **FU-663** (that slider is a 24px tap target — fold into FU-641). Two touch/mobile checks owed | `ask_assistant.py`, `AssistantSettings.vue`, `DoraBubble.vue` |
| Nutrition (complex mode) | ➗ | **Built end to end 2026-08-14** (charter cut reversed by owner): install-wide mode, schema, USDA importer, admin page, unified lookup, stock-item food picker, the recipe per-serving rollup + coverage line, the cookbook card badge + kcal filter/sort, per-day calories on the meal planner, and the lighter-alternative swap axis (FU-637). FU-635/637 closed. **FU-639 (2026-08-15): the download + food-link paths were broken in production — 4 bugs fixed, verified locally against the real USDA release; owner re-test in the container owed.** **Auto-suggest shipped 2026-08-15** — the setup-friction answer: Dora name-matches unlinked stock items against the local catalogue and offers the result as a visibly-labelled suggestion (never a write), on the stock-item page and on a new bulk **Settings → Kitchen setup → Nutrition matching** screen with an "Accept all confident" verb and a reversible per-item "Not a food" opt-out. Agent-verified live end to end; R-043/R-044 + ADR-039/040 added. **Depth extended 2026-08-16** — sugars, saturated fat, fibre and sodium now import from USDA + OFF (migration `d3a7f2b91c60`; one shared `nutrients.py` owns the per-source naming), and a linked stock item has a full per-100g Details table. Existing catalogue rows read blank until re-import (FU-645); the recipe rollup still sums only the original four (FU-646). **Depth extended again 2026-08-17** — the owner reversed the "no vitamins/minerals" scope call, so **15 micronutrients** now import from both sources (migration `b6e04c9a2f18`) and render as an optional, collapsed block. The panel table is now **server-rendered** (`nutrients.display_rows` owns labels/order/units/rounding/grouping; the client held a hand-synced copy before), reworded and reordered to match a printed panel, and pinned by 4 new e2e tests. New: **FU-657** (the new OFF scale factors are unverified against a real response). Open gap: **FU-643** (no synonym layer — "Tinned tomatoes" ≠ "Tomatoes, canned") | [FU-635 (resolved)](DORA_FOLLOWUPS_RESOLVED.md) |
| Settings & config polish | 🟡 | Active stream: household budget (value-driven), AI master-switch removed, Region & locale merged, Account/Kitchen-setup redesigns, encryption-key banner+generator, **Stock-locations rebuilt as zone cards**, **settings nav regrouped** (Account / Preferences / Kitchen setup / About), voice-picker selection bug + deals-email opt-in default (all owner-initiated, outside the DR bundle), **Kitchen-setup feedback batch 2026-08-17** (list rows unified on the shared vocab editor incl. Stock groups' fork; broken Add-store dialog fixed; store-logo upload via a new shared `ImageEditTile`; description copy), **settings feedback batch 2026-08-17 (later)** — new stock items now join the stock take by default; mobile/desktop group headings navigate to their first page and single-page groups lost their redundant chip; Assistant regrouped (Assistant chat → Providers → Zero-Input) with per-provider minimised status cards; About rebuilt end-user-first; **`compose.yml` never forwarded `DORA_SECRET_ENCRYPTION_KEY`** — root cause of the false "encryption isn't set up" banner, fixed. **Admin-settings batch 2026-08-17 (later 3)** — Admin's single "Admin · global" pile regrouped into **5 flat groups** (Users / Install / Kitchen defaults / Messaging / Data & access) with the nav sub-header level **deleted app-wide** (new rule **D-021**); Users page rebuilt (Refresh + Deals-email toggle removed, mobile row stacks, actions behind `⋮`), **admins can set a password directly** (generate stays as the escape hatch) and **deactivate a user instead of deleting them** (`is_active`, migration `a7f3c9d15e82`, last-usable-admin + self guards); Region & locale rebuilt preview-first with searchable currency/language pickers. Several new DORA_VERIFY walks queued | `CHANGELOG [Unreleased]` |
| Offline / resilience (F3) | ➗ | **2026-08-17: found broken end-to-end and fixed.** The replay used bare axios and never attached the FU-197 CSRF header, so *every* drain 403'd, was misread as a conflict, and was discarded from a memory-only pile — everything queued offline was silently lost while the UI said "Synced everything". Also fixed: no drain on app re-open (only on a network transition, which never happens on a fresh load) and a **Retry button that issued no request at all** when `navigator.onLine` was false. R-047/ADR-043 added. **Live round-trip verify owed** — mocked transports can't reproduce the failure. Open: FU-660 (conflicts have no UI), FU-661 (coverage = 6 mutation kinds), FU-662 (`attempts` unused) | `useOfflineQueue.ts` / `useNetworkStatus.ts` |
| Container config | ✅ | `compose.yml` now forwards the whole `.env` via `env_file` — the `environment:` allow-list was the structural cause of the `DORA_SECRET_ENCRYPTION_KEY` miss. Audit also found `DORA_SMTP_USER` (misspelling of `_USERNAME`, never read), a dead `DORA_SMTP_PASSWORD`, and 8 unforwarded runtime vars (Postgres components, support links, demo mode, voice dir). Pinned by `tests/test_compose_env_coverage.py` | `compose.yml` / `.env.example` |
| Data/Backup admin | ✅ | Under Settings→Admin→Data; backup library + admin-gating | FU-341/342/198 |
| Auth shell | ➗ | Shared `AuthShell`/`AuthButton` across pre-auth surfaces | `PROPOSAL_AUTH_SHELL.md` |
| Postgres datastore | ✅ | Implemented + **default** (SQLite fallback via `DORA_DB_PATH`); FU-045 closed; suite green on PG | `configuration_manager.py` |
| Recipe importer (paste-based) | ✅ | Six chunks landed; parser green 20/20; bulk-linker + PWA share target; **verify pending** | [IMPL_PLAN](docs/04_proposals/IMPL_PLAN_RECIPE_IMPORTER.md) |
| Open-source release (P7) | ⚪ | Not sold — donation/OSS/all-free. Remaining: README/showcase, release process, support channel (FU-406/557/608) | [PLAN §5](docs/01_charter/RECONCILED_FINISHING_PLAN.md) |
| Test suite | 🔴 | Frontend Vitest is **red**: 2 failures in `stockLevelDot.spec.ts` (FU-634, needs a D-001 intent call), 426 passing / 34 files. Backend + property + PG green (~1616 collected). Other remnant: Postgres **CI wiring**, blocked on FU-405 | [PROPOSAL](docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md) |
| Finalisation sweep | 🔵 | Designed, not started — 20 chunks, two-stage, single-maintainer north-star | [PLAN](docs/01_charter/FINALISATION_PLAN.md) + [COVERAGE](docs/01_charter/FINALISATION_COVERAGE.md) |

---

## ⚠️ Needs your attention now

00. **Sit in on the Step-0 alerts assessment.** `IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md`
   is written and its main chunk is *deliberately blocked* on 5 questions only you
   can answer — which of the 9 alert kinds you actually want, whether per-user
   `AlertPreference` earns its complexity, whether actionable/FYI survives next to
   `severity`, whether the digest email lives. The alerts system was largely
   AI-built from loose ideas and has never been vetted; consolidating onto it
   unassessed would make it harder to change later. It's a conversation, not code.
   Chunks 1–2 need nothing from you and can land meanwhile. See FU-683.

0. **Walk the new inference surfaces in a browser.** FU-653 shipped (recipes /
   shopping lists / meal planner, each toggled separately, all three off by
   default). The server side is verified; the three client renders have never
   been seen — the seed now carries two "Belief demo:" recipes that make it a
   30-second check. `DORA_VERIFY.md` → "Inference on recipes / lists / meal planner".

0b. **Round-trip the offline sync in a browser.** The queue was found broken end
   to end on 2026-08-17 — it queued changes and then lost every one of them
   while reporting success (CSRF header missing on replay; see the Offline row
   below). It's fixed and Vitest-pinned, but the failure mode is exactly the one
   a mocked transport can't reproduce, so the fix is unproven until someone goes
   offline, changes something, comes back, **and reloads to confirm the server
   kept it**. `DORA_VERIFY.md` → "Offline sync + Retry, end to end".

**Total open backlog is 68 items in `DORA_FOLLOWUPS.md`** (counted 2026-08-19;
the dashboard's previous "34" was a 2026-08-14 count and had drifted badly). These are the ones wanting a decision or a
running-app check, most important first.

0c. **Walk the recipe page.** The 2026-08-19 batch rebuilt its toolbar, removed
   Mark cooked / Log cook, and made the cost card expandable — and **none of the
   layout has been seen**, because the recipe page doesn't leave its loading
   skeleton in the agent pane (FU-681). The two bug fixes in the same batch
   *were* verified live against your seed (Juice Bowl: $1590 → no estimate with
   both lines explaining why; Tuna Bake: $3.15). The Print fix specifically needs
   a check **from a phone or a non-localhost host** — that's the only place the
   old code failed. `DORA_VERIFY.md` → "Recipe page: toolbar, cost card, image,
   meals". Related: **FU-682** — three more print buttons (shopping list, meal
   plan, stock overview) still carry the defect Print had.

1. **Walk the cookbook feedback-batch-2 changes in a browser.** 15 items shipped
   2026-08-19 — the filter row rebuilt on shared base components, the cook-mode
   confirm made consistent between the cookbook and the recipe page, and the
   import / add-ingredients dialogs reworked. The measurable half was measured
   live (control geometry, caret position, focus paint, mobile dialog width); the
   **recipe list and recipe detail page don't mount in the preview pane**, so the
   ingredient-picker dialog and the cook guard *from the cookbook* have never been
   seen. `DORA_VERIFY.md` → "Cookbook: filter uniformity, cook guard, modals".
2. **Walk the nutrition complex-mode surfaces against a real USDA import.** The build chunks landed 2026-08-14 (FU-635 closed) and the 2026-08-15 auto-suggest surface was agent-verified live — but on a 20-food scratch catalogue. What's genuinely unknown is **match quality on your own pantry with the real ~7,800-row dataset**, and whether the matching page loads quickly at that size; both are queued in `DORA_VERIFY.md`. That walk is also what should decide **FU-643** (the missing AU/US synonym layer). The recipe nutrition card still hasn't been seen with real data either.
3. **Continue the UX/UI review remediation (DR units).** A large owner-requested critical-drive bundle (~50 findings), mapped to DR-1..DR-16. **Done: DR-6, DR-4 (copy/leakage), DR-1 muted-contrast ramp** (all 10 themes ≥4.5:1), **DR-1b badges** (alerts + verdict, AA-verified), **DR-2** (level-colour SSOT fix — Low→amber/Out→red, footer derives from the one authority; row legend, live-verified — relocated 2026-08-15 from the filter panel to Help → Guides), **DR-3** (dialog casing sweep + open-toggle glyph/a11y + bulk-bar disabled state; R-039/ADR-035 added), **DR-5** (open-toggle mutation trap — deferred PATCH + 3-outcome dialog, Vitest-pinned). **DR-7** (toast/helper-bubble placement — de-congested the toast corner, tip auto-dismiss, greeting copy; toast-die-on-route carved to FU-624), **DR-8** (loading polish — splash rAF-wedge fix, dashboard skeletons, belief-chip/verdict reflow-free fade-in; #26 warm-splash investigated = dev-only), **DR-9 ➗** (shared PageToolbar wrap — 0 h-scroll@375px / no title-collision@1280px, verified; mobile stock-row 2-line names; toolbar-More-collapse + row-icon-overflow + stranded-cards carved to FU-631), **DR-10 closed** (owner saw a 3-way nav mockup, chose leave-as-is), **DR-14 ➗** (new `useDateFormat` date authority sharing `useMoney`'s household locale; all 26 `toLocale*` date sites migrated → AU format not browser-US; first-boot region derivation #48 + theme-split #7b carved to FU-632), **DR-11** (recipe detail now opens as a read view + explicit Edit toggle; #11 "on hand" contradiction fixed; nested-substep read display a minor follow-up). Remaining DR units: DR-12 (alerts order + calendars), DR-13 (history grouping), DR-15 (micro-motion), DR-16 (onboarding activation — owner call). **A brand-secondary rethink spun out as FU-621** (owner: secondary "feels off" + it's invisible as text on dark themes — wants a visual options board, logged FU-622). [FU-578](DORA_FOLLOWUPS.md)
4. **Products-overlay Phase-F verify + hard-delete call.** Product surfaces need a running-app walk with real data; L197 hard-delete is still an undecided design call and L205/206 bulk-select is unbuilt — the runbook's Phase-F blocker. [FU-214](DORA_FOLLOWUPS.md)
5. **⭐ Verify the champion sequence in-browser.** Four surfaces stacked and untested on this dev box — P8-07 Zero-Input Pantry, P8-08 Kitchen health, P8-09 Memory reports, plus P8-10 native Android (APK build + device walk). Pairs with the queued Settings-rework `DORA_VERIFY.md` sections.
6. **Open-source release readiness.** README/showcase + GitHub Releases process + Sponsors link — the Phase-4 gate to publishing publicly; needs your call on scope/timing. [FU-406](DORA_FOLLOWUPS.md)
7. **Stand up donation + OSS infrastructure, then swap in-app placeholders.** Owner-external checklist: make repo public, set up Sponsors / Buy-Me-a-Coffee / PayPal.me, then one placeholder-swap pass. [FU-608](DORA_FOLLOWUPS.md)
8. **Stand up the support channel.** Pick + create the (recommended) public GitHub-issues channel; a one-line config change then lights up Help / error-report / DoraBot. Pairs with FU-406/608. [FU-557](DORA_FOLLOWUPS.md)
9. **Cross-cutting feedback bundle — 4 items still open.** Final QA regression doc, UI-polish/uniqueness pass, cross-user push notifications, general UI consistency — mostly Phase-4 gates needing your steer on when. [FU-363](DORA_FOLLOWUPS.md)
10. **Real-device mobile / PWA field test.** A hands-on device pass; natural to fold into the P8-10 native verify. [FU-389](DORA_FOLLOWUPS.md)
11. **Late-game holistic theme/colour review.** Eyes-on-app pass across the full theme set (Pesto suspected over-dulled); needs the running app. [FU-010](DORA_FOLLOWUPS.md)
12. **App-wide colour-usage assessment** (primary vs secondary/accent/info). Needs eyes-on-app judgement, not a code walk. [FU-224](DORA_FOLLOWUPS.md)
13. **Ops / CI / observability (Phase 4).** Deliberately-disabled CI, backups, staging still unplanned — and CI must not be silently re-enabled; a Phase-4 decision that also unblocks FU-520 (Postgres CI) and FU-404. [FU-405](DORA_FOLLOWUPS.md)

14. **🔴 Pick a lever for `--text-on-primary`.** Three themes (pesto 3.88,
   blueberry 4.21, midnight 2.86) define it as white over a mid-brightness
   primary and fail D-002's 4.5:1 floor **app-wide** — anything painting that
   token over `--brand-primary`, not just the control that exposed it. The fix is
   either darkening those themes' ink (changes every primary button in three
   themes) or darkening their `--brand-primary` (changes the brand colour). One
   decision, then it's mechanical. [FU-674](DORA_FOLLOWUPS.md)
15. **Two mobile-touch gaps worth one pass together.** Every `.dora-btn` is 36px
   tall against D-004's 44×44 floor, and no shared wrapper exists for the app's
   72 `q-select`s (so the menu-vs-dialog behaviour on phones is accidental, and
   long lists are hard to dismiss). Both want a real phone, and the filter row
   was already raised to 44px, which makes the buttons beside it the outlier.
   [FU-678](DORA_FOLLOWUPS.md) · [FU-675](DORA_FOLLOWUPS.md)

**Lower-priority / trigger-gated** (listed for completeness, not urgent):
FU-520 (Postgres CI — waits on FU-405), FU-404 (compliance — activates
only when hosting user data), FU-576 (uploads spec — needs a bundled-Chromium
run), FU-579 (quasar-dev checker overlay — re-test), FU-575
(name-uniqueness/whitespace — opportunistic), FU-358 (Aldi scraper — when
Aldi data is next needed). *(FU-584 e2e-flake resolved 2026-08-12 — the specs it
named were deleted in the Playwright cull.)*

> **Cleared since last review (2026-08-19):** **both test suites are green** —
> backend 1858 passed / 0 failed (FU-676, an order-dependent seed-pollution
> blocker handed off red the same day) and frontend 469/469 (FU-666 / FU-634, the
> `stockLevelDot` pair that had been red for several sessions: the *spec* held the
> pre-D-001 mapping, not the component). The "frontend suite is red" item that
> stood at #1 here is gone.
>
> **Cleared at the previous review:** every item that PROJECT_STATE listed
> under "Needs attention" is now in `DORA_FOLLOWUPS_RESOLVED.md` — FU-595
> (planner freeze), the whole security thread (FU-447/515/197), FU-620
> (email-change removal), FU-612/609/346/353/606/085/429/025/549/464/355/383,
> and the P6 loop tail FU-450/451/452. Do not reintroduce them as live.

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

1. **✅ Security thread closed.** `AUTH_ASSISTANT_SECURITY_FINDINGS` is now a triaged standing register — the HIGH CSRF + MEDIUM email-change were fixed under FU-197 (2026-06-30); the 8 residual Medium/Low findings went to FU-515 (resolved); the orphan audit-follow-up FU-447 was reconciled + closed. A.5/A.6/A.7 are accepted risks (A.6 → Phase-4). Nothing open.
2. **🕸 Stale "no code yet" / "designed-not-built" headers on ~15 shipped docs (FU-445).** Bodies are accurate records; only the top status line lies (e.g. IMPL_PLAN_ALERTS, IMPL_PLAN_MEAL_RECONCILE). Judge by this register, not the header.
4. **🕸 `docs/00_DOC_GRAPH.md` is a retired stub (FU-428).** Superseded by this doc + the CLAUDE.md anti-drift rule.
5. **Backlog right-sized.** The old dashboard cited "~60 open items"; the ledger actually holds **17**. Most of the prior attention list had long since moved to `_RESOLVED`.

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
| DESIGN_REMEDIATION_PLAN | Design backlog | 🟡 active | Action the 2026-07-18 UX/design audit (DR-1…16) | DR-1/1b/2/3/4/5/6/8/10/11 done (10=owner leave-as-is), DR-7 ➗ (FU-624), DR-9 ➗ (FU-631), DR-14 ➗ (FU-632); remaining: DR-12/13/15/16 |
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
| IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION | Impl plan | 🔵 designed-not-built | Collapse the stock row's 9 competing signals → 4; one attention rule, one cadence engine | Written 2026-08-19; 6 chunks, Chunk 3 gated on Step-0 alerts assessment; FU-683 |
| IMPL_PLAN_WASTE_MINIMISATION | Impl plan | ✅ done | Waste-minimisation cluster (C-waste) | `wasteApiService.ts` + mark-as-wasted |
| IMPL_PLAN_YOUR_PRICES | Impl plan | ✅ done | "Your prices" intelligence (Phase F) | "All 8 chunks landed (FU-227/425)" |
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
| PROPOSAL_SHOPPING_LIST_UX_V2 | Proposal | ✅ done | Single-page shopping experience | "BUILT 2026-06-12" |
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
