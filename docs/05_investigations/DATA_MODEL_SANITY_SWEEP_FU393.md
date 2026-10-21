# DATA_MODEL_SANITY_SWEEP — FU-393 (P5-08)

**Date:** 2026-07-14
**Type:** Read-only investigation. No schema changes in this pass — findings +
recommendations; remediation spawned as [[FU-563]] (indexes / drift / test) and
[[FU-564]] (nullability drift).
**Purpose:** The comprehensive data-model *schema* sanity sweep P5-08 asked for —
nullability, FK-consistency, index coverage, dead columns — as a single dedicated
pass. Complements the earlier field-*usage* audit ([ORPHANED_FIELDS_AUDIT.md](ORPHANED_FIELDS_AUDIT.md),
INV-1) + its delta-check (FU-416); this one looks at the DB structure itself, not
whether a field reaches the UI.

---

## Method

Ground truth was taken from the schema itself, not by reading the 1 559-line
`table_mappings.py` by eye:

1. Built the **model schema** with `db.create_all()` (what `table_mappings.py`
   declares — the path dev + the whole e2e suite run on; see
   `startup.init_db` test/dev branch).
2. Built the **migrated schema** with `flask_migrate.upgrade()` from empty (what
   a production install runs).
3. Reflected both throwaway SQLite DBs with SQLAlchemy's `inspect()` and diffed
   columns, nullability, indexes, unique constraints, and foreign keys
   (col → target, `ondelete`).

Repro scripts (temporary, removed after the pass) lived at the repo root
(`scratch_introspect.py` / `scratch_full.py`); the analysis is reproducible by
re-reflecting the two schemas. 59 tables total.

---

## Executive summary

| # | Finding | Severity | Verdict |
|---|---|---|---|
| 1 | **Model ≠ migrations (schema drift).** `create_all()` builds **1** secondary index; `upgrade()` builds **32**. Dev + the entire e2e suite run on an almost-unindexed schema that doesn't match production. | **High** (maintainability + test-fidelity) | Remediate → [[FU-563]] |
| 2 | **FK index coverage.** **42** foreign-key columns have no covering index in the *production* schema; **35** of them carry `ON DELETE CASCADE`/`SET NULL`, so every parent delete scans the child table. | **High** (perf at scale) | Remediate → [[FU-563]] |
| 3 | **Nullability drift.** 4 columns differ model-vs-prod. 1 is a *known, documented* deferral (`User.username`); 3 (`Product.is_active`, `Product.is_available`, `Product.merchant_stockcode`) look unintentional. | **Medium** | Remediate → [[FU-564]] |
| 4 | **FK `ondelete` rules.** Every FK **in the ORM model** declares an explicit `ondelete` (0 missing). Good — no orphan-by-omission risk in the declared model. | ✅ clean | — |
| 5 | **Dead columns.** No new true orphans at the schema level beyond what INV-1 + FU-416 already tracked. | ✅ clean | — |
| 6 | **The guard that should have caught this.** `test__migrations__migrated_schema_matches_orm_metadata` only compares **table names** — not columns, nullability, or indexes — so all of the above passed CI silently. | **High** (blind spot) | Fix in [[FU-563]] |

---

## Finding 1 — Schema drift: `create_all()` (dev/test) ≠ `upgrade()` (prod)

`table_mappings.py` declares almost no secondary indexes — only PKs + 6 unique
constraints (`Barcode.barcode`, `StockItemProduct.product_id`,
`IdempotencyKey.endpoint`, `User.username`, `IngestionSource.key_hash`,
`AuthToken.token_hash`) and a single `index=True`
(`Recipe.version_group_id`). Every other index Dora relies on is created **only
in the Alembic migrations** and never mirrored back into the ORM model.

Measured (reflected from freshly built schemas):

- **Model (`create_all`): 1** non-PK index.
- **Migrated (`upgrade head`): 32** indexes.
- **31 index colsets exist in prod but are absent from the model**, e.g.
  `AuditEvent(entity_type, entity_id, occurred_at)`,
  `AuthToken(user_id, purpose)`, `MealPlanEntry(scheduled_for, consumed_at)`,
  `PriceAlert(user_id, product_id)`, `RecipeStep(recipe_id)`,
  `StockItem(last_checked_at)`, `StockItem(snoozed_until)`,
  `DoraSuggestionSuppression(kind, dedup_key)`, `IdempotencyKey(source_id, key)`,
  and 22 more.

### Why this matters

- **Dev + the e2e suite run unindexed.** `startup.init_db` builds the test/dev
  schema via `create_all()` (never migrations), so 500-item dev seeds (FU-388)
  and 1 006 e2e tests all execute against a schema missing 31 of 32 indexes.
  Behaviour that depends on an index (or breaks a `UNIQUE`) can't be exercised
  where the model doesn't declare it.
- **The ORM model is not the source of truth for the schema** — a direct
  tension with **R-003** (single source of truth) and the spirit of **R-006**
  (clean migrations shouldn't *hide* drift; here the drift is between the two
  build paths). A new table added to `table_mappings.py` ships to dev without
  the indexes a later migration adds; nothing forces them back into sync.
- **Cross-check with FU-388:** that perf sweep profiled the *dev-seed* schema
  (1 index) and found query **counts** flat at 500 vs 2 000 items — correct for
  N+1 detection, but it could not see missing-index *latency*, and it wasn't
  measuring the prod schema. Its "clean" verdict stands for N+1s; it says
  nothing about the FK-index gap in Finding 2.

### Recommendation → [[FU-563]]

Make the ORM model the source of truth for indexes: mirror the 31
migration-only index colsets into `table_mappings.py` (so `create_all()` ==
`upgrade()`), then **strengthen `test__migrations__migrated_schema_matches_orm_metadata`
to compare columns, nullability, and index colsets** — not just table names — so
this can't silently re-open. (That strengthened test will fail until the drift
is closed, which is the point: it's the regression gate.)

---

## Finding 2 — FK columns without a covering index (production schema)

Neither SQLite nor PostgreSQL auto-indexes foreign-key columns. In the
**migrated (production) schema**, **42 FK columns have no covering index**;
**35** of those have `ON DELETE CASCADE` or `SET NULL`, meaning every delete of
a parent row triggers a **full scan of the child table** to find/rewrite
matching rows — plus the same columns are the join keys for normal reads.

High-traffic examples (full list of 42 in the repro output):

| Child.column | → parent | ondelete | Note |
|---|---|---|---|
| `RecipeIngredient.recipe_id` | Recipe | CASCADE | scanned on every recipe delete; joined on every recipe read |
| `RecipeIngredient.stock_item_id` | StockItem | RESTRICT | joined for cookability / "recipes using this item" |
| `ShoppingListLine.shopping_list_id` | ShoppingList | CASCADE | scanned on list delete; the list's own line lookup |
| `ShoppingListLine.stock_item_id` / `product_id` / `selected_product_id` | StockItem/Product | CASCADE/SET NULL | membership + offer joins |
| `StockLevelChange.stock_item_id` | StockItem | CASCADE | append-only history; grows fastest |
| `StockItemPriceObservation.stock_item_id` | StockItem | CASCADE | price-history/oracle joins |
| `MealPlanEntry.meal_plan_id` / `recipe_id` | MealPlan/Recipe | CASCADE | planner reads + deletes |
| `PreferredBuy.stock_item_id` | StockItem | CASCADE | shopping-list offer sort |
| `Barcode.stock_item_id` | StockItem | CASCADE | scan-lookup path |

At the current single-household self-host scale this is largely invisible; it's
a **scale + delete-latency** issue that gets worse with pantry/history growth
(exactly the 2 000-item regime FU-388 was probing). Adding a plain index on each
FK column is low-risk and additive.

### Recommendation → [[FU-563]]

Add an index on each of the 42 FK columns (folded into the same
model↔migration reconciliation as Finding 1 — declare `index=True` on the FK
`Column`s in `table_mappings.py` and generate one migration). Composite indexes
where a query filters on `(fk, other)` can subsume the single-column one.

---

## Finding 3 — Nullability drift (model vs production)

Four columns disagree between the model and the migrated schema:

| Column | Model | Prod (migrated) | Assessment |
|---|---|---|---|
| `User.username` | NOT NULL | **nullable** | **Known / documented deferral.** The `4b1d9c2e7a31_add_user_auth` migration explicitly notes it left `username` nullable because an in-place rewrite was risky (pre-existing null/dupe rows) and the app guarantees non-null uniqueness on insert. Low priority; keep — but document the carve-out in the model. |
| `Product.merchant_stockcode` | nullable=True | **NOT NULL** | **Unintentional.** Model was loosened (the merchant→store era) but the column stayed NOT NULL in prod. A `create_all` dev DB accepts NULL; prod rejects it → a dev-passes/prod-fails insert is possible. |
| `Product.is_active` | NOT NULL | **nullable** | **Unintentional.** Model tightened; migrations never enforced. Prod can hold NULLs the ORM assumes never occur. |
| `Product.is_available` | NOT NULL | **nullable** | Same as `is_active`. |

### Recommendation → [[FU-564]]

Reconcile each: for the three `Product` columns, decide the intended nullability
and either write an `ALTER ... SET/DROP NOT NULL` migration (backfilling
defaults first where tightening) or relax the model to match reality; add a
one-line comment on `User.username` in `table_mappings.py` pointing at the
documented `add_user_auth` deferral so the drift reads as intentional.

---

## Finding 4 — FK `ondelete` rules (clean)

Every foreign key **declared in the ORM model** carries an explicit `ondelete`
(0 with no rule) — CASCADE for owned children, SET NULL for optional
references, RESTRICT where a delete should be blocked. No orphan-by-omission
risk in the declared model. *(Caveat: SQLite reflection of the migrated DB
reported `ondelete=None` for a handful of FKs — `Product.store_id`,
`ProductOffer.product_id`, `StockItem.stock_group_id/stock_level_id/stock_location_id`.
This is most likely a reflection artifact / a migration that created the FK
without the clause while the model has it; worth a spot-confirm during the
[[FU-563]] reconciliation, since it's the same "model ≠ migration" theme.)*

---

## Finding 5 — Dead columns (clean)

No new true dead columns at the schema level. The field-usage sweep
(INV-1 `ORPHANED_FIELDS_AUDIT.md`) + its delta (FU-416) already accounted for
the population; its two "unfinished feature" flags have since resolved
(`StockItem.image` was **dropped** via FU-508; `StockItemSubstitute.notes`
tracked separately). Append-only audit tables (`StockLevelChange`,
`AuditEvent`, `*Event`, ledgers) intentionally have write-once columns with no
edit UI — not dead, by design.

---

## Recommendations — spawned as follow-ups (this investigation stays read-only)

- **[[FU-563]]** — *Schema-drift + FK-index remediation.* Mirror the 31
  migration-only indexes into `table_mappings.py`; add indexes on the 42
  unindexed FK columns; confirm the reflected `ondelete=None` FKs; **strengthen
  the migration schema-match test** to compare columns + nullability + index
  colsets so the drift can't silently re-open. One clean migration (R-006).
- **[[FU-564]]** — *Nullability reconciliation.* Fix the 3 `Product`
  nullability drifts (migration or model relax, per column intent) and document
  the `User.username` deferral in the model.

Both are pre-Phase-4-gate hygiene, low-risk, and land as clean forward-only
migrations. Neither blocks current work.

**Open decisions — none.** This is a read-only audit; every recommendation is
either closed inline (Findings 4, 5) or spawned as the FU above.

---

## Coverage

FU-393 is cross-cutting (a P5-08 whole-schema sweep), not a per-surface feedback
brief, so there is no per-`F` feedback table. It maps to the P5-08 line item
("comprehensive data-model sanity sweep — nullability, FK-consistency, index
coverage, dead columns"): all four axes covered above — nullability (F3),
FK-consistency (F2, F4), index coverage (F1, F2), dead columns (F5).
