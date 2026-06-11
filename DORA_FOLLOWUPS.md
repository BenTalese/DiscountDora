# Dora Follow-ups Ledger

Stateful backlog of **follow-ups, deferred jobs, leftovers, and findings**
surfaced while running prompts — the stuff that's easy for the user to miss in a
long session summary. Distinct from the other two logs:

- `CHANGELOG.md` = product/code changes that shipped.
- `DORA_WORKLOG.md` = per-session handoff narrative.
- `DORA_FOLLOWUPS.md` (this file) = **open loops** that outlive a single session,
  each with a tracked state so every session knows what's still pending.

## How to use this file

- **On session start:** scan for `[OPEN]` items. Surface the ones whose
  *recommended resolution point* is "now" or matches the work about to start, and
  **ask the user** whether they want to review/resolve them now or defer.
- **On ending a work unit:** add any new follow-ups/leftovers/findings you
  generated. Mark items you actually resolved as `[RESOLVED]` (don't delete them —
  the trail matters), with a one-line note on how.
- **Reported defect that "doesn't reproduce" → still log it here** as `[OPEN]`
  type `finding`, resolution "confirm in browser". A static code read is not proof
  a user-reported bug is fixed. Track each reported item individually; never bury
  several as one "all fine" note. (See CLAUDE.md → "On ending a work unit".)
- Keep the newest items near the top of the Open section.

## Entry template

```
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

## [OPEN] FU-153 — Assistant LLM config: per-user, reachability probe, multi-provider
- **Raised:** 2026-06-12 (user feedback during FU-085 verify)
- **Type:** design / proposal addition (no code yet)
- **What:** `DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md §7` (new
  section, this session) captures four interlocking changes to
  the LLM client + config side, distinct from the §1–6 routing
  refactor:
  1. **§7.1 Per-user LLM config** — drop the singleton
     `AppSetting.llm_*` and move it to `User.llm_*` (+ a
     `master_llm_enabled` install-wide kill switch on
     AppSetting). Households with two desktops each running
     their own LLM stop sharing one URL.
  2. **§7.2 Reachability probe** — new `GET
     /api/assistant/ping` hit **once per chat open** (not per
     message, not on a poll). Visible "AI mode unavailable —
     using basic mode" banner + Retry when the user's
     `llm_enabled` is true but their LLM doesn't answer.
  3. **§7.3 Network-topology constraint** — document that the
     backend (not the device) reaches the LLM URL. Operator
     concern for household / remote-LLM setups; pure
     documentation, no code.
  4. **§7.4 Multi-provider** — abstract `LlmClient` with
     `OllamaClient` (existing, moved) + `OpenAiClient` +
     `AnthropicClient` + `GeminiClient`. Per-user
     `llm_provider` enum + encrypted-at-rest API key column.
     Different tool-call schemas adapt to a shared shape
     before reaching `tools.py`.
- **Sequencing (§7.5):** one migration ships §7.1 + §7.4
  schema columns; provider implementations follow per-PR;
  §7.2 probe lands last (cheap once per-user config is
  available); §7.3 is docs only.
- **Existing DORA-BOT feedback cross-ref (§7.6):** the
  per-user mode toggle / "turn the bot off completely" /
  "disabled if unavailable" items in `Feedback _ Fixes - as
  of [06-Jun-2026].md` lines 452-460 pair directly with §7.1
  + §7.2 — the toggle UI visibly reflects the probe result.
- **Recommended resolution:** treat as the next chunked
  IMPL plan after the FU-152 routing redesign (or before;
  they're orthogonal but the per-user config is a
  pre-requisite for the rules-router-per-user too). Pair
  with the AI-mode design pass.
- **State note 2026-06-12:** **user signed off** on §7.1–§7.4
  as written, with one refinement folded into §7.1: the
  per-user Assistant config lives in
  `PreferencesSettings.vue` next to the existing C-cross
  per-user toggles (`money_features_enabled`, etc.) — not a
  net-new settings page. §7.3 (network-topology docs) was
  explicitly accepted as "same connectivity story as the rest
  of the app, nothing special". Next step: draft an IMPL plan
  from §7 when this work is sequenced.

---

## [RESOLVED-MINIMAL] FU-150 — Assistant chat-mode doesn't recognise dietary/cuisine queries
- **Raised:** 2026-06-12
- **Resolved (step 1, this session):** rule-based first-match-wins
  matcher kept, but the `find_recipe` intent's trigger list now
  catches the bare-noun cases ("i need a recipe", "any breakfast
  ideas", "show me a vegetarian recipe", etc.) — and the handler
  was rewritten to **stop yanking "the bit after a preposition"**
  and instead tokenise the whole message (minus stopwords) and
  substring-match each token against name + cuisine + category +
  timeOfDay + dietaryTagNames. Vocab arrives via the extended
  `RecipeSnapshot` (`dietaryTagNames`, `timeOfDay`) hydrated in
  `DoraChat.vue` from the existing Pinia stores; vocab preload
  was added to `ensureRecipeData()`. Net effect: "i need a
  vegetarian recipe" → routes to find_recipe, filters by the
  'vegetarian' dietary tag, lists the top matches. "Asian
  breakfast recipe" → both 'asian' + 'breakfast' must hit
  (cuisine + timeOfDay). Reply echoes the tokens it filtered on
  so the user sees what was matched.
  **Limitations of step 1 (kept as the structural follow-up FU-152):**
  the matcher is still keyword-list + token-substring, with no
  proper slot extraction or query parser. Stopword list is
  hand-coded; synonyms ("veggie" → "vegetarian") aren't resolved;
  composite phrases ("gluten free" survives because the tag name
  matches, but two-word tags + free-text terms in the same
  message can produce surprising AND-filters). The redesign in
  FU-152 spec's the real fix; this RESOLVED-MINIMAL fixes the
  user-visible "vegetarian"/"asian" failure mode now.

---

## [OPEN] FU-152 — Chat-mode design: tokenise → slot-extract → filter (structural)
- **Raised:** 2026-06-12 (offshoot of FU-150's minimal fix)
- **Type:** design / structural improvement
- **What:** The current chat is a "first-match-wins keyword
  matcher" with hand-curated `matches[]` per intent + a handler
  that pulls "the noun after a preposition" and substring-searches
  recipe fields. FU-150 step 1 broadened the trigger list +
  switched the handler to whole-message tokenisation, which is
  enough for the dietary/cuisine cases but still scales linearly
  in keyword count and produces brittle behaviour for compound
  queries.
- **Proposed redesign (two axes):**
  1. **Vocab-derived triggers.** Load Cuisine + DietaryTag +
     Tool catalogues at chat init. Each catalogue contributes
     its names to a "term → intent" prior so the matcher knows
     "vegetarian"/"asian"/"slow cooker" all route to
     `find_recipe`. Auto-updates when the user adds new vocab.
  2. **Slot extraction**, separate from intent detection. After
     the intent fires, walk the message once and capture
     `slots: {cuisines[], dietaryTags[], timeOfDay?,
     stockItems[], freeText}`. Handlers consume slots
     declaratively — `filterRecipes({ dietary: ['vegetarian'],
     cuisine: 'asian' })` — instead of doing ad-hoc substring
     searches.
  3. **Intent scoring (optional)**: replace first-match-wins
     with a scoring pass per intent (each contributes keyword
     hits + vocab hits + structural cues). Highest-score intent
     wins, tie → fallback. Catches "i'm hungry, what veggie
     thing can I make?" routing to `whats_for_dinner` with a
     dietary slot, rather than tripping `find_recipe` because
     "recipe"-ish keyword fired first.
  4. **Reply transparency**: show the slots the handler
     applied ("Filtering by: vegetarian + asian"). Already
     present in FU-150 step 1 via `queryDisplay`.
- **Why deferred:** step 1 covers the immediate UX failure; the
  full slot-extraction redesign is a separate, focused work
  unit. Pair with the AI-mode sweep — the slot extractor is the
  same shape of work whether the route resolves into the
  rule-engine handler or the LLM handler.
- **Recommended resolution:** later — pair with AI-mode design.

---

## [OPEN] FU-151 — Browser-verify FU-085 fixes (FU-147 dietary picker, FU-148/149 filters, FU-150 chat)
- **Raised:** 2026-06-12 (concluding the FU-085 verify pass)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **FU-147** — open the seeded "egg fried rice" recipe → its
     two dietary tags pre-populate the picker; saving with no
     edit doesn't clear them; adding/removing tags + saving
     round-trips (re-open the page shows the new set).
  2. **FU-148** — Cookbook overview "Time of day" dropdown
     filters to Breakfast / Lunch / Dinner / Dessert / Snack /
     Any. Clearable.
  3. **FU-149** — "# ingredients ≤" filter narrows the list;
     "# ingredients" sort axis orders ascending by default
     (fewest first); the direction toggle flips it.
  4. **FU-150** (step 1) — basic chat-mode:
     - "i need a vegetarian recipe" → lists vegetarian recipes,
       header says "Filtering by: vegetarian recipe" (or similar).
     - "i need an asian recipe" → cuisine filter applied.
     - "show me a breakfast recipe" → timeOfDay filter applied.
     - "i need a recipe" with no other terms → prompt asking
       for a name/ingredient/cuisine/tag (no fallback bank).
- **Recommended resolution:** next browser session.

---

## [RESOLVED] FU-149 — Cookbook overview: add "# ingredients" filter + sort axis
- **Raised:** 2026-06-12 (user browser verify of FU-085)
- **Type:** enhancement
- **What:** New filter axis "ingredients = N" or "ingredients ≤ N"
  + new sort axis "ingredient count (asc/desc)" on the cookbook
  overview. Ingredient count is already on the Recipe DTO (via the
  `ingredients[]` array length); the work is mostly in
  `useRecipeFilters` / the overview's filter panel + sort options.
- **Why deferred:** new feature, not bug. Scope cap on the
  current session.
- **Recommended resolution:** later, batched with FU-148
  (time-of-day filter) and the other cookbook polish items.

---

## [RESOLVED] FU-148 — Cookbook overview: add "time of day" filter
- **Raised:** 2026-06-12 (user browser verify of FU-085)
- **Type:** enhancement
- **What:** `Recipe.time_of_day` exists on the entity + DTO
  (breakfast / lunch / dinner / snack / dessert / drink), and it's
  editable on the recipe detail page, but there's no filter for
  it on the cookbook overview. Add a single-select dropdown
  defaulting to "any time of day" alongside the cuisine / category
  selects. The other filters use the same `useRecipeFilters`
  pattern; this should be one mirrored predicate.
- **Why deferred:** new feature; pair with FU-149.
- **Recommended resolution:** later.

---

## [RESOLVED] FU-147 — Recipe detail dietary-tag picker loses selection on save
- **Raised:** 2026-06-12
- **Resolved:** 2026-06-12 — root cause turned out to be a backend
  bug in the detail endpoint, not a frontend race. The
  `/api/recipes/<recipe_id>` route has no `uuid:` converter, so
  Flask passes `recipe_id` to `handle_by_id` as a **string**.
  `get_tag_ids_for_recipes()` returns `dict[UUID, list[UUID]]`
  (keys come from SQLAlchemy result rows). The handler then did
  `tag_map.get(recipe_id, [])` — a Python dict lookup with a
  string key against UUID-typed keys → **always returned `[]`**,
  silently dropping every tag and tool on the detail JSON.
  Same bug affected `tool_map.get(recipe_id, [])`. Fix in
  `get_recipes.py::handle_by_id`: pass `entity.id` (the loaded
  entity's real UUID) to both `get_tag_ids_for_recipes` and the
  subsequent `.get()` calls. The list endpoint was unaffected
  because it sources ids from RecipeDtos that already carry
  UUID objects.
  Static-only fix; browser-verify is **FU-151**.

---

## [OPEN] FU-146 — Sweep external GitHub-issues references — DONE
- **Raised:** 2026-06-12 (user browser verify of FU-085: "should
  remove any mention of github issues as the repo is now private")
- **Type:** finding / hygiene
- **What:** Dora-bot fallback bank, `report_issue` intent + its
  `externalLink`, the `whats_new` "See latest release on GitHub"
  link, `HelpPage` "Report a bug" header button + Help-tab repo
  list + issues list, `AboutSettings` repo + bug-report items,
  and `PageErrorState`'s pre-filled GitHub-issues URL all linked
  to `github.com/BenTalese/DiscountDora` — a now-private repo.
- **Resolved:** 2026-06-12 — replaced the FALLBACK_REPLIES bank +
  `report_issue` intros to drop the GitHub framing; retired the
  externalLink on `fallback` + `report_issue` (Help-nav stays);
  retired the `whats_new` release URL; pulled the four GitHub
  buttons/items from `HelpPage` + `AboutSettings`; retired
  `PageErrorState`'s `reportUrl` + the "Report this" button (the
  `showReport` prop stays so a self-host operator can restore a
  similar surface pointing at their own report sink).
  **Note:** the `report_issue` intent itself stays — it's a
  useful "I found a bug" affordance — but it now navigates to
  Help instead of pointing at an external tracker.

---

## [OPEN] FU-143 — Backfill `picked_offer_price` for legacy lines
- **Raised:** 2026-06-12 (State Ownership Chunk 6 impl)
- **Type:** deferred job (optional)
- **What:** Chunk 6 moved the offer-price snapshot from
  *tick* to *add* / *select*. Rows created before this change
  with a non-NULL `selected_product_id` but NULL
  `picked_offer_price` (never ticked) won't have a snapshot
  until the user later ticks them (the belt-and-braces hook
  at `manage_shopping_list_lines.py` UpdateLineHandler tick
  path + the finish-list fallback at `manage_shopping_list.
  py:212-215`). A one-off script could snapshot-fill every
  legacy row with `selected_product_id IS NOT NULL AND
  picked_offer_price IS NULL`, picking the current offer for
  the chosen product.
- **Why deferred:** Optional. The belt-and-braces paths drain
  legacy rows organically; nothing breaks if a never-ticked
  legacy row stays unsnapshotted (it just doesn't appear in
  budget / waste aggregates until ticked). At pre-release
  scale this is fine to skip.
- **Recommended resolution:** opportunistic — only worth
  doing if a user later complains "budget number doesn't
  match what's in my old draft lists". Then a small Alembic
  data migration or one-shot script clears the deficit in a
  single pass.

## [OPEN] FU-142 — Browser-verify State Ownership Chunk 6 (snapshot-at-add)
- **Raised:** 2026-06-12 (State Ownership Chunk 6 impl)
- **Type:** finding / verification
- **What:** Exercise the new snapshot timing end-to-end:
  1. **Add line with selected offer** — confirm budget's
     "projected_active" (or post-finish "spent") reflects the
     planning-time price; price the offer up via the
     companion app and confirm the snapshot is the *original*
     value, not the moved price.
  2. **Change `selected_product_id`** via the list detail
     page's offer chip — confirm the snapshot re-captures at
     the new offer's current price.
  3. **Clear selection** — confirm the snapshot clears (the
     line shows as "no priced intent" in any UI that
     surfaces it).
  4. **Tick** an already-snapshotted line — confirm tick
     does NOT overwrite the snapshot.
  5. **Untick** — confirm the snapshot persists (the
     commit-to-offer moment didn't un-happen).
  6. **Tick a legacy line** (one created before this chunk
     with `picked_offer_price` NULL) — confirm the
     belt-and-braces hook fills the snapshot the first time.
- **Why deferred:** static-only impl; needs the running app
  + a live offer to verify price-moved-between-states.
- **Recommended resolution:** confirm in browser — same
  high-priority slot as the other Chunk-N verify items.

## [OPEN] FU-141 — Browser-verify State Ownership Chunk 4
- **Raised:** 2026-06-12 (State Ownership Chunk 4 impl;
  static-only, no env)
- **Type:** finding / verification
- **What:** Eyeball that the rename-safety refactor preserved
  every visual decision it was supposed to preserve:
  - `StockItemChip` — colour band + short label ("OK" / "Mid" /
    "Low" / "Out") still match each level. Renaming "Out of
    Stock" to "Empty" in Settings should leave colour + label
    unchanged.
  - `StockItemRow` — dim treatment fires for out-of-stock
    rows; level button colour follows the current level.
  - `useStockFilters` — summary counts (top of Stock Overview)
    + sticky-footer tones still light up correctly when a
    level is renamed.
  - `WastePage` — "Mark used" sets the level to whichever row
    matches `OUT_OF_STOCK_SEQUENCE` (rename it first to
    confirm).
  - `MealPlansOverview` — "Need to buy" lists ingredients
    whose level is None/low/out; status chip colours match the
    bucket.
  - `ProductSearch` quick-add — new tracked items still start
    in the out-of-stock bucket.
  - `RecipeCookMode` finish-rows — "leave out of stock"
    action resolves to the right level after a rename.
- **Why deferred:** static-only impl; needs a running app +
  level-rename action to exercise the renaming property
  end-to-end.
- **Recommended resolution:** confirm in browser — high-priority
  for this chunk because the whole point is "renaming a level
  no longer breaks anything". Rename one level as part of the
  smoke pass.

## [OPEN] FU-140 — Sweep Cart Button Chunk 3 typing fallout (nullable `stock_item_id`)
- **Raised:** 2026-06-12 (State Ownership Chunk 4 typecheck)
- **Type:** finding / cleanup
- **What:** Cart Button Chunk 3 made `ShoppingListLine.stock_
  item_id` nullable (a product-only line carries `product_id`
  instead). The TS model followed, but at least two consumers
  type-checked only because no other change had triggered them:
  - `NewListDialog.vue:376` — `detail.lines.map(l => l.stock_
    item_id)` previously was `string[]`, now `(string|null)[]`.
    Fixed here with a typed `.filter` to keep the chunk's
    typecheck green.
  - `ShoppingListDetail.vue:2049` — the undo-snapshot path
    passed a possibly-null id to
    `removeByStockItemFromListAsync`. Guarded here so the undo
    only registers when the id is non-null.
  There are likely more call sites in `ShoppingListDetail` and
  the cook-mode finish that haven't been audited because
  TypeScript only flags them when another change exercises the
  expression.
- **Why deferred:** out of Chunk 4's documented scope (this
  is Cart Button Chunk 3 fallout). The two blocking sites
  were fixed inline; the sweep is the open item.
- **Recommended resolution:** opportunistic — fold into the
  next Cart Button or shopping-list touch. Could also be a
  one-shot `grep` sweep for `stock_item_id` reads on
  `ShoppingListLine` and a typed audit.

## [OPEN] FU-139 — Finish migrating `getStockLevelColour(name)` callers to `colourForSequence(seq)`
- **Raised:** 2026-06-12 (State Ownership Chunk 4)
- **Type:** follow-up / cleanup
- **What:** Chunk 4 introduced `colourForSequence(seq)` and
  migrated the *decision-driving* call sites. The legacy
  `getStockLevelColour(name)` was kept as a soft-fallback so
  ~5 surfaces with only a `level_name` (no sequence in scope)
  still compile:
  - `StockItemDetailPage.vue:16, 114, 126` (the q-chip in
    the header, the level-picker dropdown label, and the
    per-level avatar in that dropdown)
  - `RecipesOverview.vue:537` (`stockLevelColourFor`
    helper consumed by ingredient chips)
  - `RecipeDetailPage.vue:1326` (`levelColourFor`)
  - `QuickAddSheet.vue:195`
  - `CreateStockItemDialog.vue:43`
  - `MyProductsPage.vue:1053`
  Each is a small migration (give the helper the level row,
  read `.sequence`, call `colourForSequence`). Once they're
  all migrated, the legacy `getStockLevelColour` + its
  literal-case `switch` in `stockLevelLogic.ts` can be
  deleted, completing the purge.
- **Why deferred:** out of Chunk 4's documented scope (these
  are display-only colour lookups, not decision-driving
  comparisons). R-007 — flag, don't drift.
- **Recommended resolution:** opportunistic, or as a focused
  follow-on session. Each surface migration is mechanical
  (~5 lines). The full sweep closes the literal-fallback hole.

## [OPEN] FU-138 — Query-count test for `GET /recipes` (no N+1)
- **Raised:** 2026-06-12 (State Ownership Chunk 2 close-gate)
- **Type:** deferred job (test infra)
- **What:** The plan's §3 perf risk for Chunks 2–3 calls for an
  integration test that pins the recipe-list endpoint's SQL
  query count, so the set-based cookability / missing-names
  aggregations can't silently regress into N+1 lazy loads.
  `missing_stock_item_names_for` (Chunk 2) is N+1-free by
  construction (pure function over the already-loaded
  ingredient tree), but a runtime guard is still the right
  long-term shape — especially once `?cookable=true` (Chunk 3)
  hits the same query path.
- **Why deferred:** the project has no precedent for query-count
  tests (no SQLAlchemy `before_cursor_execute` harness, no
  baseline numbers). Building that scaffolding belongs with
  the chunk that adds the next hot endpoint, not with a pure
  field-add.
- **Recommended resolution:** **later during State Ownership
  Chunk 3** — fold the harness build into the `?cookable=true`
  end-to-end test so it pays for itself across both chunks.

## [RESOLVED] FU-137 — `test_recipe_cookability.py` stub missing `source` attr
- **Raised:** 2026-06-12 (surfaced during State Ownership Chunk 1
  verification run)
- **Type:** finding / test breakage (pre-existing)
- **What:** `tests/test_recipe_cookability.py::_recipe()` built a
  `SimpleNamespace` recipe stub lacking `source`,
  `version_group_id`, `kcal` — fields that `RecipeDto.from_entity`
  reads. Every test in the file failed with `AttributeError`.
- **State note:** **Resolved 2026-06-12 (State Ownership Chunk 2)**
  — the stub was the scaffolding for Chunk 2's
  `missing_stock_item_names` tests, so the fix was folded into
  that chunk per the original recommendation. Added the three
  missing attributes; all 12 cookability tests now pass.

## [RESOLVED] FU-136 — `test_shopping_list_totals.py` stub missing `product_id` arg
- **Raised:** 2026-06-12
- **Resolved:** 2026-06-12 — added `product_id=None` to the `_line()`
  factory in `tests/test_shopping_list_totals.py`. Single-line stub
  fix; totals tests don't exercise the new anchor so None is the
  honest value. CI signal restored.

## [OPEN] FU-135 — Browser-verify Cart Button Chunk 4 (meal-plan generate via Axis B)
- **Raised:** 2026-06-12 (Cart Button Chunk 4 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify the four-state matrix on the meal-plan
  "Generate shopping list for this week" button:
  1. **0 draft lists:** no picker; creates a new list named
     `Meals: <plan>`; success toast says "Shopping list created
     with N items."; routes to the new list.
  2. **1 draft list:** picker opens with that draft preselected +
     a "+ Create new list" row; OK on the draft → backend merges,
     toast says "Added N items to your list.", routes to that
     list.
  3. **2+ draft lists:** picker lists all drafts (first
     preselected) + "+ Create new list"; both an existing pick
     and the create-new pick work.
  4. **Cancel/dismiss:** aborts cleanly — no list created, no
     toast, no navigation.
  Also: `nothing_to_add` path still emits the info toast and
  *doesn't* navigate.
- **Why deferred:** static-only impl; needs a real meal plan +
  varied draft-list state.
- **Recommended resolution:** confirm in browser — same
  high-priority slot as FU-130 / FU-132.

## [OPEN] FU-134 — Audit other `autoGenerate` call sites for Axis-B routing
- **Raised:** 2026-06-12 (Cart Button Chunk 4 impl)
- **Type:** follow-up
- **What:** The meal-plan "Generate shopping list for this week" button
  now offers add-to-existing vs. create-new via Axis B. Three other
  `shoppingListApi.autoGenerateAsync` call sites were left alone:
  - `web_app/src/components/dialogs/NewListDialog.vue:416` — already
    explicitly picks/creates a target list before generating; no change
    needed (already Axis-B-aware by construction).
  - `web_app/src/pages/RecipesOverview.vue:1153` — recipe "add all
    missing to a new list" path. Acceptance candidate for the same
    treatment (the proposal puts recipe bulk-add under variant="bulk"
    via the `AddToListButton`, which is the longer-term home).
  - `web_app/src/layouts/MainLayout.vue:291` — global/keyboard
    shortcut entry. Check whether this should also offer Axis B or
    is intentionally always-new.
- **Why deferred:** out of Chunk 4's documented scope (`PROPOSAL_CART_
  BUTTON.md §5` surface 10 is meal-plan generate only). Scope discipline
  (R-007) — flag, don't drift.
- **Recommended resolution:** opportunistic — re-evaluate when the
  `AddToListButton variant="bulk"` work lands for recipes (FU-131
  vicinity) and again when the global shortcut surface gets touched.

## [OPEN] FU-133 — Promote generate-target picker into a shared `TargetListPicker`
- **Raised:** 2026-06-12 (Cart Button Chunk 4 impl)
- **Type:** follow-up (R-001 carve-out)
- **What:** `pickGenerateTarget` in
  `web_app/src/pages/MealPlansOverview.vue` is a one-shot `$q.dialog`
  radio picker (drafts + "+ Create new"). If a second surface needs
  the same shape (likely candidates: FU-134 audit, future bulk
  add-all-missing flows), extract it as
  `components/dialogs/TargetListPickerDialog.vue` with props
  `{ drafts, allowCreateNew, title?, message? }` and one resolved
  payload type `{ kind: 'existing', id } | { kind: 'new' } | null`.
- **Why deferred:** single consumer today — promoting now would be
  speculative abstraction (R-001 judgement carve-out).
- **Recommended resolution:** when FU-134's audit lands a second
  consumer.

## [OPEN] FU-132 — Browser-verify Cart Button Chunk 3 (standalone-product lines + rules 1–3)
- **Raised:** 2026-06-12 (Cart Button Chunk 3 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **Migration applies cleanly** (`d7c9e4a8c2b1`) on both SQLite +
     Postgres; `verify_mappings()` passes for the now-nullable
     `stock_item_id` and the new `product_id` FK.
  2. **Rule 1** — POST `/api/shopping-lists/<id>/lines` with only
     `product_id` (no `stock_item_id`) creates a line; list-detail
     DTO carries `product_id` + null `stock_item_id`. CHECK
     constraint rejects a body with neither anchor (400 from the
     handler before DB).
  3. **Rule 2** — preconditions: a draft list contains a
     product-only line for product P; product P is not yet linked
     to any stock item. POST `/api/stock-items/<S>/products` with
     `product_id=P`. After: the orphan line is upgraded — its
     `stock_item_id` is now S (or it's been folded into an
     existing stock-item line for S, with that line's `product_id`
     set to P).
  4. **Rule 3** — preconditions: a stock-item line for S exists,
     plus a separate product-only line for P (where P is linked to
     S). DELETE the stock-item line by line-id → the nested
     product line is gone too. Same for the cart-button
     remove-by-stock-item path.
  5. **No regressions** on stock-item-only adds (the dominant
     case): existing dedupe by stock_item_id still wins.
  6. **TS compile**: `ShoppingListLine.stock_item_id: string | null`
     no longer breaks consumers (the obvious 3 spots in
     `ShoppingListDetail.vue` were null-guarded this chunk; FU-131
     covers the remaining inline-product surfaces).
- **Why:** schema change + multi-rule wiring + cascade is the
  highest-risk single chunk in the cart-button plan; the rules
  interact with the link-product handler + by-line + by-item delete
  paths.
- **Recommended resolution:** now (next session). Requires a real
  DB to exercise.

---

## [RESOLVED] FU-131 — Cart Button Chunk 3 frontend UI (rule 4 modal + inline-product variant + nested display)
- **State note:** **Resolved 2026-06-12** — all three pieces
  (rule 4 modal in `ShoppingListDetail.vue::onRemoveLine`,
  nested display via `nestedLinesFor` + new CSS classes, and
  `AddToListButton variant="inline-product"` consumed by
  `MyProductsPage`) landed in a single session. Browser-verify
  tracked separately as **FU-145**. Original entry preserved
  below for the trail.

## [OPEN] FU-145 — Browser-verify Cart Button Chunk 3 UI (FU-131 follow-on)
- **Raised:** 2026-06-12 (FU-131 impl)
- **Type:** finding / verification
- **What:** Exercise the rule-4 modal + nested display +
  inline-product variant end-to-end:
  1. **Add a product-only line** via the My Products row
     ("Add as product" button) on an unlinked product →
     confirm the line lands with the product chip + tinted
     "product only" background.
  2. **Link the product to a stock item** later via the
     stock-item detail → confirm the parent stock-item line
     appears on the same list (rule 2 backend) AND that the
     product nests visually under it (rule 2 frontend).
  3. **Remove the nested product** → rule-4 modal fires;
     "Yes" removes both, "No" leaves the stock-item parent.
  4. **Remove a product-only line** whose linked stock item
     is NOT on the list → no modal (rule 4 doesn't apply).
  5. **Inline-product Axis B** — exercise with 0 / 1 / 2+
     drafts: 0 → "create a draft first" toast; 1 → silent
     add; 2+ → radio picker, both picks work.
  6. **Existing flows still work** — linked products on the
     My Products row still hit `onAddSingle` (stock-item
     path); ticking/unticking nested children works; bulk
     mode handles parents + children sensibly.
- **Why deferred:** static-only impl; needs a populated
  database + live SPA to exercise the matrix.
- **Recommended resolution:** confirm in browser — folds
  naturally into the broader Cart Button + State Ownership
  browser-verify batch.

## [OPEN] FU-144 — Cart-state awareness for product-anchored adds
- **Raised:** 2026-06-12 (FU-131 impl)
- **Type:** follow-up
- **What:** `AddToListButton variant="inline-product"`
  doesn't show "on a list" state today — `cartStateFor` keys
  on `stock_item_id` and a product-anchored button has none.
  Result: a user can re-click "Add as product" on the same
  product and get a second product-only line (the backend's
  dedupe catches it and the toast reads "Already on your
  list", so it's safe — just not as informative as the
  stock-item variant). A parallel membership index keyed on
  `product_id` would let the button render the same
  on-list / on-multiple states the stock-item variant does.
- **Why deferred:** out of FU-131's documented scope (the
  three named pieces shipped); product-anchored membership
  is a server-side extension that touches the
  `Membership` DTO + how its `items` array is keyed.
- **Recommended resolution:** when a third product-anchored
  consumer of `AddToListButton` shows up, or when a user
  reports the double-add UX as a problem.

## [OPEN] FU-131 (original) — Cart Button Chunk 3 frontend UI (rule 4 modal + inline-product variant + nested display)
- **Raised:** 2026-06-12 (Cart Button Chunk 3 deliberate scope-down)
- **Type:** rollout
- **What:** Backend rules 1–3 + schema + DTO are wired this chunk.
  The UI side of Chunk 3 was deliberately scoped down to keep the
  schema-change PR reviewable. Remaining UI work:
  - **Rule 4 modal**: removing a product-only line should prompt
    "Also remove the stock item from this list?". Hook into the
    existing DeleteLine + RemoveByStockItem paths from the SPA.
  - **`AddToListButton variant="inline-product"`** + a
    `product-id` anchor path (couples with the **My Products**
    page link affordance, L195) — current `AddToListButton` only
    accepts `stockItemId`; this chunk needs a parallel
    `productId` prop.
  - **Nested display on the shopping-list detail page** — render
    a product line that shares a `stock_item_id` with another
    line as a child of that line, not a sibling. Render
    product-only lines with a "product only" badge.
  - **Backup / restore round-trip** — verify the snapshot JSON
    survives the new column (the table is already part of the
    snapshot but the field set changed).
- **Recommended resolution:** opportunistic — pair with the next
  shopping-list-detail polish pass, or do as one focused UI sweep
  before Cart Button Chunk 4.

---

## [OPEN] FU-130 — Browser-verify Cart Button Chunk 2 (combined modal for 2+ products)
- **Raised:** 2026-06-12 (Cart Button Chunk 2 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **0 linked products** → row cart click adds silently via the
     existing single-item flow (no modal). One toast.
  2. **1 linked product** → same silent add. No modal.
  3. **2+ linked products** → row cart click opens `QuickAddSheet`
     pre-populated with the stock item; target-list dropdown +
     offer radio + quantity editable; Add → one toast.
  4. **2+ products AND 2+ drafts** → still routes through the same
     `QuickAddSheet` (single surface, no stacked modals).
  5. `linked_product_count` shows up on the `/stock-items` JSON
     response (network panel); 0 with no `StockItemProduct` rows;
     count increments as products are linked.
  6. Bulk variant unaffected — still resolves target once + one
     summary toast regardless of per-item product counts.
- **Why:** the modal-routing gate is new code; verify the count
  hydration stays O(1) DB calls per list page (single GROUP BY).
- **Recommended resolution:** now (next session).

---

## [OPEN] FU-127 — Browser-verify Cart Button Chunk 1 (AddToListButton + double-toast fix)
- **Raised:** 2026-06-12 (Cart Button Chunk 1 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **Stock overview row cart button** behaves: not-on → adds (one
     toast); on exactly 1 list → click removes silently; on 2+ →
     popover with each list's "Remove from <name>" + "Remove from
     all" + "Add to another list".
  2. **Recipe detail ingredient row** cart button: same behaviour.
  3. **Stock item detail toolbar** "Add to list" button: same
     behaviour at a larger size + label.
  4. **Bulk-add from Stock Overview**: select N items → toolbar "Add
     N to list" → resolves the target ONCE (uses sessionStorage
     pick or membership's quick_add_target) and surfaces a single
     summary toast (no per-item toasts).
  5. **FU-038 specifically**: re-adding an already-on-list item via
     the row button **never** produces the contradictory pair
     ("0 added, 1 already" + "Added").
  6. **No regressions**: keyboard shortcut `a` (add focused or
     selected) still works via the legacy `bulkAddToPrimary`
     pathway (kept for keyboard ergonomics).
- **Why:** ~3 visible surfaces adopted in this chunk; the popover
  + bulk variants are new code paths. The remaining hand-rolled
  cart paths on other surfaces (Cookbook overview card,
  MyProductsPage, MealPlansOverview, QuickAddSheet entry,
  ProductSearch) will be adopted opportunistically — they were
  left in-place this chunk for risk control. **Logged as FU-128.**
- **Recommended resolution:** now (next session).

---

## [OPEN] FU-128 — Adopt `AddToListButton` on remaining cart surfaces
- **Raised:** 2026-06-12 (Cart Button Chunk 1 scope cap)
- **Type:** rollout
- **What:** Chunk 1 spec'd ~9 surfaces from proposal §1 (#1, #3, #5,
  #6, #7, #11 row/toolbar/menu + #2, #9, #13 bulk). This commit
  adopted **#1 StockItemRow**, **#3 StockItemDetailPage toolbar**,
  **#5 RecipeDetailPage ingredient row**, **#9 StockOverview bulk**.
  The remaining surfaces still carry hand-rolled add buttons:
  - **#6 MyProductsPage**
  - **#7 MealPlansOverview**
  - **#11 ProductSearch**
  - **#13 QuickAddSheet** (entry buttons elsewhere)
  Each is mechanically the same change: swap the hand-rolled q-btn
  for `<AddToListButton variant="row|toolbar" :stock-item-id="..." />`
  and delete the dead handler.
- **Why deferred:** plan says "do them in one PR so the old paths
  all die together" — I held the line on risk by adopting only the
  highest-traffic surfaces. The rest are mechanical follow-ups.
- **Recommended resolution:** opportunistic — pair with the next
  edit to each surface, or do them as one tidy sweep before
  Chunk 2.

---

## [OPEN] FU-126 — Rename `RecipeImageField` → `ImageUploadField`
- **Raised:** 2026-06-12 (Stock Overview Chunk 6 / FU-033 impl)
- **Type:** tidy-up
- **What:** `RecipeImageField` is now used by both
  `RecipeDetailPage` and `StockItemDetailPage` — it carries no
  recipe-specific logic, just `previewUrl` + `name` props +
  `pick` / `clear` emits. R-001's threshold (second consumer)
  has been hit; rename to `ImageUploadField` + move to
  `components/` (not `components/recipes/`). Touch points:
  the component file, the two import sites, and the inline
  "Recipe image" alt text (parameterise via a prop).
- **Why deferred:** scope discipline this chunk. Trivial rename,
  no behavioural change.
- **Recommended resolution:** opportunistic — pair with the next
  image-touching change, or do as a standalone tidy when convenient.

---

## [OPEN] FU-125 — Browser-verify Stock Overview Chunk 6 / FU-033 (stock images + product fallback)
- **Raised:** 2026-06-12 (Chunk 6 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **Upload from detail page.** Open a stock item → Overview tab.
     Upload a photo via the new image field at the top of the right
     column → saves immediately, row in the overview gains a
     thumbnail on next load. "Remove" clears it.
  2. **Product fallback.** Pick a stock item with no own image but a
     linked product that has one → the row's thumbnail shows the
     product's image. The detail page's `has_image` flag should
     still be true. Unlink the product → flag goes false, row drops
     back to placeholder.
  3. **Both empty.** Stock item with no own image + no linked
     product image → row shows the neutral placeholder; the bytes
     endpoint 404s (check Network tab — no broken-image icon).
  4. **List endpoint performance.** With a >50-item pantry, watch
     the network panel during overview load — `GET /stock-items`
     response should be small, no image bytes inlined. Bytes only
     load when the row actually mounts an `<img>`.
  5. **Show/hide toggle from Chunk 3** still flips the image
     column on/off (denser rows).
  6. **Race protection** — uploading while the row is mounted
     should bump `imageVersion` and the row should refetch the
     new image on the next list refresh (the toggle does that, or
     reload the page).
- **Why:** the image route + fallback query are new server code;
  the deferred-column mapping is a SQLAlchemy behaviour change.
  Both need a real DB to confirm.
- **Recommended resolution:** now (next session).

---

## [OPEN] FU-124 — Browser-verify Stock Overview Chunk 5 (responsive detail nav + long-press)
- **Raised:** 2026-06-12 (Stock Overview Chunk 5 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **Desktop (≥ md breakpoint):** tap a row → splitter peek opens
     with the shared `StockItemDetailPage` embedded; tap again →
     closes. Same behaviour as before.
  2. **Mobile (< md breakpoint):** tap a row → full-page navigation
     to `/stock/<id>`; no drawer/peek. Same `StockItemDetailPage`
     renders in non-`embedded` mode. The back button returns to the
     overview with state preserved.
  3. **Bulk mode (any breakpoint):** tap toggles selection (no nav,
     no peek).
  4. **Long-press a row on mobile:** enters bulk-select mode and
     ticks the held item. Subsequent taps add/remove items. Cancel
     button exits bulk mode.
  5. **Long-press on desktop:** is a no-op (the `<md` guard in
     `onRowLongPress`). Desktop users have the toolbar's Bulk
     select button.
  6. **Resize browser across the md breakpoint** while a peek is
     open — peek stays attached to the row's existing state; future
     row-taps then use the new breakpoint's behaviour.
- **Why:** `v-touch-hold` was newly registered in `quasar.config.ts`
  this chunk; verify it actually fires on touch devices (Chrome
  mobile emulation works). The breakpoint branching uses
  `$q.screen.lt.md` — confirm that `boot/quasarScreen.ts`'s
  `Screen.setDebounce(100)` has the plugin active (it does for
  every other consumer, but a sanity check costs nothing).
- **Recommended resolution:** now (next session).

---

## [OPEN] FU-123 — Browser-verify Stock Overview Chunk 4 (expiry control)
- **Raised:** 2026-06-12 (Stock Overview Chunk 4 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **No expiry set** → tap the row's expiry button → q-date picker
     appears (popup on desktop, dialog on mobile). Picking a future
     date PATCHes the stock item and the row immediately reflects the
     new date (icon switches to a coloured "ok" / "soon" tone via
     existing logic). Picking past dates is blocked by
     `dateOptionsFuture`.
  2. **Expiry set** → tap the row's expiry button → menu shows
     **+1 day · +7 days · +14 days · Clear** (no +30 anymore).
     +1/+7/+14 each PATCH the right ISO date; Clear nulls it and
     the button reverts to the "no expiry" date-picker state.
  3. **Tone outline still flips correctly**: setting a date <7 days
     in the future triggers `stock-row--warn` (amber); a past date
     should not be settable but if one exists from earlier data,
     `stock-row--alert` (red) still applies.
  4. **No regressions** on the surrounding right-cluster buttons
     (#recipes, open/in-use, cart).
- **Why:** date-picker swap is the highest-risk part; q-date's
  `options` function uses `YYYY/MM/DD` strings while the emitted
  `model-value` uses the configured `mask` — verify both code paths
  actually agree on what "today" means.
- **Recommended resolution:** now (next session).

---

## [OPEN] FU-122 — Browser-verify Stock Overview Chunk 3 (row rebuild + image toggle)
- **Raised:** 2026-06-12 (Stock Overview Chunk 3 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **Row layout** reads left→right: bulk-checkbox (when in bulk mode)
     → coloured level square → name (bold) + zone (inline) → image
     placeholder (if `show_stock_images` is on) → ... → expiry → #recipes
     (when >0) → open/in-use → cart.
  2. **Level button** click opens the picker; selection updates the
     row's colour immediately (optimistic).
  3. **Zone** is clickable and filters the list to that location.
  4. **Status outline:** healthy row has no coloured border; an item
     expiring within 7 days gets an amber border; "Out of Stock" or
     expired items get a red border AND dim. Cross-theme check
     (Pesto light/dark, Cherry Cola dark — colours come from
     `--q-warning` / `--q-negative`).
  5. **Selection fills the row** (light primary tint) when bulk-mode
     selected; the splitter-peek state still draws its own solid
     outline; focus still draws the dashed accent outline.
  6. **Image toggle** at the top right flips between image / image-off
     icon; the row's image slot disappears when off and the row
     becomes visibly denser; reload-survives (server PATCH /me).
  7. **No regressions:** chip-shaped StockItemChip is GONE from rows
     but still renders on shopping-list lines + the stock-item
     detail page. "On N lists" chip is gone. The cart button still
     adds the item to the active draft list (C-7 will replace this
     properly later).
  8. **Virtualised list** still works after the row-size change — the
     `VIRTUAL_SCROLL_ITEM_SIZE = 72` constant in StockOverview.vue
     may need a tweak if rows feel too compact/spacious; q-virtual-
     scroll self-corrects after the first measure but tune the hint
     to match what you see.
- **Why:** static-only impl. Row rebuild is the biggest chunk of the
  plan; cross-theme + cross-state checks are the highest-risk
  verification. The image toggle is the FU-106 surface and needs an
  end-to-end PATCH /me confirmation.
- **Recommended resolution:** now (next session) — confirm and mark
  RESOLVED, or log defects.

---

## [OPEN] FU-121 — Browser-verify Stock Overview Chunk 2 (top toolbar + filters + footer)
- **Raised:** 2026-06-12 (Stock Overview Chunk 2 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **Top toolbar order**: New item · Export · Bulk select · Scan ·
     Stocktake · (spacer) · Search. Bulk select shows "Cancel" once
     bulk-mode is on.
  2. **Filter bar closed by default** on every page that uses
     `FilterBar` (Stock Overview, Cookbook overview, anywhere else
     it appears). Click "Filters" → panel expands; clicking again →
     collapses. Active-filter badge still surfaces while collapsed.
  3. **Level filter** is a single "Any level" dropdown; selecting a
     level filters; clearable. No floating count badges visible.
  4. **"Used in a recipe" filter is gone.**
  5. **Search placeholder** reads "Search" (no parenthesised hint).
  6. **Footer counts** in order: Shown · Well-stocked · Sufficient ·
     Low · Out · Flagged · Auto-add · Needs attention. Counts reflect
     the filtered set; recompute live when filters change.
  7. **No console errors** from the dropped `usedInRecipeOnly` /
     `getStockLevelColour` references.
- **Why:** static-only impl; the FilterBar default flip is a global
  change that touches every consumer, the level dropdown swap touches
  the most-used filter, and the composable's filter set lost one
  field (other callers might still expect it).
- **Recommended resolution:** now (next session). Includes the
  cross-page smoke pass for the FilterBar default flip.

---

## [OPEN] FU-120 — Browser-verify Stock Overview Chunk 1 (50-cap fix + virtualisation + filtered export)
- **Raised:** 2026-06-12 (Stock Overview Chunk 1 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. With a pantry of ≤50 items, the overview renders inside the existing
     `ListTransition` (glide-in still works); switch the threshold or load
     more items to confirm the swap to `q-virtual-scroll` above 50.
  2. Create / seed a pantry with **>50 items** (e.g. 120) and confirm
     every item is now reachable in the list (scroll the virtual list);
     `filteredStockItems.length` matches the backend count.
  3. **Filtered CSV export** — apply a level/location filter, hit Export
     → CSV, open the file → only the filtered rows appear. Repeat with
     **no filter active** → confirm the URL has no `ids=` param (the
     "everything" fast-path stays cheap).
  4. **Filtered Print/PDF** — same workflow against the print-view tab.
  5. Bulk-select + per-row actions still work inside the virtualised
     list (Quasar reuses DOM nodes; the row's emit handlers should
     fire normally).
  6. Splitter "peek" still opens when clicking a row in the virtualised
     list.
- **Why:** static-only impl. `q-virtual-scroll` swaps in-place for the
  existing list wrapper; row markup is unchanged but the wrapper change
  is the riskiest part. The filtered export round-trip also needs a
  real-DB pass.
- **Recommended resolution:** now (next session) — confirm and mark
  RESOLVED, or log defects.

---

## [OPEN] FU-119 — Browser-verify Cookbook Chunk 10 (multi-part recipes via named sections)
- **Raised:** 2026-06-12 (Chunk 10 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. `alembic upgrade head` applies migration `f6c8e3a9b1d2` on SQLite
     + Postgres; app boots; `verify_mappings()` passes for the new
     `RecipeSection` mapping + the `section_id` column on
     `RecipeIngredient` / `RecipeStep`.
  2. Existing recipes still load and render unchanged (no sections =
     same flat ingredient list, same cook-mode location grouping).
  3. **Create a recipe with two sections** ("Sauce", "Filling"); add
     ingredients, pick a section per row; save; reload → sections +
     section assignments persist; `RecipeCard` shows "2 parts" badge.
  4. **Cook mode:** ingredient panel groups under "Sauce" / "Filling"
     instead of by location; step card shows the section name as a
     chip; "All steps" overview repeats the header at each transition.
  5. **Delete a section** in the editor → its rows fall back to
     "Main" (FK SET NULL), save, reload → no orphans, no FK error.
  6. **Rename a section** in the editor (without touching ingredient
     rows) → server keeps the rows pinned because editor always sends
     `ingredients[]` + `sections[]` together; confirm no rows
     unsectioned themselves.
- **Why:** static-only impl; the section back-fill SQL UPDATE in the
  create handler and the `_resolve_section` UUID-vs-client_id branch
  in the update handler are the highest-risk new code paths and both
  need a real-DB pass.
- **Recommended resolution:** now (next session) — confirm in
  browser, then mark RESOLVED with whatever surfaces.

---

## [OPEN] FU-118 — Drag-and-drop for moving ingredients between sections
- **Raised:** 2026-06-12 (Chunk 10 deliberate scope-down)
- **Type:** enhancement
- **What:** Right now the only way to move an ingredient between
  sections is the per-row Section picker (`q-select`). The chunk plan
  also mentioned "drag", but the picker is already R-001-friendly
  (reuses the existing select) and ships the feature without net-new
  infra. Add drag-and-drop reorder + section reassignment when the
  same instinct hits the steps editor (see FU-094 for the parallel
  steps DnD work).
- **Why:** Power users with many ingredients in many sections will
  want bulk reassignment; the picker is fine for a few rows.
- **Recommended resolution:** later, opportunistic — pair with
  FU-094 (steps DnD) so we ship one DnD library / pattern.

---

## [OPEN] FU-117 — `RecipeStepsEditor` should let you pick a step's section
- **Raised:** 2026-06-12 (Chunk 10 deliberate scope-down)
- **Type:** enhancement
- **What:** Chunk 10 wired `section_id` on `RecipeStep` end-to-end
  (entity, table, DTO, cook-mode read path), but the steps editor
  doesn't yet surface a section picker. Hand-entered steps ship with
  `section_id = NULL` until this lands; URL importers can populate
  the field directly if they detect `HowToSection`. Surface should
  be: a small chip / select on each top-level step row in
  `RecipeStepsEditor` mirroring the ingredient row picker; sub-steps
  inherit visually so no picker needed there.
- **Why:** Without it, multi-part recipes still render correctly in
  cook mode if the importer (or a future bulk tool) sets `section_id`
  on steps — but a user editing in the SPA can't move a step into a
  named section.
- **Recommended resolution:** later, when there's another
  cookbook-polish session; small change, isolated to
  `RecipeStepsEditor.vue` + a `sectionOptions` prop.

---

## [OPEN] FU-116 — Browser-verify Cookbook Chunk 9 (cost + simple nutrition, opt-in)
- **Raised:** 2026-06-11 (Chunk 9 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. `alembic upgrade head` applies `e5b9d2c8a4f3` on SQLite +
     Postgres; app boots; `verify_mappings()` passes for the
     reshaped `Recipe`.
  2. **Both flags off (default):** open the recipe detail page →
     the editor has **no** kcal input next to servings; the sidebar
     shows **no** cost card and **no** nutrition card. The
     cookbook overview has **no** Kcal sort option and **no** Kcal ≤
     filter. (Confirms the gates work.)
  3. **Turn on nutrition (Settings → Account → Nutrition → Simple,
     install layer already on):** editor gains the **kcal per
     serving** input. Type a value → save → reload → value persists.
  4. **Nutrition card** appears in the detail sidebar when the
     recipe has a kcal value.
  5. **Cookbook overview Kcal axis + filter:** Sort by → **Kcal**
     option present. Pick it, flip direction → "Highest kcal first"
     / "Lowest kcal first" reads in the tooltip. Recipes without a
     kcal value sink to the bottom in either direction.
  6. **Kcal ≤ filter** input renders in the filter row. Type
     "500" → only recipes with kcal ≤ 500 (and recipes with no
     kcal value at all) survive.
  7. **Turn on money (Settings → Account → Money & budgets, install
     layer already on):** open a recipe whose ingredients link to
     products with current offers → sidebar shows **Estimated cost**
     card with a dollar value, a help-icon tooltip describing the
     math, and "(N / M ingredients priced)" coverage badge.
  8. **Cost math sanity:** pick a simple recipe (3 ingredients, all
     with linked products). Compute expected: for each ingredient,
     `quantity × current offer price ÷ product size_value`. Sum.
     Compare to the card's number — should match to 2 decimal
     places.
  9. **No linked products:** open a recipe whose ingredients aren't
     linked to any product → the Estimated cost card **doesn't
     render** (estimated_cost is null).
  10. **Partial coverage:** open a recipe where some ingredients
      have linked products and others don't → card renders with
      e.g. "(2 / 5 ingredients priced)".
  11. **Old freeform Nutrition expansion gone** from the detail
      page. A recipe with an existing `nutrition` text value still
      saves cleanly (the column round-trips through PATCH).
  12. **Money OFF + Nutrition ON:** cost card hidden, kcal
      input/sort/filter/card all visible.
  13. **Money ON + Nutrition OFF:** cost card visible, no kcal
      surfaces anywhere.
  14. **PATCH wire shape:** changing the kcal value sends
      `{ kcal: <int> }` and nothing else. Clearing it sends
      `{ kcal: null }`.
  15. Cross-theme (Pesto Light + Pesto Dark + Cherry Cola Dark) —
      both new sidebar cards read in all three.
- **Recommended resolution:** now/when env available — closes
  Cookbook Chunk 9.

## [OPEN] FU-115 — Drop the freeform `Recipe.nutrition` text column
- **Raised:** 2026-06-11 (Cookbook Chunk 9 impl)
- **Type:** finding / cleanup
- **What:** Chunk 9 stopped rendering/editing the freeform
  `recipe.nutrition` text column in favour of the structured
  `kcal: int | None` field. The column survives in the DB + on the
  DTO + in the form's hydrate/save plumbing so existing data isn't
  destroyed mid-session. Before dropping, **audit prod-style
  installs** (or any non-seed user data) to confirm no user has
  typed something irreplaceable in there — possibly a recipe note
  on macros / micros that pre-dates Chunk 9. If nothing is found
  worth saving, write a migration that drops the column and clean
  up the four places it's still referenced in the SPA / API.
- **Where it still lives (as of Chunk 9):**
  - `domain/entities/recipe.py` — `nutrition: str | None` field.
  - `persistence/table_mappings.py` — `Column("nutrition", String, ...)`.
  - `features/recipes/get_recipes.py` — RecipeDto carries it.
  - `features/recipes/create_recipe.py` /
    `update_recipe.py` — request models accept it.
  - `web_app/src/models/recipe.ts` — `nutrition: string | null`.
  - `pages/RecipeDetailPage.vue` — `form.nutrition` still round-
    trips on save (hidden from UI, but preserved).
- **Recommended resolution:** later, after Chunk 9 has been in real
  use for a beat and we can confirm no user has typed something
  important there. Dedicated cleanup chunk: migration + audit +
  removal sweep.

## [OPEN] FU-114 — Browser-verify C-cross Chunk 5 (image-display opt-in + deferred image column)
- **Raised:** 2026-06-11 (Chunk 5 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. `alembic upgrade head` applies `d4a7c9b3e8f1` on SQLite +
     Postgres; app boots; `verify_mappings()` passes for the
     reshaped `User`.
  2. New user → `show_recipe_images` and `show_stock_images` both
     default **true**. Existing users post-migration are the same
     (server default `'1'`).
  3. Open Cookbook overview. The header now has an **image** icon
     button next to "Import from URL". Tooltip reads "Hide recipe
     photos · saved across sessions".
  4. Recipe cards render their photos as today.
  5. Open a recipe detail page with an image → header preview
     shows the photo.
  6. **Click the toggle.** Icon flips to `image_not_supported`,
     success toast "Recipe photos hidden." appears.
  7. Recipe cards now show the coloured-initial placeholder (no
     photo). **In DevTools Network**, confirm the bytes endpoint
     `GET /api/recipes/<id>/image` is **NOT** called for the
     visible cards (the previous flag-on behaviour would have
     fetched them).
  8. Open a recipe detail page (with an image). The header preview
     shows the placeholder; **the editor's pick/clear buttons
     still work** — pick a new image → preview shows the
     freshly-picked image (the dirty-form branch ignores the
     opt-in, per the IMPL plan's "editor stays usable" carve-out).
     Save → reload → preview hides again (saved image is gated).
  9. **Toggle back on.** Toast "Recipe photos shown." Cards +
     detail show photos again. Saved images survived intact.
  10. **/me payload:** `GET /api/users/me` carries
      `show_recipe_images` + `show_stock_images` on every load.
      The toggle PATCH sends only `{ show_recipe_images: bool }`
      and nothing else.
  11. **Cross-session persistence:** flip the toggle, sign out,
      sign back in — the toggle remains in the chosen position.
      Sign in from a second device → same.
  12. **FU-090 perf fix:** load the cookbook overview with N≥10
      recipes that all have images. The recipe-list response
      payload size is now substantially smaller than before
      (image bytes are no longer included in the rows; only
      `has_image: bool` survives). Backend logs / `sqlalchemy.echo`
      show no `SELECT image FROM Recipe` on the list path.
  13. **Stock-side flag round-trips even though no UI writes it
      yet** (FU-106 will land the inline button in C-1 row
      redesign): `PATCH /me` body `{ show_stock_images: false }`
      survives a reload.
  14. Cross-theme (Pesto Light + Pesto Dark + Cherry Cola Dark) —
      the new icon button reads in all three.
- **Recommended resolution:** now/when env available — closes the
  C-cross pre-consumer foundations.

## [OPEN] FU-113 — Browser-verify C-cross Chunk 4 (location-display policy)
- **Raised:** 2026-06-11 (Chunk 4 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. Open Stock Overview. A stock item assigned to e.g.
     **Pantry → Middle shelf → Left side** now shows **"Pantry"** on
     its location chip (zone-only). Hover the chip → tooltip reads
     *"Pantry › Middle shelf › Left side · Filter to this location"*.
  2. A stock item assigned only to **Pantry** (zone, no sub-area) →
     chip reads *"Pantry"*; tooltip is just *"Filter to this
     location"* (no path prefix because there's no sub-detail to
     reveal).
  3. **Click the chip** — filters the overview to that location.
     Filter still uses the underlying `stock_location_id`, no
     regression.
  4. Open a stock-item detail page. The Location row in the header
     panel reads as the zone (or `—` if unset). Hover → tooltip
     reveals the full breadcrumb when one exists.
  5. Open a shopping-list detail. Each line's `place`-icon location
     reads the zone only. Hover → full breadcrumb tooltip.
  6. **Start shop mode** on a list with lines spread across
     sub-areas under the same zone (e.g. two Fridge lines under
     "Crisper" + one under "Top shelf"). Confirm:
     - The section label above the current item shows the **zone**
       ("Fridge"), not the sub-area.
     - The hover tooltip on the section label shows the full path
       for the current line.
     - The **shop order still splits the two sub-areas apart** —
       crisper items aren't interleaved with top-shelf items just
       because they share the zone (sortKey discipline still uses
       the full breadcrumb).
  7. Open RecipeCookMode. The ingredient group headers continue
     to show zone-only (this hasn't changed) — confirm no
     regression. Per-row location chips don't render in cook
     mode, so there's no chip tooltip to test there.
  8. Cross-theme sanity (Pesto Light + Pesto Dark + Cherry Cola
     Dark) — tooltips read in all three.
- **Recommended resolution:** opportunistic — the policy change is
  small enough that the next time a verifier opens the app, this
  audit takes ~3 minutes.

## [OPEN] FU-112 — Browser-verify C-cross Chunk 3 (per-user nutrition mode + reserved seam)
- **Raised:** 2026-06-11 (Chunk 3 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. `alembic upgrade head` applies `c8d3f4a9b2e1` on SQLite +
     Postgres; app boots; `verify_mappings()` passes for the reshaped
     `User` + `AppSetting`.
  2. Open Settings → Account → **Nutrition** card. Three-way toggle
     reads **Off** by default. Captions read sensibly.
  3. **Install OFF, user Off (default):** whole toggle is disabled,
     caption reads "This install has nutrition turned off…".
  4. Admin enables `nutrition_enabled` in System → Features. Return
     to Account → Nutrition. **Off** + **Simple** are now clickable,
     **Complex** is disabled. Caption explains complex needs a source.
  5. Flip to **Simple** → success toast → reload → still on Simple.
  6. Flip back to **Off** → success toast → reload → still off.
  7. **Server rejects complex without seam:** as an admin, send
     `PATCH /api/users/me` with body `{ nutrition_mode: 'complex' }`.
     Get a 400 with the "Complex nutrition mode needs a nutrition
     data source configured…" message.
  8. **Configure the seam:** as an admin, send
     `PATCH /api/app-settings` with body
     `{ nutrition_db_source: 'usda-fdc' }`. `GET /api/health` now
     reports `features.nutrition_complex_available: true`.
  9. Return to Account → Nutrition (refresh page so `useFeatureFlags`
     picks up the change). **Complex** is now clickable. Pick it →
     success toast → reload → still on Complex.
  10. **Re-empty the seam** via PATCH with `nutrition_db_source: ''`.
      Refresh the Settings page. The user remains on Complex
      *server-side* (we don't auto-rewrite), but the toggle's
      Complex option is disabled and the caption reads accordingly.
      The user can switch back to Off / Simple normally.
  11. **PATCH wire shape:** flipping the toggle sends a body with
      `{ nutrition_mode: '<mode>' }` and nothing else. Confirm in
      DevTools Network.
  12. **/me payload** carries `nutrition_mode` on every load.
  13. Cross-theme (Pesto Light + Pesto Dark + Cherry Cola Dark) —
      the new card reads in all three.
- **Recommended resolution:** now/when env available — before C-4
  Chunk 9 (cost + nutrition) lands on top.

## [OPEN] FU-111 — Browser-verify C-cross Chunk 2 (per-user money opt-in)
- **Raised:** 2026-06-11 (Chunk 2 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. `alembic upgrade head` applies `b5c1d9a4e3f2` on SQLite + Postgres;
     app boots; `verify_mappings()` passes for the reshaped `User`.
  2. As a regular signed-in user, open Settings → Account. The new
     **Money & budgets** card appears above the Grocery budget card
     with a toggle, currently off (the default).
  3. **Install ON, user OFF (default):** the toggle is enabled, the
     Grocery budget card is **hidden**. Flip the toggle on → success
     toast → Grocery budget card appears → set a budget number + a
     period → reload → toggle still on, budget settings persisted.
  4. **Toggle off again** → success toast → Grocery budget card
     hides → reload → toggle is off, **but the saved budget number
     is still on the server** (verified by flipping back on and
     seeing the same value appear).
  5. **Install OFF (admin disables in System → Features → Money):**
     the per-user toggle is **disabled** with a caption *"This
     install has money features turned off…"*. Grocery budget card
     stays hidden regardless of the per-user value.
  6. **PATCH wire shape:** flipping the toggle sends
     `PATCH /api/users/me` with body `{ money_features_enabled: true|false }`
     (and nothing else). Confirm in DevTools Network.
  7. **/me payload:** `GET /api/users/me` carries
     `money_features_enabled` in its response body.
  8. **Composable layering:** `useMoneyEnabled().moneyEnabled.value` is
     `installEnabled && userEnabled` — confirm via DevTools when one or
     both are flipped.
  9. **Error path:** flip the toggle while the server is reachable but
     the PATCH 500s → the toggle reverts to its previous state +
     negative toast fires.
  10. Cross-theme (Pesto Light + Pesto Dark + Cherry Cola Dark) — the
      new card reads in all three.
- **Recommended resolution:** now/when env available — before C-cross
  Chunk 3 lands on top.

## [OPEN] FU-110 — Browser-verify C-cross Chunk 1 (feature-flag panel + opt-in plumbing)
- **Raised:** 2026-06-11 (Chunk 1 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. `alembic upgrade head` applies `a3b8e2f4c1d7` on SQLite + Postgres;
     app boots; `verify_mappings()` passes for the reshaped `AppSetting`.
  2. As an admin user: open Settings → System → **Features** panel.
     Five toggles appear (Meal planning ON, Money / Nutrition /
     Companion ingestion / Weekly deals emailer all OFF). Captions
     read sensibly.
  3. Flip each toggle on → success toast + the saved value persists
     across a reload.
  4. Flip each toggle off → success toast + persists.
  5. As a non-admin user: the panel renders the "no admin
     permissions" banner; the toggles aren't visible.
  6. **Health endpoint contract:** `curl /api/health` JSON carries
     `features.meal_planning` / `features.money` / `features.nutrition`
     / `features.companion_ingestion` / `features.deals_email` keys
     alongside the pre-existing `auth` / `audit` / `scanning` /
     `multi_user` / `email` / `assistant`. Values match what the
     panel shows.
  7. **Composable freshness:** open the panel + open a second tab on
     any page using `useFeatureFlags()` (today there are no
     consumers — verify via DevTools that `flagsLoaded.value` is
     `true` and the named computeds match the panel). Flip a toggle
     in tab 1 → composable cache only refreshes in tab 1 (per-session
     cache; documented as Chunk-1 behaviour; cross-tab refresh is a
     later layer).
  8. **Migration safety on existing installs:** an install that's
     been using meal planning happily should see
     `meal_planning_enabled = True` after the migration (its server
     default). Confirm against a non-empty pre-Chunk-1 row.
  9. **Save error path:** disable network / wait for PATCH to
     500-out → toggle reverts to its previous state; negative toast
     fires with the error caption.
  10. Cross-theme sanity (Pesto Light + Pesto Dark + Cherry Cola
      Dark) — the new panel reads in all three.
- **Recommended resolution:** now/when env available — before
  C-cross Chunk 2 lands on top.

## [OPEN] FU-109 — Decide whether to re-add the RecipeCard "would-be-cookable" dim
- **Raised:** 2026-06-10 (FU-083 follow-up; user wants a real decision
  later)
- **Type:** open product / UX decision
- **What:** FU-083 removed the `RecipeCard --dim` opacity treatment.
  The dim previously fired in **two** places (both used the same
  `highlightStockItemIds` prop):
  1. **`StockItemDetailPage.vue:332`** — "Recipes that use this
     item" tab. A recipe dimmed when restocking *this* item alone
     wouldn't make it cookable (i.e. it was missing other ingredients
     too).
  2. **`RecipesOverview.vue`** — when the user had any ingredient in
     the "Uses ingredients" include list. Same semantics: a recipe
     dimmed when it was missing other ingredients beyond the
     highlighted set.
  Removal landed in both surfaces; the prop is still on `RecipeCard`
  but unused for visual.
- **Why removed:** FU-083 feedback said the dim wasn't immediately
  obvious without a legend, and the card already carries a
  "Missing N ingredients" copy on its face — so the dim doubled up
  the same signal.
- **Why it might come back:** the dim conveys "restocking *just*
  this item wouldn't be enough" without requiring the user to count.
  It's particularly valuable on the **stock-item detail** surface
  (the dim said "go shop for these others too"). On the cookbook
  overview the value is murkier because the filter set is the user's
  own input.
- **What the decision needs:**
  1. **Keep removed everywhere?** (current state) — leaves the card
     copy as the only "this is missing things" signal.
  2. **Re-add only on `StockItemDetailPage`?** — that was the
     surface where the dim was most defensible (single-item context;
     user looking at "what does restocking this unlock?").
  3. **Re-add everywhere, with a legend?** — `q-tooltip` on dimmed
     cards explaining the semantics; same icon/text legend on the
     filter bar so the meaning is discoverable.
- **Recommended resolution:** **user decision required.** When you
  pick a direction, the code path is:
  - Re-add the `dim` computed in `RecipeCard.vue` (was lines 279–283
    pre-removal — see git history).
  - Re-bind `:class="{ 'recipe-card--dim': dim }"` on the root.
  - Re-add the `.recipe-card--dim { opacity: 0.55 }` rule.
  - If overview-only: gate on a prop like `:dim-when-incomplete`
    that the consumer passes (off by default; on for
    `StockItemDetailPage`).

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

## [OPEN] FU-107 — Standardise API date serialisation on ISO 8601 (drop RFC 2822 default)
- **Raised:** 2026-06-10 (FU-083 "Planned" filter follow-up — RFC vs ISO
  parse bug)
- **Type:** finding / cross-cutting cleanup
- **What:** Flask's default JSON encoder serialises Python `date` /
  `datetime` as **RFC 2822** with a GMT suffix (e.g.
  `"Wed, 10 Jun 2026 00:00:00 GMT"`). That format is an HTTP-Date relic
  — fine for `Last-Modified` headers but actively painful in JSON
  payloads consumed by JS clients, because:
  1. **No timezone semantics** for what's a calendar-only date —
     "Wed, 10 Jun" is parsed by `new Date()` as midnight UTC, which
     becomes "Tue, 09 Jun" in any negative-offset timezone. Every
     consumer either needs to know it's calendar-only and reconstruct
     from UTC parts (the workaround just applied to the "Planned"
     filter), or it gets day-off-by-one bugs.
  2. **Fragile string-based parses** — Chunk 1's first attempt at the
     "Planned" filter sliced `YYYY-MM-DD` from the front of the
     string. That works on ISO; silently fails on RFC 2822
     ("Wed, 10 Ju") and drops every entry.
  3. **Differs from every other modern API** the SPA talks to —
     `created_at` / `expiry_date` etc. all come back RFC, but the
     same data going *out* (PATCH requests) is sent ISO by the SPA.
     Inconsistent.
- **Where it bites today:**
  - `MealPlanEntryDto.scheduled_for` (Date) — caught + worked around.
  - `MealPlanDto.start_date` (Date).
  - `Recipe.last_made_on` (DateTime).
  - `StockItem.expiry_date` (Date or DateTime).
  - Audit events, shopping-list shop-day, alert created_at, etc. —
    anywhere a Python `date` / `datetime` lands in a DTO.
- **Recommended resolution:** override Flask's JSON provider (Flask 2.3+
  ships `app.json_provider_class`) with one that emits ISO 8601 for
  `date` and `datetime`. Either:
  - Calendar-only `date` → `"2026-06-10"`; `datetime` → full ISO with
    offset → `"2026-06-10T15:00:00+00:00"`; **or**
  - Both use ISO with appropriate granularity.
  Tests cover round-trips through every dated DTO + the SPA models that
  read them. Drop the RFC-aware workarounds where they exist (start
  with `plannedRecipeIds` in `RecipesOverview.vue`).
- **Recommended timing:** **later — dedicated `api-date-iso-shift` pass**.
  Not a one-line change because every existing SPA consumer that
  parses these fields needs auditing — some might be relying on
  `new Date(rfc)` happening to work for their use case. Schedule as
  its own focused PR with a tested verification list of every dated
  field.

## [RESOLVED] FU-106 — Stock Overview image collapse/expand inline button (C-cross §2.8 surface)
- **Raised:** 2026-06-10
- **Resolved:** 2026-06-12 by Stock Overview Chunk 3 — inline image
  toggle next to the search input flips `show_stock_images` via the
  existing `useImagePrefs()` composable; the row's image slot is
  `v-if="showStockImages"` so density actually changes when toggled.
  Slot is currently a neutral placeholder (40×40 sunken square); it
  becomes the real photo container when FU-033 wires
  `StockItem.image` bytes. Static-only impl; browser-verify is
  **FU-122**.

## [OPEN] FU-105 — Browser-verify Cookbook Chunk 8 (versions + detail-endpoint fix)
- **Raised:** 2026-06-10 (Chunk 8 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. `alembic upgrade head` applies `e1f6a2b4c8d9` on SQLite + Postgres;
     app boots; `verify_mappings()` passes for the reshaped `Recipe`.
  2. **Detail endpoint hydrates:** open a recipe with structured
     steps. Confirm the editor's Structured / Freeform toggle
     populates with the saved steps. (Latent bug from Cookbook
     Chunk 6 / Cook-Mode Chunk 5 — the SPA's `getAsync(id)` used
     to drop them.)
  3. **New version action:** open a recipe → kebab → "New version".
     - Source had no `version_group_id` (singleton): the action
       allocates one + back-fills the source. Both source and copy
       now share the id.
     - Source already had a group: the copy reuses it.
  4. **Sibling card renders:** after "New version", both the source
     and the copy show an "Other versions" card listing the other
     row(s). Singletons (no siblings) hide the card.
  5. **Naming:** first "New version" on a singleton → "(v2)". A
     second click on the source → "(v3)". A click on the copy →
     also lands on the next number (server counts siblings, not
     parent).
  6. **Round-trip carry-through:** the new version inherits
     ingredients, tools, structured steps (with sub-step + ingredient
     refs remapped to the new ingredient ids), tags, cuisine,
     category, collection, source URL, image. The image shows on
     the copy without re-uploading.
  7. **Independent edits:** edit the copy → save → confirm the
     source is unchanged. Same the other way round.
  8. **Sibling delete:** delete one version → the other(s) stay,
     "Other versions" card on the survivor updates.
  9. **Meal plan + cookable:** confirm the meal-plan recipe picker
     and the cookable filter see *both* siblings (DEC-2: users pick
     when allocating). No special version-aware UI.
  10. **Allocations stay per-recipe:** schedule both siblings on a
      meal plan day. Allocated badge on each reads its own
      `available_meals`, not a merged total.
  11. **Backup → restore:** `version_group_id` round-trips through
      backup/restore (it's a column on the Recipe row — no manual
      section change was needed).
- **Recommended resolution:** now/when env available — pairs with
  FU-103 (Chunk 7) and FU-093 (Chunk 6) for a single cookbook
  walkthrough.

## [OPEN] FU-104 — Move the URL recipe importer into the private companion app (legal posture)
- **Raised:** 2026-06-10 (user, during Cookbook Chunk 7 review)
- **Type:** policy / distribution-posture decision (cross-cutting)
- **What:** The URL importer (`features/recipes/import_recipe_from_url.py`
  + the SPA dialogs added in Cookbook Chunk 7) **fetches third-party
  pages and extracts content** — schema.org JSON-LD for the happy path,
  raw `<title>` + body text in the degraded path. That's
  user-initiated, single-page, and modest-scale, but it's still:
  - **automated retrieval of copyrighted content** (recipe text /
    instructions are often editorial copyright, even if individual
    ingredient lists aren't);
  - **likely against most recipe-site ToS** (which boilerplate-ban
    scraping / automated access);
  - **fetched from our server's IP** in the current shape, not the
    user's browser — so the *operator* of a hosted Dora instance is
    the one making the request, not the user. That's the part most
    likely to attract a takedown letter / IP block / CFAA-style
    claim if it ever runs at scale on a public managed instance.
  - **CDN-fingerprintable** at scale via the `_FETCH_HEADERS`
    user-agent.
  The IMPL_PLAN_COOKBOOK shape lets it live anywhere; the master
  `RECONCILED_FINISHING_PLAN.md` Decision 1 already moved the
  **retailer scraper** out of the core app for the same reason (the
  precedent is established).
- **What this FU is asking us to decide:**
  - **Move the importer into the private companion app** (the same
    self-hosted / "personal-use, off-by-default, runs on the user's
    machine, hits sites from the user's own IP" surface that owns the
    retailer scraper). Core Dora keeps the schema (Recipe.source,
    structured steps, the create endpoint that accepts the parsed
    DTO) — the *fetcher* is what relocates.
  - **Or:** keep it in core but switch the architecture so the
    *browser* fetches the URL (CORS-permitting only — recipe sites
    rarely allow CORS, so practical coverage drops to maybe 10%) and
    posts the HTML up to the parser. Lower legal exposure but a much
    worse import experience.
  - **Or:** keep as-is, scope it as a personal-instance feature
    documented as "use only on URLs you have permission to scrape"
    + drop the named-site list in the dialog copy so we're not seen
    as encouraging it.
- **Why discuss now (not later):** the importer just got a more
  visible surface (overview button) in Chunk 7 + a graceful-degrade
  path that *succeeds* even on no-JSON-LD pages, which broadens the
  set of URLs it'll get pointed at. Better to settle the posture
  before users get used to the current shape and the named-site copy.
- **Constraints to honour in the decision:**
  - **Distribution posture (R-005):** core stays SaaS-style /
    self-hostable from one codebase. Moving the importer to the
    companion app means defining a clean "companion sends parsed
    DTO to core" boundary (companion is its own deployable; core
    treats it as an authenticated source of preview DTOs).
  - **Charter principle P10 Anti-creep:** don't bake "scrape any
    URL" into core if the legal answer is uncertain.
  - **Charter principle P1 Effortless:** users still expect the
    feature to work — the answer can't be "we removed it"; it can be
    "you run a companion locally and it stays effortless from your
    perspective".
- **Recommended resolution:** **discuss + design with user before
  next prompt that touches the importer.** Surface to a proposal
  doc (`docs/04_proposals/IMPORTER_DISTRIBUTION_POSTURE.md` or
  similar) once a direction is picked. Likely outcome: move the
  *fetcher* to the companion app (precedent: retailer scraper),
  keep the *parser* + Recipe.source schema in core. Until then, no
  new public-facing surface should advertise the importer (so:
  Chunk 7's overview button + named-site copy is fine for the
  self-hosted single-user case but should be flagged on any
  managed-instance / multi-user deployment as the next prompt
  here.) — see also `RECONCILED_FINISHING_PLAN.md §7.5` for the
  distribution-posture checklist this needs to pass.

## [OPEN] FU-103 — Browser-verify Cookbook Chunk 7 (source + URL importer)
- **Raised:** 2026-06-10 (Chunk 7 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. `alembic upgrade head` applies migration `d0e5f1a3b8c7` on SQLite
     and Postgres; app boots; `verify_mappings()` passes for the
     reshaped `Recipe` (`source` field present).
  2. **Detail-page source field:** open a recipe; the Source URL card
     appears under Instructions / Nutrition. Typed value round-trips
     through save → reload. Clearing the field → save → reload shows
     it empty (explicit null clears server-side).
  3. **Open affordance:** entering an `http(s)://` URL surfaces the
     "Open" ghost button; clicking opens the page in a new tab.
     Non-http values (or blank) hide the button.
  4. **Detail-page importer:** import a recipe from a schema.org-rich
     site (e.g. BBC Good Food). The source URL lands in the
     `source` field (NOT appended to Instructions). Steps/ingredients
     are parsed.
  5. **Degraded fallback:** import a URL that has no schema.org/Recipe
     JSON-LD (any random blog post). Confirm:
     - the importer doesn't 422;
     - the page title + body text land in name/instructions;
     - the warning toast fires: "Couldn't auto-structure that page";
     - `source` is set to the URL.
  6. **Overview Import button:** the new "Import from URL" button sits
     next to "New recipe". Click → dialog opens → paste a URL →
     Import → new recipe appears in the cache → router lands on its
     detail page.
  7. **Unmatched ingredients toast:** import a URL whose ingredients
     mostly don't match your stock items. Confirm the success toast
     counts the unmatched ones ("3 ingredients couldn't be matched —
     add them manually").
  8. **Degraded path from overview:** import a no-JSON-LD URL via the
     overview button. Warning toast fires; new recipe is created with
     the scraped body text in Instructions; detail page opens.
  9. **No "Source: <url>" appendix:** an existing recipe with the old
     in-instructions "Source: …" line still loads fine (no migration
     is attempted) — the user can move the URL into the new field
     manually.
  10. **Backup → restore:** the new `source` column round-trips
      through backup/restore without a manual section change.
- **Recommended resolution:** now/when env available — pairs with
  FU-093 (Chunk 6 structured steps) and FU-091 (Chunk 5 images +
  tools) for a single cookbook end-to-end walkthrough.

## [OPEN] FU-102 — Extract `RecipeImportDialog` shared component (R-001 threshold hit)
- **Raised:** 2026-06-10 (Cookbook Chunk 7 impl)
- **Type:** R-001 cleanup
- **What:** Chunk 7 adds an import-from-URL dialog on
  `RecipesOverview.vue`. The detail page already has one
  (`RecipeDetailPage.vue`); the two now share copy + the URL input
  shape + the importer call + the degraded-vs-success toast branching.
  They diverge on what happens with the preview — detail overwrites
  the current form, overview creates a new recipe and navigates. Two
  surfaces ≈ R-001's "if a pattern recurs (≈2–3 uses)" threshold;
  extract a `RecipeImportDialog.vue` with a `mode: 'overwrite' |
  'create'` prop (or two events: `@preview` for overwrite,
  `@created` for create) once a third caller appears or the duplicated
  copy starts to drift.
- **Recommended resolution:** opportunistic — when the dialog needs
  to change in both places at once (copy tweak, validation rule,
  loading-state UI), do the extraction in the same PR.

## [OPEN] FU-101 — Browser-verify Cook Mode Chunk 6 (cooking-for headcount rescale)
- **Raised:** 2026-06-09 (Chunk 6 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **Default seed:** open cook mode on a recipe with `servings = 4`.
     The "Cooking for" input shows 4. Recipe with `servings = null`
     shows 1.
  2. **Rescale up:** bump to 6. Every ingredient quantity rescales by
     1.5×. `200g flour` → `300g` (or `300 g` if continuous-snap
     produces `300`); `2 eggs` → `3 eggs` (round up from 3).
  3. **Rescale down:** drop to 2. `200g` → `100g`; `4 eggs` → `2 eggs`.
  4. **Fraction snap (continuous):** a 4-serving recipe with `1 cup`,
     scaled to 3, gives `¾ cup` (not `0.75`). Scaled to 6, gives
     `1½ cup`.
  5. **Countable rounding:** a 4-serving recipe with `1 egg`, scaled to
     3, gives `1 egg` (rounds 0.75 → 1, floored at 1). Scaled to 6,
     gives `2 eggs` (1.5 → 2).
  6. **Floor at 1:** any countable that would round to 0 stays at 1
     (can't cook with 0 eggs).
  7. **Sub-tolerance fractions:** `0.5 cups`, scaled by 1.0 (no change)
     shows `½ cup` directly.
  8. **Blur clamp:** clear the input → loses focus → re-clamps to 1
     (and quantities don't collapse to zero / NaN mid-cook).
  9. **Min=1:** typing `0` and blurring → re-clamps to 1.
  10. **Session-only:** rescale, exit cook mode, come back. The input
      shows the recipe's original `servings` again. Saved recipe is
      unchanged.
  11. **Gram fraction edge case (note from impl):** a recipe step that
      produces e.g. `7.5g` of an ingredient will render `7½ g`, not
      `8g` as the IMPL plan's example suggested. Watch a few real
      recipes — if gram fractions read weird in practice, flip
      `g/kg/ml/l/mg` to integer rounding in `scaleQuantity.ts`
      (would treat them as countable for rounding purposes while
      leaving the spacing convention via `formatQuantity` intact).
- **Recommended resolution:** now/when env available — pairs with
  FU-093 (Chunk 6 structured steps), FU-096 (Chunks 1–3),
  FU-100 (Chunk 5) for a single end-to-end cook-mode walkthrough.

## [OPEN] FU-100 — Browser-verify Cook Mode Chunk 5 (highlight + tools + hints)
- **Raised:** 2026-06-09 (Chunk 5 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **Structured recipe (Cookbook Chunk 6 editor):** open cook mode on
     a recipe with structured steps that name specific ingredients
     and tools per step. Confirm the highlight tracks:
     - the named ingredient rows tint + get a left accent;
     - the tools panel shows below ingredients (it only appears when
       the recipe lists tools);
     - the step-referenced tools light up; other tools dim.
  2. **Sub-step:** a step nested under a parent shows the "Sub-step"
     chip above its headline.
  3. **Hint:** a step with a hint renders the hint line under the
     headline with the lightbulb icon.
  4. **Unstructured fallback:** open cook mode on a recipe with only
     `instructions` (no structured steps). Confirm the text-matched
     highlight still fires when ingredient names appear in step text.
  5. **No tools panel** when the recipe lists no tools.
  6. **Tick state really gone:** no checkbox on ingredient rows; no
     checkbox in the "All steps" expansion (tap the step text to jump
     there).
  7. **Finish flow** now lists *every* ingredient on the recipe (with
     swaps applied), regardless of any mid-cook interaction.
  8. **Voice:** "Done" command is gone from the Sous Chef help popover.
     "Next" / "Previous" / "Repeat" / timer verbs still work.
  9. **Step navigation** via the "All steps" expansion still jumps to
     the right index; sub-steps render indented in the list.
  10. **Cross-theme** sanity check (Pesto Light + Pesto Dark + Cherry
      Cola Dark) — the highlight tint reads in dark mode.
- **Recommended resolution:** now/when env available — pairs with
  FU-096 (Chunks 1–3 verify) and FU-093 (Chunk 6 verify) for a single
  cook-mode + structured-steps walkthrough.

## [OPEN] FU-099 — Raw backend / Pydantic error strings leak into user-facing toasts → design pass
- **Raised:** 2026-06-09 (user, after the recipe-save Pydantic error)
- **Type:** design discussion needed (cross-cutting UX)
- **What's broken:** When a request fails server-side validation, the
  toast surfaces the **raw Pydantic message** as the caption — e.g.
  *"Input should be a valid integer, unable to parse string as an
  integer"* or *"String should have at least 1 character"*. These are
  developer-facing messages intended for API client implementers; to an
  end user they read as jargon (the recipe-save flow is what surfaced
  the report, but the pattern lives in `describeApiError(err)` and
  affects most pages).
- **Where it leaks today (initial scan, not exhaustive):**
  - `services/errorHandling/apiErrorHandler.ts` — likely concatenates
    the backend's `errors` map values verbatim.
  - Most page-level catch blocks: `caption: describeApiError(err) || ''`
    in recipe save, stock item save, shopping list edits, etc.
- **Status:** **NOT to be implemented yet — prompt the user to design
  this first.** The right answer touches the API error-shape contract,
  the client error-mapping layer, and every form's field-error
  rendering. Before writing code, the next session should walk the
  user through the design choices below and reach decisions.
- **Design questions to put to the user (start of next session on
  this item):**
  1. **Server vs client mapping** — does the backend stay verbatim
     Pydantic and the client translate, or does the backend ship a
     friendlier message per field (and keep the raw code alongside
     for debugging)?
  2. **Inline vs toast** — when a save fails on a field the user can
     see, should the toast disappear in favour of an inline
     `error-message` on the offending q-input? Or both? What about
     forms where the bad field isn't currently rendered (collapsed
     section, off-screen)?
  3. **Generic vs specific copy** — is *"Servings must be a whole
     number"* worth the per-field copy budget, or is *"Couldn't save
     — check the highlighted fields"* + inline enough?
  4. **Network / unknown failures** — what's the fallback caption
     when the failure isn't a validation error (5xx, network down,
     auth expired)? Currently mixed.
  5. **Dev debuggability** — agreed that the raw detail goes to
     `console.warn` for dev visibility, but should there also be a
     keyboard shortcut / hidden affordance for dev users to copy the
     raw error from the toast?
  6. **Scope** — only the most-trafficked forms (recipe / stock item
     / shopping list / edit dialogs) for the first pass, or sweep the
     app?
- **Recommended resolution:** **discuss + design with user first**,
  *then* spin a proposal/IMPL plan. Do not patch toasts piecemeal — the
  fix lives in one shared layer, not in 20 catch blocks.

## [OPEN] FU-098 — Unsaved-changes guard on navigation (app-wide)
- **Raised:** 2026-06-09 (user, after cook-mode batch)
- **Type:** finding / cross-cutting UX gap
- **What:** Navigating away from an editor while it has unsaved edits
  **silently discards** them — there's no confirm prompt. The user noticed
  this on the recipe detail page, but it's likely app-wide: stock item
  detail, shopping-list detail, settings, anywhere there's an `isDirty`
  ref on a form. The recipe detail page already tracks `isDirty.value`
  for the cook-mode guard, so the data is there — what's missing is a
  generic guard that intercepts router navigation (`beforeRouteLeave` /
  `onBeforeRouteLeave`) **and** browser-level navigation (`beforeunload`)
  when any tracked page is dirty.
- **Scope:** every editable surface, not just recipes. Should be a
  shared pattern (a composable `useUnsavedChangesGuard(isDirtyRef)`)
  rather than 10 copies — fits **R-001** (componentise the recurring
  pattern). The confirm copy should match A3 modal standard (Cancel /
  Discard changes / Save & continue — though "Save & continue" requires
  a per-page save function so it's optional).
- **Pages currently lacking the guard (spot list, not exhaustive):**
  - `RecipeDetailPage.vue` — tracks `isDirty`, no guard.
  - `RecipeCookMode.vue` — cook session state not guarded.
  - `StockItemDetailPage.vue` — likely no guard.
  - `ShoppingListDetail.vue` — line edits.
  - Settings pages (theme, vocab, system).
- **Recommended resolution:** **next polish prompt / Wave-A follow-on** —
  ship `useUnsavedChangesGuard` as a single composable wired into every
  editor page via `onBeforeRouteLeave` + a `beforeunload` listener.
  Probably a 1–2 hour pass; do it as one focused PR rather than
  drip-feeding per page.

## [OPEN] FU-097 — Roll out `formatQuantity()` to recipes/shopping-list surfaces
- **Raised:** 2026-06-09 (Cook Mode Chunk 2)
- **Type:** finding / R-001 + R-003 cleanup
- **What:** The new
  `web_app/src/helpers/formatQuantity.ts` centralises DEC-3 unit spacing
  (`ml g kg l mg oz lb floz pt qt` = no-space; everything else spaced) but
  Chunk 2 only swapped the cook-mode ingredient row over. Other surfaces
  still inline the quantity + unit by hand:
  - `RecipeDetailPage.vue` ingredient editor rows
  - `RecipeEditDialog.vue`
  - `RecipeCard.vue`
  - `ShoppingListDetail.vue` + shop-mode card
  - Print/export view (`ExportPrint.vue`)
  - Cookbook overview cards
  Each currently formats independently (some space, some don't, some leave
  the unit blank when null). Switch them to `formatQuantity` so the
  convention can never drift.
- **Recommended resolution:** opportunistic — fold into the next prompt
  that touches each surface; or a focused 30-minute "quantity spacing
  sweep" pass.

## [OPEN] FU-096 — Browser-verify Cook Mode Chunks 1–3
- **Raised:** 2026-06-09 (Cook Mode Chunks 1–3 impl; static-only, no env)
- **Type:** finding / verification (blocks trusting Cook Mode rewrite)
- **What:** Verify, in order:
  1. **Chunk 3 ingredient grouping:** open cook mode for a recipe whose
     ingredients span several locations. Confirm one card per *base*
     location (a sub-area like "Pantry > Spice Rack" collapses to
     "Pantry"). Ingredients with no location land in a final "No
     location" group.
  2. **No mid-cook stock-level chips:** the StockItemChip is gone from
     the ingredient row. Substitutes still render their chip + undo.
  3. **Quantity spacing:** an ingredient with `unit = "g"` reads `"250g"`;
     `unit = "tbsp"` reads `"1 tbsp"`; `unit = null` reads just the qty
     (or empty when both null).
  4. **Chunk 2 Sous Chef rename:** the voice button reads **Sous Chef**
     with a tooltip; the help icon (?) opens a popover listing the 8
     commands.
  5. **Chunk 2 timer:** detect a "10 minutes" step → fill-bar shows below
     MM:SS → bar empties as time runs → at 0 the bar turns negative
     colour, the toast fires, **a short beep plays** (silently no-ops on
     iOS / PWA without a user-gesture activation, that's OK), and the
     reset button works to clear it.
  6. **Chunk 1 finish flow:** mark a few ingredients used, finish →
     dialog shows one row per used ingredient with the current stock
     level chip, action chips (Down one / Out / Unchanged, default Down
     one), override dropdown, and per-row Add-to-list button.
  7. The `meals_cooked` field defaults to **0**. Confirm a Done press
     with 0 toasts *"All eaten — hope it was good."* With N>0 it toasts
     *"You saved N meals — enjoy."* (with proper pluralisation).
  8. **Per-row override > action**: pick an explicit level for one row
     → on Done, that row's stock_level_id flips to the override.
     `Unchanged` rows leave stock alone.
  9. **Fail-soft:** one row pointing at a deleted stock item shouldn't
     stop the others from updating (Promise.allSettled).
  10. **Click-out cancels:** open the finish dialog, click outside →
      dialog closes, **no level / cook calls fired**.
  11. **Session swap interaction:** swap an ingredient to its
      substitute, finish → the *substitute*'s level (not the original
      recipe ingredient) is what updates.
- **Recommended resolution:** now/when env available — before C-3 Chunk 5
  lands on top.

## [OPEN] FU-095 — RecipeEditDialog (quick-create) has no structured-steps surface
- **Raised:** 2026-06-09 (Cookbook Chunk 6 impl)
- **Type:** follow-up
- **What:** The quick "New recipe" dialog (`RecipeEditDialog.vue`) only
  collects the basics — name, ingredients, cuisine/category, tags, tools,
  image. Structured steps were intentionally **not** added to keep the dialog
  lean for the common "create a stub then edit it" workflow. Users add
  structure via the detail page's Structured/Freeform toggle. If a future
  prompt makes the dialog the primary create path (or users complain about
  switching to detail), wire the `RecipeStepsEditor` into the dialog with
  the same `steps_mode` toggle.
- **Recommended resolution:** opportunistic / when next touching the dialog.

## [OPEN] FU-094 — Steps editor: drag-and-drop reorder (replaces up/down)
- **Raised:** 2026-06-09 (Cookbook Chunk 6 impl)
- **Type:** follow-up
- **What:** Per `IMPL_PLAN_COOKBOOK.md §6`, structured steps should reorder
  via the drag-handle pattern already used on shopping-list lines
  (`onLineDrop` off-by-one fix). Chunk 6 ships with **up/down arrow
  buttons** instead — functionally complete but less ergonomic on long
  recipes, especially because nesting (top-step vs sub-step) constrains
  the valid drop zones (siblings only). Replace once the basic editor is
  proven and the nesting drop-zone UX is worked out.
- **Recommended resolution:** later — once Chunk 6 has been browser-verified
  (FU-093) and the editor is in real use.

## [OPEN] FU-093 — Browser-verify Cookbook Chunk 6 (structured recipe steps)
- **Raised:** 2026-06-09 (Chunk 6 impl; static-only, no env)
- **Type:** finding / verification (blocks trusting Chunk 6 + cook-mode Chunk 5)
- **What:** Verify, in order:
  1. `alembic upgrade head` applies migration `c9d4f8e2a5b6` on SQLite **and**
     Postgres; app boots; `verify_mappings()` passes for `RecipeStep`.
  2. On a recipe, switch the new toggle to **Structured**, add a top step
     (text + hint + ingredient + tool), add a sub-step under it, reorder
     via the ↑/↓ buttons, save → reload → the structure round-trips.
  3. Switch the toggle to **Freeform**, save → `steps[]` is wiped server-side
     (re-open → editor shows zero steps); the textarea content remains.
  4. Toggle back to **Structured** and add steps again → save → editor
     reflects the new state.
  5. **URL importer:** import a recipe whose source uses schema.org
     `HowToStep` (e.g. major recipe sites publish JSON-LD) → the editor
     auto-fills Structured with the parsed steps. Import a site that only
     ships `recipeInstructions` as a string → editor stays in Freeform
     with the textarea filled.
  6. **HowToSection** import: a source that groups steps under sections
     produces top-level "section" steps with sub-steps under each.
  7. Delete an ingredient that a step references → the step's ingredient
     chip disappears (cleanup in `removeIngredient`) and save round-trips
     without errors.
  8. Edge: try to save a step with empty text → server returns 400 with
     "Every step must have non-empty text."
  9. **Backup → restore** round-trips RecipeStep / RecipeStepIngredient /
     RecipeStepTool in FK-correct order; structured recipes show the same
     steps after a restore.
- **Recommended resolution:** now/when env available — before cook-mode IMPL
  Chunk 5 lands on top.

## [OPEN] FU-092 — Audit ALL implicit / automatic / "magic" behaviour (hidden-magic risk)
- **Raised:** 2026-06-09 (user, during C-7 cart-button design — started as the
  "preferred product" worry, broadened to every automatic behaviour)
- **Type:** open question / app-wide UX assessment (product-direction call)
- **What:** The user is wary of **background behaviour the app performs without an
  explicit instruction** — anything that makes someone go *"why did the app do
  that? that's annoying."* The trigger was "preferred product/merchant", but the
  concern is general: every silent default, auto-mutation, and inference should be
  audited for whether the convenience is worth the surprise. Effortless (P1) is a
  Charter principle, but so is not blindsiding the user; this audit finds where
  the balance is wrong.
- **Assessment framework — for each automatic behaviour, decide:**
  (a) **keep silent** (genuinely effortless, low-surprise, easily reversible);
  (b) **make it visible/explainable** (a hint/undo/"why" affordance, e.g.
  "pre-selected your preferred — change?" or a toast that names what happened);
  (c) **make it opt-in / a setting** (off by default, or per-item);
  (d) **drop it** for an explicit choice.
  Bias: silent is fine when it's reversible + obvious; needs surfacing when it
  changes money, data, or list contents in a non-obvious way.
- **Catalogue of behaviours to inventory** (confirmed-seen marked ✓; others
  to verify during the audit):
  - ✓ **Preferred product / merchant** auto-pick in add-to-list / cheapest-offer
    paths (`StockItem.preferred_product_id`). *The original trigger.*
  - ✓ **Cart target inference (C-7 Axis B):** 0 draft lists → silently **create**
    one; 1 → silently use it; the **app-wide session "remembered list"** default.
  - ✓ **Auto-add-when-low** (`StockItem.auto_add_when_low`) — items appearing on
    a list without the user adding them.
  - ✓ **Meal-plan reconciliation** — past days auto-draining the recipe pool /
    auto-decrementing `available_meals` when a day rolls past
    (`reconcile_consumed_meals`).
  - ✓ **Auto-generate shopping list** from low/out/essentials.
  - **"Cheapest" auto-selection** of an offer.
  - ✓ **URL importer** auto-resolving scraped cuisine/category → existing vocab ids.
  - ✓ **Inline-create** of a stock item from a recipe ingredient.
  - ✓ **Mark-cooked / cook** auto-bumping last-cooked date + pool.
  - **Dora / dashboard suggestions** that surface or pre-fill actions
    (`suggestionStore`).
  - **Onboarding** auto-seeding groups / locations / vocab defaults.
  - **Substitute behaviour** (note: the old auto-swap-edits-the-recipe was already
    judged wrong in feedback — confirms the instinct).
  - **Expiry / stock alerts** firing automatically; any auto-status changes.
  - …plus anything else found: grep for places the app **mutates or chooses
    without a direct click** (auto-, default, inferred, silently, primary).
- **Output:** a short audit doc (e.g. `05_investigations/MAGIC_BEHAVIOUR_AUDIT.md`)
  listing each behaviour + verdict (a/b/c/d) + where it's surfaced, so the
  individual fixes become their own follow-ups.
- **Recommended resolution:** the **preferred-product slice** before/with **C-7
  Chunk 1** (it hardens product resolution); the **full audit** as its own pass
  (opportunistic, but ideally before more inference is added — e.g. C-2
  allocation, alerts C-9).
- **State note:** open — assessment not started.

## [OPEN] FU-091 — Browser-verify + run Cookbook Chunk 5 (images + tools)
- **Raised:** 2026-06-09 (Chunk 5 implementation; static-only, no env)
- **Type:** finding / verification (blocks trusting Chunk 5)
- **What:** verify, in order:
  1. `alembic upgrade head` applies migration `b8e3f1a6d2c4` (Tool + RecipeTool tables + seed) on SQLite **and** Postgres; app boots; `verify_mappings()` passes for the new `Tool` entity.
  2. `GET /api/tools` returns seeded tools; Settings → "Recipe tags & categories" has a **Tools** editor (create/rename/delete + recipe counts).
  3. Recipe create/update round-trips `tool_ids`; the edit dialog + detail page tools multiselect populate + save.
  4. Overview **Tools** tri-state filter (include/exclude) filters correctly.
  5. **Images:** upload on the detail page (RecipeImageField) → save → image shows on detail + card (via `GET /recipes/<id>/image`); change + remove work; cache-busts after save; oversized file (>4MB) is rejected client-side; create dialog can attach an image.
  6. Backup → restore round-trips Tool/RecipeTool + recipe images.
- **Recommended resolution:** now/when env available — before Chunk 6.
- **State note:** open — nothing executed.

## [RESOLVED] FU-090 — Recipe list query loads all image blobs (perf)
- **Raised:** 2026-06-09 (Chunk 5)
- **Resolved:** 2026-06-11 (C-cross Chunk 5). Folded into Chunk 5 per
  the IMPL plan ("the bandwidth-saving promised by 'images off' is
  otherwise hollow"). `Recipe.image` is now mapped with SQLAlchemy
  `deferred()` so the column never loads on the recipe-list query.
  `RecipeDto.from_entity` defaults `has_image=False`; a new
  `_hydrate_has_image()` runs a single bulk
  `SELECT id, image IS NOT NULL FROM Recipe WHERE id IN (...)` and
  fills the field — same hydrator pattern as tags / tools /
  structured-step flag. The image-bytes endpoint
  (`get_recipe_image`) still reads `recipe.image` directly via
  attribute access (one query per detail call, the intended path);
  the new-version handler's `image=source.image` copy also triggers a
  single lazy load per call.
- **Files:** `dora_api/persistence/table_mappings.py`,
  `dora_api/features/recipes/get_recipes.py`.

## [OPEN] FU-089 — Browser-verify Cookbook Chunk 4 (detail-page cleanup)
- **Raised:** 2026-06-09 (Chunk 4 implementation; static-only)
- **Type:** follow-up / browser verification
- **What:** On a recipe detail page, confirm:
  1. Sticky top toolbar: Mark cooked (prominent) / Cook mode / Log cook / Print / Save / kebab(Delete); buttons stay at the **top** on a narrow window (don't drop to the bottom). Delete is not adjacent to Mark cooked.
  2. **Mark cooked** bumps the pool +1 and last-cooked; **Log cook…** still logs N; **Print** opens the print view; **no CSV** option anywhere.
  3. Name is an editable labelled field; blanking it blocks save with an inline error.
  4. **Save**: leaving an ingredient row without a stock item blocks the save (prompt) rather than eating the row; saving with an unchanged name succeeds (no "already exists").
  5. Ingredient rows show a single chip (Missing wins) + tinted row when missing; no double chip.
  6. Cookable/missing box readable in dark themes (Pesto Dark / Cherry Cola Dark).
  7. **Cook mode guard**: with unsaved edits OR not-cookable, Cook mode shows a confirm with a working **Cancel**; clicking outside doesn't navigate; "Save & start" only proceeds if the save succeeds.
  8. **Cook mode exit returns to the recipe detail page** (not the overview).
  9. "Available meals" label; meal ± shows no not-allowed cursor flash.
- **Recommended resolution:** now/when next in the app.
- **State note:** open — nothing executed.

## [OPEN] FU-088 — Browser-verify Cookbook Chunk 3 (card redesign + naming)
- **Raised:** 2026-06-09 (Chunk 3 implementation; static-only)
- **Type:** follow-up / browser verification
- **What:** Confirm in a running app:
  1. Recipe cards render with the placeholder media tile, emphasised name, chips, dietary chips, and the meals box; equal-height cards in a grid row.
  2. The card ± **MealStepper** adjusts the cooked pool (updates immediately; decrement disabled at 0). Same stepper works on the recipe detail page and on the stock-item detail page's recipe cards.
  3. **Allocated badge**: appears only when `committed_meals > 0`; **red** when `available_meals < committed_meals` (put a recipe on a future meal-plan day with servings exceeding its cooked pool to test), neutral otherwise. Requires the new `committed_meals` DTO field to populate (verify the API returns it).
  4. Card has **only Cook** as a primary button; kebab shows just add-all-to-list + add-to-meal-plan (no Edit/Duplicate/Delete); clicking the card opens detail.
  5. Collection groups are **collapsible rounded boxes** (header toggles; chevron flips).
  6. **Naming**: main-menu reads "Cookbook"; `g r` + command palette "Go to Cookbook"; detail breadcrumb reads "Cookbook".
- **Recommended resolution:** now/when next in the app — pairs with FU-087 (the filter bug blocks seeing the cards under filters, but the cards themselves are independently testable).
- **State note:** open — nothing executed.

## [RESOLVED] FU-087 — Recipes overview filter panel shows nothing / toggle does nothing
- **Raised:** 2026-06-09 (user browser test of FU-083 + FU-085)
- **Resolved:** 2026-06-09. Reproduced via DOM inspection — the FilterBar's
  panel had `display: none` because `expanded` was permanently `false`. Two
  latent bugs in `FilterBar.vue` (and therefore every page using it,
  including StockOverview): **(1)** Vue 3 coerces an unset Boolean prop to
  `false`, so the manual `props.modelValue === undefined` sentinel
  distinguishing controlled-vs-uncontrolled never fired — clicks mutated
  `internal` but the getter kept returning the coerced-false `modelValue`.
  **(2)** `$q.screen.gt.sm` was read without the Quasar Screen plugin being
  activated anywhere, so every viewport check returned `false` (the "open on
  desktop by default" rule silently failed regardless of viewport). Both
  invisible to static type-checking and produced no console output.
- **Fix:** rewrote with the framework-idiomatic patterns: Vue 3.4
  `defineModel()` (handles controlled/uncontrolled correctly; a function
  default sidesteps the Boolean coercion); plus a new
  `web_app/src/boot/quasarScreen.ts` calling `Screen.setDebounce(100)` (the
  documented Quasar 2.x activation, registered in `quasar.config.ts`).
  Promoted the lesson to **R-011 / ADR-004** in
  `docs/01_charter/ENGINEERING_STANDARDS.md` — "use the framework's
  idiomatic, current-recommended pattern" — so this class of hand-rolled
  workaround doesn't recur.
- **Files:** `web_app/src/components/FilterBar.vue`,
  `web_app/src/boot/quasarScreen.ts` (new), `web_app/quasar.config.ts`,
  `docs/01_charter/ENGINEERING_STANDARDS.md`, `CHANGELOG.md`.
- **Unblocks:** FU-083 (Cookbook Chunk 1 filter verify) and the filter half
  of FU-085 (Chunk 2 cuisine/category/dietary filters).

## [OPEN] FU-085 — Run + verify Cookbook Chunk 2 (tag taxonomy overhaul) in a real env
- **Raised:** 2026-06-09 (Chunk 2 implementation; nothing was run — no Python venv / node_modules on the Windows dev box)
- **Type:** finding / verification (blocks trusting Chunk 2)
- **What:** Chunk 2 is a large, unrun backend+frontend change (FK-ify cuisine/category, DietaryTag table, 3 CRUD endpoints + settings, tri-state filter). Verify, in order:
  1. `alembic upgrade head` applies cleanly on **SQLite and Postgres** (migration `a7d2f4c9e1b8`: batch-mode Recipe alter dropping cuisine/category strings + adding cuisine_id/category_id FKs, RecipeTag rebuild to dietary_tag_id, vocab seed). Also test `downgrade`.
  2. App boots — `verify_mappings()` passes for Cuisine/Category/DietaryTag + the reshaped Recipe (risk: the `_cuisine_id`/`_category_id` hidden-FK mapping + the selectin relationships).
  3. `repository.get(Recipe).all()` actually selectin-loads `recipe.cuisine`/`.category` (assistant + global_search depend on it; if not, they'll show null cuisine/category).
  4. Recipe create/update/list round-trips `cuisine_id`/`category_id`/`dietary_tag_ids`; `GET /recipes/tags` returns DB-backed tags (value = id) + disclaimer.
  5. Overview: cuisine/category single-selects filter; tri-state DietaryTagFilter cycles +/−/neutral and stays open; RecipeCard shows cuisine/category names + tag chips.
  6. Edit dialog + detail page: cuisine/category selects + dietary multiselect populate from existing recipe + save correctly; URL importer pre-fills matched cuisine/category.
  7. Settings → "Recipe tags & categories": create/rename/delete for all three vocabularies; usage counts + delete warnings; deleting a cuisine/category nulls recipes (SET NULL), deleting a dietary tag removes the links (CASCADE).
  8. Backup → restore round-trips Cuisine/Category/DietaryTag/RecipeTag in FK-correct order.
  9. Dora assistant: search_recipes/suggest_recipes still filter by cuisine + dietary tags (now Python-side / name-resolved).
- **Recommended resolution:** now / first thing once a working env is available — before building Chunk 3+ on top.
- **State note:** 2026-06-09 — first user browser pass: migration applied + app boots + settings CRUD + add-modal dietary tags all **confirmed working** (items 1,2,4,7 effectively ✅). Two gaps found: (a) overview filters unusable → split out as **FU-087**; (b) no dietary-tag editor on the detail page (only the add modal) → **fixed** (added a multiselect to `RecipeDetailPage.vue`, L264). Still to verify: items 3 (selectin), 5 (filters), 6 (detail-page tags), 8 (backup), 9 (assistant).
- **State note:** 2026-06-12 — second user browser pass surfaced
  five concrete findings split out as their own FUs (so FU-085
  doesn't become an umbrella for everything cookbook-shaped):
  - **FU-146** (RESOLVED this session) — GitHub-issues mentions
    swept out (repo private).
  - **FU-147** — detail-page dietary-tag picker doesn't
    pre-populate + chips clear after save (item 6 partial fail).
  - **FU-148** — Cookbook overview missing "time of day" filter.
  - **FU-149** — Cookbook overview missing "# ingredients"
    filter + sort axis.
  - **FU-150** — assistant chat-mode doesn't recognise dietary
    or cuisine queries (item 9 partial fail).
  FU-085 itself stays OPEN until items 3 (selectin), 5 (filters
  end-to-end), 6 (FU-147 fix verified), 8 (backup), 9 (FU-150
  fix verified) are all green.

## [OPEN] FU-084 — Consider an ADR/rule for "selectin for small always-wanted lookups"
- **Raised:** 2026-06-09 (Chunk 2)
- **Type:** finding / engineering-standards
- **What:** Chunk 2 made `Recipe.cuisine`/`.category` relationships `lazy="selectin"` (vs the codebase's noload default) so the ~10 read sites don't each need an `.include()`. If this pattern recurs for other small reference-data relationships, promote it to an `R-0NN` + ADR in `ENGINEERING_STANDARDS.md` (with the caveat: only for tiny, always-wanted lookups — not for large/optional relations where noload + explicit include is correct).
- **Recommended resolution:** opportunistic — when the next selectin-vs-noload call comes up.
- **State note:** open.

## [RESOLVED] FU-083 — Browser-verify Cookbook Chunk 1 + user feedback pass
- **Raised:** 2026-06-09 (post-Chunk-1 implementation)
- **Resolved:** 2026-06-10. User did the browser pass and surfaced
  nine concrete pieces of feedback; all addressed in this session.
- **Original verify items 1–7 plus user-flagged tweaks, by status:**
  1. ✅ Comparison gone — clean (no warnings).
  2. ✅ Chip filters toggle; `activeFilterCount` updates.
  3. ✅ Numeric inputs — **`:hint` removed** on `Meals ≥` / `Missing ≤`
     (and the old `Free from ingredient(s)` input is gone entirely);
     filter row alignment is no longer offset by the extra
     under-input copy.
  4. ✅ Sort axes — now with an explicit **`sortDir` toggle**
     (asc/desc) on a dedicated direction button next to the Sort by
     dropdown. Null sentinels (last_made, total_time) still sink to
     the bottom regardless of direction. Axis-switch snaps direction
     to the conventional default (name=A→Z, recently-made=newest
     first, etc.).
  5. ✅ Stock-item picker — **dot kept, level text removed** from
     the dropdown row (user flagged the caption as redundant);
     `?usesStockItem=` deeplink still hydrates.
  6. ✅ **`Planned` filter bug fixed.** Was string-comparing
     `scheduled_for` without parsing, and didn't skip consumed
     entries — user reported yesterday's still surfacing. Now
     parses `YYYY-MM-DD` explicitly into a local-midnight `Date`,
     skips any entry with `consumed_at` set, and gates on the
     parsed `>= today` check. Also renamed the chip from
     **"Planned in"** to plain **"Planned"** per the feedback ("In
     adds nothing").
  7. ✅ **RecipeCard dim removed.** The "restocking this item alone
     wouldn't make it cookable" semantics wasn't legible without a
     legend, and the card already shows "missing N ingredients" on
     its face. `highlightStockItemIds` prop kept (used by deep-link)
     but no longer drives a `--dim` class.
  8. ✅ Filter-bar alignment — **hints + the free-text "Free from"
     control removed**; the row now reads cleanly without the
     under-input height jitter.
  9. ✅ **"Free from ingredient(s)" replaced by a "Doesn't use"
     stock-item picker** (+/- partner to "Uses ingredients" — same
     option source, same search UX). Trades free-text fuzziness for
     an exact stock-item exclude; users who want raw-text exclude
     can ask if they hit a real gap.
  10. ✅ **"Uses stock items" → "Uses ingredients"** label rename.
  11. ✅ **Read-only "Last cooked" card** added on the recipe detail
      page sidebar (under the cookable card); reads
      `recipe.last_made_on` and shows "Never" when null.
- **Files touched:** `pages/RecipesOverview.vue`,
  `pages/RecipeDetailPage.vue`, `components/RecipeCard.vue`.
- **Unblocks:** nothing specific; the cookbook overview UX gripes
  are now closed.

## [OPEN] FU-082 — Add `created_at` to Recipe DTO so "Recently added" sort axis can land
- **Raised:** 2026-06-09 (Cookbook Chunk 1; IMPL plan called for the axis)
- **Type:** finding / Phase-2
- **What:** `IMPL_PLAN_COOKBOOK.md` Chunk 1 listed five sort axes including `created-at`. Recipe DTO has no created timestamp today, so Chunk 1 shipped four (`name`, `last_made`, `meal_count`, `total_time`). Adding it is mechanical: a `created_at` column already exists on most domain tables; expose it through `table_mappings.py` and the recipe DTO + SORT_OPTIONS const in `RecipesOverview.vue`.
- **Recommended resolution:** Phase 2 (ingestion API) or when Cookbook Chunk 4 (detail cleanup) is touched — that's the chunk likely to touch the recipe DTO anyway.
- **State note:** open.

## [OPEN] FU-081 — Move "Planned in" filter from client-side to server-derived Recipe.is_planned
- **Raised:** 2026-06-09 (Cookbook Chunk 1)
- **Type:** finding / state-ownership
- **What:** The "Planned in" filter in `RecipesOverview.vue` derives the set of upcoming recipe ids client-side by walking `mealPlanStore.mealPlans[].entries[]` and matching `scheduled_for >= today`. This is a cross-entity rule (recipes × meal plans × today) — R-003 says server-owned. Chunk 1 was constrained to "no model changes" so it shipped client-side; logged here so it gets folded into the right Phase-1 work.
- **Recommended resolution:** when `IMPL_PLAN_STATE_OWNERSHIP.md` lands the server-owned cookability work, add `is_planned: bool` (any future entry exists) to the Recipe DTO and switch `plannedRecipeIds` to read it directly. Cheap to migrate the filter — one ref + one predicate line.
- **State note:** open — current implementation is acceptable but flagged.

## [RESOLVED] FU-080 — Browser-verify the menu-highlight subroute fix
- **State note:** 2026-06-09 — user confirmed in browser: menu highlighting works on subroutes. ✅
- **Raised:** 2026-06-09 (after the menu-highlight fix landed)
- **Type:** follow-up / browser verification
- **What:** The fix moves main + side menu active-state from Vue-Router's route-record matching to a path-prefix composable (`useMenuLinkActive.ts`), and re-targets the "Recipes" menu link from `/recipes` (redirected) to `/cookbook` with `activePrefixes: ['/recipes']`. Confirm in browser:
  1. Each top-nav button highlights on its base path **and** on every subroute it owns: `/stock/:id` under Stock; `/cookbook` + `/recipes/:id` + `/recipes/:id/cook` under Recipes; `/shopping-lists/:id` + `/shopping-lists/:id/shop` under Shopping Lists; `/meal-plans` subroutes; `/data/*` (Data menu has /backup, /import, /export, /barcodes); etc.
  2. The sliding accent-coloured indicator on `MainMenuButtonStrip` still tracks position when navigating between sections.
  3. SideMenuButton (hamburger drawer) highlights correctly on subroutes too (the `exact` prop was dropped).
  4. No double-highlight: only the *most specific* match should look active. Path prefix is greedy by design — `/data` would match `/data/backup`, which is desired; but verify no two sibling links both match the same URL.
- **Recommended resolution:** now/when next in the app — quick visual sweep.
- **State note:** not yet verified.

## [RESOLVED] FU-079 — Confirm hotfix resolves the blank-screen report
- **State note:** 2026-06-09 — user confirmed: can navigate to `/shopping-lists` and Detail renders correctly. Hotfix verified in browser.
- **Raised:** 2026-06-08 (user reported blank screen on /shopping-lists with no console errors)
- **Type:** follow-up
- **What:** A hotfix landed in this session: Overview + Detail now surface `loadError` via banners with Retry buttons, the store explicitly `console.error`s API failures, Detail's FadeTransition gained a v-else "list isn't available" fallback so the content area is never blank, and three lint errors were cleared (duplicate v-else-if, dead `onFinish`, floating-promise on Esc).
  - **Leading suspect for the original blank screen:** the `e1a4c7b2f9d0` migration (Chunk 7 `planned_shop_date` column) was not applied on the user's Linux machine. The API's `SELECT` on `ShoppingList` would 500 with "no such column"; the store caught silently; the UI rendered nothing.
- **Recommended resolution:**
  1. Pull the hotfix.
  2. `alembic upgrade head` to apply `e1a4c7b2f9d0`.
  3. Restart the API + Quasar dev.
  4. Navigate to `/shopping-lists`. Confirm: either the redirect to a list works, or the new red banner shows an actual error message (no more blank).
  5. Open the browser dev console — any `[shoppingListStore] refreshAsync failed` lines surface what's actually broken.

## [RESOLVED] FU-078 — Write IMPL plan for C-4 cookbook
- **Raised:** 2026-06-08 (after FU-077 closed)
- **Type:** follow-up
- **What:** Natural next document after the C-4 design decisions closed (PROPOSAL_COOKBOOK §5a) — chunked IMPL plan mirroring `IMPL_PLAN_SHOPPING_LISTS.md` and `IMPL_PLAN_COOK_MODE.md`. Bigger than C-3 (nine design sections, ~10 chunks expected).
- **State note:** 2026-06-08 — wrote `docs/04_proposals/IMPL_PLAN_COOKBOOK.md` (10 chunks + verify-state, first-chunk DoD, risks, feedback coverage, run order). All 6 open decisions had been closed in PROPOSAL_COOKBOOK §5a beforehand; DEC-2 deviated meaningfully from the brief (siblings via `version_group_id` instead of snapshot+pointer) and the plan reflects the user's flatter model. Wired into the doc-graph (new C-impl row + cross-map row).

## [RESOLVED] FU-077 — Write IMPL plan for C-3 cook-mode
- **Raised:** 2026-06-08 (C-3 decision pass)
- **Type:** follow-up
- **What:** With C-3's open decisions resolved (`PROPOSAL_COOK_MODE.md §5a`) and the structured-steps dependency homed in C-4 (`PROPOSAL_COOKBOOK.md §2.6a`), the natural next document is an implementation plan mirroring `IMPL_PLAN_SHOPPING_LISTS.md` — chunked, self-contained, no code. Chunks suggested by C-3 §6 + §5a: (1) finish-flow + click-out + celebration + meals-cooked-from-zero, (2) timer polish + unit fix + sous-chef discoverability, (3) location grouping + ingredient-UI rebuild, (4) structured-steps (lives in C-4 but lands as a co-sequenced cook-mode-blocker), (5) highlight-instead-of-tick + per-step tools + per-step hints + per-step timers, (6) serving auto-adjust (gated on C-5 onboarding default).
- **State note:** 2026-06-08 — wrote `docs/04_proposals/IMPL_PLAN_COOK_MODE.md` (6 chunks + verify-state, first-chunk DoD, risks, feedback coverage, run-order). Wired into the doc-graph (new C-impl row + cross-map row for the IMPL plan). Open decisions all closed in PROPOSAL_COOK_MODE §5a; no co-design questions remain for the implementation phase.

## [OPEN] FU-076 — P6-01 Chunk 7 browser smoke
- **Raised:** 2026-06-08 (Chunk 7 impl)
- **Type:** follow-up
- **What:** Run the migration locally (`alembic upgrade head` lands `e1a4c7b2f9d0`), restart the API + web app, then:
  1. Open a list → header chip reads "No shop day" → click → date dialog → save 2026-07-01 → chip updates → refresh → still set.
  2. Clear the date via the dialog's *Clear* button → chip → "No shop day".
  3. Create a list via **New list** dialog with a date → detail loads → chip shows the date.
  4. Set a DRAFT's date to today → navigate to `/shopping-lists` → lands on that draft (priority pick).
  5. With today set: the in-detail banner appears with info-tone "Shopping day is today."
  6. With a past date (e.g. yesterday) set + status still DRAFT: warning-tone banner says "Planned shop day was … — still unfinished."
  7. Selector dropdown: a list with a planned date sorts ahead of unscheduled lists; today's list sits at the top of its band.
  8. Cross-theme: Pesto Light + Pesto Dark + Cherry Cola Dark.
- **Why deferred:** no live API/DB in this session.
- **Recommended resolution:** now (alongside FU-066/068/069/072/073).

## [OPEN] FU-075 — Run the new `test_shopping_list_planned_shop_date` e2e
- **Raised:** 2026-06-08 (Chunk 7 impl)
- **Type:** follow-up
- **What:** Apply migration `e1a4c7b2f9d0` to the test DB, then `pytest tests/e2e/dora_api/test_shopping_list_planned_shop_date.py -v`. Four cases (create-with-date, create-without, PATCH set-and-clear-with-null, PATCH preserves the date when not sent).
- **Why deferred:** no live server in the implementation session; py_compile is not a runtime check.
- **Recommended resolution:** now, with FU-076.

## [OPEN] FU-074 — Wire planned-shop-day into the real alert pipeline (C-9)
- **Raised:** 2026-06-08 (Chunk 7 impl)
- **Type:** finding (deferred-by-design)
- **What:** Chunk 7 surfaces planned-shop-day as a banner on the list detail. The IMPL plan says it "feeds C-9's new alert types" — the actual alert pipeline (alerts bell badge, suggestion-feed insertions, optional push) belongs to the C-9 prompt's surface. When C-9 runs, register a new `shopping_day_today` / `shopping_day_overdue` alert type that fires on the same condition as the banner, and de-dupe so the banner stays the in-page hint while the alerts list / bell badge handle global notification.
- **Why deferred:** alert types + their dedupe semantics live in C-9, not in P6-01 Chunk 7.
- **Recommended resolution:** when C-9 (alerts) executes.

## [OPEN] FU-073 — P6-01 Chunk 6 browser smoke
- **Raised:** 2026-06-08 (Chunk 6 impl)
- **Type:** follow-up
- **What:** Verify the in-store polish behaves in the real browser:
  1. Start shopping → tap *Skip* → next item shows → refresh page → the skipped item is still at the end (persisted).
  2. Tap the centre qty number → dialog opens → type "12" → Save → qty row shows 12; refresh → still 12.
  3. Tap **Peek list** (header) → modal lists ticked + unticked → tap an unticked item → modal closes + that item is now next-up → refresh → still next-up.
  4. Detail page (DRAFT): drag line from position 1 onto position 5 → it lands at index 5 (visual slot of the row it was dropped on). Drag from 5 to 1 → lands at index 1. Off-by-one no longer present (feedback L414).
  5. Detail page header: confirm the old back-arrow is gone (replaced by the list selector).
  6. Cross-theme: open in Pesto Light + Pesto Dark + Cherry Cola Dark.
- **Why deferred:** vue-tsc clean is not a UX test; no dev server in this session.
- **Recommended resolution:** now (alongside FU-066/FU-068/FU-069).

## [OPEN] FU-072 — Chunk 6 audit: pricing-as-you-go + group-by-aisle still respect their contracts
- **Raised:** 2026-06-08 (Chunk 6 impl)
- **Type:** finding
- **What:** Two Chunk 6 line items in the IMPL plan were observed as already-implemented in code (`openPriceEditor` exposed from the shop-mode card; `lineGroups` on the detail page reads `stock_location_breadcrumb` and never writes `sequence`). They need a five-minute browser confirmation that (a) the price editor still opens mid-shop and saves `actual_unit_price`, (b) toggling group-by-location → none → group-by-merchant doesn't quietly mutate the saved order. Once confirmed, flip this to `[RESOLVED]`.
- **Why deferred:** no dev server in the implementation session; pure static read isn't enough proof per CLAUDE.md.
- **Recommended resolution:** confirm in browser (alongside FU-073).

## [RESOLVED] FU-070 — `goBack()` in Detail is now a self-bounce
- **Raised:** 2026-06-08 (Chunk 5 impl)
- **Type:** finding (UX)
- **What:** The back-arrow in `ShoppingListDetail.vue` pushes `/shopping-lists`, which the new router landing immediately `replace`s back to a chosen list — usually the same one. So the back button now effectively no-ops (or, worse, picks a different list than the user expected). Two reasonable resolutions: (a) point it at `/`, or (b) drop the button entirely now that the in-page list selector exists.
- **State note:** 2026-06-08 — resolved option (b) in Chunk 6: dropped the `<BaseButton variant="icon">` back-arrow + the `goBack()` function from `ShoppingListDetail.vue`. The in-page list selector replaces it; the sidebar nav still exits the shopping-lists surface.

## [OPEN] FU-069 — P6-01 Chunk 5 browser smoke
- **Raised:** 2026-06-08 (Chunk 5 impl)
- **Type:** follow-up
- **What:** Verify the merged surface end-to-end:
  1. `/shopping-lists` with multiple lists → lands on SHOPPING list if any, else newest DRAFT, else newest DONE.
  2. `/shopping-lists` with zero lists → empty-state renders the **New list** button; clicking opens the dialog; submitting routes to the created list.
  3. Detail list-selector: dropdown opens with **Active** group (current highlighted), **Archived** group below the separator, **+ New list** at the top, **Manage templates…** at the bottom.
  4. Active row kebab → Copy unticked / Archive / Delete each behave correctly. Archived row kebab → Copy archived / Delete.
  5. Deleting the currently-open list bounces to the landing and the landing picks the next list.
  6. **+ New list** in the selector opens the dialog; submit routes to the created list.
  7. Switching to a different list via the selector loads its detail (status watcher / shop-mode redirect still works for SHOPPING).
  8. Cross-theme: open in Pesto Light + Pesto Dark + Cherry Cola Dark.
  9. Mobile width: the dropdown is still usable (the proposal eventually wants a dedicated mobile dropdown surface — see FU-071).
- **Why deferred:** vue-tsc clean is not a UX test; no dev server in this session.
- **Recommended resolution:** now (alongside FU-066/FU-068).

## [OPEN] FU-071 — Desktop right-panel + mobile-top-dropdown list selector
- **Raised:** 2026-06-08 (Chunk 5 impl)
- **Type:** finding (UX polish per proposal §2.3 / feedback L405-L406)
- **What:** Proposal calls for a desktop **right panel** (always visible) and a mobile **top dropdown**. Chunk 5 ships a single `q-btn-dropdown` shared across viewports as a viable interim. The dedicated right-panel layout (always visible on >=md, the dropdown collapses below that) is the next step.
- **Why deferred:** would have nearly doubled Chunk 5's edit surface; the dropdown is the same UX *capability* on both viewports, just less ambient on desktop.
- **Recommended resolution:** opportunistic — pair with Chunk 7 (planned shop day + cleanup) or as standalone polish.

## [OPEN] FU-068 — P6-01 Chunk 4 browser smoke
- **Raised:** 2026-06-08 (Chunk 4 impl)
- **Type:** follow-up
- **What:** Verify the unified "New shopping list" dialog handles every old door correctly:
  1. Toolbar *New list* → *Empty + Create new* → produces an empty list, routes into it.
  2. *Empty + auto-fill: low-or-out + new* → equivalent of the old "From all low/out stock".
  3. *Template + new* → uses `instantiateAsync`; lines match the template.
  4. *Recipe + new* → bulk-adds the recipe's ingredient stock items.
  5. *Meal plan + new* → bulk-adds `getIngredientsAsync` results.
  6. *Empty + auto-fill: flagged + essentials-only + merge into existing* → equivalent of old "Top up the primary list".
  7. *Template + merge*: confirm the temp-list-then-delete dance leaves no orphan list in the overview (refresh after).
  8. Empty-state — when no active lists and stock has low/out items, the kickstart "New list" button opens the dialog with *low-or-out* pre-ticked.
  9. Cancel button discards the form (re-open shows defaults again).
  10. Cross-theme: open in Pesto Light + Pesto Dark + Cherry Cola Dark.
- **Why deferred:** vue-tsc clean is not a UX test; no dev server in this session.
- **Recommended resolution:** now (alongside FU-066).

## [RESOLVED] FU-067 — Drop unused `appendLowStockEssentialsAsync` endpoint
- **Raised:** 2026-06-08 (Chunk 4 impl)
- **Type:** finding (R-007 scope-discipline housekeeping)
- **What:** The detail page's "Append low + essentials" menu (the 5th of the proposal's five doors) is gone, but the underlying API method `appendLowStockEssentialsAsync` and its backend route `/shopping-lists/{id}/append-low-stock-essentials` were still present with no UI consumer. The unified `New list` dialog covers the same use case via *auto-fill: low + flagged + essentials-only + merge into this list*.
- **State note:** 2026-06-09 — resolved. Confirmed via static grep the frontend method had zero callers, then removed the `append_low_stock_essentials` route/handler from `features/shopping_lists/auto_generate.py` and the `appendLowStockEssentialsAsync` method from `shoppingListApiService.ts`. No orphaned imports (`AutoGenerateSources/Request`, `not_found`, `AutoGenerateResult` all still used elsewhere). Static-only; not run.

## [OPEN] FU-066 — P6-01 Chunk 3 browser smoke
- **Raised:** 2026-06-08 (Chunk 3 impl)
- **Type:** follow-up
- **What:** Eyeball the lifecycle end-to-end in the running app:
  1. DRAFT detail → *Start shopping* button → confirm router lands on /shop directly.
  2. SHOPPING /shop → tick a few items → kebab *Finish & restock* AND footer button → confirm the dialog lists the ticked items (capped at 8 + "and N more") → confirm restock + archive.
  3. SHOPPING /shop → back-arrow → confirm tooltip reads "Back to editing", confirm status flips to DRAFT, confirm route lands on detail (not bouncing back).
  4. DONE detail → *Reopen* → confirm restock changes reverse and status returns to DRAFT.
  5. PWA "Shop now" — confirm the existing status-driven routing (1 SHOPPING → resume; else 1 DRAFT → open; else overview) still works end-to-end.
  6. Open in Pesto Light + Pesto Dark + Cherry Cola Dark to confirm dialog / primary-button styling still reads.
- **Why deferred:** dev server not run in this session; vue-tsc clean is not a UX test.
- **Recommended resolution:** now (before Chunk 4).

## [OPEN] FU-065 — Ticked-summary string duplicated across both finish dialogs
- **Raised:** 2026-06-08 (Chunk 3 impl)
- **Type:** finding (R-003 lite — same display string built in two places)
- **What:** `ShoppingListDetail.vue` and `ShoppingListShopMode.vue` each build the "N items will be bumped to Well-Stocked: a, b, c, and N more." string for their respective Finish-and-restock dialog. Identical algorithm, two copies. If the wording or cap-count changes, both need editing.
- **Why deferred:** extracting a single helper is one line of value today; both copies are 4-line, Type-C display logic, and the two dialogs *do* differ (Detail has the copy-unticked-to-new-list radio, ShopMode appends a one-line note). Worth a helper only if a third caller appears, or if the wording becomes prose worth localising.
- **Recommended resolution:** opportunistic — when C-locale (FU-043) lands, fold both summaries through one localised builder. Otherwise leave alone.

## [OPEN] FU-062 — Doc-graph: verify cited paths + original-spec Feature Board mappings
- **Raised:** 2026-06-08 (doc-graph build)
- **Type:** finding
- **What:** `docs/00_DOC_GRAPH.md` was assembled with heavy use of Grep/Glob but no per-citation existence pass. Two specific gaps to close:
  1. Walk every cited path in the graph and confirm the file exists at that path (catch typos and stale references introduced by the agent).
  2. The original-spec `Feature Boards/*.md` mappings (one per surface) were inferred by filename-to-surface heuristic, not by opening each board. Open each Feature Board and confirm the surface mapping is right; correct any mis-mappings.
- **Why deferred:** the build pass prioritised breadth (every prompt has a section) over per-citation verification; doing both in one pass would have blown the context budget.
- **Recommended resolution:** opportunistic — fold into the first prompt run that actually consumes the graph (FU-063), or run as a standalone audit.

## [OPEN] FU-063 — Doc-graph: first-use stress test
- **Raised:** 2026-06-08 (doc-graph build)
- **Type:** follow-up
- **What:** The graph is unproven until a prompt is actually executed through it. The next time any `03_prompts/` prompt is run, do the full ritual: open the row, read every cited doc, then run. Record whether the cited docs surfaced anything the prompt body alone would have missed, and whether anything *should* have been cited but wasn't. Update the graph from what you learn.
- **Why deferred:** can only be tested by running a prompt; no prompt run this session.
- **Recommended resolution:** when next executing a `03_prompts/` prompt.

## [OPEN] FU-064 — Doc-graph: maintenance cadence / regeneration prompt
- **Raised:** 2026-06-08 (doc-graph build)
- **Type:** deferred job
- **What:** The graph will go stale as new proposals/investigations/FUs land and prompts complete. Decide: (a) add a small `docs/03_prompts/META_refresh_doc_graph.md` prompt that re-runs the cross-reference, OR (b) make graph-update part of every prompt's close-gate (cheaper, more drift-prone). User flagged this as an open question in the worklog.
- **Why deferred:** needs user direction.
- **Recommended resolution:** awaiting user decision; revisit after FU-063 confirms the graph is paying off.

## [OPEN] FU-061 — Promote doc-graph to in-prompt blocks (Option B) if agents skip the ritual
- **Raised:** 2026-06-08 (doc-graph build)
- **Type:** deferred job
- **What:** Today the per-prompt required-reading lives in one central file (`docs/00_DOC_GRAPH.md`). If sessions skip the ritual (don't open the graph), promote to Option B: edit every `03_prompts/*.md` to add a `## Required reading (do this first)` block above `## Impact & decisions`, copying its row from the graph. Higher maintenance, impossible to skip.
- **Why deferred:** start with the lighter scheme; only escalate on evidence of drift.
- **Recommended resolution:** when a worklog entry shows the agent didn't consult the graph (a clear miss), OR after 5–10 prompts have run and you want to audit consultation rate.

## [OPEN] FU-060 — Chunk 2 browser smoke: 2+-draft picker, shop-now routing, set-primary removal
- **Raised:** 2026-06-07 (P6-01 Chunk 2 implementation)
- **Type:** finding / browser verification
- **What:** Verify in the running app:
  1. With 2+ drafts, the stock-overview cart click pops the disambiguation
     dialog; the chosen draft persists across cart clicks for the rest of the
     tab session (sessionStorage). Finishing the chosen draft clears the
     stale-hint and the next cart click re-prompts.
  2. With 0 drafts, the cart click shows the "No draft list" dialog → "Open
     lists" lands on the overview.
  3. PWA "Shop now" shortcut: 1 SHOPPING list → goes straight to shop mode; 1
     DRAFT (and no SHOPPING) → goes to that draft's detail; anything else →
     overview.
  4. No "Set as primary" / "Make primary" / "Primary" badge / Primary chip is
     visible anywhere (Shopping lists overview, Shopping list detail,
     ShoppingListTemplates use-as-primary action, ExportPrint primary chip).
  5. Migration `d5e9f3b2a1c8` applies cleanly on a real dev DB (alongside
     FU-057 for the c4d8e1a6f3b9 migration).
- **Recommended resolution:** **confirm in browser** — these are functional
  paths a static type-check can't fully cover; FU-059's line-tick fix
  similarly waits on browser confirmation.

## [RESOLVED] FU-059 — Shopping-list line tick/delete always 404'd (UUID-vs-str guard)
- **Raised:** 2026-06-07 (P6-01 Chunk 1 — surfaced by new lifecycle e2e)
- **Type:** finding → fixed this session
- **What:** `update_line` / `delete_line` in
  `dora_api/features/shopping_lists/manage_shopping_list_lines.py` guarded parent
  ownership with `line.shopping_list_id != shopping_list_id`. The entity FK is a `UUID`;
  the Flask path param is always a `str` (no uuid converter registered), so the
  comparison never matched and **every** PATCH (tick/qty/select) and DELETE on a line
  returned 404. Pre-existing since the file was created (commit `fa399e2`); no e2e
  covered it until now. The frontend (`shoppingListApiService.updateLineAsync`) hits
  exactly this route, so in-store ticking would have been broken in the running app.
- **Resolved (symptom):** compared as strings (`str(...) != str(...)`) in both guards,
  with an inline comment. Verified by the new e2e `test__finish_then_reopen…` (which
  ticks a line). **Still worth a browser confirm** of shop-mode ticking.
- **R-010 carve-out / leftover:** the `str()`-both-sides fix is the symptom fix the new
  rule R-010 warns against — it keeps the ids weakly typed. The *root* fix is to coerce
  the path params to `UUID` once at the route boundary (matching the codebase's existing
  `UUID(raw)` idiom) so the comparison is typed. Deferred to avoid scope creep this
  session; do it opportunistically when next touching `manage_shopping_list_lines.py`
  (and audit sibling line routes for the same coercion).

## [RESOLVED] FU-058 — Finish snapshot captured no level_restores (noload relationship)
- **Raised:** 2026-06-07 (P6-01 Chunk 1)
- **Type:** finding → fixed this session
- **What:** the Finish handler captured each restocked item's prior level by reading
  `item.stock_level` (the relationship). That relationship is mapped `lazy="noload"`
  (`table_mappings.py`), so it returns `None` unless eager-loaded — meaning
  `finish_snapshot.level_restores` was always `[]` and Reopen restored nothing (status
  flipped back but levels stayed Well-Stocked).
- **Resolved:** the Finish query now `.include("stock_level")` before reading the prior
  level. Verified by the new e2e (reopen restores Out-of-Stock). R-003 (server-owned
  undo) now actually holds.

## [OPEN] FU-056 — P6-02 deferred: register-against-product UI + ingestion EAN auto-populate
- **Raised:** 2026-06-07 (P6-02 implementation — "Cleanup now, UI later")
- **Type:** deferred job
- **What:** The backend `POST /api/data/barcodes/register-against-product` route exists and
  is tested, but there is **no UI** to drive it (scan unknown barcode → pick a Product →
  create `ProductBarcode`). Also: ingestion should auto-populate `ProductBarcode` from a
  feed's EAN/UPC field so most barcodes resolve without manual registration.
- **Why deferred:** `Product` has no EAN field today (only `merchant_stockcode`), so a manual
  register UI now would be the only path and low-value. Ingestion is the natural place to
  add an EAN field + auto-fill `ProductBarcode` at scale.
- **Recommended resolution:** later during **Phase 2 (ingestion API)** — design is in
  `docs/04_proposals/PROPOSAL_BARCODE_SCANNING.md` §5–§6.

## [OPEN] FU-057 — P6-02: browser-verify the gated scanning surface + apply migration
- **Raised:** 2026-06-07 (P6-02 implementation)
- **Type:** finding
- **What:** The scanning/QR gating was verified by static read + frontend sweep only. Not
  confirmed in a running app: toggling `scanning_enabled` in Settings → System actually
  shows/hides the Stock Overview scan/print buttons, stock-item "Show QR", and the Data →
  "Scanning & QR labels" section/off-state banner. Migration `a3f1c7d2e9b4` (drops
  `StockItem.barcode`, adds `AppSetting.scanning_enabled`) has not been applied to a live DB.
- **Why deferred:** e2e suite pre-existing broken ([[FU-048]]); no browser smoke test this
  session.
- **Recommended resolution:** **confirm in browser** + run migration on a dev DB before P6-01.

## [RESOLVED] FU-055 — P6-02 barcode/QR: design pivoted; build-vs-defer decision pending
- **Raised:** 2026-06-07 (P6-02 design discussion)
- **Type:** deferred job (blocked on user decision)
- **State note:** RESOLVED 2026-06-07 — user chose Option 1 ("Cleanup now, UI later").
  Dropped `StockItem.barcode` (col/routes/UI/DTOs/export), kept `ProductBarcode` +
  Dora QR, added off-by-default `scanning_enabled` flag gating the whole surface,
  relabelled honestly, wrote `PROPOSAL_BARCODE_SCANNING.md`, reworded CLAUDE.md. The
  EAN question is answered (Product has no EAN, only `merchant_stockcode`) →
  register-against-product UI + ingestion auto-populate deferred to Phase 2 ([[FU-056]]).
  See WORKLOG 2026-06-07 "P6-02 barcode/QR — IMPLEMENTED".
- **What:** P6-02 was going to be "remove real-world barcodes wholesale, keep only Dora QR"
  (legacy spec). A design discussion **changed the shape**: `ProductBarcode` (barcode→Product)
  is the CORRECT model and is KEPT; `StockItem.barcode` (one barcode per item) is the WRONG
  model and is DROPPED. Real-world-barcode scanning becomes a *navigation* aid (scan product →
  open linked stock item), complementary to Dora QR (for unbarcoded/loose items), both opt-in /
  off-by-default, never live deal-lookup. **Full context + the verified code map + the resolved
  decisions are in the DORA_WORKLOG.md entry dated 2026-06-07 "P6-02 barcode/QR — DESIGN
  DISCUSSION".**
- **Resolved already:** flag = install-wide `AppSetting` (`scanning_enabled`, default false);
  recommend ONE flag for the whole surface.
- **OPEN — ask the user first:** how much to build *now* vs defer? (1) [recommended] cleanup +
  gate now, defer the register-against-product UI to Phase 2 (auto-populate from scraped EANs);
  (2) build the full vision now; (3) pause and write the proposal/CLAUDE.md update first.
- **Also verify:** does scraped Product data carry an EAN today? (Only `merchant_stockcode`
  seen.) Determines whether auto-populate is feasible / whether to defer the register UI.
- **Doc changes agreed-in-principle (not yet done):** reword CLAUDE.md "Removed features" P6-02
  line (deal-lookup stays removed; ProductBarcode-as-navigation kept; StockItem.barcode dropped);
  write `docs/04_proposals/PROPOSAL_BARCODE_SCANNING.md`.
- **Recommended resolution:** **now** — first user message next session.

## [RESOLVED] FU-054 — Shop-mode + lists-overview still sum line prices client-side
- **Raised:** 2026-06-07 (Phase 1 Chunk 5 — Type B)
- **Type:** follow-up
- **State note:** RESOLVED 2026-06-07 (Chunk 5b). Both turned out to operate on a
  single fetched detail (shop-mode = the open list; overview `loadPrimaryStats` =
  the *primary* list — not multi-list), so they now read `detail.totals` (added in
  Chunk 5) directly. Removed the client sums + the unused `priceOfLine`/
  `savingsOfLine` imports. Per-line `priceOfLine` display retained in the detail page.
- **What:** Chunk 5 moved *whole-list* totals to the server (`ShoppingListDetailDto.totals`)
  and switched the dashboard + detail page to read them. Two surfaces still sum
  `priceOfLine`/`savingsOfLine` client-side: `ShoppingListShopMode.vue:408-411`
  (sums over `sortedLines`/`remainingLines` — *subsets*, possibly route-ordered, so
  not a straight `detail.totals` read) and `ShoppingListsOverview.vue:522-525` (sums
  per-list across *multiple* lists in the overview — the overview may not fetch each
  list's full detail, so it has no `totals` to read).
- **Why deferred:** subset/multi-list summation needs either per-list-summary totals
  on the lists endpoint (so the overview shows totals without full details) or
  careful subset handling in shop mode — bigger than the named flagship (R-007).
- **Recommended resolution:** **opportunistic / fold into the shopping-list redesign
  pass** — expose per-list totals on the shopping-list *summary/list* endpoint for the
  overview; for shop mode decide whether its subset totals can read `detail.totals` or
  genuinely need a filtered sum. Per-line `priceOfLine` display stays client-side
  (accepted Type-C).

## [RESOLVED] FU-053 — "Best deals" card still fetches all products + sorts by discount client-side
- **Raised:** 2026-06-07 (Phase 1 Chunk 5 — Type B / proposal §8.2)
- **Type:** follow-up
- **State note:** RESOLVED 2026-06-07 (Chunk 5b). Added `GET /api/products/best-deals?limit=N`
  (`GetBestDealsHandler`, ranks on-special products by discount % server-side via the
  new `dora_api/domain/product_offer.discount_percent`); the dashboard queries it for
  the top 3 instead of downloading all products. Inline `discountPctFor` removed; the
  `% off` badge uses the shared `discountPercent` (widened to accept a `Product`).
  Future optimisation (noted, not done): a SQL `ORDER BY` on the discount expression
  instead of loading all products + ranking in Python — fine at current scale.
- **What:** The dashboard "best deals" card (`DashboardPage.vue` `bestDeals` ~L1190,
  `loadProducts` fetches *all* products via `GET /api/products`) filters + sorts by
  discount % in the browser and slices top-3. The discount-% is computed inline
  (`discountPctFor`) duplicating the shared `scrapedProductOfferLogic.discountPercent`
  (a tiny Type-C dup). Proper fix (proposal §8.2): a `?sort=discount&limit=N`
  (or focused best-deals endpoint) so the server sorts and returns only the top N.
- **Why deferred:** `price_now`/`price_was` come from the joined `Product.current_offer`,
  not Product columns, so sorting by `(price_was - price_now)/price_was` is a derived
  expression over a join — the generic field-based sort in `get_products.py` doesn't
  support it. That's a distinct capability (expression order_by + the on-special filter
  + null-RRP handling), riskier than the Chunk-5 flagship and best done deliberately.
- **Recommended resolution:** **later — a focused "best deals query" unit.** Add
  discount-sort support (or a `/products/best-deals?limit=N` endpoint) computing the
  discount server-side; switch the card to query it; fold `discountPctFor` onto the
  shared helper at the same time. Until then the card works (just over-fetches).

## [OPEN] FU-052 — Switch cookable surfaces to the server query + optimise the helper
- **Raised:** 2026-06-07 (Phase 1 Chunk 4 — queryable cookability)
- **Type:** follow-up
- **What:** Chunk 4 added the `?cookable` / `?max_missing` API + `cookable_count`,
  but the **shared-store surfaces still fetch all recipes and filter client-side**
  on `r.cookable` (RecipesOverview's cookable toggle / missing-max; the dashboard
  "Cookable tonight" list). Proposal step 4 ("switch the cookable surfaces to
  query") isn't finished. Two parts: (a) make those surfaces *query* the server
  (tricky — the recipes Pinia store is shared and does multi-facet client filtering,
  and the dashboard top-3 needs server-side sort+limit, currently client-sorted by
  favourite/last-made); (b) `load_recipe_cookability` loads **all recipes + full
  ingredient trees** on every dashboard summary and every cookable-filtered query —
  one query (not N+1) and fine at personal scale, but a set-based `COUNT(...) GROUP
  BY recipe` would scale better (watch SQLite/Postgres portability — avoid engine-
  specific `FILTER`).
- **Why deferred:** the store rewire is a real refactor needing browser verification
  (FU-051), and the perf optimisation is premature at current scale (R-007).
- **Recommended resolution:** **later — fold into the Type-B aggregates pass / when
  recipe counts grow.** Backend capability already exists; this is the client
  adoption + optimisation tail.

## [OPEN] FU-051 — Chunks 3–5 client changes not type-checked / browser-verified
- **Raised:** 2026-06-07 (Phase 1 Chunk 3); extended (Chunks 4, 5)
- **Type:** finding
- **What:** The Vue/TS files edited in Chunks 3, 4 **and 5** were verified only by
  manual grep (no dangling references) + reasoning. **They were not run through
  `eslint`/`vue-tsc` or the browser** because `web_app/node_modules` is absent on
  this machine and the local Node is v14.17 (too old for the Quasar toolchain).
  Risk: a type mismatch or template-binding slip could slip through. Likewise the
  Chunk-4/5 **server** additions (cookability filter + `cookable_count`; shopping-list
  `totals`) were unit-tested for their pure logic but **not run against real data**
  (this env's SQLite has no migrated tables — see FU-048), so the DB-backed query
  paths are unproven end-to-end.
- **Why deferred:** no runnable frontend toolchain / migrated DB in this session.
- **Recommended resolution:** **now/next session with a working env** — `npm install`
  then `npm run lint` + `quasar dev`; exercise: Recipes overview (cookable filter +
  footer count + compare dialog), a recipe card chip, recipe detail sidebar + editor
  "Missing" badge, meal-plans palette, dashboard "Cookable tonight" + count, Dora's
  "what's missing" (Chunks 3-4); **and the dashboard primary-list stats + the
  shopping-list detail headline totals (Chunk 5) — confirm $ remaining / savings /
  counts match what the lines imply.** On the server, hit
  `GET /api/recipes?cookable=true|false`, `?max_missing=1`, `/api/dashboard/summary`,
  and `GET /api/shopping-lists/<id>` (check the `totals` block) against seeded data.

## [OPEN] FU-050 — Broader `'Out of Stock'` name-match smell beyond the 7 cookability copies
- **Raised:** 2026-06-07 (Phase 1 Chunk 3)
- **Type:** finding
- **What:** Chunk 3 removed the 7 *recipe-cookability* client copies. A grep
  shows `'Out of Stock'` / `'Low Stock'` name-matching still lives in non-recipe
  surfaces: `MealPlansOverview.vue:484,494` (the meal-plan "need to buy"
  `stockLevelName`/`needToBuy`), `ShoppingListsOverview.vue:489` (restock
  sources), `RecipeCookMode.vue:559` (cook-mode availability), `StockItemChip.vue`,
  `StockItemRow.vue`, `useStockFilters.ts` (stock-page filters). Some are
  legitimately client-side (stock-page filters = state-ownership Type D) or use
  the shared `stockLevelLogic.getStockLevelColour` helper (accepted Type C); but
  `needToBuy`, the restock sources, and cook-mode availability are the same
  cross-entity rule the §8.3 addendum flags as the "wider smell" and could adopt
  the StockItem server booleans (now on the TS model) instead.
- **Why deferred:** out of Chunk-3 scope (R-007 — Chunk 3 is specifically the 7
  cookability copies).
- **Recommended resolution:** **opportunistic / a follow-on state-ownership pass** —
  migrate `needToBuy`, restock sources, and cook-mode availability to read
  `stockItem.is_out_of_stock` / `is_low_stock` / `needs_restock`. Leave the
  stock-page filters (Type D) and the color helper (Type C) per §8.1.

## [OPEN] FU-049 — RecipeDetailPage cookability reflects saved recipe, not live edits
- **Raised:** 2026-06-07 (Phase 1 Chunk 3)
- **Type:** finding
- **What:** The recipe-detail sidebar "Cookable now / Missing N" + in/tracked
  counts now read the *loaded* `recipe.value` server fields rather than the live
  editable `form.ingredients`. So while a user adds/removes ingredients (before
  saving), the sidebar aggregate doesn't update until save (which reloads the
  recipe). The per-ingredient editor "Missing" badge *does* update live (reads
  the stock store's `is_out_of_stock`). Previously the whole sidebar updated live
  off client-recomputed stock joins.
- **Why deferred:** the server can't know unsaved ingredients, and recomputing
  the aggregate client-side is exactly the duplication Chunk 3 removed. The page
  reloads after every save, so the steady-state is correct.
- **Recommended resolution:** **confirm acceptable in browser** (FU-051). If
  live-while-editing is wanted, derive the aggregate from the editor rows'
  `isMissingItem` (already server-boolean-based) instead of `recipe.value` — a
  small, contract-clean change.

## [OPEN] FU-048 — e2e suite (`tests/e2e/dora_api/`) is pre-existing broken on this branch
- **Raised:** 2026-06-06 (Phase 1 Chunk 1 — stock-status contract)
- **Type:** finding
- **What:** Running `tests/e2e/dora_api/test_stock_level_router.py` /
  `test_stock_item_router.py` yields dozens of failures/errors. They fail
  **identically with my Chunk-1 changes stashed**, so they predate this work.
  Sampled root cause: `test_stock_level_router.py:17` does
  `requests.get('/api/stock-levels').json()[0]` and gets `KeyError: 0` — the
  endpoint returns a paginated/enveloped shape now, but the tests still assert a
  bare list. Likely a broad response-shape/auth drift the e2e tests were never
  updated for. The server itself boots and returns 200s.
- **Why deferred:** out of scope for Chunk 1 (the contract change is verified by
  the new unit test + in-process smoke). Fixing the e2e harness is its own job and
  touches many test files.
- **Recommended resolution:** **later — dedicated "repair e2e suite" pass** (align
  the e2e assertions with the current paginated response shape + auth/session
  setup). Until then the e2e suite can't gate Phase 1 work; lean on unit tests +
  in-process smokes.

## [OPEN] FU-047 — `confirm_actions._resolve_level` still maps phrases → hardcoded level names
- **Raised:** 2026-06-06 (Phase 1 Chunk 1 — stock-status contract)
- **Type:** finding
- **What:** `dora_api/features/assistant/confirm_actions.py` `_LEVEL_ALIASES`
  maps user phrasings ("out", "gone", "low", "plenty") to canonical level
  **name** strings, then `_resolve_level` looks the level up by `name.eq(...)`
  with a substring fallback. This is NLU input resolution (deliberately left out
  of the Chunk-1 sequence migration), but it's still name-coupled and brittle:
  the aliases use `"Sufficient"` / `"Well Stocked"` which do **not** exactly match
  the seeded `"Sufficient Stock"` / `"Well-Stocked"`, so those alias paths fall
  through to the substring fallback (latent — "ok"→"Sufficient" won't exact-match).
- **Why deferred:** §3.1 scope is server-*derived* status facts, not free-text
  user→level resolution; converting it cleanly means mapping phrase → `StockStatus`
  → `level_for_status(...)`, a small assistant-side refactor better done with the
  assistant work.
- **Recommended resolution:** later during the assistant/SLM work (or
  opportunistic) — re-key `_LEVEL_ALIASES` to `StockStatus` and resolve via
  `level_for_status`, fixing the `"Sufficient"`/`"Well Stocked"` mismatch at the
  same time.

## [OPEN] FU-046 — A1 theme chunks D–F regressed since "done"; CHANGELOG over-claims
- **Raised:** 2026-06-06 (A1 STEP 2 Chunk D verify/finish)
- **Type:** finding
- **What:** `CHANGELOG.md` [Unreleased] (committed in `5819fe8 "Begin major rework —
  part A1 A2…"`) claims A1 STEP 2 Chunks **D, G, C, B, E, H, F** all theme-token-
  compliant. They *were* at that commit, but later wave-A/B feature work re-introduced
  Quasar palette literals on several surfaces. Confirmed live offenders on a
  2026-06-06 scan: **Chunk D** — `RecipesOverview`/`RecipeDetailPage`/`RecipeCard`
  (4 literals; **fixed this session**); **Chunk B** — `StockItemRow.vue:274`
  (`colour:'grey-5'`); **Chunk E** — `MealPlansOverview.vue:96-97` (`'grey-4'`/
  `'grey-9'` cookable chip, same pattern as RecipeCard); **Chunk G** —
  `ProviderHealthChip.vue:23` (`'grey-7'`). Broader `grep` flags ~12 surfaces total,
  but several are accepted carve-outs (ScanOverlay DEC-4, ProductSearchCard DEC-8,
  MerchantLogo DEC-9, settings theme swatches DEC-10) — needs a per-file pass to
  separate regressions from carve-outs.
- **Why deferred:** out of scope for "finish Chunk D" — fixing B/E/G/etc. regressions
  is a separate sweep, and the carve-out/regression split needs per-file judgement
  against the DEC list. Logged so the stale "all chunks done" CHANGELOG claim doesn't
  fool the next agent into skipping a needed re-sweep.
- **Recommended resolution:** **opportunistic — run an "A1c regression re-sweep"**
  (re-grep every claimed-done chunk surface for palette literals, fix genuine
  regressions, leave DEC carve-outs) before signing A1 off as complete. The
  cookable-chip `positive/grey` pattern (RecipeCard + MealPlansOverview) is the most
  common regression shape — worth a shared neutral-chip approach.

## [OPEN] FU-045 — Migrate to Postgres as the standard datastore (SQLite kept for lightweight self-host)
- **Raised:** 2026-06-06 (distribution posture — Decision 5 / §7.5)
- **Type:** deferred job
- **What:** Make **Postgres the standard datastore** for dev + hosted; SQLite stays
  supported as the zero-dependency lightweight self-host option (user decision:
  Postgres-default, *not* Postgres-only — retiring SQLite would raise the self-host
  bar). Motivation: SQLite feels too unstable for the long term. Scope when done:
  local Postgres dev setup (docker-compose or similar), confirm Alembic migrations
  run clean on both engines, keep the dev reset flow (`drop_all` /
  `DORA_ALLOW_DESTRUCTIVE` — see memory) working on Postgres, and re-check the
  UUID/`text()` binding sharp edge (Postgres has native UUID, so the raw-`text()`
  workaround likely simplifies — verify both inbound and outbound). Keep the
  ORM/migration layer portable both ways per discipline #2.
- **Why deferred:** posture recorded now; the actual migration is real engineering,
  best done as its own focused unit rather than mid-stream. No urgency — SQLite works
  today.
- **Recommended resolution:** **later — fold into Phase 4 productionize**
  (`RECONCILED_FINISHING_PLAN.md §5`, which already lists "Postgres/gunicorn/Redis"),
  OR opportunistically sooner if the user wants to dev against Postgres before then.
  Not a blocker for Phase 0/1.

## [OPEN] FU-044 — C-help opt-in help-overlay brief written; awaiting approval + per-surface hint rollout
- **Raised:** 2026-06-06 (user-floated idea → `PROPOSAL_HELP_OVERLAY.md`)
- **Type:** deferred job (design brief done; implementation pending approval)
- **What:** A persistent "?" toggle overlaying dismissible per-element "what does
  this do" hints — the opt-in inverse of the forced tour C-5 removed. Net-new
  cross-cutting front-end component (no existing tour/coachmark system). The
  expensive part is **content** (a hint per control, kept from rotting), so the
  brief defers the hint corpus to a per-surface rollout folded into each C-1..C-9
  implementation prompt.
- **Why deferred:** brief-only per the Wave-C ritual; no code until the user
  approves and resolves §4 open decisions (reveal style, content model, mascot,
  discoverability).
- **Recommended resolution:** **when the user approves the brief** — build the
  mechanism + `v-help` directive first (§8.1), then seed hints on the highest-
  confusion surfaces, then roll out per-surface as each C-brief implements. Pair
  the C-5 finish-card mention (§4-4) with C-5 implementation.

## [OPEN] FU-043 — C-locale international-readiness brief written; awaiting approval
- **Raised:** 2026-06-06 (user-floated idea → `PROPOSAL_LOCALE_I18N.md`)
- **Type:** deferred job (design brief done; implementation pending approval)
- **What:** Make Dora usable outside Australia. Companion split solves product
  sourcing; Dora-core still has AU residue — hardcoded `$` currency, `en-AU` voice
  default (`useVoiceInput.ts`), AU merchant branding/copy/seed in core, and a
  **dormant vue-i18n scaffold** (installed in `boot/i18n.ts`, locale hardcoded
  `en-US`, stub messages, zero `$t()`). Brief recommends Layer A (currency/format
  neutrality) + Layer B (de-AU core) now; Layer C (full UI translation) deferred.
- **Why deferred:** brief-only; no code until approval + §3 open decisions
  (currency home, vue-i18n adopt-vs-rip, C-10 currency field, merchant-logo fate).
- **Recommended resolution:** **when the user approves** — fold the currency
  setting + shared money formatter into the C-cross config work (they share the
  config layer); coordinate the C-10 currency field with the ingestion impl;
  de-AU (voice/branding/seed) is independent and low-risk. Layer C stays parked.

## [OPEN] FU-042 — Alerts bell count ≠ list count (badge excludes low + ignores snooze)
- **Raised:** 2026-06-06 (C-9 brief; feedback L438)
- **Type:** finding (reported bug — root cause found statically)
- **What:** The bell badge shows fewer than the dropdown lists ("I see 6, the bell
  shows 10"). Two causes: (1) badge = `high_count + medium_count` (`alertStore:99`)
  — it **excludes low-severity**, but the list shows all severities; (2) the badge
  uses raw backend counts while the list filters **client-snoozed** alerts
  (`alertStore:81`), so snoozing shrinks the list but not the badge.
- **Why open:** real reported bug; fixable independently of the full C-9 page.
- **Recommended resolution:** define ONE "what counts" set (C-9 §2.3) and derive
  the badge, bell list, dashboard card, and page from it — badge number must equal
  the count of items in its tier, and snooze must apply everywhere. Confirm in
  browser after. Can ship ahead of the control-centre page.

## [OPEN] FU-041 — Onboarding "you already have groups/locations" copy on first-run
- **Raised:** 2026-06-06 (C-5 brief; feedback L32/L33)
- **Type:** finding (reported defect — didn't reproduce statically)
- **What:** User reported the seed step says "You already have some groups set
  up…" / "You already have locations…" during *first-time* setup. Static read
  shows that copy is gated on `has_groups`/`has_locations` (`onboarding.py:94-117`,
  `WelcomeWizard.vue:161-172,195-205`), which are false on a truly-empty DB — so it
  shouldn't render on a clean install. The user likely had dev/seed data or a prior
  seed run. No migration pre-creates *user* groups/locations (confirmed).
- **Why open:** the report came from real usage; a static read isn't proof.
- **Recommended resolution:** **confirm in browser** on a genuinely fresh DB
  (register first user → onboarding) that the "already have" copy does NOT appear
  and the seed checkboxes are enabled. If it DOES appear, find what's seeding user
  groups/locations and fix. Folded into the C-5 §2.6 design either way.

## [RESOLVED] FU-040 — C-4 should model structured recipe steps (C-3 depends on it)
- **Raised:** 2026-06-06 (C-3 brief)
- **Type:** follow-up (design dependency)
- **What:** Recipe instructions are a freeform text blob (`recipe.py` instructions;
  cook mode splits on newlines, `RecipeCookMode.vue:356-363`). Cook mode's richer
  per-step features — reliable ingredient highlighting (instead of fragile
  text-match), per-step tools, per-step hints, per-step timers — all need
  **structured steps** (step = text + optional sub-steps + hint + the
  ingredients/tools it uses). This is a recipe-model change that belongs in **C-4**
  (adjacent to its multi-part "sections"), not cook mode.
- **State note:** 2026-06-08 — resolved at the design level: C-3 DEC-2 chose "Structured steps in C-4 + remove ticks", and `PROPOSAL_COOKBOOK.md §2.6a` was added with the model (`RecipeStep`: text, sub_steps, hint, ingredient_refs, tool_refs), the editor + importer story, and a §6 sequencing slot (item 5a) flagging it as a blocker for C-3 highlight/per-step features. Freeform recipes degrade gracefully. Code implementation is still outstanding (no model migration written yet) — flip to a fresh implementation FU when work begins.

## [RESOLVED] FU-039 — Wire up `Recipe.image` (parallels StockItem.image)
- **Raised:** 2026-06-06 (C-4 brief)
- **Type:** deferred job
- **What:** `Recipe.image` was a dead field. C-4 Chunk 5 (L249) wires it end-to-end.
- **State note:** 2026-06-09 — implemented (static-only; browser-verify in FU-091).
  **Pattern pioneered (FU-033 StockItem.image should follow it):** the image is
  stored as a **data-URL string** (UTF-8 bytes) in the existing LargeBinary
  column; create/update accept an `image` data-URL field (6M-char cap); a new
  `GET /api/recipes/<id>/image` parses the data URL and returns raw bytes +
  mimetype; the list/detail DTOs carry only `has_image: bool` (no inlined
  base64); the SPA renders via `<img src=recipeImageUrl(id)>` (cache-busted on
  the detail page after save) with a coloured-initial placeholder fallback.
  Reusable `RecipeImageField.vue` handles pick/preview/clear.
  See [[stockitem-image-substitute-notes-intent]].

## [RESOLVED] FU-038 — Cart button fires contradictory double-toast on already-on-list
- **Raised:** 2026-06-06 (C-7 brief; feedback L154)
- **Resolved:** 2026-06-12 by Cart Button Chunk 1. The blind re-add
  path is gone — already-on-list now **toggles** (remove silently on
  1 list; popover with explicit Remove / Add-to-another on 2+). No
  more "0 added, 1 already on list" + "Added to your primary list"
  collision because the button never fires the add path when the
  item is already on a list. Static-only impl; browser-verify is
  **FU-127**.

## [OPEN] FU-037 — `.secret_key` hardcoded to `./data/`, ignores DORA_DATA_DIR
- **Raised:** 2026-06-06 (INV-3 re-verification)
- **Type:** finding (latent bug)
- **What:** `dora_api/app.py:23` resolves the session-secret file as
  `Path('data') / '.secret_key'` — a literal CWD-relative path, NOT
  `DORA_CONFIG.get_data_dir()`. Everything else (DB, config, uploads, logs)
  honours `DORA_DATA_DIR`. So on the desktop app (data dir =
  `%LOCALAPPDATA%\BenTalese\Dora`) the secret key instead writes to `./data/`
  relative to the launch CWD.
- **Why it matters:** the secret escapes the configured/backed-up data dir; it's
  CWD-dependent, so launching from a different folder regenerates it and silently
  invalidates all existing session cookies (everyone logged out). Found via
  static read; not yet observed at runtime.
- **Recommended resolution:** now/soon — change to resolve via
  `DORA_CONFIG.get_data_dir() / '.secret_key'`. Low-risk one-liner. Confirm in
  browser/desktop that sessions persist across a restart from a different CWD.

## [OPEN] FU-036 — Confirm Shop Mode "Substitute" swaps offer-only (gates INV-8)
- **Raised:** 2026-06-06 (INV-8)
- **Type:** finding
- **What:** Static read says Shop Mode's "Substitute" button
  (`ShoppingListShopMode.vue:176-182`) swaps the **merchant offer**, while the
  permanent stock-item substitute swap lives in the full-list per-line menu
  (`ShoppingListDetail.vue:756-763`). INV-8's "rework into Shop Mode" recommendation
  depends on this being true.
- **Why deferred:** INV is investigation-only; needs runtime confirmation.
- **Recommended resolution:** confirm in browser — in Shop Mode, tap "Substitute"
  on a line and verify it changes the offer/merchant (not the stock item). If it
  actually swaps the item, INV-8's recommendation changes.

## [RESOLVED] FU-035 — Stock overview silently shows only the first 50 items
- **Raised:** 2026-06-06 (INV-2)
- **Type:** finding (real bug)
- **What:** `stockItemStore.getStockItemsAsync` paged once and ignored
  `page.total`, so pantries with >50 items lost the tail.
- **Resolved:** 2026-06-12 by Stock Overview Chunk 1 — added
  `stockItemApiService.getAllPagesAsync()` (loops until a short page
  or `total` is reached, asks for `limit=500` per call), and switched
  the store to use it. Pairs with `q-virtual-scroll` so the now-larger
  list still renders smoothly. Static-only impl; browser-verify is
  **FU-120**.

## [OPEN] FU-034 — Wire up `StockItemSubstitute.notes` (substitution notes)
- **Raised:** 2026-06-06 (INV-1)
- **Type:** deferred job
- **What:** `StockItemSubstitute.notes` column exists (added in the
  `c8a1d3b6e9f4` undirected-refactor migration) but was never wired up.
  `add_substitute.py:66` hardcodes `notes=None`; absent from `SubstituteDto`;
  zero frontend references. **Intended feature** (user confirmed): notes should
  capture *how* to substitute, e.g. "X butter → Y amount of olive oil".
- **Why deferred:** wire-up work, not no-regret; best done with the substitute
  surface so the note shows where it's useful (incl. B8 cook-mode swap).
- **Recommended resolution:** later — fold into **INV-8** (substitute
  swap-into-list assessment) or **B8** cook-mode temporary-swap work.

## [RESOLVED] FU-033 — Wire up `StockItem.image` (own image + product fallback)
- **Raised:** 2026-06-06 (INV-1)
- **Resolved:** 2026-06-12 by Stock Overview Chunk 6. End-to-end:
  - Backend: `image` column deferred on the mapping (list endpoint
    no longer pulls megabytes per row). New `has_image` field on
    `StockItemDto` + `StockItemDetailDto`, hydrated by a single bulk
    SELECT that **OR**s the item's own image with any linked
    product's image — so the SPA's "show thumbnail?" decision
    matches what the bytes route will serve. New
    `GET /stock-items/<id>/image` route mirrors the recipe-image
    pattern; resolves own-image first, falls back to the first
    linked product that decodes cleanly, 404s if both miss.
  - Backend: `CreateStockItemRequest` and `UpdateStockItemRequest`
    accept `image` as a data-URL string (~6 MB cap); update treats
    explicit null as "clear".
  - Frontend: new `stockItemImageUrl(id, version?)` helper; row
    renders `<img>` with placeholder fallback (gated on
    `showStockImages`); `StockItemDetailPage` overview tab gets a
    `RecipeImageField` (reused, R-001) that saves immediately and
    bumps an `imageVersion` to bust the browser cache.
  - Static-only impl; browser-verify is **FU-125**.

## [OPEN] FU-032 — C-2: confirm B6 allocation works end-to-end in browser
- **Raised:** 2026-06-06 (C-2 recon)
- **Type:** finding
- **What:** Backend `_hydrate_unallocated` (in `get_recipes.py`) computes
  `unallocated_meals = max(available_meals - sum(future un-consumed
  servings), 0)` via a single GROUP BY. The recipe palette renders the
  result directly. On static read, B6 (allocation reduces "X unallocated
  of Y on hand") works correctly. Original B6 report was from real usage,
  so per the CLAUDE.md MANDATORY rule it stays `[OPEN] confirm in
  browser` until eyeballed.
- **Recommended resolution:** confirm in browser — cook 4 meals of a
  recipe, drop it on two future days (2 servings each), verify palette
  shows "(0/4)". If it doesn't, capture the response from
  `GET /recipes?...&include=unallocated` and re-open as a real bug.

## [OPEN] FU-031 — B9.3: stale "Recipes" labels after A8 cookbook rename
- **Raised:** 2026-06-06 (B9.3 sweep)
- **Type:** leftover
- **What:** A8 renamed Recipes → Cookbook (`/cookbook`; `/recipes` redirects).
  The command palette still says "Go to Recipes" → `/recipes`. Functional via
  the redirect, but the label is now stale. Same likely in other static lists
  (tour cards, help text). Worth a one-shot rename sweep.
- **Recommended resolution:** opportunistic — fold into the A8 wrap-up or
  next polish pass.

## [RESOLVED] FU-030 — Fullscreen 404 page redesigned (login-theme + Dora pic)
- **Raised:** 2026-06-06 (B9.9; user follow-up 2026-06-12: "page
  looks a bit boring, maybe use the login theme instead and add a
  suitable dora pic")
- **Resolved:** 2026-06-12 — rewrote `pages/ErrorNotFound.vue` to
  mirror `LoginPage.vue`'s "off-app" treatment: three drifting
  mesh-gradient blobs (magenta / dora amber / mint), floating
  mascot using `dorabot-fatal-error-or-offline.png`, glassy card
  with gradient "404", "This page wandered off" headline, and a
  "Take me home" CTA. Locally-scoped CSS variables (forced light
  tokens) for the same reason LoginPage does it — 404 can render
  pre-auth and `data-theme` can flip dark before sign-in.
  Respects `prefers-reduced-motion`. `ErrorPageNotFound.vue` (the
  in-layout variant via `PageErrorState`) was already themed and
  stays untouched.

## [OPEN] FU-029 — B9.4: confirm command-palette commands all trigger
- **Raised:** 2026-06-06 (B9.4; CLAUDE.md confirm-in-browser rule)
- **Type:** finding
- **What:** Ctrl+K palette: every static command has a wired action.
  `create.stock-item` navigates to `/stock?create=1` and the page already
  watches `route.query.create`. Reported defect "doesn't trigger some
  actions" did not reproduce in static code.
- **Recommended resolution:** confirm in browser — open palette, run each
  Create / Navigate / Shopping-lists / View / Help command, verify each
  produces the intended outcome. If any really is broken, re-open as a
  real bug with the command id.

## [OPEN] FU-028 — B9.1: confirm shopping-list drag-drop ordering
- **Raised:** 2026-06-06 (B9.1; CLAUDE.md confirm-in-browser rule)
- **Type:** finding
- **What:** Static walk-through (both drag-up and drag-down examples) ends
  with the dragged item correctly placed BEFORE the target index. Backend
  `bulk_operations.reorder_lines` sorts by `(sequence, id)`. Frontend
  `ShoppingListDetail.onLineDrop` insertAt math
  (`fromIdx < toIdx ? toIdx - 1 : toIdx`) is correct.
- **Recommended resolution:** confirm in browser — reorder a few times,
  drag both directions, drop on a row and check the dragged item lands
  exactly where the dashed outline showed. If wrong, capture the exact
  before/after order and we'll re-investigate.

## [OPEN] FU-027 — B9.7: log-rotation model decision (timed vs size)
- **Raised:** 2026-06-06 (B9.7)
- **Type:** open decision
- **What:** `dora_api/infrastructure/logging_setup.py:87` wires
  `RotatingFileHandler` size-based at 10MB × 5 backups. The current
  ~46k-line file is well below the 10MB trigger, so it has simply not
  rotated yet. The user's reported symptom — "logs span the wrong date
  range" — implies an expectation of *time-based* rotation (e.g. one
  file per day).
- **Decision needed:** keep size-based (and just trust the threshold), or
  switch to `TimedRotatingFileHandler` (and pick `when` — typically
  'midnight' for daily). Could also go hybrid (whichever fires first)
  but Python's stdlib doesn't ship that out of the box.
- **Recommended resolution:** decide before any other log-related work
  (INV touches `.local` folder layout — natural pair).
- **State note:** 2026-06-06 (INV-3) — root cause confirmed and a concrete
  recommendation written in `docs/05_investigations/LOGGING_AND_DATA_LAYOUT.md`
  (switch to `TimedRotatingFileHandler`, midnight, ~14 backups; keep `data/` +
  `cache/` split; no `.local` folder exists). Still `[OPEN]` pending the
  user's go-ahead to implement.
- **State note:** 2026-06-06 (post re-verification) — user asked whether the
  folder layout was actually verified; it was NOT originally (code-resolved paths
  described as if observed). Re-read the resolver directly: layout is less clean
  than first stated — `.secret_key` hardcoded escape (FU-037) + dev-vs-desktop
  log-nesting difference. On-disk confirmation still pending (app never run on
  this checkout); checklist added to the memo.

## [PARTIALLY RESOLVED] FU-026 — B9.5: precise repro for "undo behaves oddly across surfaces"
- **2026-06-07 update (P6-01 Chunk 1):** the *shopping-list finish→reopen* undo path is
  now server-owned — Reopen reverses from `finish_snapshot` instead of a brittle
  client-held `level_restores` snapshot, which directly addresses feedback L421 ("undo of
  done list is bad"). The cross-surface staleness vector below (an originating surface
  not refetching after an inverse runs elsewhere) is **still open** for non-list undos.
- **Raised:** 2026-06-06 (B9.5)
- **Type:** finding / open verification
- **What:** `useUndo` registry is sound (per-entry inverse closures, redo
  stack cleared on new register, pending optimistic states). The
  surface-level mutations (`updateStockItemAsync`) capture pre-state
  field-by-field and register an inverse and redo closure for every
  changed field — including expiry pushes and clears. Static read shows
  the example flow (push expiry on dashboard → clear on detail page →
  Ctrl-Z twice) yields the correct end states.
  - Closest plausible "oddly" without a repro: the *originating surface*
    (Dashboard alerts) caches its own `alerts.value` and does NOT
    refetch after an inverse runs on another surface. So Ctrl-Z mutates
    the store correctly, but the Dashboard renders stale state until
    the user navigates / refreshes.
- **Recommended resolution:** capture an exact reproduction (which
  action on which surface in which order, what was expected, what
  actually happened, ideally a screen recording). Then either fix the
  staleness vector with a surface-level refetch on the affected store
  or pick a different design.

## [OPEN] FU-025 — Eyeball A6 text scale (xl + slightly-larger default) on dense screens
- **Raised:** 2026-06-05 (A6)
- **Type:** finding
- **What:** A6 widened the steps to 14 / 16.5 / 20.5 / 23px (added Extra-large) and
  bumped the default a touch (16 → 16.5px), so EVERY md user sees slightly bigger
  text now. Needs a real-browser check: at **Extra large**, spot-check dense
  screens (Stock Overview, Recipe detail, Meal plans) for layout breakage; confirm
  tooltips now scale (new `.q-tooltip` rule); confirm the small step's ~9–12px
  captions are still readable. Light + dark.
- **Why deferred:** can't run the app (node_modules absent).
- **Recommended resolution:** now-ish — when the app is next run. Deliberately-fixed
  px left in place (ScanOverlay camera UI, PriceHistoryChart SVG labels, Dashboard
  3px/7.5px micro-gauge) are intentional carve-outs, not bugs.

## [OPEN] FU-024 — A7 leftovers: dead banner CSS + wider footer adoption
- **Raised:** 2026-06-05 (A7)
- **Type:** leftover
- **What:** (a) Removing StockOverview's summary banner left its scoped
  `.stock-summary-banner` / `.stock-summary-stat` CSS unused (harmless dead
  rules). (b) `PageCountsFooter` is only wired on the 3 prompt pages
  (StockOverview, RecipesOverview, MyProductsPage); other list pages
  (ShoppingLists, MealPlans, etc.) could adopt it for consistency.
- **Why deferred:** dead CSS is harmless; broader adoption was out of A7's
  defined scope (3 pages).
- **Recommended resolution:** opportunistic — delete the dead CSS next time
  StockOverview is touched (or during the Wave-C Stock Overview top-area
  teardown); adopt the footer on other list pages if/when they get polish.

## [OPEN] FU-023 — A5 leftover: spinners not yet migrated on deferred surfaces
- **Raised:** 2026-06-05 (A5)
- **Type:** leftover
- **What:** A5 unified loading on the active app pages, but left raw `q-spinner`
  on the **deferred surfaces** (Reports, Data→Export/Print, Settings sub-pages —
  per the prompt-pack "deferred" list) and on **DoraChat's typing dots** (a
  deliberate `q-spinner-dots` indicator). Also: overview pages got `AppSpinner`
  rather than list-skeletons — fine, but list-skeletons would be a nicer touch.
- **Why deferred:** those pages are flagged "do not design yet"; a spinner swap
  is harmless but low-value there, and DoraChat's dots are an intentional style.
- **Recommended resolution:** opportunistic — migrate the deferred-page spinners
  to `AppSpinner` whenever those pages are next worked on. Decide DoraChat dots
  separately (keep as a typing indicator, or switch to AppSpinner). Consider
  list-skeletons for the big overviews during the FU-010 holistic look pass.

## [OPEN] FU-022 — Confirm A4 reported filter bug did NOT reproduce
- **Raised:** 2026-06-05 (A4; back-filled per the non-issue rule)
- **Type:** finding
- **What:** A4 was built around a reported bug — "clearing a filter input filters
  *everything* out instead of behaving as filter off (empty MUST = off)." Static
  read across StockOverview / RecipesOverview / MyProductsPage / ProductSearch
  found it did **not** reproduce — every page already skipped blank predicates
  (truthiness / `!= null` / empty-array / boolean-false). A4 hardened them to be
  explicit anyway, but the original symptom was never observed.
- **Why deferred:** can't run the app (node_modules absent); the report came from
  real usage, so a static read isn't proof.
- **Recommended resolution:** confirm in browser — on each of the four pages,
  clear each filter and verify all rows return (no wipe-out). If a wipe still
  happens somewhere, re-open as a real bug.

## [OPEN] FU-021 — Confirm A3 reported modal bug did NOT reproduce
- **Raised:** 2026-06-05 (A3; back-filled per the non-issue rule)
- **Type:** finding
- **What:** A3 was built around reported bugs — modals that "navigate/commit away
  on click-outside" (esp. the unsaved-changes modal navigating instead of
  staying) and modals with "no Cancel." Static read found these did **not**
  reproduce in current code: the `$q.dialog` confirms (recipe delete,
  unsaved-changes, cook-start) only commit/navigate on explicit `.onOk()` and
  resolve false on dismiss; template dialogs don't commit on `@hide`; all had a
  Cancel/Close. A3 standardised them via `BaseDialog` anyway.
- **Why deferred:** can't run the app (node_modules absent); reported from real
  usage, so a static read isn't proof.
- **Recommended resolution:** confirm in browser — backdrop-click / Esc on the
  key modals (new-recipe, recipe delete, cook-finish, and especially the
  unsaved-changes dialog) must cancel WITHOUT navigating or committing. Re-open
  any that still misbehave.

## [OPEN] FU-020 — Recipe-detail substitute swap affordance (cook-mode-only for now?)
- **Raised:** 2026-06-05 (B8)
- **Type:** finding / open question
- **What:** B8 made substitute swapping a temporary **cook-session** action (in
  cook mode only). The recipe-detail "Find substitutes" dialog is now purely
  informational. Open question for the user: do you also want a quick swap
  affordance on the recipe detail page itself, or is cook-mode-only the intended
  model?
- **Why deferred:** cook-mode-only was the chosen scope for B8; adding a second
  swap entry point is a UX decision, not a bug.
- **Recommended resolution:** now-ish — quick user call. If "yes", design where it
  applies (a swap that's still non-destructive to the saved recipe — likely a
  "pre-stage this swap for the next cook" rather than editing the recipe).

## [OPEN] FU-019 — Confirm B8 reported defects that did NOT reproduce (per-defect)
- **Raised:** 2026-06-05 (B8)
- **Type:** finding
- **What:** Three user-reported B8 defects could not be reproduced in a *static*
  read of current code (post meals→recipes merge). Each was REPORTED from real
  usage, so each needs an in-browser confirm before it can be called resolved —
  tracked individually below, not dismissed as a blanket "all fine":
  - **(a) "Remove-from-favourites does nothing."** Static read: chain looks sound
    (`toggleFavouriteAsync` sends `!is_favourite` → PATCH → backend assigns →
    refetch). Confirm un-favourite persists in the running app. If it fails,
    likely PATCH-semantics (cf. B3) — re-open as a real bug.
  - **(b) "Clicking a related recipe dumps you on the Cookbook overview."** Static
    read: there is **no related-recipes section anywhere** in the current UI.
    Confirm whether the user expects one (i.e. is the real ask "add related
    recipes"?) or whether this is genuinely gone.
  - **(c) "All recipe actions inert except Cook."** Static read: every action
    (favourite, save, log-cook, adjust-meals, import, add-to-list, delete,
    export) is wired to a working handler. Confirm each actually fires in-app.
- **Why deferred:** can't run the app (node_modules absent); needs eyeballing.
- **Recommended resolution:** now-ish — confirm each of (a)/(b)/(c) when the app
  is next run. Flip to `[RESOLVED]` only once verified; re-open any that still
  break as real bugs.

## [OPEN] FU-018 — B7: wider sweep for "store mutation + page toast" double-emits
- **Raised:** 2026-06-05 (Wave-B self-audit)
- **Type:** finding
- **What:** B7's "no other double-toast patterns" verdict only walked
  `useShoppingListActions.addItems` callers. Same pattern could exist
  for any store mutation that toasts internally and a page handler that
  toasts on success after. Worth grepping for `$q.notify` and
  `notifyOk` calls inside store/composable methods, then cross-checking
  every caller for a follow-up notify.
- **Why deferred:** out of B7's original scope; opportunistic cleanup.
- **Recommended resolution:** opportunistic — fold into the next polish
  pass.

## [OPEN] FU-017 — B3: user re-test "can't save unless I change the name"
- **Raised:** 2026-06-05 (Wave-B self-audit)
- **Type:** open verification
- **What:** Static read says every update handler already does the right
  thing (`model_fields_set` + exclude-self on the name-uniqueness check).
  No code changed this session for B3. But the user originally reported
  the symptom in browser testing, and the Wave-B self-audit found two
  other "looked fine on paper, broken in browser" cases — so this might
  also reproduce despite the static evidence.
  - To re-test: edit a stock item, change only e.g. `expiry_date`, save.
    Then edit a recipe, change only `servings`, save. Both should
    succeed without a "name already exists" 422.
  - If it reproduces, capture the request payload + response body and
    share — that will tell us whether (a) wrong endpoint is being hit
    (e.g. the create-new path), (b) the frontend is sending a
    different `name` value than displayed, or (c) something else.
- **Why deferred:** can't reproduce statically; cheaper to wait for a
  live error than keep tracing speculative paths.
- **Recommended resolution:** when the user gets a browser session up
  next — try the test above; report back.

## [OPEN] FU-016 — Audit other "frontend cache vs backend mutation" guard races
- **Raised:** 2026-06-05 (B5 follow-up)
- **Type:** finding
- **What:** The onboarding "dead button" bug was a stale `authStore.currentUser`
  read by the router guard after `onboardingApi.completeAsync()` updated the
  backend. The same shape could exist for any flow where the backend mutates
  user-scoped state that a guard or computed reads from a frontend cache —
  candidates worth scanning: account changes (email/role/admin flag), data
  import/restore, restart-onboarding, and stock-item Undo restore. Look for
  `currentUser?.*` reads in router and layout guards, and pair each with the
  store mutation that should refresh them.
- **Why deferred:** out of B5's bug-fix scope; cross-cutting audit.
- **Recommended resolution:** opportunistic — fold into a Wave-A or polish
  pass once one obvious symptom shows up; not worth a dedicated session.

## [OPEN] FU-015 — B5: Onboarding tour "Alerts" card points at stock, not /alerts
- **Raised:** 2026-06-05 (B5)
- **Type:** finding
- **What:** `WelcomeWizard.vue` `TOUR_CARDS` "Alerts — Dora pings you" still
  routes to `/stock?attention=true` (its description even says "deep-link
  into Stock"). Now that `/alerts` exists as a real page, the tour card
  could go there instead — or keep both as different teaching moments
  (Stock + filter vs the dedicated list).
- **Why deferred:** out of B5's bug-fix scope; user-style decision.
- **Recommended resolution:** opportunistic, or fold into the C-wave
  alerts control centre brief.

## [OPEN] FU-014 — B1: confirm `image` field round-trips for product create
- **Raised:** 2026-06-05 (B1)
- **Type:** finding
- **What:** `CreateProductRequest.image` is typed `Base64Bytes | None` but the
  frontend ships `offer.image` as a string (likely a raw URL or a `data:` URL).
  B1 didn't change this — pre-existing — but the offer-spread fix in
  `ensureSaved` now sends `image` explicitly, so it'll exercise the parse path
  every save. If creates 422 on `image`, switch the request model to
  `str | None` (a URL, not bytes) or make the frontend omit the field.
- **Why deferred:** out of B1's scope (B1 was field-list mismatches, not type
  mismatches); no node_modules so couldn't test live.
- **Recommended resolution:** opportunistic — first time the user actually
  saves a scraped product in browser, watch for a 422 on `image`.

## [OPEN] FU-013 — A4 leftover: "consistent multi-select control" only partial
- **Raised:** 2026-06-05 (A4)
- **Type:** leftover
- **What:** A4 standardised the filter-bar shell (panel/search/active-count/clear)
  but did NOT build a dedicated shared multi-select control. Multi-selects remain
  page-specific: `RecipesOverview` uses `q-select multiple use-chips`,
  `ProductSearch` merchant picker + `StockOverview` levels are bespoke chip UIs.
- **Why deferred:** the bespoke chip pickers carry extra behaviour (health
  icons, level colours, counts) that a generic control would lose; forcing one
  control would be a regression. The shell was the high-value standardisation.
- **Recommended resolution:** opportunistic — only if a future page needs a plain
  multi-select; otherwise leave the bespoke ones. Not no-regret.

## [OPEN] FU-012 — FilterBar panel has no visual container
- **Raised:** 2026-06-05 (A4)
- **Type:** finding
- **What:** `FilterBar`'s collapsible panel is a plain div. `ProductSearch`
  previously wrapped its filters in a bordered `q-card`; that border is now gone
  (so all four pages match the borderless inline style the others always used).
- **Why deferred:** consistency was the goal; the other 3 pages never had a card.
  Whether the panel wants subtle containment (border/elevation) is a design call.
- **Recommended resolution:** fold into the FU-010 holistic look review, or a
  quick tweak to `FilterBar.vue` if the panel reads as too bare in the browser.

## [OPEN] FU-011 — AuditLogSettings filtering not standardised
- **Raised:** 2026-06-05 (A4)
- **Type:** finding
- **What:** `settings/AuditLogSettings.vue` has ~9 filter fields with its own
  apply/clear UX. A4 deliberately did not touch it (the prompt scoped A4 to the
  four data-list pages and excluded the deferred/settings pages); its filtering
  is also server-side (sends a query), not the client-predicate pattern FilterBar
  assumes.
- **Why deferred:** out of A4's defined scope; different (server-side) mechanism.
- **Recommended resolution:** later — only if settings/admin gets a dedicated
  polish pass; low priority.

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
- **Also feed in:** other light themes' `--text-muted` contrast nudge ([[FU-003]]),
  and the structural dual-source collapse ([[FU-004]]) so the review isn't fighting
  a moving target.
- **Why deferred:** look-and-feel polish is best judged late, in one sitting, on a
  near-final app — not litigated token-by-token mid-build.
- **Recommended resolution:** later — a dedicated pass during **Phase 3 (champion
  polish)** or just before **Phase 4 (commercialize)**, once the app is feature-
  complete enough to eyeball holistically. Requires the app actually running
  (deps installed) and ideally a side-by-side across all themes.

## [OPEN] FU-009 — Decide fate of the 3 specialised overlays vs BaseDialog
- **Raised:** 2026-06-05 (A3)
- **Type:** finding
- **What:** `AlertsBell` (seamless drawer), `CommandPalette` (search overlay), and
  `ScanOverlay` (persistent camera) were intentionally left on raw `q-dialog` —
  they aren't standard card modals.
- **Why deferred:** folding them into BaseDialog adds no value and risks their
  custom layout/positioning.
- **Recommended resolution:** now (quick yes/no from user) — otherwise leave as the
  documented permanent exception.

## [OPEN] FU-008 — Unify dialog chrome via BaseDialog `title`/`#actions` slots
- **Raised:** 2026-06-05 (A3)
- **Type:** deferred job
- **What:** A3 migrated dialogs as a shell transform; each still carries its own
  header/footer markup. BaseDialog already exposes `title`/`closable`/`#actions`
  to standardise chrome.
- **Why deferred:** rewriting ~28 heterogeneous dialogs' internals is large and
  risky for a cosmetic-consistency gain.
- **Recommended resolution:** opportunistic — convert a dialog's chrome whenever
  it's being touched for another reason; no dedicated pass needed.

## [OPEN] FU-007 — Eyeball A3 modals in a real browser
- **Raised:** 2026-06-05 (A3)
- **Type:** leftover
- **What:** A3 was verified statically only — `node_modules` isn't installed in
  this checkout, so no lint / `quasar build` / dev-server run happened. Need to
  confirm backdrop+Esc dismiss without committing, and that the comparison /
  orphans / quick-add cards (scoped-class → `card-style` fix) still size right.
- **Why deferred:** can't run the app without installing deps.
- **Recommended resolution:** now-ish — once deps are installed / before signing
  off Wave A.

## [OPEN] FU-006 — Migrate the remaining ~289 `q-btn` to BaseButton
- **Raised:** 2026-06-04 (A2 Phase 2); rescoped 2026-06-05
- **Type:** deferred job
- **What:** A2 took the app from 399 → ~304 `q-btn`; it currently sits at **~289
  plain `q-btn`** (+ 4 `q-btn-dropdown`, 6 `q-btn-toggle`) across ~40 files. This
  is **NOT part of the standard plan** — A2's prompt was scoped to *toolbar*
  buttons + "New X" placement only, and no other prompt covers the rest. So the
  remainder is a genuine unplanned leftover, captured here on purpose.
- **Breakdown / nuance (don't treat as one uniform job):**
  - **Inline list-row action buttons** — the bulk (recipe cards, stock rows,
    shopping-list lines, settings rows). Low visual impact, the main target.
  - **Products surface** (`MyProductsPage` ~20, `ProductSearch` ~18) — **skip
    these**: that surface is moving to the companion app (master Decision 1), so
    it's intentionally minimal-touch. Migrating them is likely wasted effort.
  - **`q-btn` in `q-input` append slots** (search-clear, copy-to-clipboard) —
    intentionally the minimal pop-out style; leave as-is.
  - **`q-btn-dropdown` / `q-btn-toggle`** — different APIs, out of BaseButton
    scope by design (see FU-005).
  - **`DoraChat` (~14)** — its own component; migrate only if DoraChat is being
    reworked anyway.
- **Why deferred:** out of A2's defined scope; high count, mostly low-impact, and
  a chunk of it (products) shouldn't be migrated at all.
- **Recommended resolution:** later — a dedicated low-priority pass *after* Wave A,
  explicitly excluding the products surface, q-input append buttons, and the
  dropdown/toggle variants. Or purely opportunistic (migrate a page's inline
  buttons whenever that page is open for other work). Not no-regret; not urgent.

## [OPEN] FU-005 — `q-btn-dropdown` / split-button wrapper component
- **Raised:** 2026-06-04 (A2)
- **Type:** deferred job
- **What:** 4 `q-btn-dropdown` + 6 `q-btn-toggle` usages are out of BaseButton's
  scope (different APIs). A wrapper would unify split-buttons if there's appetite.
- **Why deferred:** different component API; not needed for A2.
- **Recommended resolution:** later — only if a design need arises; not no-regret.

## [OPEN] FU-004 — Collapse `themeService.ts` THEMES dict into CSS-var reads
- **Raised:** 2026-06-04 (A1b)
- **Type:** finding
- **What:** 7 themes still have the dual-source coupling between the `THEMES`
  palette dict in `themeService.ts` and `themes.scss`. Their values currently
  match (Pesto / Pesto Dark / Lemon Tart Dark were synced), but it's a latent
  drift hazard.
- **Why deferred:** values match today, so it doesn't block anything.
- **Recommended resolution:** later — a clean-up before commercialise (Phase 4),
  or when a theme bug points back to the dual source.

## [OPEN] FU-003 — Other light themes' `--text-muted` contrast nudge
- **Raised:** 2026-06-04 (A1b)
- **Type:** follow-up
- **What:** only the Pesto family got the `--text-muted` 50→42 lightness bump.
  Other light themes (Lemon Tart, Blueberry, Cherry Cola light, Sourdough light)
  may want the same for AA contrast.
- **Why deferred:** wanted to eyeball Pesto first before touching the whole family.
- **Recommended resolution:** later during a dedicated A1b contrast pass, after the
  user has eyeballed the themes.

## [OPEN] FU-002 — LoginPage `--lp-*` token ladder revisit
- **Raised:** 2026-06-04 (A1)
- **Type:** deferred job
- **What:** `LoginPage.vue`'s private `--lp-*` colour ladder was deliberately left
  untouched (DEC-2 — intentional splash).
- **Why deferred:** it's a one-off intentional design, not theme drift.
- **Recommended resolution:** later during **C19** (shared auth-shell) — revisit
  the whole auth surface together.

---

# Resolved

## [RESOLVED] FU-001 — "Flat danger" BaseButton variant for low-emphasis deletes
- **Raised:** 2026-06-04 (A2 Phase 2)
- **Type:** follow-up
- **What:** A2 left flat-negative delete buttons as raw `q-btn` because BaseButton
  had no flat-danger shape.
- **Why deferred:** needed a new BaseButton variant.
- **State note:** RESOLVED 2026-06-05 — `danger-ghost` variant added
  (`{ flat: true, color: 'negative' }`) and wired into `StockItemDetailPage`
  (Delete + clear-expiry) and `MealPlansOverview` (Delete plan).
