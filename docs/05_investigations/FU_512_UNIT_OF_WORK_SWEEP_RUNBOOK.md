# FU-512 — Unit-of-work refactor sweep runbook

**Status:** analysis-only (2026-07-08). No code changes yet. This document is the
runbook for the next session to execute FU-512 mechanically. Written on the back
of the FU-456 pattern-setter (create_recipe.py, shipped 2026-07-08).

## Prerequisite reading

The executor should skim these before starting any batch:

- [dora_api/features/recipes/create_recipe.py](../../dora_api/features/recipes/create_recipe.py) — the FU-456 reference implementation.
- [tests/e2e/dora_api/test_create_recipe_unit_of_work.py](../../tests/e2e/dora_api/test_create_recipe_unit_of_work.py) — the test contract shape.
- [dora_api/persistence/sqlalchemy_repository.py](../../dora_api/persistence/sqlalchemy_repository.py) L30-70 — `add()` assigns `entity.id = uuid4()` client-side, so **no flush is required to obtain an id**. `flush()` is only needed when a *downstream* Core-level `db.session.execute(insert/update(...))` needs the row's FK visible on the wire.
- [dora_api/infrastructure/audit.py:239](../../dora_api/infrastructure/audit.py) — audit middleware skips 4xx responses, so a dirty session on a 400-return can never be committed by the middleware. Combined with Flask-SQLAlchemy teardown (`session.remove()`), error branches roll back automatically — no explicit rollback needed anywhere below.

**Key mental model:** any place we commit "just to get an id" is dead weight now
that `SqlAlchemyRepository.add()` assigns UUIDs client-side. Grep the rest of
the codebase (`grep -n "save_changes" ... near a fresh add()`) for other
instances after FU-512 lands.

---

## Revised inventory

The task's original "19 handlers" over-counted. After reading each file at the
class scope (not raw line refs, which sometimes pointed at sibling route
handlers), the corrected split is:

- **10 handlers genuinely multi-commit** — need refactor (list below).
- **9 handlers already fine** — either mutually-exclusive branches (one commit
  per request) or the raw line ref pointed at a different route handler.

---

## No-refactor-needed list (already correct)

These 9 handlers commit exactly once per request; the two `save_changes()`
calls sit in different methods behind different routes, or in mutually-
exclusive branches within one method.

| Handler | Why fine |
| --- | --- |
| `AlertInteractionHandler` (`interact_with_alert.py` L75/81/86/93/105) | Five methods (`set_read`, `snooze`, `dismiss`, `clear_suppression`, `mark_all_read`) each behind their own route. One runs per request. Task's "5-commit boss" framing was wrong. |
| `PushSubscriptionHandler` (`push_subscriptions.py` L105/118) | `upsert()` vs `remove()` — different routes. |
| `PreferredBuyHandler` (`preferred_buys.py` L72/85/93) | Three methods (`add`/`rename`/`delete`), separate routes. |
| `PriceObservationHandler` (`price_observations.py` L89/103) | `add()` vs `delete()`, separate routes. |
| `MoveStockItemHandler` (`move_stock_item.py` L47/57) | L47 is the early-return branch; L57 is the else. Only one runs (verified by `return` at L48). |
| `CreateProductHandler` (`create_product.py` L109/139) | Existing-product branch vs new-product branch, each `return`s immediately after committing. |
| `GetOnboardingStateHandler` route bodies (`onboarding.py` L143/158) | The line refs point at `complete_onboarding` (L143) and `restart_onboarding` (L158) — two separate route bodies, not the state-getter handler. Each is one-mutation-one-save. |
| `GetSuggestionsHandler` (`suggestions.py` L110 only) | The task listed L110/174/215/242, but L174/215/242 are the `dismiss`/`snooze`/`remove_suppression` route handlers each with a single save. Only L110 is inside `GetSuggestionsHandler`, and it's already single-save. |
| `LogWasteEventHandler` (`waste.py` L237 only) | Same misread. L301 is the `delete_waste_event` route body — separate endpoint. Only L237 is inside `LogWasteEventHandler`, single-save. |

**Optional cleanup:** add a one-line docstring to each of these ("single commit
per request; multi-branch") to defuse the next drive-by grep. Skip if the
executor wants the diff tight.

---

## Handlers requiring refactor (10)

### 1. `CreateMealPlanTemplateHandler` — `meal_plan_templates/manage_templates.py` (L208, L220)

**Shape:** Snapshot a week of `MealPlanEntry` rows into a new `MealPlanTemplate` + N `MealPlanTemplateEntry` children.

**Save-point map:**
- L208 — habit commit after `add(template)`. Child rows only need `template.id`, which `add()` has already assigned client-side.
- L220 — real end-of-unit commit after adding children.

**Failure surfaces:** None reachable between commits today (both `source_not_found` and `no_entries` return **before** L208). Shape-uniformity refactor.

**Refactor plan:**
- Delete L208.
- Keep L220 as the sole final commit. No `flush()` needed.
- No response-field changes.

**Complexity:** trivial.

**Test:** `tests/e2e/dora_api/test_create_meal_plan_template_unit_of_work.py`. Happy path only. **State in the docstring:** "no reachable failure between commits; shape-uniformity change."

---

### 2. `CloneMealPlanTemplateHandler` — `meal_plan_templates/manage_templates.py` (L341, L351)

**Shape:** Deep-copy an existing template + its entries under a new name.

**Save-point map:**
- L341 — habit commit after `add(clone)`.
- L351 — guarded by `if entries:`; skipped when template has no entries.

**Failure surfaces:** None reachable (loop over already-loaded rows).

**Refactor plan:**
- Delete L341.
- Save unconditionally at end (drop the `if entries:` guard — an empty session commit is a no-op).
- No flush, no field changes.

**Complexity:** trivial.

**Test:** Happy path only.

---

### 3. `CreateSetHandler` — `meal_plan_template_sets/manage_sets.py` (L190, L196)

**Shape:** Create a `MealPlanTemplateSet` + N ordered `MealPlanTemplateSetItem` children.

**Save-point map:**
- L190 — habit commit after `add(s)`.
- L196 — guarded by `if request.template_ids:`.

**Failure surfaces:** `missing_template_ids` check runs *before* L190.

**Refactor plan:**
- Delete L190.
- Save unconditionally at end (drop the `if` guard for the same reason).
- No flush.

**Complexity:** trivial.

**Test:** Happy path only. Missing-template-ids branch already returns pre-commit, so no rollback test can distinguish pre/post-refactor.

---

### 4. `SeedHandler` — `onboarding/onboarding.py` (L222, L282, L303)

**Shape:** Optionally seed default `StockGroup` rows AND optionally seed a nested `StockLocation` tree (zone → children).

**Save-point map:**
- L222 — end of the groups block. Genuine checkpoint between the two subsystems.
- L282 — **inside the locations loop, after each zone insert**. The tricky one: child rows on the next iterations set `parent_id = zone_entity.id`. The id is client-assigned, but a Core-level insert of a child before its parent hits the wire could trip FK on Postgres / SQLite `PRAGMA foreign_keys=ON`.
- L303 — intended final commit.

**Failure surfaces:** Very few. Loop over parsed JSON.

**Refactor plan (recommended: collapse to one final commit):**
- Replace L222 with `self.repository.flush()`.
- Replace L282 with `self.repository.flush()` **and** add an inline comment naming the local contract in `sqlalchemy_repository.py:57-67` (classic mapper doesn't know parent/child depend on each other without a `relationship()`, so we flush to make the parent visible before the child insert).
- Keep L303 as the sole final commit.
- No response-field changes (counts are Python-side).

**Complexity:** moderate — this is the only handler in the sweep with a genuine "child depends on parent's DB-visible row" case. Use it as the reference for future flush-point comments citing the local contract.

**Test:** `tests/e2e/dora_api/test_seed_onboarding_unit_of_work.py`. Happy path — the seed loops don't naturally raise. Note in docstring that a rollback test would need a test-only override of `_load_seed` to return a poisoned entry; defer.

**Watch-outs:**
- `existing_pairs` set is mutated as the loop progresses; a rollback would leave Python state ahead of DB state on retry. Not a problem in practice (handler runs once per request).
- `_find_existing` on L271 does an `.all()` scan — expensive, pre-existing, leave alone.

---

### 5. `NewRecipeVersionHandler` — `recipes/new_recipe_version.py` (L129, L186)

**Shape:** Clone a recipe (ingredients, name, vocab, image), then bolt on cloned tags/tools/steps/images via the access helpers.

**Save-point map:**
- L129 — after adding cloned ingredients + `new_recipe`. Habit-commit.
- L186 — after all access-helper writes (tags, tools, steps, step-images).

**Failure surfaces:** Between L129 and L186, `replace_steps_for_recipe` can raise `ValueError` on a bad parent chain (mirrors CreateRecipe's step-replace). Because we're cloning from a valid source, empirically unreachable — but the *shape* is FU-456's shape.

**Refactor plan:**
- Replace L129 with `self.repository.flush()` — access helpers use `db.session.execute(insert(...))` at Core level, so the new-recipe FK must be visible.
- Keep L186 as the sole commit.
- No response-field changes (source_not_found returns before any add).

**Complexity:** trivial (structurally identical to CreateRecipe post-refactor).

**Test:** `tests/e2e/dora_api/test_new_recipe_version_unit_of_work.py`. Happy path only; document no failure surface reachable from valid input.

**Watch-outs:** `_sibling_count` at L191 uses `db.session.execute(select(...))` after `add()` but before commit. Reads pending inserts — no change needed.

---

### 6. `AutoGenerateHandler` — `shopping_lists/auto_generate.py` (L259, L282)

**Shape:** Multi-source dedupe → build shopping-list lines. Either merges into an existing list OR creates a new one.

**Save-point map:**
- L282 — inside `_create_list()`. Commits the new `ShoppingList` before returning. "Get the id" habit-commit — `target.id` is client-assigned, so not required.
- L259 — real end-of-unit commit after adding all `ShoppingListLine` rows.

**Failure surfaces:** Between `_create_list()` and L259, only a Python loop over the deduped map. No 4xx path fires between commits today.

**Refactor plan:**
- Delete L282. `target.id` is client-assigned; the FU-351 empty-list-guard on L215-219 already prevents the phantom-empty-list bug.
- L259 remains the sole commit.

**Complexity:** moderate — spans two files' worth of context, has FU-351 empty-list logic to preserve.

**Test:** `tests/e2e/dora_api/test_auto_generate_unit_of_work.py`. Happy path asserting list + lines persist together.

**Watch-outs (CRITICAL — verify before shipping):**
- Line 227's `.get(ShoppingListLine).all(...).eq(target.id)` runs AFTER `_create_list()`. Post-refactor, `target` is still pending. **Verify that the ORM builder surfaces newly-`add`-ed rows in the same session query.** If not, add `self.repository.flush()` in `_create_list()` in lieu of the deleted `save_changes()`. If `.all()` doesn't see pending inserts, `next_sequence` at L231 becomes wrong on the merge-into-empty-new-list path. Confirm with a REPL round-trip or by running the test suite.

---

### 7. `CopyShoppingListHandler` — `shopping_lists/manage_shopping_list.py` (L423, L434)

**Shape:** Copy a shopping list (all lines or unticked only) into a new list.

**Save-point map:**
- L423 — habit-commit for `target.id`.
- L434 — after adding all copied `ShoppingListLine` rows.

**Failure surfaces:** None reachable (loop over already-loaded source lines).

**Refactor plan:**
- Delete L423.
- L434 remains the sole commit.

**Complexity:** trivial.

**Test:** Happy path only.

---

### 8. `CreateTemplateHandler` (shopping list templates) — `shopping_list_templates/manage_templates.py` (L191, L203)

**Shape:** Create `ShoppingListTemplate` + optional `ShoppingListTemplateLine` children. Structurally identical to `CreateMealPlanTemplateHandler`.

**Refactor plan:**
- Delete L191.
- Drop `if request.lines:` guard on L202; save unconditionally.

**Complexity:** trivial.

**Test:** Happy path only.

---

### 9. `InstantiateTemplateHandler` — `shopping_list_templates/manage_templates.py` (L483, L510)

**Shape:** Create a new `ShoppingList` from a template's lines, skipping lines whose `stock_item_id` no longer exists.

**Save-point map:**
- L483 — habit-commit for `new_list.id`.
- L510 — guarded final commit (`if added:`).

**Refactor plan:**
- Delete L483.
- Drop `if added:` guard on L509; save unconditionally.

**Complexity:** trivial.

**Test:** Happy path only.

---

### 10. `SnapshotFromListHandler` — `shopping_list_templates/manage_templates.py` (L568, L587)

**Shape:** Snapshot a `ShoppingList`'s lines into a new `ShoppingListTemplate`.

**Save-point map:**
- L568 — habit-commit for `template.id`.
- L587 — guarded final commit.

**Refactor plan:**
- Delete L568.
- Save unconditionally at end (drop `if added:`).

**Complexity:** trivial.

**Test:** Happy path only.

---

## Batching recommendation

**Batch 1 — trivial pattern-mirrors, ship together (7 handlers):**
`CreateMealPlanTemplateHandler`, `CloneMealPlanTemplateHandler`, `CreateSetHandler`,
`CopyShoppingListHandler`, `CreateTemplateHandler`, `InstantiateTemplateHandler`,
`SnapshotFromListHandler`. All the same pattern: delete the habit-commit after the
parent `add()`, drop any `if children:` guard on the final commit. One test file
per handler, all happy-path. Ship in one PR.

**Batch 2 — trivial with a real (but empirically unreachable) failure surface (1):**
`NewRecipeVersionHandler`. Convert L129 to `flush()` (access helpers use Core-level
inserts). Ship alone or with Batch 3.

**Batch 3 — moderate, needs careful reading (2 handlers):**
`AutoGenerateHandler` (verify `.all()` sees pending inserts on the merge-into-just-
created-list path) and `SeedHandler` (use `flush()` in the locations loop; collapse
to single final commit across groups+locations). Ship together in a second PR.

**Batch 4 (optional):** docstring-note the 9 no-refactor handlers to defuse the next
drive-by grep. Skip if keeping the diff tight.

---

## Deliverable checklist for the executor

For each of the 10 refactored handlers:

- [ ] Interior `save_changes()` deletions / flush conversions per plan above.
- [ ] Sole final `save_changes()` at success-path end.
- [ ] Response fields carrying partial-commit ids remain populated only on the
      success path (all already comply — none of the 10 sets an id in an
      error branch).
- [ ] New `tests/e2e/dora_api/test_<name>_unit_of_work.py` — happy-path
      minimum; rollback test only where a genuine failure surface exists
      (none in this sweep except `NewRecipeVersionHandler`'s theoretical
      step-shape path, which can't be triggered from a valid source).
- [ ] R-003 / R-023 style inline comment in `SeedHandler` naming the flush
      contract.
- [ ] `AutoGenerateHandler`: **verify** the `.all()` pending-insert visibility
      claim in Watch-outs before merging.

Ledgers:

- [ ] `DORA_FOLLOWUPS.md` entry logged for the "GET /api/suggestions writes"
      surprise finding — see below.
- [ ] Worklog entry noting the corrected inventory (10 refactored, 9 no-refactor).
- [ ] `CHANGELOG.md` `[Unreleased]` bullet under "Internal" for FU-512 completion.
- [ ] Move FU-512 from `DORA_FOLLOWUPS.md` to `DORA_FOLLOWUPS_RESOLVED.md`.

---

## Surprise findings (log independently of FU-512)

1. **`GetSuggestionsHandler` writes inside a GET** (suggestions.py L109 remove +
   L110 commit). Every `/api/suggestions` call takes a write lock and can fail
   under DB contention. Not FU-512's job to fix — logged as a separate FU.
2. The task's raw line-count numbers included lines that belong to sibling route
   handlers, not the named class. **Trust the class scope, not the raw line
   refs** — this is a general lesson for future sweeps.
3. **Commit-just-to-materialise-an-id** is a pattern to grep for after FU-512
   lands. `SqlAlchemyRepository.add()` assigns UUIDs client-side, so any
   `save_changes()` immediately after a fresh `add()` is dead weight (or a
   `flush()` at most, if a downstream Core-level insert needs the FK visible).
4. **No handler in this sweep calls an external service between commits.** The
   FU-456 "one transaction" pattern applies uniformly. No handler requires
   partial-persist-on-purpose (onboarding progress persists via the
   `onboarding_completed_at` timestamp, which is its own request).
