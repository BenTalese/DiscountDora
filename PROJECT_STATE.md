# Dashy Dora — Project State

**Last reviewed: 2026-09-06 (products program: 5 of 8 batches shipped).** Milestone-progress front door — phase board,
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

The app remains in owner-feedback-sweep mode rather than feature-build mode, and 09-05
ran three units back to back. After the seven-item cross-surface batch (cookbook cost per
serving, About rebuilt as cumulative usage stats, one chef-hat icon, and the app-wide
tap-target sweep that finally closed FU-678 + FU-641) and the five-item dashboard
follow-up (hero rebuilt as a grid, *Next to cook* dropping its Ready chip, Cook now
opening at a batch's whole yield), a **thirteen-item meal-planner batch** landed: the
rail's shopping card collapsed from four pieces of chrome to one row, the two duplicated
entry menus extracted into `MealPlanEntryMenu`, the phone's day laid out by meal slot
(retiring the "Which slot?" sheet), and **money reaching the planner** — per-entry,
per-day and per-week cost plus a Cheapest ordering sharing the cookbook's comparator. The
batch's headline bug was structural rather than cosmetic: the servings stepper closed its
own menu because `PATCH /meal-plans` re-mints every forward entry id, so the `v-for` key
changed on every tap — fixed at the rendering layer with content-identity keys
(**R-086/ADR-083**), with the server-side churn logged honestly as FU-878 rather than
papered over. Gates on the current tree: **pytest 2317 passed** with only the four known
buy-verdict reds (FU-762), **vitest 705 / 63 files**, `vue-tsc` and `eslint src/` clean,
`quasar build` green, driven live at 1440 and 375 against the seeded e2e backend. Phase 1
still has exactly one unbuilt item (meal-reconcile Chunk 6); everything else is
browser-verify debt, which is now the dominant form of remaining work project-wide. The
live risks are unchanged and structural: a flag that gates nothing while shipped copy says
it does (**FU-866**), a deploy path still broken owner-side (**FU-790**), and four red e2e
tests every gate has been run around (**FU-762**).

---

## Phase board

| Phase | Scope | Status | Remaining |
|---|---|---|---|
| **0 — Foundations & truth** | Theming, filters, modals, loading, text, renames (P8-01), Wave-B bugs, config/opt-ins | ✅ ~99% | Residual token debt only: FU-674 (`--text-on-primary` under floor in three themes), FU-801 (`--brand-primary` same ink test), FU-850 (`--accent-mark` adoption), FU-834/FU-764 (~20 undeclared custom properties, no lint gate), FU-777, FU-839, FU-865 (scrollbar rule reads `:root` while the palette is on `<body>`). The opt-in spine's own defect class is **FU-866**. |
| **1 — Close the loop** | Shopping lists, cook mode, stock, cookbook, meal planner, suggestions, costing, stocktake | ➗ ~96% | **Meal-reconcile Chunk 6 (settings row/copy) is still the only unbuilt item.** Everything else is browser-verify, and 09-05 added a third layer of it: the whole thirteen-item planner batch (rail disclosure + counts, the slot-sectioned phone day, the surviving servings menu, cost on strip/day/card/rail), on top of the `cook_fresh` batch-household path, the dashboard's batch-household and manual-reconcile states and its money-off/products-off card gates (FU-868). Still owed from before: stock overview (08-20/21/22), the stocktake three-phase runner, cookbook batch 3, the older recipe-page batches, the buy-verdict money gate, `planned_store_id` round trip. |
| **2 — Ingestion API + companion** | `/api/ingest` seam, standalone companion, Merchant→Store | ➗ reopened 2026-09-06 | **The whole products area was reopened by the owner and re-planned as a seven-batch program spanning both repos — [IMPL_PLAN_PRODUCTS_PROGRAM](docs/04_proposals/IMPL_PLAN_PRODUCTS_PROGRAM.md), agreed and unstarted.** L197 hard-delete is now **decided (build it)**; L205/206 move to batch F; FU-214 narrows to a browser pass over four already-look-fixed bullets. New: **FU-881** the companion's save button can push the *wrong product* (it re-scrapes by name) — the keystone, since "Dora is the source of truth" and hard-delete both rest on it; **FU-882** batch push ignores the selection; **FU-884** four Aldi provider defects + a needed rewrite. Unchanged: **FU-856** (`pack_count` unreachable through the products API), **FU-866** (ingest route never checks its own flag). |
| **3 — Champion** | Zero-Input Pantry, buy/wait oracles, barcode-add, Dora Score, culinary memory, native app | ➗ ~95% (verify pending) | P8-01..P8-10 built. Device/browser verify of P8-07/08/09/10 owed; native FCM push parked until Phase 4 (FU-465). |
| **4 — Open-source release** *(was Commercialize)* | README/showcase, release process, support channel, ops/CI | ⚪ ~0% | Not sold — donation/OSS/MIT. FU-406 (README+release), FU-608 (OSS infra), FU-557 (support channel), FU-861 (no real build number — needs a version source feeding both bundle and API; tagging is on this phase's critical path). Ops/CI (FU-405) gates FU-520/404/721. SaaS work parked. |

---

## Major workstreams

| Workstream | Status | Where it's at | Governing doc |
|---|---|---|---|
| **Meal planner** | 🟡 | The most active stream again — a **13-item owner batch on 09-05**, on top of the ~35-item sweep and `cook_fresh`. The rail's "This week's shopping" became *Missing this week*, folded into the disclosure header with tinted out/low count circles and the cart beside it; both rail disclosures are now one hand-rolled `MealPlanRailDisclosure` because `q-expansion-item` structurally can't keep an action visible when collapsed. The two entry menus (`MealPlanEntryChip` / `MealPlanRichCard`) were **copy-paste identical** and became `MealPlanEntryMenu` (R-001). The phone's day is now a section per slot in the household's own order, every slot present with its own Add — which retired the "Which slot?" sheet. **Money reached the planner**: `_hydrate_cost` gives per-entry cost at planned servings, a per-day rollup, a week total with coverage counts, plus an A-Z/Cheapest rail ordering off the newly extracted `recipeCostSort.ts`. The servings-stepper bug was **`:key` churn** — `PATCH /meal-plans` replaces every forward entry, minting new ids (**R-086/ADR-083**; server-side churn deferred as FU-878). None of the batch, and none of `cook_fresh`, has been walked by the owner. Open: FU-879, FU-878, FU-863, FU-862, FU-802 | [PROPOSAL_MEAL_PLANS](docs/04_proposals/PROPOSAL_MEAL_PLANS.md) · R-086 |
| **Settings & admin IA** | 🟡 | Unchanged since 09-03's ~25-item sweep: five nav groups → **three** (Install · Kitchen features · Data & access), the **Features** and **Hosting** pages dissolved with every switch sent to the surface it governs (scanning → Stock, money → `AdminSystemMoneySettings`, companion ingestion → `AdminSystemIngestionSettings`, weekly deals mail + public URL → Email, audit retention → Audit log), both retired routes redirect. Eleven routes stopped prefixing `System: ` onto the mobile title. Open: FU-867, FU-866, FU-858..861 | `CHANGELOG [Unreleased]` · R-081 |
| **Feature flags & opt-ins** | 🔴 | Still the standing defect class. `meal_planning_enabled` claimed to hide the meal-plans surface and never did — column, health flag, DTO field, API field, planned-demand `enabled` key and client ref all dropped in **`a7c3e5d19f2b`** (**R-081/ADR-078**). The same shape is still live and unfixed: **FU-866**, `companion_ingestion_enabled` doesn't gate `POST /api/ingest`, and it defaults to `False` | `ENGINEERING_STANDARDS` R-081 |
| **Cook mode / Sous Chef** | ➗ | Unchanged. Voice batch: **"ingredients"** and **"tools"** answer for the current step, scaled to headcount and naming session substitutes, both bypassing the narration toggle deliberately; **"stop"** cancels speech or pauses a timer instead of exiting. Earlier: one header band, Prev/Repeat/Next clearing 44px, shared `StockLevelPicker` + `AddToListButton` in the finish modal. Open: FU-853 (chime blocked by the app's own CSP), FU-854, FU-763 | `RecipeCookMode.vue` |
| **Theming & design tokens** | 🟡 | FU-709 resolved after ~2 weeks open — Quasar's `body.body--dark` out-specified `app.scss`, so all seven dark themes painted `#14171a`; `themeService` now syncs `--q-dark-page` (R-080/ADR-077). **Salt & Pepper** rebuilt as an achromatic modern-OS palette, its blue re-tuned 09-04 (deeper in light, sky in dark). **Lemon Tart Dark** on the gold axis; **D-024** gives every theme a hairline under the header. Seven families total. Open: FU-865, FU-850, FU-801, FU-674, FU-834, FU-764 | `themes.scss` · `DESIGN_STYLE_GUIDE.md` |
| **Zero-Input Pantry / inference** | 🟡 | Extended to recipes, lists and the planner, each behind its own off-by-default opt-in. **Planned demand** ships as a sibling signal (R-074/ADR-071) with a card on the stock-item page; its dead `enabled: false` short-circuit went with `meal_planning_enabled`. Open: FU-851 (cache goes stale after a plan edit off the detail page), FU-849 (not on the shopping list yet) | [PROPOSAL](docs/04_proposals/PROPOSAL_ZERO_INPUT_PANTRY.md) |
| **Products-as-overlay** | ➗ | Phases 0–E code-complete and backend-green; **browser-verify has never been done on any of it**. Single Alembic head, now `d4f9b2e7a318` (was `c4e6a8b1d3f5` when this row was written). FU-178 remains a fresh-SQLite boot blocker that tests bypass via `drop_all + create_all`. **The Phase-F tail is superseded** by the products program below | [RUNBOOK](docs/04_proposals/PRODUCTS_OVERLAY_RUNBOOK.md) |
| **Products program (Dora + companion)** | 🟡 active — 5 of 8 batches done | Agreed 2026-09-06. **The Dora↔companion data path is complete, and the page the owner actually asked about is rebuilt.** ✅ **B** push carries the offers the user picked (FU-881/882) · ✅ **C2** finished lists keep their lines (FU-883) · ✅ **C** product hard delete (L197) · ✅ **D** scheduled refresh; inactive now means "don't scrape" (PF-8) · ✅ **F** My Products rebuilt — two view modes (cards + compact rows), flattened card actions per OD-1, standard toolbar, bulk-select with the three stock-crossed selections, Refresh gone, one shared `DiscountChip` (FU-885). Remaining: **A** companion key UI (small) · **E** scrapers + Aldi rewrite (**needs OD-3**) · **G** Price History + stock-item tab. Established **R-087/ADR-084**. Open: **OD-3** only — OD-1 is closed | [PLAN](docs/04_proposals/IMPL_PLAN_PRODUCTS_PROGRAM.md) |
| **Prices surface** | 🔴 | Unchanged. All price *reading* capability still sits on the product axis at `/price-history`, which has no nav entry, while the everyday user gets a single-item modal. **FU-703** is the keep/cut call and gates FU-704..708 | [ASSESSMENT](docs/05_investigations/PRICES_SURFACE_UX_ASSESSMENT.md) |
| **Email & notifications** | 🔴 | 09-03 made the shape legible without changing behaviour — `email_enabled` (SMTP subsystem) and `deals_email_enabled` (one scheduled mail) now share a page, with the deals InfoTip naming its real dependency. The finding underneath stands: **FU-860** — with products off, Dora sends **no scheduled email at all** | FU-860 |
| **Recipes & cookbook** | ➗ | **R-076/ADR-073** gave one `_item_price` helper authority over "what does one of these cost?", allowed to answer *no*. 09-05 took cost to the cookbook (per-serving on rows and cards, a Cost-per-serving sort, two queries for the page, skipped outright with money off, plus a money-**on** query-count test because the existing one passed vacuously) — and the comparator behind that sort has now been extracted to `recipeCostSort.ts` and reused by the planner rail. The units investigation (`RECIPE_PRICE_UNIT_MISMATCH.md`) found the density bridge exists and is never called. Open: FU-874 (the dead `ingredient=` argument — **recommended now-ish**), FU-875, FU-855, FU-856, FU-857, FU-876 | `recipe_cost.py` · [INVESTIGATION](docs/05_investigations/RECIPE_PRICE_UNIT_MISMATCH.md) |
| **Shopping lists (v4)** | ✅ | Built end to end, all three faces on one row skeleton. Open: FU-808, FU-805, FU-738, FU-769 | [SHOPPING_LIST_UX_V2](docs/04_proposals/SHOPPING_LIST_UX_V2.md) |
| **Dashboard** | ➗ | The 19-item sweep (14 cards → 9, four fixed zones deleted, `use_it_up` + `before_you_shop` + `shopping_lists` replacing the cards that restated the alerts bell, kitchen health swapping diligence signals for `plan_adherence` + `plan_coverage`) plus a **five-item follow-up on 09-05**: the hero rebuilt as a 3×2 grid so the greeting sits beside the mascot at every width, Cards icon-only below `sm`, *Next to cook* hiding its badge only when the meal is cookable — which exposed the recipe name resolving to **zero width** at 375px (now floored at `7ch`) — and Cook now opening at a linked batch's whole yield via a new server-derived `cook_batch_total_servings`, fetched from the whole batch rather than folded from the visible week. Open: FU-868..872, FU-831, FU-832, FU-836..839, FU-841, FU-864 | [IMPL_PLAN_DASHBOARD_REBUILD](docs/04_proposals/IMPL_PLAN_DASHBOARD_REBUILD.md) |
| **Reports** | ✅ | Review closed, five chunks, money-gated (R-058); ECharts deleted (549 KB → 24 KB, R-073/ADR-070). Title and "estimates, not accounting" caveat dropped 09-04. Open: FU-843..847 | [REVIEW](docs/05_investigations/REPORTS_PAGE_REVIEW.md) |
| **Shared component anatomy** | 🟡 | The extraction habit is now the batches' default move: `StockLevelPicker`, `NumberStepper`, `LocationAddChip`, `css/settingsCards.scss`, then 09-05's `MealPlanEntryMenu`, `MealPlanRailDisclosure`, `MealPlanRailCount`, `mealPlanEntryKey.ts` and `recipeCostSort.ts` (shared cookbook↔planner). **FU-848** (merging `BaseSegmented` / `DoraSegmented`) stays its own unit — 19 consumers pass Quasar props that would go inert | `BaseSegmented.vue` |
| **Touch affordances / tap targets** | ➗ | New stream, 09-05. The D-004 44px floor was violated app-wide — `BaseButton` at 36px, 38 `q-list dense` menus across 26 files at 32px rows, stock and cookbook rows at 30px. FU-678 and FU-641 both diagnosed it in August and both deferred it on the assumption the fix had to apply everywhere; D-004's own text scopes it to fingers. Fixed under `@media (pointer: coarse)` in two shared places plus the two rows that pin their own size. Measured in both contexts: **touch 44/44/260×44, mouse 32/36/200×32 unchanged**. **R-085/ADR-082**; resolves FU-678 + FU-641. Open: **FU-877** (the 36–40px second tier, deliberately untouched) | `BaseButton.vue` · `css/app.scss` |
| **Assistant / voice / offline** | ➗ | Voice download was broken for every voice, always (`NameError`) — fixed with the first tests ever to touch `voice_provision`. Firefox TTS still unverified (FU-751, FU-788, FU-787); offline CSRF round-trip owed (FU-724); FU-722 clipped speech unconfirmed | `useOfflineQueue.ts` |
| **Design remediation (DR)** | 🟡 | DR-1..11/14/15 done or done-with-carve-outs; **DR-13 and DR-16 remain (owner call)**; DR-12 half-settled | [DESIGN_REMEDIATION_PLAN](docs/04_proposals/DESIGN_REMEDIATION_PLAN.md) |
| **Build & deploy** | 🔴 | The 08-23 backups/import 404 was the deploy script, not the app (`--exclude='data'` matched at any depth and `--delete`d `dora_api/features/data/`) — one-character fix, still owner-side. FU-790 blocks deploying outright. FU-719, FU-720, FU-721 | FU-719/720/790 |
| **Verify tooling** | 🟡 | Isolated pairing (scratch backend 5171 + SPA 5174) is proven and now the default for live drives — the 09-05 batches used throwaway Playwright scripts written, run and deleted in-session per the DORA_VERIFY_TRIAGE stance. Pane limits stand: `QMenu` never opens, `screenshot` times out, stock-item detail and the cookbook list won't mount. The four `:5170` + `DORA_ALLOW_DESTRUCTIVE=true` configs remain the footgun (**FU-758**) | FU-758 |

---

## ⚠️ Needs your attention now

**Total open backlog is ~208 items in `DORA_FOLLOWUPS.md`**; the list below is the slice
that wants a decision or a running-app check now.

**Decisions the owner owns**

1. 🔴 **FU-866 — `companion_ingestion_enabled` gates nothing, and the new copy says it does.** `submit_ingestion_batch()` authenticates the bearer token and proceeds without ever reading the flag — the second instance of exactly what R-081 was written for, on the same page as the first. The fix is a one-line 403, but the column **defaults to `False`**, so guarding it breaks every install already pushing data (including yours). *Guard it and accept existing pushers must switch it on, or flip the default for existing rows in the same migration.* **Resolution: now.**
2. 🔴 **FU-790 — `name: dashy-dora` in `compose.yml` orphans the deployed stack.** The server was deployed under the directory-derived project `discountdora`; pinning the name strands it, and `container_name` makes it fatal. **Blocks deploying.** Pairs with the still-unapplied one-character `--exclude='data'` deploy-script fix.
3. 🔴 **FU-762 — four buy-verdict e2e tests are red** (`test_list_buy_verdicts.py`, all four 403 against the money gate). Every gate this week ran with these excluded, and they were re-confirmed pre-existing against a stashed tree. Likely a one-line fixture change; a red suite blocks everyone.
4. 🟡 **FU-874 — recipe costing never passes the ingredient name, so the density bridge is dead code.** `units.convert()` bridges mass↔volume given an `ingredient=` name against a 77-entry table; `recipe_cost._line_cost` omits the argument, so every mass-vs-volume ingredient reports *unpriced*. Your ice-cream case fails twice — the argument isn't passed **and** `'ice cream'` isn't in the table. **One keyword argument plus table rows**, and it is the half of the cost story that turns gaps back into numbers. Does not weaken ADR-073: unknown ingredients still report unpriced. **Resolution: now-ish.**
5. 🔴 **FU-774 — may a planned meal change a buy verdict?** Nothing built; gates FU-775 and FU-776 and the whole axis.
6. 🔴 **FU-703 — the fate of the product price axis** (`/price-history`, My Products). Reports chunk 4 built the "trend in Reports" half, so the call is better-informed but still open, and still scopes FU-704..708.
7. 🔴 **FU-860 — with products off, Dora sends no scheduled email at all.** The Email block is `v-if="productsEnabled"` because the deals mail is the only scheduled mail. Which second email earns being unprompted? The evening brief is cheapest — it exists, it's scheduled, only the channel is missing.
8. 🔴 **Theme colour cluster — FU-622 is the vehicle, FU-621 / FU-674 / FU-801 / FU-777 are the decisions.** `--brand-secondary` measured **1.10:1** on Cherry-Cola-Dark; `--text-on-primary` fails the D-002 floor in three themes; `--brand-primary` fails the same ink test. These want an options board and your eye, not a blind swap.
9. 🟡 **FU-872 — `load_recipe_cookability` returns confidently wrong numbers depending on what ran before it.** The eager include can't populate `StockItem.stock_level` (`lazy="noload"`) once those rows are in the session, so every ingredient reads unstocked — it made Kitchen health announce *"none of your 6 planned meals can be cooked"* beside a card offering to cook five. Fixed **only by ordering** in `_gather_inputs`, which any future edit can silently undo (**R-082/ADR-079**). Four recipe surfaces read this helper. **Do this before anything else touches it.** Its sibling **FU-873** is the same trap sitting armed in `frequently_added.py`.
10. 🟡 **FU-878 — `PATCH /meal-plans` re-mints every forward entry id on every save.** The UI symptom (a menu destroying itself mid-edit) is fixed at the rendering layer, but the write shape still churns ids, which makes any future id-keyed UI or client cache quietly wrong. Converting replace-the-week to match-and-update is a real refactor with its own defect history — worth scheduling deliberately, not folding into a UI batch.
11. 🟡 **FU-855 — the ADR-073 cost narrowing.** "2 tins" of a `400 g` product with no `pack_count` now reads *unpriced* where it used to guess. Deliberate, but it's a loss of coverage — walk a costed recipe and say whether it reads acceptably. Its other half is **FU-856** (`pack_count` isn't accepted by the products API at all).
12. 🟡 **FU-758 — the four `.claude/launch.json` verify configs still point at `:5170` with `DORA_ALLOW_DESTRUCTIVE=true`**, next to the proven-safe 5171 pair. One mis-launch away from the real DB.

**Running-app checks**

13. 🟢 **The 09-05 meal-planner batch, none of which you've seen.** The rail's new disclosure header and count circles, the phone day's per-slot sections (and that the retired "Which slot?" sheet is genuinely unmissed), the servings menu surviving repeated taps on a *real* touch device, and the cost figures — week total, per-day, per-card — reading sensibly on a partly-unpriceable week (`"$42.87 (5/7)"`). Plus the Cheapest ordering — settled as the answer to the cost ask (FU-880 resolved), so this is a "does it work in use" look rather than an open question.
14. 🟢 **The 09-05 tap-target sweep on a real phone.** Sizes were *measured* in both contexts, so the mechanism is proven; what isn't is how the **level chip** looks at 44px — it is a colour block, so it gained visual weight, not just hit area, and it is the one change in the sweep that alters a signed-off surface's appearance. Also owed: cookbook cost with money on *and* off, the sort snapping back to Name when money is switched off, and About's rebuilt stats block.
15. 🟢 **The dashboard's two unwalkable halves.** The 09-04 walk ran on the dense seed, which has batch cooking **off** and money + products **on** — so the batch-household "Next to cook" (`needs_cooking || cook_fresh`), the manual-reconcile `plan_adherence` path, the Shopping-lists card with money off and Price-drops disappearing with products off (**FU-868**) were reasoned about, never seen. The batch-yield `serves N` agreeing with what cook mode opens at is in the same bucket — the seed can't configure it.
16. 🟢 **Nothing of the `cook_fresh` batch is walked at all** — the per-entry ⋮ toggle on desktop chip and mobile card, the week strip's neutral "N fresh" cell, a fresh meal surviving a plan edit, the auto-drain sweep leaving the pool alone, `?for=` landing on 6 from a linked cook, and 375px on all of it.
17. 🟢 **The 09-03 batches still unwalked:** the admin-settings sweep end to end (the money and ingestion flags change what *other* surfaces show; both retired routes should redirect), and the four dark themes now painting their real page colour for the first time — Blueberry, Cherry Cola, Sourdough, Dragonfruit — plus 375px on the rebuilt Salt & Pepper and Lemon Tart Dark.
18. 🟢 **The three new voice commands need a mic** ("ingredients", "tools", and that "stop" no longer exits). Bundle with **FU-722** (Sous Chef clipping the start of sentences — *open the "?" popover first and note which engine is speaking*; that one fact decides which of the three shipped fixes was even relevant), **FU-751** (Firefox TTS) and **FU-853** (the timer chime is blocked by the app's own CSP — a silent-by-config and a silent-by-bug chime look identical in code, so listen).
19. 🟢 **Confirm the companion's Save button in a browser** — batch B fixed it (FU-881/882 resolved: push now carries the offers you picked, verified end-to-end over HTTP), but the SPA half was never walked, since it needs live merchant scraping. Steps are in `DORA_VERIFY.md` under "Companion".
20. 🟢 **The CHECK-constraint naming bug found during C2** — `ck_%(table_name)s_%(constraint_name)s` is re-applied on every batch rebuild, so this repo has a constraint literally named `ck_ShoppingListLine_ck_ShoppingListLine_ck_ShoppingListLine_ck_ShoppingListLine_ck_…`. C2 normalised that one and works around it by reflecting the name, but **the bug will recur** on the next batch rebuild of any table with a named CHECK. Worth a real fix in the naming convention / `env.py`.
21. 🟢 **Products-as-overlay has never been browser-verified — any of it.** Phases 0–E are backend-green and eyes-free. FU-214 (now narrowed to a browser pass over four already-look-fixed bullets) and the FU-210 tail are the entry points. The dev seed *does* build products with offer history, so the "waits for real data" blocker no longer applies.
22. 🟢 **Reported defects still awaiting a confirm:** FU-710 (barcode register 404s on your install), FU-769 (changing a line's store doesn't move it between store groups), FU-715 (needs-attention filter, specifically after a bulk action), FU-736 (ingredient free-text flow), FU-797 (Firefox-mobile login), FU-729/739 (run and receipt faces have never been walked on a real phone).

---

## Where the detail lives

- **`DORA_WORKLOG.md`** — per-session handoff narrative (what ran, decisions, what's next).
- **`CHANGELOG.md`** — product/code changes that shipped.
- **`DORA_FOLLOWUPS.md`** — the full ~208-item open backlog (this dashboard shows only the top).
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

21. **✅ Security thread closed.** `AUTH_ASSISTANT_SECURITY_FINDINGS` is now a triaged standing register — the HIGH CSRF + MEDIUM email-change were fixed under FU-197 (2026-06-30); the 8 residual Medium/Low findings went to FU-515 (resolved); the orphan audit-follow-up FU-447 was reconciled + closed. A.5/A.6/A.7 are accepted risks (A.6 → Phase-4). Nothing open.
22. **🕸 Stale "no code yet" / "designed-not-built" headers on ~15 shipped docs (FU-445).** Bodies are accurate records; only the top status line lies (e.g. IMPL_PLAN_ALERTS, IMPL_PLAN_MEAL_RECONCILE). Judge by this register, not the header.
23. **🕸 `docs/00_DOC_GRAPH.md` is a retired stub (FU-428).** Superseded by this doc + the CLAUDE.md anti-drift rule.
24. **Backlog right-sized.** The old dashboard cited "~60 open items"; the ledger actually holds **17**. Most of the prior attention list had long since moved to `_RESOLVED`.

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
| DESIGN_REMEDIATION_PLAN | Design backlog | 🟡 active | Action the 2026-07-18 UX/design audit (DR-1…16) | DR-1/1b/2/3/4/5/6/8/10/11 done (10=owner leave-as-is), DR-7 ➗ (FU-624), DR-9 ➗ (FU-631), DR-14 ➗ (FU-632), DR-15 ➗ (FU-694); remaining: DR-13/16 + the **Alerts half** of DR-12 (its meal-plans mini-month was overruled by D7 and built as a month grid 2026-08-30) |
| DORA_ASSISTANT_ARCHITECTURE_PROPOSAL | Proposal | ➗ carve-outs | Unify assistant capability model + LLM config | §2.2 registry deliberately not built; §7 multi-provider shipped |
| IMPL_PLAN_ALERTS | Impl plan | ✅ done | Alerts control-centre (C-9) | Digest+push+prefs shipped; header stale |
| IMPL_PLAN_AUTH_SHELL | Impl plan | ✅ done | Extract shared AuthShell + AuthButton (C-19) | `AuthShell.vue`/`AuthButton.vue` exist |
| IMPL_PLAN_CART_BUTTON | Impl plan | ✅ done | Unify add-to-list into one cart control (C-7) | `AddToListButton` in use |
| IMPL_PLAN_CONFIG_AND_OPTINS | Impl plan | ✅ done | Feature-flag/opt-in spine (C-cross) | `useFeatureFlags`/health flags shipped |
| IMPL_PLAN_COOKBOOK | Impl plan | ✅ done | Recipe domain rebuild (C-4) | Structured steps/tags shipped |
| IMPL_PLAN_COOK_MODE | Impl plan | ✅ done | Cook-mode rebuild (C-3) | `RecipeCookMode.vue` live |
| IMPL_PLAN_DASHBOARD_REBUILD | Rebuild brief | ✅ done | Rebuild DashboardPage around savings | Phases 0-7 shipped; the **two commitments the 2026-09-02 re-audit found unmet are now both met**: §2.2's card census is encoded at 14 registered / 11 default-on with `dashboardCards.spec.ts` holding it (FU-830), and §6's DoD "thin composition over `components/dashboard/*` — the 1964-line monolith is gone" closed for real at chunk 5 — all 14 card bodies extracted, page 3,258 → 1,888 lines (FU-829, R-072/ADR-069) |
| IMPL_PLAN_ENV_TO_APPSETTING | Impl plan | ✅ done | Promote 12 env vars to AppSetting (FU-333B) | Header "SHIPPED 2026-07-05/06" |
| IMPL_PLAN_ERROR_HANDLING | Impl plan | ➗ carve-outs | App-wide error-message polish (FU-099) | `apiErrorHandler.ts` live; full 166-catch sweep unconfirmed |
| IMPL_PLAN_HELP_CHIPS | Impl plan | ✅ done | Add (?) hover-help chips (FU-044) | `help_outline` tooltip pattern across pages |
| IMPL_PLAN_INGESTION_API | Impl plan | ➗ carve-outs | Ingestion `/api/ingest` + Your-Prices (C-10) | Built; browser-verify pending |
| IMPL_PLAN_MEAL_PLANS | Impl plan | ✅ done | Build meal-plans surface (C-2) | Rebuild doc: all F1–F49 shipped |
| IMPL_PLAN_MEAL_PLANS_REBUILD | Critique+rebuild | ✅ done | Re-critique + rebuild the C-2 result | `useMealPlanner.ts` + components exist |
| IMPL_PLAN_MEAL_RECONCILE | Impl plan | 🟡 in-progress | Manual meal-plan reconcile (FU-317) | Chunks 1–5 shipped; Chunk 6 pending; header stale |
| IMPL_PLAN_ONBOARDING | Impl plan | ✅ done | Onboarding redesign + de-persona (C-5/FU-210) | Onboarding pages live |
| IMPL_PLAN_PRODUCTS_AS_OVERLAY | Impl plan | ➗ carve-outs | Chunk detail for products overlay | Phases 0–E done; Phase-F tail superseded by IMPL_PLAN_PRODUCTS_PROGRAM |
| IMPL_PLAN_PRODUCTS_PROGRAM | Impl plan | 🔵 designed-not-built | Governing doc for the reopened products area across Dora + companion: data-flow contract PF-1..PF-9, batches A–G + C2, decisions D-1..D-11, feedback coverage MP/PH | Written 2026-09-06, owner-agreed, no code |
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
| BRIEF_BUY_VERDICT_PLAN_AXIS | Design brief (2026-08-28) | 🔴 needs-a-decision | A fourth `plan` axis feeding the buy verdict from planned meals | No code; blocked on FU-774 (collides with the 2026-08-17 "shortfall is unchanged" directive). FU-775/776 downstream |
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
| PROPOSAL_SHOPPING_LIST_UX_V2 | Proposal | ➗ superseded in part | Single-page shopping experience | "BUILT 2026-06-12"; the rail + status enum survive, but its toolbar, header cluster and row anatomy are replaced by the 2026-08-23 three-face redesign (worklog) and now by v3's overview card |
| PROPOSAL_SHOPPING_LIST_UX_V3 | Proposal | ✅ done | The overview card — replaces the detail page's header block, TripCard, plan StoreSpendCard, order-by bar and shop-mode sticky footer with one collapsible card across all three faces; toolbar recomposition (Export splits, shop date arrives, New list leaves for the rail, lifecycle actions leave for the card) | Written **and built** 2026-08-29 from an 11-bullet owner batch; all 11 decisions closed in §7, three build deviations in §10. New shared `CollapsibleCard.vue` (adopted by `StoreSpendCard` + `PantryBeliefCard`), new `ShoppingListOverviewCard.vue`, `TripCard.vue` deleted, sticky footer deleted, "Order by" deduped across faces, rename became a dialog on every width. Three reported bugs fixed (page-blanking `load()` on every list-level edit, chip vanishing while renaming, footer overlap). Driven live on all three faces at 1280/375. FU-783 resolved, FU-784 narrowed, **FU-785 new** (pre-existing: a benign ResizeObserver warning fires an "Oops" toast *and* `executeRollbacks()`) |
| PROPOSAL_SHOPPING_LIST_UX_V4 | Proposal | ✅ done | The surface pass — v3's information architecture is kept intact; this changes containers, grid, type scale and control density. Direction B (two-tier surface + row diet) for plan/run, direction A (document) for the receipt face; direction C (dense table) deferred as an evolution of the same row. **Chunk 0 is a blocking behavioural baseline** (`05_investigations/SHOPPING_LIST_BASELINE.md`) — every affordance, flag combination and edge state catalogued before any markup changes, so the cutover is auditable rather than assumed | Written 2026-08-31 from a 12-bullet owner batch (W1–W12). Findings: the surface uses `--radius-md` + a flat border everywhere and **zero** elevation tokens while `--radius-lg/xl/2xl`, `--elevation-card` and `--hero-gradient` sit unused; the row has **no grid** (flex + four competing `min-width`s), which is the mechanical cause of the reported misalignment; savings is **offer-only** (`_line_savings` returns 0 without an offer carrying `price_was`) while prices resolve actual→historic, so the two have different audiences; **both `money` and `products` default to `False`**, making the no-money tier the design baseline. Four open decisions; **7.1 and 7.2 closed 2026-08-31 by owner call** — quantity is a tile at rest that becomes a stepper on hover/focus, and the `--hero-gradient` band runs on plan+run but the receipt face is **flat**, which promotes the band from decoration to a state channel (gradient = still happening, flat paper = finished record). 7.3/7.4 resolve out of chunk 0. **Chunk 0 complete** — `05_investigations/SHOPPING_LIST_BASELINE.md`, 79 affordances catalogued from source (toolbar, both picker renderings, page furniture, overview card, three row variants, eight dialogs, keyboard/DnD/responsive, thirteen edge states, T0/T1/T2 matrix); destination/decision columns fill during chunks 1-3 and **chunk 4 is blocked until none read TBD**. Two findings amended the proposal: the mockups omitted six live page surfaces entirely (trim banner + preview, suggestions strip, deferred section, receipts strip, danger footer), and the "nine always-visible affordances" claim was an overstatement (reorder is already gated on manual sort; most of the rest is data-conditional). **Chunk 1 (the row) built and driven live** — new `ShoppingListPlanRow.vue`, `q-item` dropped for a CSS grid, always-on set cut to name/quantity/money, store select + three chip variants folded into one caption line, reorder arrows joined delete, name raised above the price. Alignment verified *numerically* (one distinct x per column across six rows) and the no-reflow constraint likewise (money x and row height identical across a hover). **Three defects the static suites missed and the running-app gate caught**: an import path `vue-tsc`+`eslint` both passed but the bundler rejected; a 375px overlap from keying the grip's hiding to `hover:none` while the column count keyed to `max-width`; and 483px phone rows from an auto-sized money column starved by its own caption. Baseline §5.1 filled — 16/16 kept-or-moved, **nothing cut**. **Chunk 2 (card + page furniture) built and driven live** on all three faces, in pesto-dark and at 375px. Card on `--radius-xl` + `--elevation-card`, headline off a magic `1.9rem` onto `--font-size-3xl`, `--hero-gradient` band on plan+run and **flat on the receipt** so the surface encodes state. **The §1.6 dark-theme worry dissolved**: `--surface-component` is already lighter than the page in dark and darker than white in light, so one declaration is correct both ways. **§7.3 closed** — the money-off headline is per-face (items-to-buy / left-to-pick / items-bought) instead of one flat count, which matters because money is the *default* install. **New C19** closes the §1.5 concealment: the total now carries `~` + "n items with no price yet" instead of burying it in the disclosure. Order-by is `BaseSegmented pill`, reusing the owner's 2026-08-31 shape (D-015). All ten furniture panels share one `.sl-panel`. Baseline §3+§4 filled; **still nothing CUT anywhere**. **Chunk 3 (receipt face) built and driven live** — the done list is a document: multiplier, name, dotted leader, amount, with `TOTAL` under the itemisation above a dashed rule and **no gradient band** (`bandIsGradient: false` against the other two faces' `true`). The §4.3 constraint was met by extracting the shared skeleton to **`src/css/shoppingRow.scss`** — grid shell, name/caption/money type scale, inset divider — consumed by both faces, rather than a `face` prop putting two mutually-exclusive control sets behind `v-if` in one component (R-001); this is the third application of the `dnd.scss`/`subbar.scss` precedent, so **no new ADR**. **A T0 carve-out came out of the running app**: with money off (the default install) the leader ran to the sheet edge and read as a number that failed to load — it is now suppressed when there is nothing at the end of it. The sheet's own header was removed as verbatim duplication of the overview card 40px above (E2 `moved`, not cut — count and date still on the card, total and unpriced-count in the footer). Plan face re-verified after the CSS extraction (single x per column, zero hover reflow). Baseline §5.3 filled; **still nothing CUT anywhere across chunks 1-3**. **Chunk 4 — the blocking cutover audit — PASSED 2026-09-01.** All 79 affordances carry a decision; **nothing was CUT across chunks 1-4**, so no owner sign-off is outstanding. §1/§2/§6/§5.2 were untouched by the rebuild and confirmed rendering live rather than assumed from a diff; all thirteen edge states rendered (five from seeded data, eight by rewriting the API payload in flight, stated as such). Three catches nothing else would have made: **P8 never existed** (the census recorded a picker kebab removed three days before it was written), **chunk 1 orphaned 165 lines of dead CSS** (`ShoppingListDetail.vue` 3,273 → 3,108 — neither `vue-tsc` nor `eslint` can see an unused class), and **the shop face is now the odd one out**, still `bordered` + `--radius-md` + `q-item` while the other two faces moved on. **K2 resolved**: `space`/`u` are guarded on `status !== 'shopping'` and verified inert on a draft — but advertised in the cheatsheet on every face (FU-808). **Chunk 5 closed FU-807 the same day** (owner: *"consistency matters"*), completing §4's "direction B for plan/run". Root cause was structural: `.sl-panel` / `.sl-list` / `.sl-section*` lived in the page's **scoped** block, so the run face *could not reach them* — a shared visual language in a page's scoped styles silently excludes every child component. They moved into the shared sheet (renamed `shoppingRow.scss` → `shoppingList.scss`), and a new `ShoppingListRunRow.vue` joined the plan and receipt rows on one skeleton. The row is a `role="button"` div (it contains the price button, and a button inside a button is invalid), so Enter/Space were wired explicitly and **re-verified live** — `q-item clickable` had been providing them for free. All three faces now measure the same slab radius, elevation and 18.5625px name; tick verified by click and by Enter; the price button opens the sheet without ticking. **v4 is built end to end.** Owed: `DORA_VERIFY` D8 (receipt lightbox — needs an attachment the seed doesn't ship); open FU-808, FU-805 |
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

## 05_investigations — reports (22)

| Doc | Type | State | Purpose/Notes | Evidence |
|---|---|---|---|---|
| DASHBOARD_PAGE_REVIEW | PO+eng review | ✅ all 6 chunks built | The dashboard as a **drift audit**, not a design pass — the surface was designed properly (`IMPL_PLAN_DASHBOARD_REBUILD`, 7 phases) and it is the plan's *structural* commitments that lapsed: curated 8-card default → 13 of 17; DoD "monolith is gone" → 3,258 lines. Also re-opens feedback D2 (dark mode) and L254 (money opt-in) | Written 2026-09-02; 13 FUs (817-829); all 8 §8 decisions closed. All 6 chunks shipped 2026-09-02 — both structural commitments met and the design-rule sweep done (FU-828/829/830/840 resolved). Spin-offs still open: FU-835/837/838/839/841 |
| REPORTS_PAGE_REVIEW | PO+eng review | 🟡 active/in-progress | `/reports` first-ever review — stands in for the empty REPORTS feedback section. **Chunks 1–4 of §7 built and driven live 2026-09-02**; only chunk 5 (the design sweep) remains | Written 2026-09-02; 8 FUs (809-816). §7 carries a live build-status block. FU-809/810/811/812 answered by the owner; FU-816/815/813/814/833 **resolved**; FU-843 item 2 closed, item 1 downgraded; FU-844/845/846/847 spun off; FU-703 D3’s trend half built. One item corrected by `DASHBOARD_PAGE_REVIEW` §3.10: the `themeTick` bug originated on the dashboard, so FU-824 superseded half of FU-814 |
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
