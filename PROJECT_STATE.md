# Dashy Dora — Project State

**Last reviewed: 2026-09-02.** Milestone-progress front door — phase board,
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

Phases **0** and **2** are effectively done, **Phase 1** sits at ~95% with only
meal-reconcile Chunk 6 left to build, and **Phase 3 (champion)** is fully built at
~95% pending device walks; **Phase 4 (open-source release) remains ~0%**. The work
is a sustained **owner-feedback polish stream**, and the last three units all
landed on the shopping list and the recipe surfaces: the 21-item shopping-list
batch closed on 08-28 (planning split from recording via `planned_store_id`,
R-063/ADR-060), then **UX-v3 collapsed the page's five stacked top blocks into one
overview card** and deleted the mid-shop sticky footer outright, then a six-item
recipe-view batch fixed the bug that mattered most — **a recipe with ingredients
linked to a step could not be saved at all**, and because the page re-sends those
links on every save, one linked step made *every* later edit to that recipe fail
(an ORM-write/Core-read autoflush seam, now **R-064 / ADR-061**). The recent
pattern is that reported "design" complaints keep having real bugs underneath
them: a filter width justified by a label deleted a week earlier, a unit picker
that filtered its own vocabulary down to one entry and then stored the option
object, a `load()` that blanked the page on every list-level edit. Suites are at
their highest counts — backend **2176 passed** / 1 skipped / 1 xfailed, frontend
**571 vitest**, `vue-tsc` + `eslint src/` clean — with the four pre-existing
buy-verdict e2e failures outstanding (FU-762). The dominant debt is unchanged and
still growing: a large stacked body of shipped UI has never been seen in a
browser, though the last three units were each driven live against a scratch
stack, so the newest work is the exception rather than the rule. **2026-09-01 added a second cook-mode
batch** — eleven owner items, and the pattern held again: the "is the timer
guessing?" complaint was a real design defect (a regex over step prose driving a
countdown, indistinguishable from one the cook set) and the "modal looks terrible"
complaint was two controls saying the same thing in different vocabularies plus a
default that quietly wrote a stock drop onto every ingredient of every finished
cook. Both fixed; **R-068 / ADR-065** promoted from the first. **A third 2026-09-01 batch** took three cross-cutting items: the brand accent now has an ink-strength sibling token (`--accent-ink`) because the fill tone measured 1.25–2.04:1 as text in every light theme — which is why the stock-item tabs were unreadable — plus one glyph (the mascot burger) for every "Dora thinks / Dora suggests" surface, and About back at the foot of Settings. **R-069 / ADR-066** promoted from the first; the same measurement says `--brand-primary` fails the identical test (FU-801), but it is consumed through Quasar's own `color="primary"` machinery, so it is its own unit. **As of
2026-08-30 the active stream is the meal planner**, which was parked behind
eight owner decisions: all eight are now answered and **all three of its units are
built and driven live** — the app-shell conversion, the rail rebuild and the
month-grid calendar. **A 21-item owner batch followed on 2026-09-01** and held the
pattern again: the "which slot? doesn't honour settings" complaint and the
"could not update the plan" errors were the *same* seam seen from two ends (a
store cached a vocabulary a settings page wrote behind it), and underneath that
sat a second, worse bug — deleting a meal slot is documented as preserving
existing labels, but the update endpoints then refused to accept those preserved
labels back, so one entry on a deleted slot made the whole week unsaveable
(**R-070 / ADR-067**). The printed week had its slot columns hardcoded too. What the brief still owes is its own §11 ledger debt: the
`COVERAGE_GAPS.md` flip for the 13 bullets `IMPL_PLAN_MEAL_PLANS_REBUILD.md`
§13 re-graded 🟡. **2026-08-31 added a second dev dataset**, `dense` (now the
default for interactive boots; `bulk` stays for load testing and is what the e2e
suite uses). It is aimed squarely at the browser-verify debt above: no generated
filler, every row placed to put some surface into a state worth walking —
including the structured and image cook-mode faces, which had no fixture in
either seed until now (FU-754, resolved). **Later the same day a six-item recipe-view
batch landed** and kept the pattern going: two of the six reported "design"
complaints had real defects under them — a page that scrolled sideways once you
added tools to a free-text method (an app-wide `BaseSelect` rule written for
single-value fields leaking onto the chip ones), and a cart button baseline-pinned
to the first line of a wrapping ingredient row. The missing and swappable chips
merged into one three-state chip, and a colour pass caught it nearly shipping at
2.1:1 contrast. One report — a flickering line beside the login mascot in Firefox
on Android — is **mitigated but not reproduced** on this box and needs the
reporting phone (FU-797). **2026-09-01 ran two more owner batches over the same
two surfaces** — four cookbook chip/tooltip items, then five recipe-view clarity
items — and both were driven live end to end. Their shared theme is that the app
kept *showing* numbers where it owed an *explanation*: the batch pool's "0 free
of 1" never mentioned that the meal plan had claimed the meal, the cook-mode
confirm counted missing ingredients without naming them, and the cost bars
measured share-of-the-dearest-line while reading as share-of-total. Two
`colours.scss` chip classes came out of the pair (`--neutral`, then `--tint`),
promoting **R-066 / ADR-063**: a chip's look is a shared class, never
per-component CSS. The now-familiar pattern held once more — measuring the two
chips side by side exposed a real defect (a two-word label wrapping inside its
own tint, 37px beside a 28px neighbour) that neither report had named.

---

## Phase board

| Phase | Scope | Status | Remaining |
|---|---|---|---|
| **0 — Foundations** | Theme/buttons/modals/filters/text-size/renames + bug clusters + config/opt-ins | ✅ ~99% | Residual polish only. Live token debt: FU-674 (`--text-on-primary` fails D-002 in three themes), FU-709 (dark themes' `--surface-page` never paints), FU-764 (no lint gate on undefined custom properties — four more files render fallbacks and never follow the theme), FU-777 (`ExpiringChip` numbered Quasar palette class). |
| **1 — Close the loop** | Shopping lists, cook mode, stock overview, cookbook, suggestions, costing, stocktake | ➗ ~95% | **Nothing left to build except meal-reconcile Chunk 6** (settings row/copy). Everything else is browser-verify: stock overview (three batches, 08-20/21/22), stocktake's three-phase runner, cookbook batch 3, the recipe page's older stacked batches (08-24 and the 08-20 parity pass — the 08-27/08-29 batches were driven live), the buy-verdict money gate, and the `planned_store_id` round trip (blocked, not skipped). |
| **2 — Ingestion API + companion** | `/api/ingest` seam; standalone companion; Merchant→Store rename | ✅ done (backend-green) | Phase-F tail only: product-surface browser-verify (FU-214), L197 hard-delete decision, L205/206 bulk-select unbuilt, FU-210 tail browser pass. |
| **3 — Champion** | Zero-Input Pantry, buy/wait oracles, barcode-add, Dora Score, culinary memory, native app | ➗ ~95% (verify pending) | P8-01..P8-10 fully built. Browser/device-verify of P8-07/08/09/10 remains; native FCM push parked until SaaS (FU-465). |
| **4 — Open-source release** (was Commercialize) | README/showcase + release process + support channel (Postgres done) | ⚪ ~0% | **Not sold — donation/OSS/MIT, all free.** FU-406 (README+release), FU-608 (donation/OSS infra), FU-557 (support channel). Ops/CI (FU-405) gates FU-520/FU-404/FU-721. SaaS parked. |

---

## Major workstreams

| Workstream | Status | Where it's at | Governing doc |
|---|---|---|---|
| **Cook mode** | ➗ | **Second batch (eleven items) landed 2026-09-01, driven live end to end.** The headline is a schema change: the timer card was a **regex over the step's text** for all three faces, which produces a 2880-minute countdown off a pizza dough's "48 hours in the fridge" and presents it beside a timer you set. A structured step now records `RecipeStep.timer_minutes` (migration `a7c3f1e9b482`, editor toggle mirroring the `hint` two-state); the sniff survives for free-text/photo — the payloads with nowhere to record it — and now captions itself "from this step's wording". **R-068 / ADR-065**: *record the fact, don't parse it back out of prose; if you must infer, say so.* The other ten: the three panels (ingredients / tools / steps) collapsed to one header + card + row treatment with the app's real icons and no "N total" counts; tool rows gained the ingredient rows' highlight; the substitute button now renders only on low/out ingredients and a picked substitute keeps its ratio + note on screen; the **finish modal was rebuilt** — a row carried an *action* control, a *destination* select and a colour chip all saying one thing, and is now the household's levels as one segmented control with the current level preselected, so "unchanged" is the default (it used to write a level drop onto every ingredient of every recipe you finished); the meals field is `batchEnabled`-gated, reworded off "pool", and a ± stepper; the progress bar's segments are jump targets with a 44px hit pad. Seed gap closed on the way: the dense dataset had **no substitute ratios at all**, so that half of the swap hint had no fixture. Earlier — **rebuilt 2026-08-28 and driven live at both viewports.** The header was rebuilt for mobile eight days earlier and the owner filed the same complaint again, wider — because the layout was never the problem: `.cook-header`, `.cook-header__identity` and `.cook-header__cooking-for` all declared `gap: var(--space-sm)`, and **that token has never existed** (Dora's scale is `--space-1..12`), so every gap was zero. Header is now three stacked bands and the controls never share a line with the title at any width. Sous Chef is a labelled button above `lt.sm` and a 44px icon below (D-004, over BaseButton's 36px default); the "what can I say?" popover only renders when something can hear you; **Cooking for** is a bordered ±44px stepper with typing deliberately dropped (a keyboard over the hob). The step indicator + image counter became one `CookStepProgress.vue` (R-001) — tinted display-size badge beside a per-step segment track, falling back to a fill bar past 14 steps. `RecipeCookModeImageView` went from scroll-everything to a pager with a genuine 2.5× magnify. Two unreported bugs found: **image mode could never finish a cook** (`openFinish()` was only reachable from the step view's nav row, so photo cooks decremented no stock and logged no meals), and `icon-right` used raw Material names on an MDI set so the Next arrow rendered nothing. Owed: FU-765 (never re-fetches on a recipe-id change — deliberately unfixed, wants `:key` not a watcher), FU-763 (`text-h4` step text on a phone, owner's call), and two device-only checks | worklog 2026-08-28 · `RecipeCookMode.vue` |
| **Nutrition rating schemes** | ➗ | **Two schemes, one picker, built 08-27 — no browser pass.** The HSR shipped 08-27 as a full FSANZ transcription (Calculator + Style Guide v8.1) and was verified live on hand-seeded foods; **Nutri-Score** followed, transcribed from Santé publique France's V11 FAQ *and* the official workbook, with every threshold cross-checked between them and the workbook's three worked examples as golden vectors. The real trap was **FVL ≠ FVNL** — the 2023 update moved nuts and seeds out of the positive numerator while leaving them in the denominator, so `food_categories` now carries `is_fvl_category` beside `is_fvnl_category` and the rollup reports both percentages; feeding either scheme the other's numerator silently misgrades food. `health_star_rating_enabled` became `nutrition_rating_scheme` (closed-set string, R-010 carve-out, new migration `a7f4c2e9b1d6` rather than amending the committed one). **`none` by default everywhere including Australia** — Dora doesn't pick a nutritional authority for a household. Three published Nutri-Score rules are documented-not-implemented in the module docstring; the badge is drawn in-house (the logo is a registered collective mark) but reproduces the published five-colour scale as a documented D-002 carve-out. `RecipeRatingChip` collapsed what would have been four copies of the rating block. Open: FU-750, FU-748, FU-749, FU-760, FU-761, FU-746 | `dora_api/domain/nutri_score.py` · `health_star_rating.py` |
| **Recipe page** | ➗ | **Five batches deep and, since 08-26, the only page — the 2,727-line original is deleted.** The 08-29 batch (six items) was **driven live** and two of its items turned out to be one bug: **a recipe with ingredients linked to a step could not be saved at all**, and because the page re-sends those links on every save, one linked step made *every* later edit to that recipe fail whatever you changed. Cause was a seam, not a typo — `update_recipe` mutates ingredients through the ORM and the step-link check reads with a Core `select()`, which does not autoflush (**R-064 / ADR-061**; `create_recipe` had flushed for this reason since FU-456). The unit picker had two more, both proven in the browser: `fill-input` re-filtered the vocabulary to the row's current unit (empty list, since `loaf` isn't in the table), and a missing `emit-value`/`map-options` stored the option *object* and tore the dialog down. Also: one shared `RecipeInfoCard` now dresses all three details drawers including the nutrition one (R-001), and the cook-now sub-line is gone. The 08-27 batch (26 items) shipped driven live: R-055 block-editing finally reached the ingredient rail and the method, `RecipeStructuredMethod.vue` renders both faces off one `editing` prop (three components deleted — ADR-052), step↔ingredient highlighting became bidirectional and tappable (the hover-only version was unreachable on a phone), tools are derived server-side, and the image-steps bug's real cause was the viewer reading `recipe.step_images` (the last-*loaded* list). Owed: the browser walk across the older stacked `DORA_VERIFY` sections (08-24 and the 08-20 parity pass — 08-27 and 08-29 were driven live), with FU-691's off-token stylesheet sweep queued behind it. New: FU-786 (a legacy free-text unit like `loaf` can never be re-selected once changed away — a vocabulary decision). Two things can't be agent-driven — the native file picker and any Quasar dropdown (FU-737) | [PROPOSAL](docs/04_proposals/PROPOSAL_COOKBOOK.md) |
| Shopping lists (three-face redesign) | ➗ | Three faces built; price comes from **what you last paid**, server-resolved with provenance (R-053/054). **The 21-item owner batch is complete — all three sub-batches shipped 2026-08-28**, batches 1 and 2 driven live end to end, batch 3 driven live except one blocked check. **Batch 1: the draft face was impersonating shop mode** — tick boxes, a ring measuring them, a price editor, a bulk bar. All gone; a draft shows a count. Picked items stopped vanishing (**Picked (N)** section, tap to put back), substitutes left the surface (INV-8 closed), and the finish dialog now **forces** a decision on leftovers. Two bugs under the owner's questions: the draft price button was the **one** ungated money surface, and **the budget counted unticked lines as spent** — $60 shop + $40 leftovers reported $100, fed to the trim optimiser (**R-061/ADR-058**; four more surfaces infer the same, FU-768). The "white store colour" was a palette bug: swatches are pale tints meant to sit *behind* a placeholder letter, so as a bar segment or 8px dot they read as white — they now carry a saturated `fill`. **Batch 2: the picker was carrying jobs that weren't picking.** Grew forever (29 rows, 26 demo receipts) → drafts + shopping + 5 most-recent done, rest behind a searchable **See older**, 29 → 8. Vanished mid-shop for a differently-shaped "Switch list" button → now always present, producing **D-023** (*a persistent control keeps its shape and its place across modes*). Kebab gone, **copy-to-new cut entirely** (Save as template is the same idea, better named). Name renders once on mobile; the header absorbed the shop day, fixing an unfiled gap — it lived on a plan-face-only card, so **a list you were actively shopping never showed which day it was for**. **Batch 3: planning and recording stopped sharing a field.** `purchased_store_id` was the only writable store on the plan face, so "get this at Aldi this week" and "I got it at Aldi" were one edit — and it *worked*, being rung 1 of the ladder, which is why it survived. New `planned_store_id` (migration `b2d9f4a7c3e1`), chained `usual → planned → purchased` as defaults never write-backs, no backfill — **R-063/ADR-060**. The five-rung ladder moved out of an inline if/elif into `_line_price.resolve_store_id` beside the money ladder, pinned by a mutation-checked `test_store_ladder.py`. Draft prices became read-only estimates; the shop sheet became a real line editor (price + quantity + store); Log price added for something *not* on the list. Two same-session follow-ups: the picker flipped to **newest-first** (oldest-first put a wall of history above the only lists you can act on) and lost its full-height scroller so **See older** sits under the lists rather than at the floor of an empty column — which broke name truncation until the row was made to own it (`q-item` measured 433px inside a 300px rail). And the spend bar's **"No store set"** slice a floor width (it was 0% and vanishing while still listed as a chip) and a **hatched** themed grey — a flat grey measured 1.02:1 against a neighbouring segment in Cherry Cola Dark, and no grey can be guaranteed to separate from logo-derived brand colours, so the distinction is texture (D-001). **Owed: the `planned_store_id` round trip** — blocked, not skipped: the scratch backend was serving pre-batch code and Dora hard-codes the reloader off, with both scratch pairings held by parallel sessions. Also owed: FU-739, FU-729 (device walk), FU-740, FU-757, FU-766..769, **FU-780** (page is 3,784 lines — R-001, extract now the row's shape has settled). **2026-08-29 — UX-v3 rebuilt the page's top section**: five stacked blocks (header cluster, trip card, store card, "Order by" bar, mid-shop sticky footer) collapsed into **one overview card** across all three faces, with the figure each face actually wants (estimated cost / **remaining** spend + ring / spent) and everything you ask once behind a chevron — including savings on the receipt, which existed nowhere after the shop. The sticky footer was **deleted**, not slimmed: it had been floating over the last rows and the destructive footer for the whole scroll, with the mascot on top of its CTA. Toolbar rebalanced — lifecycle actions to the card, New list to the picker, Export split, Shop day in and gone once shopping starts. "Finish & restock" → "Finish". Three reported bugs fixed, all cheap once found: `load()` blanked the page on *every* list-level edit, one `v-if` hid the status chip while renaming, and renaming shoved the layout (now a dialog, measured at `dy=0 dh=0`). Driven live on all three faces at 1280/375 | worklog 2026-08-29 |
| Meal Plans | ➗ | **A 21-item owner batch landed 2026-09-01, driven live end to end — and two of the "design" complaints had real bugs under them.** (a) Editing meal slots in Settings was invisible to the rest of the session: `mealSlotStore` cached the vocabulary while the settings page wrote straight to the api service behind it, so the planner kept offering a deleted slot until a reload, and arming it produced the owner's separate *"could not update the plan"* report. The store now owns every write — **R-062 extended** rather than a new rule, since its violation signal already covered it. (b) That was only half: with the sync fixed, the PATCH still 400'd `Invalid meal slot 'Snack'`. Deleting a slot is deliberately non-cascading (entries keep their label, there is a test, the dialog promises it) but `update_meal_plan` validated its **whole payload** against the live vocabulary while the planner resends every forward entry on each edit — so one preserved entry made the week permanently unsaveable, and the request that would have *fixed* the slot was refused for carrying it. `update_recipe` had the identical seam. **R-070 / ADR-067**: *validate new values, not whole payloads.* (c) The print-out's slot columns were a hardcoded `("Breakfast","Lunch","Dinner","Snack")` tuple, so it printed a Snack column after Snack was deleted and omitted anything added — now the `MealSlot` table (R-003). The other eighteen were the surface itself: the right rail's two ingredient lists had diverged into two answers to one question and are now one `MealPlanIngredientRow` (level as the app-standard left dot, not a right-hand chip; quantity-only caption; cart button; hover-to-highlight, which full-demand never had); the summary's display-size figure over a caption became one line that counts the **whole** week's shopping rather than only the unlisted part ("3 of 8 still to buy this week"), absorbing the "N already on a list" line and dropping a "N to cook" that was duplicated from the toolbar a few centimetres away; the three right-rail panes finally share one right edge (the calendar sat *outside* the scroller, behind a scrollbar gutter whose width is the OS's — it moved inside and went `position: sticky`); the rail is 340px (names were clamping to two lines) and lost its cook-time/kcal meta line, its "Log a cook…" button and dialog, and gained a **second filter axis** — time of day + difficulty as selects, not more chips, because the chip row is one mutually-exclusive shortlist; "Show all meal slots" left the overflow menu (it changes what you look at, everything else there acts *on* the week); past days fold when the week contains today; the phone day strip drew one dot where the month grid drew a pip per meal, now one shared `MealPlanDayPips`; and clicking a recipe with no slot armed does nothing instead of toasting an instruction that is already on screen. New: FU-802/803/804. Earlier — **unparked 2026-08-30 — all eight FU-782 decisions answered in one pass and Unit 1 (the app-shell conversion) is built and driven live** at 1024/1280/1440/375. The page was document-scroll with two `position: sticky` rails; it's now the fixed-height three-pane shell copied from `StockOverview.vue`, so the rail, the week and the calendar+shopping each scroll and the document doesn't. That killed a live bug and it's the textbook case for R-036's *never hardcode the offset* clause: `.planner-sticky` used `calc(100vh - 32px)` and accounted for neither the 64px header nor a rendered `OfflineBanner`, so **both rails hung off the bottom of the window by about a header's height** (now all three pane bottoms land at 884 in a 900 viewport). The toolbar consolidated five scattered things — three toolbar siblings, a row holding one toggle, a right-pane card wrapping one button, the status block that scrolled away, and an arrow stranded at the page floor — into two pinned rows plus a ⋮ menu. **Drag-and-drop retired** (D1): it was mouse-only, carried its payload on a module ref rather than `dataTransfer`, and would have silently stopped working below the fold once the week owned a scroller. Two owner answers went **against** the brief's recommendation and bind the next units: **D3** the rail is always collapsed on arrival and opens only on a slot selection or a click on itself (no empty-week auto-open), **D4** the page takes no title at all. One acceptance gap the brief missed: the toolbar met "≤96px at 1280" but **wrapped to 129px at 1024** (the FU-738 failure mode) — fixed with `StockOverview`'s own `compactToolbar` pattern, threshold to be re-measured in Unit 2 once the collapsed rail hands the week ~234px back. Also fixed in passing: a literal-duration D-010 violation in the week carousel and a second `65vh` viewport formula inside the picker. **Unit 2 (the rail) shipped the same day, also driven live**: the four collapsible trays became one flat list plus five filter chips, and the tray builder was deleted — its FU-578 #47 one-recipe-one-home dedupe is *superseded*, because as filters that rule is wrong (you ask for Regulars, so every regular shows) and one-active-filter prevents double-render inherently. It also closed the R-003 leak the brief flagged: the old builder selected on the server's `not_made_recently` flag but then sorted by `last_made_on` on the client. **"Dora suggests" is new** — a `GET /meal-plans/suggestions` endpoint that adds *no* domain logic, reusing the week builder's own pure ranker and its frozen reason vocabulary, shipping tokens rather than prose so the server owns *why* and the client owns the wording. The rail collapses to a 46px labelled strip under a documented D-023 carve-out whose asymmetry is the point: **the system may only ever open it, never close it.** Three unreported bugs came out of driving it — focus never reached the rail on auto-open (two stacked causes: a template ref read before the child mounted, then `QMenu` undoing it twice on close), the armed slot was never named on the week because an unused slot renders no row, and the targeted slot still wore a dashed drop-zone outline for a drag that no longer exists. **Unit 3 shipped the same day, closing the brief**: the calendar was a *week picker wearing a calendar costume* — only the week row was clickable while the day squares carried the status colour, and only Mondays showed a number — so it is now a real month grid with every date, dimmed-but-clickable neighbouring months, a filled disc for today (never a ring, which would collide with the focus ring now that days are focusable), per-meal pips, and a hover that names the actual meals instead of a status word. **Clicking a day jumps the week and scrolls to that day's card** — the payoff of the whole redesign, and only possible because Unit 1 gave the week a scroll container. One subtle bug came out of driving it: arrowing across a month boundary paged unnecessarily (a six-week grid already spills into both neighbours, so July's grid reaches 9 August), which focused a cell in the *outgoing* grid and left focus on `<body>` when it unmounted — taking the grid's key handler with it, so further arrows silently paged the *week* instead. **DR-12 is overruled for this surface and now says so, with the reasoning**; its Alerts half stays open. Open: **FU-791** (the rail row is a third copy of the list-row chrome the brief wanted extracted — deliberately not done, R-007; the 09-01 batch touched that file again without taking the extraction, see FU-802). Earlier: the 08-27 batch made the planner's one-shot "generate the week's list" the **same** `AddToListDialog` the recipe page uses — one component, four call sites, `RecipeIngredientPickerDialog` deleted — with quantities, which-meals provenance, week-wide optional aggregation (optional only if *every* contributing row was), and a "to buy" count that subtracts what's already on a list. Produced **R-057 / ADR-054**: *a replaced endpoint's response is an inventory, not a casualty list* — the old endpoint was the only place the app ever named ingredients it couldn't put on a list | [PROPOSAL](docs/04_proposals/PROPOSAL_MEAL_PLANS.md) |
| Stock Overview | ➗ | Signal consolidation code-complete, all six chunks; the row went 9 visual channels → 4, attention is one server-owned rule (`stock_attention.py`). Three feedback batches since (08-20/21/22) added the expiry-menu date header, the uncertainty ring, and **six bulk endpoints** replacing per-item request loops. **None of those three batches walked in a browser.** A fourth, small batch shipped 2026-08-28 **and was driven live**: the create-item dialog gained **Usual store** + a **Stocktake** toggle seeded from the install's new-item default (new `stocktake_policy` block on `/api/health` — the same seam as `cooking_policy`/`budget_policy`, because `/app-settings` is admin-gated), and stacked filter rows got a 2px gap applied once in the shared `FilterRow`. Open: FU-713, FU-714 (call sites that still loop) | [IMPL_PLAN](docs/04_proposals/IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md) |
| Stock-item detail | ➗ | 08-21 batch (10/12) plus the 08-24 batch: Barcodes tab became **Scanning** and absorbed the QR label, new shared `HelpHint` moved explainer prose into Help → Guides, header stopped wrapping long names. FU-648 + FU-710 both sit on this tab's critical path; both were downstream of the deploy bug and now need a redeploy plus a phone or non-localhost host | `DORA_VERIFY` → Stock: 2026-08-24 |
| Buy verdict oracle (P8-05/06) | ➗ | Regraded 08-24 to a `strength` scale (0–3) with `confidence` split out as evidence quality. **Money became a prerequisite 08-27 (R-058/ADR-055)** after an audit found the leak was wider than the visible strings — `_price_axis` was ungated, `wait` was reachable only via price signals, and `_PRICE_STRENGTH_MODIFIER` was silently price-weighting the *ranking* on installs that had opted out of money. Now gated at endpoint (403), render and settings toggle, with the user's own preference preserved underneath. Price prose moved off the server's hardcoded `$`, with a guard test. **Both the wording-verify and the money-gate verify are owed, and FU-762's four red e2e tests should be settled before commit**. A **fourth `plan` axis** is now designed but explicitly **not built** — a planned meal is arguably the strongest need evidence the oracle can hold (a stated intention with a date, where every current input is an inference), but it changes an answer, which the owner's 2026-08-17 "a planned meal's shortfall is unchanged" directive forbids. Blocked on **FU-774**; FU-775 (which flag) and FU-776 (discount items already listed) sit behind it | [PROPOSAL](docs/04_proposals/PROPOSAL_BUY_VERDICT_ORACLE.md) · [PLAN-AXIS BRIEF](docs/04_proposals/BRIEF_BUY_VERDICT_PLAN_AXIS.md) |
| Cookbook | ➗ | Chunks 1–10 plus **five** feedback batches. Batch 5 (08-29, driven live) is two consistency asks, and the width one had a fossil under it: `FilterRow` ran a second, 20px-wider track for the numeric bounds, justified by a label — "Missing ingredients ≤" — **deleted on 2026-08-20**, so the only thing holding the two tracks apart was that they existed. One 210px track now, measured across all thirteen controls with no clipped labels; the sort field keeps its own because it packs a direction chip inside itself. The rating star went 14px → 18px, matching the filter fields' own leading glyphs. Batch 3 re-ordered filters to reported use, added `Serves ≥`, deleted meal-slot names from Category (migration `c8b3e5f0a712`). **Batch 4 shipped 2026-08-28, driven live**, off a report that the health-star and kcal filters "don't work" — three causes, only one of them the filters. The dominant one: **the recipe list was a permanent session cache**. `ensureLoadedAsync` never refetched and nothing invalidated it on a stock write, so linking nutrition to a stock item and walking to the cookbook rendered the pre-edit payload — which also explains "I don't see the rating on the cards" (the chip was there since 08-27; it had no data). A recipe DTO carries five stock-derived fields, so that became **R-062 / ADR-059**. Second, both thresholds exempted any recipe under `RELIABLE_COVERAGE_RATIO`, which on a young pantry is all of them — **owner reversed it: judge the figure you displayed**, sorts included. Third, "kcal looks off" and the dead filter were the same fact: the chip rendered `:outline` exactly when the rollup was unreliable. The rating became a **score pill beside the favourite heart** — five inline stars said little and, sitting behind per-recipe chips, never landed at the same x down a grid — with the full five-star render in the hover; Nutri-Score keeps its badge. Verification needed Playwright: **the Browser pane never advances a CSS transition**, so no routed page renders in it at all. Open: FU-773 (**owner call** — re-measured 08-29 after the row lost ~100px of width: still three wrapped rows at 1280px, not the two asked for), FU-772, FU-771, FU-770, FU-760, FU-691, FU-692, FU-693 | [PROPOSAL](docs/04_proposals/PROPOSAL_COOKBOOK.md) |
| Nutrition (complex mode) | ➗ | Built end to end: install-wide mode, USDA + OFF import, 15 micronutrients, server-rendered panel, recipe rollup, cookbook badge, auto-suggest matching. Both rating schemes ride on top. Open: FU-643 (no AU/US synonym layer), FU-645, FU-646, FU-657, and **FU-750** | `AdminSystemNutritionSettings.vue` |
| Products-as-overlay | ➗ | Phases 0–E code-complete; Phase-F tail is FU-214 browser-verify + L197 hard-delete decision + L205/206 bulk-select + the FU-210 tail pass | [RUNBOOK](docs/04_proposals/PRODUCTS_OVERLAY_RUNBOOK.md) |
| Prices surface | 🔴 | Investigation confirms the owner's diagnosis: all price *reading* capability sits on the product axis at `/price-history`, which has **no nav entry**, while the everyday user gets a single-item modal with no range and no compare. Placement settled; the keep/cut call is **FU-703** and gates FU-708 | [ASSESSMENT](docs/05_investigations/PRICES_SURFACE_UX_ASSESSMENT.md) |
| ⭐ Zero-Input Pantry (P8-07) | 🟡 | Built and extended to recipes, shopping lists and the meal planner, each behind its own off-by-default opt-in (FU-653 now resolved). Server verified live; **all three client renders and the original P8-07 walk remain unseen** — the seed's two "Belief demo:" recipes make it a 30-second check | [PROPOSAL](docs/04_proposals/PROPOSAL_ZERO_INPUT_PANTRY.md) |
| Stocktake Mode | ✅ | Three-phase runner, queue least-certain-first, install-wide switch. **08-27: it finally has a dataset** — the belief fixtures were never `stocktake_alerts` enabled, so nothing could rank `confident` and the Review phase was unreachable by construction. Both seeds now span all three ranks plus a Sweep fixture; seeding that Sweep exposed a naive-vs-aware datetime 500 in `resolve_newly_swept`. The (?) now deep-links to Help → Guides → Stocktake. Verify owed; FU-700, FU-728 open | [PROPOSAL](docs/04_proposals/PROPOSAL_STOCKTAKE_MODE.md) |
| Meal reconcile | ➗ | Chunks 1–5 shipped; **Chunk 6 (settings row/copy) is the last unbuilt Phase-1 item** | [IMPL_PLAN](docs/04_proposals/IMPL_PLAN_MEAL_RECONCILE.md) |
| Alerts control centre | ✅ | Nine kinds cut to six, severity the only importance scale, email digest deleted whole. Open: FU-702, FU-701 | [PROPOSAL](docs/04_proposals/PROPOSAL_ALERTS.md) |
| Settings & config polish | 🟡 | Active owner-driven stream: nav regrouped, Admin split into five flat groups, Users rebuilt with deactivate-not-delete, Region & locale rebuilt preview-first — now the host for **Units** (metric / imperial / US, replacing the invisible `unit_pricing_locale`, R-056/ADR-053) and the rating-scheme nudge, which reads IANA timezone first and language second. **Appearance lost its "Recipe photos" toggle on 08-29** — the owner asked what it was for and the answer was "almost nothing": a preference designed to govern every recipe photo in the app had decayed, one locally-reasonable change at a time, to one hero image behind a switch that reclaimed none of its space, and its help text had started naming the surface it *didn't* cover. Cut end to end including the `User` column (**R-065 / ADR-062**, migration `e3b1d7f5a904`); the audit of the other seven per-user flags came back clean, because they are enforced server-side and this was the only client-only one. Several verify walks queued | `CHANGELOG [Unreleased]` |
| Assistant surface | ✅ | Per-user rate limits, SLM default path, multi-provider config, chat-window batch; now also hosts the money-gated buy-verdict toggle. Browser-verify owed | `ask_assistant.py` |
| Voice / TTS | ➗ | Reworked 08-27: Dora checks for actual installed voices rather than the API's presence and falls back to her own neural voice instead of going silent (the usual Firefox state). Settings → Voice names the live engine; a Help guide answers "which browsers can Dora speak in?". Open: FU-751 (never verified *on* Firefox), FU-722 | worklog 2026-08-27 |
| Offline / resilience (F3) | ➗ | Was broken end-to-end (replay never attached CSRF, every drain 403'd silently while the UI said "Synced everything"); fixed, R-047/ADR-043. **Live round-trip verify owed** — a mocked transport cannot reproduce it. FU-724 (`custom-service-worker.ts` is dead code, and it's the file you'd reach for) | `useOfflineQueue.ts` |
| Design remediation (DR) | 🟡 | DR-1..11/14/15 done or done-with-carve-outs; **DR-13 and DR-16 (owner call) remain, and DR-12 is now half-settled** — its meal-plans mini-month was *overruled* by D7 on 2026-08-29 and rebuilt as a full month grid rather than the directive's 14-day strip, because DR-12's rationale (a calendar competing with an actionable list) is the Alerts page's problem, not the planner's; the Alerts half of DR-12 is still open. New adjacent debt: FU-764's undefined-token class of bug, which R-060 names but nothing yet enforces | [DESIGN_REMEDIATION_PLAN](docs/04_proposals/DESIGN_REMEDIATION_PLAN.md) |
| Build & deploy | 🔴 | The 08-23 backups/import 404 was **the deploy script, not the app**: `--exclude='data'` matches the basename at any depth, so every deploy `--delete`d `dora_api/features/data/` (15 files) and `DATA_ROUTER` registered with zero routes. One-character fix, still owner-side. FU-720 (nothing verifies the deployed route map — the app boots clean while serving 404s), FU-719 (`_iter_submodules` swallows a subpackage that fails to import), FU-721 (CI/Release workflows) | FU-717 (resolved) → FU-719/720 |
| Verify tooling | 🟡 | **Half-fixed 2026-08-28.** A proven-safe isolated pairing is now committed in `.claude/launch.json` — `dora-verify-backend-5171-linux` (scratch `data/scratch-verify.db`, gitignored) + `dora-spa-5171` (SPA 5174 → API 5171) — and was used end to end for the cook-mode pass while the owner's :5170 ran untouched. The four original `dora-verify-backend*` configs still bind :5170 with `DORA_ALLOW_DESTRUCTIVE=true` and remain the footgun FU-758 describes. **Correction 2026-09-01: breakpoint branches ARE now drivable in the pane.** Assigning `q.screen.width` / `name` / `lt` / `gt` on the live `$q` sticks (it did not used to), and with `resize_window` alongside it the meal planner's desktop three-pane shell mounts and drives fully — the whole 09-01 batch was verified that way. Two limits remain: `QMenu` never opens (reach the component's `setupState` instead), and a week/month transition leaves the outgoing DOM in place, so page by reloading on a `?monday=` URL rather than clicking the arrow. `screenshot` still times out. Also added: `dora-verify-backend-5171` (Windows) — only the `-linux` variant of the isolated pairing existed | FU-758 |
| Postgres datastore | ✅ | Implemented + default (SQLite fallback); migrations kept portable (bare boolean predicates, not `= 1`). CI wiring remains, blocked on FU-405 | `configuration_manager.py` |
| Test suite | ✅ | Green 2026-09-01: backend **2206 passed** / 1 skipped / 1 xfailed, frontend **585 vitest**. Caveat: 4 pre-existing buy-verdict e2e failures (FU-762). This machine: bare `pytest` throws ~56 spurious setup errors — pass `--basetemp=<real dir>` or set `TMP`. Open: FU-756/743 (`web_app/test/` is outside the lint scope and has drifted), FU-520 (Postgres CI) | [PROPOSAL](docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md) |
| Open-source release (P7) | ⚪ | Not sold — donation/OSS/all-free. README/showcase, release process, support channel (FU-406/557/608) | [PLAN §5](docs/01_charter/RECONCILED_FINISHING_PLAN.md) |
| Finalisation sweep | 🔵 | Designed, not started — 20 chunks, two-stage, single-maintainer north-star | [PLAN](docs/01_charter/FINALISATION_PLAN.md) |

---

## ⚠️ Needs your attention now

**Total open backlog is 168 items in `DORA_FOLLOWUPS.md`** (recounted 2026-09-02:
FU-809 through FU-816 opened by the reports review).
These are the ones wanting a decision or a running-app check, most important first.

1. **Four calls on `/reports`, all from one review (FU-809/810/811/812).** The
   page has never been designed or reviewed — it's a faithful build of the 2025
   N6 spec, and the feedback file's REPORTS section is literally `?`. Read
   `docs/05_investigations/REPORTS_PAGE_REVIEW.md`; the four questions it can't
   answer for you are: **(809)** should Reports share the dashboard's card
   registry — five cards and five endpoints are already common; **(810)** does
   "Savings captured" survive, given it measures the retailer's advertised
   discount rather than money you kept; **(811)** correcting the shared 18px card
   radius/padding onto the token scale changes how the *dashboard* looks;
   **(812)** ECharts is a 562KB chunk for the app's only chart consumer. 809 and
   810 gate the restructure. Separately and needing no decision: the page renders
   every dollar surface with money switched off (FU-816), which contradicts your
   own L254 bullet.

2. **Does the burger read at 12–14px, and does the deepened accent still look
   like the accent? (FU-800, and the `DORA_VERIFY.md` "Accent ink" section.)**
   Two of your 2026-09-01 items shipped as app-wide colour and icon changes, so
   both want one pass of your eyes: the accent hue is now two tokens (bright as a
   fill, deep as ink — the ink one is what makes tab labels readable at 5.1:1
   instead of 1.3:1), and every "Dora thinks / Dora suggests" surface draws the
   mascot burger. Both were verified as *wiring* in the pane, but the pane never
   paints, so nobody has actually looked at them. If the small burger is mushy the
   fallback is a size floor, not a different glyph.

3. **🔴 May a planned meal change a buy verdict? (FU-774)** Your own idea, and the
   brief agrees with it — a planned meal is the *strongest* need evidence the oracle
   can hold, because every other input is an inference and that one is a stated
   intention with a date on it. But your directive of **2026-08-17** says "a planned
   meal's shortfall is unchanged", and an axis that moves a verdict from `unsure` to
   `buy` breaks it head-on. Nothing was built. One call, and it gates FU-775, FU-776
   and the whole axis. Design:
   [BRIEF_BUY_VERDICT_PLAN_AXIS.md](docs/04_proposals/BRIEF_BUY_VERDICT_PLAN_AXIS.md).
4. **🔴 Four launch configs will still destroy the dev DB (FU-758) — but the safe alternative now exists.** The `dora-verify-backend*` entries bind **:5170** (the real dev DB) with `DORA_ALLOW_DESTRUCTIVE=true`, which drop_alls on boot; that's what cost two sessions their browser pass. As of 08-28 a proven pairing is committed beside them — `dora-verify-backend-5171-linux` + `dora-spa-5171`, scratch DB, driven end to end. Your call: point the four at it, or delete them. One decision, no investigation left.
5. **🔴 Four buy-verdict e2e tests are red and the money-gate work is uncommitted (FU-762).** They pre-date that session's change but sit directly on the surface it modified. Your call whether they're fixed before that work is committed — everything else on the buy-verdict row is downstream of it.
6. **🟡 One character in `deploy-dora.sh`, and it's still on your desktop.** The deploy rsyncs with `--exclude='data'`, which matches the **basename at any depth** — so every deploy deleted `dora_api/features/data/` (15 files) off the server and all of `/api/data/*` 404'd. Change it to `--exclude='/data'` and redeploy. Until you do, FU-648 and FU-710 stay unreproducible. The script also holds your SSH password in plaintext at mode 0664. Follow-ups: **FU-720** (nothing verifies the deployed route map — the app booted clean while serving 404s) and **FU-719**.
7. **Existing installs need a re-import prompt or their ratings are wrong in a specific direction (FU-750).** USDA's category was never stored before migration `d1e5b8c3f7a2`, so pre-existing foods score **0 fvnl points** — and on a dish with ≥13 baseline points that *also* locks out the protein credit under the FSANZ gate. Both schemes come out systematically pessimistic with nothing on screen saying so. The fix is a user action ("re-run the import"); what's missing is the banner telling them.
8. **Walk both rating schemes against a real USDA import.** Everything was verified end-to-end on **hand-seeded foods**, not your ~7,800-row catalogue — so match quality and panel behaviour at real scale are unknown, and Nutri-Score has had **no browser pass at all**. The region nudge on a second device is untested (FU-746). That same walk should decide **FU-643** (the missing AU/US synonym layer).
9. **🟡 Four more surfaces still read "has a price" as "was bought" (FU-768).** The budget bug fixed on 08-28 was one instance of a class: `picked_offer_price` is snapshotted when a line is *added*, so an unticked line carries a price it never cost. Suggestions, pantry belief, buy verdict and waste all still infer purchase from price — one of them with a comment asserting the opposite. These feed belief, verdicts and waste, all of which you read as signal. Not one filter: it needs a call on what counts as proof of purchase, then a chokepoint in `_line_price.py` (R-061/ADR-058).
10. **🟡 A benign browser warning can silently revert an in-flight mutation (FU-785).** A `ResizeObserver` loop notification from `MainMenuButtonStrip.vue:47` — app chrome, proved pre-existing on the dashboard and the meal planner — shows an "Oops" toast, but `window.onerror` also runs `executeRollbacks()`, so a layout hiccup can roll back an optimistic write. The toast is the lesser half. Named as the next unit. (FU-738, which sat here, is waived: you said *"disregard this issue for now, i'm going to remove buttons from the toolbar at some point"*, and UX-v3 has since moved the lifecycle actions off that band entirely.)
11. **🔴 Decide the fate of the product price axis (FU-703).** You named the cause yourself: products got demoted to a push-your-own-data niche while the stock item was upgraded to carry everyday price functionality. Placement is already settled (price lens on Stock overview + trend section in Reports; alerts advanced-only). The keep/cut call is yours and **gates FU-708**. FU-704/705/706/707 are independent.
12. **Walk what's left underneath the recipe page.** The 08-26, 08-27 and 08-29 batches were each driven live; what's owed is everything beneath them — the 08-20 parity pass and the 08-24 batch. Two things genuinely can't be agent-driven: the **native file picker** on Change photo, and any **Quasar dropdown**, which never renders in the agent browser pane (FU-737).
13. **Walk the 2026-08-22 stock-overview batch — the bulk-bar network check is the one that matters.** Six bulk endpoints replaced per-item request loops on log-waste (and Undo), add-to-list, add-to-chosen-list, mark-restocked, remove-from-list and move. Open devtools Network: **if any bulk action still fires N requests, a call site was missed** — and FU-714 already names one that does.
14. **Walk the whole stock + stocktake surface — it's all built and none of it has been seen (FU-683).** Six chunks, Chunks 3–6 never run in front of a human. Two things to *confirm* rather than check: an overdue shopping day now counts on the bell badge, and the Review phase now genuinely has a dataset behind it (both seeds were fixed on 08-27).
15. **Confirm the "Needs attention" chip in a browser after a bulk action (FU-715).** The static read found the chip now does a bare `needs_attention === true` with no client fallback, plus two gaps that would look intermittent: optimistic/offline mutations don't recompute attention until a refetch, and the rule honours mutes but not snooze/dismiss — so **the chip and the bell disagree on a real install**.
16. **🔴 Two install-state bugs that only reproduce on your box.** FU-710 — the barcode register POSTs 404 (same module as the QR 404, so likely cleared by item 3's redeploy). FU-648 — the QR dialog failure has never reproduced in three attempts, but the error now names status + ref. Both need the redeploy plus a phone or non-localhost host.
17. **🔴 Three token decisions, all small and all mechanical afterwards.** FU-674 — `--text-on-primary` fails D-002's 4.5:1 floor **app-wide** in three themes (pesto 3.88, blueberry 4.21, midnight 2.86); either darken the ink or darken `--brand-primary`. FU-709 — every dark theme declares a `--surface-page` that nothing renders. **FU-764** — the new one, and the reason both of the above are easy to miss: four more files reference custom properties `tokens.scss` never declares, and because they wrote fallbacks they render *something* and silently ignore your theme forever. `TriStateFilter.vue` has no fallback at all, so it renders no background today. The durable fix is a stylelint rule; R-060 currently only asks people to remember.
18. **🔴 Small decisions that clear the stock row (FU-685, FU-686).** The row's expiry button still colours off a hardcoded 7 days while its outline reads your configured window — a 14-day setting can outline a row whose expiry pill is still green. And `PantryBeliefChip.vue` is orphaned while three comments still call it the live row form.
19. **Walk the inference surfaces and round-trip offline sync.** Inference: recipes / shopping lists / meal planner, each toggled separately, all off by default; the seed carries two "Belief demo:" recipes that make it a 30-second check. Offline: it once queued changes and lost every one while reporting success — go offline, change something, come back, **and reload to confirm the server kept it**.
20. **⭐ Verify the champion sequence (P8-07/08/09/10) and the products Phase-F tail (FU-214).** Four champion surfaces stacked and untested, plus the native Android APK build + device walk; pairs naturally with FU-389. Products need a real-data walk, L197 hard-delete is undecided and L205/206 bulk-select is unbuilt.
21. **Phase-4 release readiness needs your steer on scope and timing.** FU-406 (README/showcase + Releases process), FU-608 (make the repo public, stand up Sponsors / BMC / PayPal, then one placeholder-swap pass), FU-557 (support channel — a one-line config change lights up Help / error-report). Ops/CI (FU-405) gates FU-520/FU-404/FU-721.

---

## Where the detail lives

- **`DORA_WORKLOG.md`** — per-session handoff narrative (what ran, decisions, what's next).
- **`CHANGELOG.md`** — product/code changes that shipped.
- **`DORA_FOLLOWUPS.md`** — the full 135-item open backlog (this dashboard shows only the top).
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

## 05_investigations — reports (21)

| Doc | Type | State | Purpose/Notes | Evidence |
|---|---|---|---|---|
| REPORTS_PAGE_REVIEW | PO+eng review | 🔵 designed-not-built | `/reports` first-ever review — stands in for the empty REPORTS feedback section. Page is a faithful build of the 2025 N6 spec, ungated against the money flag | Written 2026-09-02; 8 FUs (809-816), chunks gated on FU-809/810 |
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
