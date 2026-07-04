# Implementation Plan — Recipe importer (paste-based rebuild)

**Status:** Plan for review · **Date:** 2026-07-04 · **No code yet** —
phased plan + first reviewable chunk.
**Source proposal:** none — briefed inline in the current worklog session
(recipe importer legal + smart-import discussion, 2026-07-03/04). The
paste-vs-companion decision was resolved verbally: **legalize in place,
no companion split**. This doc formalises the plan.
**Adjacent plans:** `IMPL_PLAN_COOKBOOK.md` §Chunk 7 (URL importer polish
— **superseded** by Chunks 5–6 here); nothing else.
**Phase:** Phase 1 polish / pre-champion — closes three long-standing
followups (FU-104 legal, FU-199 SSRF, FU-396 GPL blocker in the importer
file) and adds a schema affordance (persistable unlinked ingredients)
that unlocks a "recipes + shopping list only" persona previously
gated on stock-item engagement.

**Open FUs this plan resolves:**
- [FU-104](../../DORA_FOLLOWUPS.md) — URL recipe importer's legal posture
  (was: "move to companion"; now: "legalize in place").
- [FU-199](../../DORA_FOLLOWUPS.md) — SSRF in recipe import-from-URL
  (closes by construction — no outbound HTTP means no SSRF surface).
- [FU-396](../../DORA_FOLLOWUPS.md) — `fuzzywuzzy` → `rapidfuzz` in the
  importer file (partial close — `global_search.py` still has fuzzywuzzy;
  will spin a residual FU for it).

**Related engineering rules:** `R-003` (server owns derived facts —
cookability rule change), `R-005` (distribution posture — legalizing in
place means core stays SaaS-safe), `R-010` (closed-set sentinels — the
new cookability tri-state), `R-014` (feature-flag / shown-disabled — the
neutral cookability rendering everywhere it's consumed).

**Charter alignment:** P1 Effortless (paste = one gesture the user does
anyway on any recipe site), P3 Honest (neutral cookability instead of
guessing True/False), P10 Anti-creep (no new server-side scraping
surface, no crawler infra), P12 No-invent (unlinked ingredients render as
"unlinked", not as a fabricated match).

---

## 0. Verify-state-first: no drift

Re-checked 2026-07-04 against the live code:

- **Fetcher** ([import_recipe_from_url.py:310-337](../../dora_api/features/recipes/import_recipe_from_url.py))
  — `requests.get(url, headers=_FETCH_HEADERS, timeout=10, allow_redirects=True, stream=True)` with a 3 MB cap. No scheme validation, no host validation, no redirect re-check. This is the SSRF surface FU-199 flagged.
- **Parser** ([import_recipe_from_url.py:229-247](../../dora_api/features/recipes/import_recipe_from_url.py))
  — `_first_recipe_from_html` walks `<script type="application/ld+json">` for
  a schema.org/Recipe object. When missing, `_degraded_import` at
  [:181-226](../../dora_api/features/recipes/import_recipe_from_url.py) dumps
  `<title>` + body text into `instructions` with `is_degraded=True` and
  returns **zero structured ingredients**. That is the current text-input
  floor.
- **Quantity/unit grammar** ([:255-303](../../dora_api/features/recipes/import_recipe_from_url.py))
  — permissive regex, reusable as-is against text-parsed ingredient lines.
  Handles fractions ("1/2", "1 1/2"), decimals ("1.5"), a fixed unit
  vocabulary (`cups?|tbsps?|tsps?|tablespoons?|teaspoons?|g|kg|ml|l|oz|
  lb|lbs|cloves?|cans?|pinch|slices?|sprigs?|bunch(?:es)?|knob|stick|pieces?`).
- **Fuzzy match** ([:386-392](../../dora_api/features/recipes/import_recipe_from_url.py))
  — uses `rapidfuzz.process.extractOne` (imported as `fuzz_process`); the
  file's `requirements.txt` line still declares `fuzzywuzzy==0.18.0`
  ([FU-396](../../DORA_FOLLOWUPS.md)). Match threshold is 70.
- **RecipeIngredient schema** ([table_mappings.py:686-704](../../dora_api/persistence/table_mappings.py)):
  `stock_item_id` is `nullable=False`, `ondelete="RESTRICT"`. No `raw_text`
  column. Entity dataclass ([recipe_ingredient.py:9-32](../../dora_api/domain/entities/recipe_ingredient.py))
  has `stock_item: StockItem` — no `| None`.
- **`CreateRecipeIngredientRequest`** ([create_recipe.py:50](../../dora_api/features/recipes/create_recipe.py))
  requires `stock_item_id: UUID`. Missing IDs return
  `missing_stock_item_ids` and reject the create. Preview DTO
  [`ImportedIngredientDto`](../../dora_api/features/recipes/import_recipe_from_url.py)
  allows `stock_item_id: UUID | None`, so the *wire* already supports the
  unlinked case; the *persistence* doesn't.
- **`ShoppingListLine`** ([table_mappings.py:286-299](../../dora_api/persistence/table_mappings.py))
  requires `stock_item_id IS NOT NULL OR product_id IS NOT NULL`. No
  freeform-text-only lines. Rules out "add unlinked ingredient to
  shopping list as a freeform line" without a second schema change we
  don't want. **"Add missing to list" surfaces a linking prompt for
  unlinked ingredients** instead (§Chunk 4).
- **Cookability** — `is_cookable_now` is a bool today (server-owned,
  R-003). Consumers: cookbook overview filter chip, RecipeCard badge,
  RecipeDetailPage chip, DashboardPage cookable-now card, meal-plan
  calendar chip, assistant `cookable_recipes` tool. All will get a
  tri-state (`True | False | None`) in §Chunk 3.
- **Corpus** — 20 fixtures under `docs/99_scratch/recipes/`. Class A
  (explicit `Ingredients` / `Instructions` headers): AllRecipes ×3,
  RecipeTin Eats ×3, Half Baked Harvest ×3, Sally's Baking ×2, Simply
  Recipes ×3, Taste.com.au ×1, Woolworths ×2 = **17 Class A**. Class B
  (no headers, `Serves N` anchor + prose): Smitten Kitchen ×3.

**Precedent:** `RECONCILED_FINISHING_PLAN.md` §7 Decision 1 (retailer
scraper moved to companion) informs the legal thinking but does *not*
apply here — that decision was about *ongoing scale* fetching against
retailer sites for pricing data; recipe import is *user-initiated,
one-off, per-URL* and legalises cleanly by shifting the fetch to the
user's browser (via Ctrl+A). No new companion surface required.

---

## 1. Chunked plan (each chunk = one reviewable PR)

Six chunks. Chunks 1–3 are pure parser + tests, low blast radius. Chunk 4
is the schema foundation (invisible until Chunk 5 activates it). Chunk 5
is the legalization moment (FU-104 + FU-199 close). Chunk 6 is the
leverage (bulk-linker turns the "save fast, link later" thesis into a
real speed win).

### Chunk 1 — Corpus + baseline tests ★ FIRST REVIEWABLE CHUNK
**Closes:** foundation only; no FUs.

**Deliverable:**
- Move 20 fixtures from `docs/99_scratch/recipes/` →
  `tests/fixtures/recipe_paste_corpus/`.
- Author `tests/fixtures/recipe_paste_corpus/_expectations.yaml` with
  minimum-shape assertions per fixture, hand-drafted from reading each
  fixture end-to-end:
  ```yaml
  recipetineats1:
    min_ingredients: 15
    min_steps: 6
    servings: 5
    prep_minutes: 15
    cook_minutes: 25
    first_ingredient_contains: chicken
    name_contains: portuguese
  ```
  Loose fences, not exact match — pinning `qty=2, unit=tsp,
  text="paprika"` per row makes every parser tweak break dozens of tests.
- New `tests/test_parse_recipe_from_text.py` — parametrized over the
  fixture dir + expectations file. Calls a stub
  `parse_recipe_from_text(text: str) -> ImportedRecipeDto` that raises
  `NotImplementedError`; the test wraps in `pytest.xfail` until Chunk 2.
- **No production code touched.** No SPA changes. Nothing shipped.

**Review criterion:** the YAML expectations look right to the user
(hand-off gate — the user reviews the ground-truth ceiling I've drafted
before I start parser work).

**Risk:** none — pure test infra.

---

### Chunk 2 — Class A parser (header-anchored)
**Closes:** foundation for Chunk 5.

**Deliverable:**
- New module `dora_api/features/recipes/_parse_recipe_from_text.py` (or
  inline in the eventual `import_recipe_from_content.py` — TBD by
  file-layout preference at review).
- `parse_recipe_from_text(text: str) -> ImportedRecipeDto` implementing
  anchor-based extraction:
  - **Section anchors**: case-insensitive line matches on
    `^\s*ingredients?\s*:?\s*$`, `^\s*(instructions?|method|directions?)\s*:?\s*$`,
    `^\s*(notes?|nutrition|comments?|related)\s*:?\s*$` (stop markers).
  - **Meta block regex**:
    - `servings?:\s*(\d+)` / `serves?\s+(\d+)` / `yield:\s*(?:.*?)(\d+)` / `makes?\s+(\d+)`
    - `prep(?:\s+time)?:?\s*(\d+)\s*(mins?|minutes?|hrs?|hours?)`
    - `cook(?:\s+time)?:?\s*(\d+)\s*(mins?|minutes?|hrs?|hours?)`
    - `total(?:\s+time)?:?\s*(\d+)\s*(mins?|minutes?|hrs?|hours?)`
    (units normalised to minutes; hours × 60).
  - **Ingredient extraction**: from the block between `Ingredients` and
    the next stop marker; strip common list-marker prefixes (`▢`, `-`,
    `*`, `•`, leading digits+`.`), run each stripped line through the
    existing `_parse_qty_unit`. Sub-section headers (lines that end in
    `:` or match a known section-header regex like `^for the .+:?$`) get
    passed through as `RecipeSection` client markers so the existing
    section-plumbing on save works unchanged.
  - **Step extraction**: from the block between `Instructions` (or
    `Method` / `Directions`) and the next stop marker; strip leading
    `\d+\.\s*` markers so structured-steps land clean.
  - **Name extraction**: first non-nav line before the meta block; fall
    back to fixture-provided title fixture if we can't isolate one
    heuristically.
  - Returns the same `ImportedRecipeDto` shape the existing importer
    uses. `is_degraded` is set true only when < 3 ingredients found
    (parser gave up).
- **Fuzzy matching**: reuse the existing `_match_vocab` + `_QTY_PATTERN`
  helpers; the parser depends on nothing else in the current importer.
- **Tests**: all 17 Class A fixtures pass `_expectations.yaml`
  minimum-shape. Smitten still fails (Class B — Chunk 3).

**Review criterion:** parser handles 17/20 fixtures. Failures on Smitten
are expected; the test suite reports which fixtures failed and why so we
can plan Chunk 3 against real data.

**Risk:** medium — the parser is subjective. Fixture-driven iteration
keeps the criterion objective.

---

### Chunk 3 — Class B parser + RapidFuzz sweep
**Closes:** FU-396 (importer half; the residual `global_search.py` swap
gets its own small FU).

**Deliverable:**
- Grammar-based Class B fallback in `parse_recipe_from_text`, triggered
  when no anchor headers are found:
  - **Recipe-start anchor**: `Serves\s+\d+` / `Yield:\s*.*` / `Makes\s+\d+`.
  - **Ingredient-line grammar**: from the anchor down, collect lines
    that match one of:
    - starts with a fraction / decimal / integer + optional unit
      (i.e. matches `_QTY_PATTERN`),
    - starts with `A|An` followed by an ingredient noun,
    - is under ~120 chars AND doesn't contain sentence-ending
      punctuation followed by capital-letter word ("this is prose").
  - **Sub-section header inference**: bare lines matching
    `^\s*(For the [^:]+|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:?\s*$`
    interspersed with the ingredient block promote to `RecipeSection`
    markers. Ambiguity heuristic: sub-section headers are followed by
    ≥2 lines that look like ingredients before another prose paragraph
    appears.
  - **Instruction start**: first long prose paragraph (> 120 chars OR
    starts with a verb prefix like `Make X:` / `Prepare X:`) after the
    ingredient block ends.
  - **Stop markers**: `Print Recipe`, `Email Recipe`, `Save to`,
    `Related`, `See more:`, `Post navigation`, `Share this`, `Leave a
    Reply`, `\d+ comments?`. Any recipe body ends when we hit these,
    even mid-instruction (the current Smitten fixture footer is a good
    stress test for this).
- **Swap `fuzzywuzzy` → `rapidfuzz`** in `requirements.txt` and any
  remaining explicit `import fuzzywuzzy` in the importer file. Score
  scale is identical (0–100); `_MIN_MATCH_SCORE = 70` stays.
- Log a new FU for the residual `global_search.py` swap so FU-396 can
  close cleanly on the importer half.
- **Tests**: all 20 fixtures pass `_expectations.yaml`.

**Review criterion:** 20/20 corpus green. RapidFuzz swap doesn't change
match behaviour on the existing importer tests.

**Risk:** medium — grammar-based text parsing on Smitten Kitchen is the
hardest case in the corpus. If the heuristic over-generalises it'll
mis-identify prose as ingredients on Class A sites too. Chunk 2's
anchor-based path takes precedence, so this fallback only fires when
anchors are absent — bounds the blast radius.

---

### Chunk 4 — Schema: persistable unlinked ingredients + neutral cookability
**Closes:** foundation for Chunk 5. No user-visible change on ship — no
recipe has unlinked ingredients yet.

**Deliverable — persistence:**
- New migration `<hash>_20260704_recipe_ingredient_unlinked.py`:
  - `RecipeIngredient.stock_item_id` → `nullable=True` (FK stays
    `ondelete="RESTRICT"` for linked rows so deleting a StockItem in-use
    still blocks; unlinked rows are unaffected).
  - Add `RecipeIngredient.raw_text: String(500), nullable=True`.
  - Backfill: for every existing row, set `raw_text` to the joined
    `StockItem.name` value. Preserves the ingredient label if the user
    later unlinks or the StockItem is deleted.
  - Add `CheckConstraint("stock_item_id IS NOT NULL OR raw_text IS NOT NULL",
    name="ck_recipe_ingredient_anchor")` — at least one anchor.
- Entity ([recipe_ingredient.py:9-32](../../dora_api/domain/entities/recipe_ingredient.py)):
  `stock_item: StockItem | None`, add `raw_text: str | None`.
- Mapping ([table_mappings.py:690-704](../../dora_api/persistence/table_mappings.py))
  matches the migration.

**Deliverable — cookability tri-state:**
- Server-side `Recipe.is_cookable_now` becomes `bool | None` (R-010
  closed-set: True / False / None). If any ingredient on a recipe has
  `stock_item_id IS NULL`, the answer is `None` — regardless of what the
  other (linked) ingredients look like. This is P3 Honest by construction.
- DTO layer: [get_recipes.py](../../dora_api/features/recipes/get_recipes.py)
  DTO exposes `is_cookable_now: bool | None`. Same for
  [get_dashboard.py](../../dora_api/features/dashboard/get_dashboard.py)
  cookable-now count (only counts `True`), meal-plan cookability, and the
  assistant `cookable_recipes` tool (excludes `None` from the "cookable"
  answer set; separately reports "N recipes need linking").
- **`CreateRecipeIngredientRequest`** ([create_recipe.py:50](../../dora_api/features/recipes/create_recipe.py)):
  `stock_item_id: UUID | None`, add `raw_text: str | None`, Pydantic
  validator enforcing at-least-one.
- **"Add missing to shopping list"** action:
  gathers linked-missing rows and adds them normally; returns
  `unlinked_ingredient_count` separately so the SPA can render *"N
  ingredients need linking first"* alongside the success toast. Wiring
  the jump target ("go link them") to the bulk-linker (Chunk 6) — until
  then the button opens the same recipe's detail page and highlights the
  unlinked rows.

**Deliverable — frontend cookability sweep (R-014):**
- **Cookbook cookable-now filter chip** (`RecipesOverview.vue`) — third
  state "unknown" is *not* introduced; the chip is a two-state toggle,
  and applying it excludes `None` from the result set (same as excluding
  `False`).
- **RecipeCard** — cookable badge renders dimmed with class
  `recipe-card__cookable--unknown` and a `<q-tooltip>` reading *"Link
  ingredients to check cookability — this is a stock-item feature."*
- **RecipeDetailPage** cookability chip — same neutral rendering + tooltip.
- **DashboardPage** cookable-now card — displays *"N cookable · M need
  linking"* when unlinked recipes exist, else the existing "N cookable"
  copy.
- **Meal-plan calendar cookability chip** — dimmed same as RecipeCard.
- **Assistant** — Dora's `cookable_recipes` answer includes a follow-up
  clause: *"Also, K recipes have unlinked ingredients — link them at
  Settings → Data → Unlinked ingredients."* when K > 0.

**Tests:**
- Existing recipe tests (all-linked ingredients) — no regressions.
- One new test: create a recipe with an unlinked ingredient →
  `is_cookable_now` returns `None` regardless of other ingredients' stock
  status.
- Migration test: forward + reverse on a seeded SQLite DB with existing
  linked-only rows; verify `raw_text` backfilled from `StockItem.name`.

**Review criterion:** existing recipes look identical; no user-visible
change until Chunk 5 introduces the first unlinked ingredient.

**Risk:** medium-high — cookability sweep touches ≥6 files across
backend + frontend. The fact that no data goes neutral on ship (existing
recipes are all-linked) means we can ship this alone and verify
zero-regression before Chunk 5 activates the unlinked path.

---

### Chunk 5 — Endpoint reshape + paste importer (THE LEGALIZATION LANDING)
**Closes:** FU-104, FU-199, and covers feedback bullets L261, L269, L296.

**Deliverable — backend:**
- Rename endpoint `POST /api/recipes/import-from-url` →
  `POST /api/recipes/import-from-content`. Body:
  ```
  { content: string, source_url?: string }
  ```
  `content_kind` field explicitly *not* added — we're text-only per the
  2026-07-04 decision. If the user pastes HTML (uncommon but possible),
  the parser handles it as text; the JSON-LD path in the current
  importer is deleted.
- Rename file
  `dora_api/features/recipes/import_recipe_from_url.py` →
  `dora_api/features/recipes/import_recipe_from_content.py`.
- Delete `requests.get(...)` block, `_FETCH_HEADERS`, `_FETCH_TIMEOUT`,
  `_MAX_BYTES`, `_degraded_import`, `_first_recipe_from_html`,
  `_iter_recipe_objects`, `_minutes_from_iso8601` (still used by parser
  for `PT30M`-style hints in the meta block — keep if the parser calls
  it; delete otherwise).
- Wire `parse_recipe_from_text` (Chunks 2–3) as the sole parse path.
- `source_url` is metadata only — stamped on `Recipe.source` at Save,
  never fetched. `git grep` verification that no downstream reads it as
  a fetch target.
- **FU-199 closes** — the SSRF surface is deleted, not fixed. No host
  validation, redirect-hop re-check, or block-list needed because
  there's no outbound HTTP.

**Deliverable — frontend:**
- `RecipeImportDialog.vue` (or the equivalent — grep during Chunk 5) gets
  restructured:
  - Top: single **paste textarea** with placeholder *"Paste the recipe
    (Ctrl+A / Ctrl+C on the recipe page)"* and a compact hint chip
    linking to a short list of sites known to work well (RecipeTin,
    AllRecipes, HBH, etc. — corresponds to L296 in a new-shape way:
    guidance is "these sites paste cleanly" not "these sites' JSON-LD
    works").
  - Below: optional `"Where's this from? (optional)"` URL field. Blank
    is fine; if filled, stamped on `Recipe.source` and the parser sees
    it as a hint (title fallback when name extraction fails, etc.).
  - Existing preview → confirm → save flow reused entirely. Response
    DTO shape unchanged (`ImportedIngredient`) — new field: unlinked
    rows already sent as `stock_item_id: null`, now render with a subtle
    "Unlinked" pill in preview.
  - **Save works with unlinked ingredients present.** Charter P1
    Effortless: don't force the user to resolve link decisions mid-flow.
- Cookbook overview "Import" button (added by Cookbook Chunk 7,
  L269-covered) stays — points at the same dialog.
- Old URL-input UI + related copy deleted.

**FU close-out notes filed into `DORA_FOLLOWUPS_RESOLVED.md`:**
- FU-104: "Legalised in place. The fetcher is deleted; parser accepts
  user-supplied content only. No companion split needed."
- FU-199: "Closed by construction. No outbound HTTP in the importer
  path; SSRF surface deleted."
- FU-396 (importer half): "Swapped `fuzzywuzzy` → `rapidfuzz` in Chunk 3;
  residual `global_search.py` swap tracked as FU-46X."

**Review criterion:** paste-import works end-to-end for at least 3
fixtures pasted verbatim from the corpus (browser verify). SSRF surface
`git grep`-clean. FU trail current.

**Risk:** low-medium — the parser has fixture tests as its floor; the
endpoint delete is mechanical; the SPA reshape is one dialog. The only
behavioural surprise is that recipes with unlinked ingredients now
render neutral-cookability — but Chunk 4 shipped that behaviour already.

---

### Chunk 6 — Bulk-linker page + PWA share target
**Closes:** completes the speed thesis + covers L261's paste flexibility.

**Deliverable — bulk-linker:**
- New page **Settings → Data → Unlinked ingredients**
  (`web_app/src/pages/settings/AdminDataUnlinkedIngredients.vue`).
- Server endpoint `GET /api/recipes/unlinked-ingredients` — returns
  grouped rows:
  ```json
  { unlinked: [
      { raw_text: "chicken breast", used_in_recipe_ids: [uuid, uuid, uuid], count: 3 },
      { raw_text: "olive oil",      used_in_recipe_ids: [uuid],             count: 1 },
      ...
  ] }
  ```
  Grouping key is `raw_text` case-insensitively normalised (trim,
  collapse whitespace, lowercase). Sorted by count desc, then raw_text
  asc.
- Row UX: `raw_text • used in N recipes` on the left, a `q-select`
  autocomplete against the user's StockItems on the right (same picker
  the recipe editor uses), plus **"Create new stock item"** action which
  opens the new-stock-item dialog pre-populated with `raw_text` as name.
- **Bulk apply**: picking a StockItem updates every RecipeIngredient row
  with matching normalised raw_text (one PATCH call per group). Recipes
  that transition from "any unlinked" → "all linked" flip
  `is_cookable_now` back to a real True/False.

**Deliverable — PWA share target:**
- Extend `manifest.json`:
  ```json
  "share_target": {
      "action": "/recipes/import",
      "method": "POST",
      "enctype": "multipart/form-data",
      "params": { "title": "title", "text": "text", "url": "url" }
  }
  ```
- New route `/recipes/import` (SPA-side) reads `title` / `text` / `url`
  from the URL query (GET fallback) or POST body, pre-fills the paste
  dialog: `content = text`, `source_url = url`, prompts the user to
  hit **Import**. Zero net-new server code.
- Verify on Android Chrome: system Share sheet shows "Dashy Dora" as a
  target after PWA install.

**Deliverable — coverage L261:**
- Recipe-edit dialog's instructions field gains a hint: *"Paste the
  recipe text or type freeform — Ctrl+V works."* Cheap copy tweak;
  L261's real answer is the paste import flow itself (Chunk 5), but the
  quick-create dialog benefits from the same signal.

**Tests:**
- Unit: raw_text grouping normalisation.
- E2E: `test_unlinked_ingredients_router.py` — GET returns groups; bulk
  apply updates all recipes; cookability re-derives correctly.

**Review criterion:** import 3 recipes from the corpus verbatim,
resolve their unlinked ingredients in one sitting on the bulk-linker
page (browser verify).

**Risk:** low — additive surfaces, no existing behaviour changed.

---

## 2. Data model diff summary

| Table / Entity | Before | After (Chunk 4) |
|---|---|---|
| `RecipeIngredient.stock_item_id` | `nullable=False, ondelete=RESTRICT` | `nullable=True, ondelete=RESTRICT` |
| `RecipeIngredient.raw_text` | — | `String(500), nullable=True` (backfilled from joined `StockItem.name` for existing rows) |
| `RecipeIngredient` CHECK | — | `stock_item_id IS NOT NULL OR raw_text IS NOT NULL` |
| `Recipe.is_cookable_now` (DTO / server-derived) | `bool` | `bool \| None` (None when any ingredient is unlinked) |
| `CreateRecipeIngredientRequest.stock_item_id` | `UUID` | `UUID \| None` + Pydantic at-least-one validator |
| `CreateRecipeIngredientRequest.raw_text` | — | `str \| None` |
| `ShoppingListLine` | `stock_item_id IS NOT NULL OR product_id IS NOT NULL` | **no change** — "add missing" surfaces a linking prompt for unlinked (Chunk 4 backend), not a schema loosening |

---

## 3. Suggested run order

1. **Chunk 1** — corpus + baseline test infra. Ship alone; wait for user
   YAML review before proceeding.
2. **Chunk 2** — Class A parser. Ship alone; 17/20 fixtures green.
3. **Chunk 3** — Class B parser + RapidFuzz swap. Ship alone; 20/20
   fixtures green.
4. **Chunk 4** — schema + cookability sweep. Ship alone; **verify
   zero-regression** in the browser (existing recipes still show
   True/False cookability, no visual changes on already-linked recipes).
5. **Chunk 5** — endpoint reshape + SPA paste importer. Ship alone;
   FU-104 / FU-199 close.
6. **Chunk 6** — bulk-linker + PWA share. Ship alone; the "smart
   importer" speed thesis pays off here.

Total: **six** landings. Each self-contained and reviewable in isolation.

---

## 4. Charter + rule alignment

- **P1 Effortless** — Ctrl+A / Ctrl+C / Ctrl+V is the muscle memory the
  user already has for any recipe site. No new UI verbs to learn. Save
  works with unlinked ingredients so the "just get this recipe in"
  moment isn't gated on linking decisions.
- **P3 Honest** — neutral cookability is the P3 kicker: the app admits
  "I don't know" instead of guessing True/False for recipes with
  unlinked ingredients. The tooltip explains *why*.
- **P10 Anti-creep** — no new server-side scraping surface, no crawler
  infra, no user-agent fingerprint, no host block-list to maintain.
  The whole "SSRF hardening" work item disappears because the surface
  disappears.
- **P12 No-invent** — unlinked ingredients render as unlinked, not as
  fabricated matches to arbitrary StockItems. Fuzzy threshold 70 stays;
  below-threshold matches are honestly reported as no-match.
- **R-003** (SSoT: server owns derived facts) — cookability tri-state
  is derived server-side and never duplicated on the client. The
  frontend only *renders* the state the server hands it.
- **R-005** (distribution posture) — core stays SaaS-safe. No
  companion-only feature, no self-hosted-only carve-out. Same artifact
  runs everywhere; managed deployments no longer carry an SSRF risk.
- **R-010** (closed-set sentinels) — `is_cookable_now: True | False |
  None`. Explicit tri-state; no untyped nulls floating in the code.
- **R-014** (feature-flag / shown-disabled) — neutral cookability
  renders dimmed with a tooltip explaining "this is a stock-item
  feature." Doesn't hide the surface entirely — that would be
  dishonest — but signals opt-in.

---

## 5. Coverage table — feedback bullets + FUs

Per the CLAUDE.md "Cross-checking against the original feedback" rule.
This work is cross-cutting (importer + persistence + cookability), so
the table maps only bullets and FUs that **motivated** the plan, not
every bullet across the cookbook surface.

| Bullet / FU | Description | Section |
|---|---|---|
| **L261** | Instructions field — flexible for copy+paste? | Chunk 5 (paste is now the primary import path) + Chunk 6 (quick-create dialog hint) |
| **L269** | Import from overview (good/bad idea?) | Chunk 5 — the overview import button (Cookbook Chunk 7) stays, now points at the paste dialog |
| **L296** | Importer site guidance | Chunk 5 — guidance shifts from "JSON-LD sites work" to "these sites paste cleanly", surfaced as a compact hint chip in the paste dialog |
| **FU-104** | Move URL importer to companion (legal) | **Superseded** — resolved by legalising in place (Chunk 5). No companion split. |
| **FU-199** | SSRF in `import-from-url` | Chunk 5 — surface deleted, not hardened. |
| **FU-396** | fuzzywuzzy → rapidfuzz (GPL blocker) | Chunk 3 — importer half. Residual `global_search.py` swap logged as a new FU. |
| **L295** | Recipe source as its own field | **Already closed** by Cookbook Chunk 7 (`Recipe.source` column). Chunk 5 preserves the behaviour — `source_url` stamps `Recipe.source` at save. |

**Coverage gaps updated:** L261 was previously uncovered; Chunk 5 + 6
adopt it. L269 / L296 previously assigned to IMPL_PLAN_COOKBOOK Chunk 7;
Chunk 5 here **supersedes** that Chunk 7 scope. `COVERAGE_GAPS.md` will
be updated on Chunk 1 landing to reflect the reassignment.

---

## 6. What this plan does NOT change

- **Recipe schema outside `RecipeIngredient`.** No changes to `Recipe`
  itself, `RecipeStep`, `RecipeSection`, `RecipeStepIngredient`,
  `RecipeStepTool`, `RecipeStepImage`. All Chunk-6-of-Cookbook structured
  steps + Chunk-10 sections stay intact.
- **ShoppingListLine.** Stays anchored to StockItem or Product. No
  freeform-text lines. "Add missing" surfaces a linking prompt for
  unlinked ingredients, not a schema loosening.
- **Existing cookability behaviour for all-linked recipes.** True /
  False continue to work identically. The `None` state only appears
  when a recipe carries an unlinked ingredient.
- **Companion app scope.** No new companion surface. The user's
  ownership of the fetch stays in *their* browser via the paste flow,
  not in a companion process.
- **Assistant capabilities.** Dora's answers about cookable recipes get
  a follow-up clause when unlinked recipes exist ("K recipes need
  linking"), but her capabilities registry doesn't grow.
- **`global_search.py` fuzzywuzzy usage.** Left as-is; logged as a
  residual FU so FU-396 can close cleanly on the importer half without
  half-open ambiguity.
