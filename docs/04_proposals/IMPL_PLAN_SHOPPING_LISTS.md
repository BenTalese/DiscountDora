# Implementation Plan — Shopping Lists (C-impl)

**Status:** Plan for review · **Date:** 2026-06-06 · **No code yet** — phased plan + first chunk.  
**Source proposal:** `SHOPPING_LIST_REDESIGN_PROPOSAL.md` (2026-06-04).  
**Phase:** Master plan **Phase 1 (the loop)** — after the state-ownership enabler,
alongside cook-mode.

---

## 0. Verify-state-first: no drift

Re-checked 2026-06-06. The code matches the proposal's diagnosis and has **not**
moved toward the solution:
- Four independent flags (`is_primary`, `is_archived`, `is_in_progress`,
  `completed_at`) in `shopping_list.py` + `table_mappings.py:175-184`; **no
  `status` enum.**
- Creation is **already one `/auto-generate` endpoint** (`sources` +
  `merge_into_list_id`) wrapped by **5 frontend buttons** — a UI-consolidation job,
  not a backend one.
- `is_primary` leaks into **~7 consumers** (quick-add `/primary/lines`, shop-now,
  finish auto-promote `manage_shopping_list.py:244-258`, create `make_primary`,
  update `is_primary`, unfinish restore, overview/detail UI).
- **Brittle client-snapshot undo** (`unfinish_shopping_list.py` takes
  `level_restores` from the client); finish bumps stock to Well-Stocked with **no
  server audit** (`manage_shopping_list.py:228-242`).
- **No `planned_shop_date`** field (confirmed absent).

---

## 1. Chunked plan (each chunk = one reviewable PR)

### Chunk 1 — Status model + server-owned finish/reopen  ★ FIRST REVIEWABLE CHUNK ✅ IMPLEMENTED (2026-06-07)
**Two approved deviations from the plan below:**
- **Old booleans dropped now, not in Chunk 7.** Pre-release = no compat shims, so
  `is_archived` / `is_in_progress` were removed in this chunk (no dual-read). `is_primary`
  and `completed_at` stay (primary removal is Chunk 2).
- **Snapshot-on-list, not a separate audit table.** Finish writes a `finish_snapshot`
  JSON-in-text column on the list (`{was_primary, promoted_primary_list_id,
  level_restores}`); reopen reverses from it and clears it. Lighter than an audit row,
  same server-owned-undo guarantee (R-003).

The crux (proposal §2.1, §3). Data model + the risky cross-domain path, together.
- Add a **`status` enum** column (`draft` / `shopping` / `done`) + migration:
  `is_archived→done`, `is_in_progress→shopping`, else `draft`. **Keep the old
  boolean columns** for now (dual-read, rollback safety; dropped in Chunk 7).
- Add a **`done → draft` reopen** transition.
- **Record stock-level deltas server-side at finish time** (an audit row), so
  reopen reverses them **without trusting the client** — replacing the brittle
  `level_restores` snapshot. Treat finish/restock as **one transaction with an
  audit row** (proposal §3: risk concentrates here; this also gives reliable undo
  for free and fixes the "Clear all has no undo, Finish has a fragile one"
  inconsistency).
- **Coordinate with `IMPL_PLAN_STATE_OWNERSHIP.md` Chunk 6** (offer-snapshot-at-add)
  — build the snapshot/audit story once.
- *Risk:* touches every shopping-list query (~47 refs) + the DTOs. Migrate reads to
  the new column behind the dual-write; the finish transaction is the highest-risk
  surface — land with tests on finish → reopen round-trips restoring exact levels.
- *Acceptance:* lists carry a single `status`; finish writes an audit; reopen
  reverses from the audit (client snapshot no longer required); existing rows
  migrated correctly.

### Chunk 2 — Contextual target inference (remove stored `is_primary` reads)
Proposal §2.4. Replace the stored primary with DRAFT-count inference:
- **Quick-add** (`/primary/lines`): 0 draft → create; 1 → use silently; 2+ → ask +
  **remember the session pick**. (This is the **same rule the C-7 cart button
  consumes** — build the resolver once, share it.)
- **Shop-now** PWA shortcut: 1 SHOPPING → resume; else 1 DRAFT → offer to start;
  else → overview.
- **Remove finish auto-promote**, `make_primary` (create), `is_primary` (update),
  and the unfinish primary-restore. **Keep the `is_primary` column** temporarily
  (rollback); drop in Chunk 7.
- *Risk:* the 7 consumers; do behind the inference resolver with tests for 0/1/2+
  draft cases.

### Chunk 3 — Lifecycle UI (one primary-action button)
Proposal §2.1-2.2. `DRAFT → [Start shopping] → SHOPPING → [Finish & restock] →
DONE`, with "← back to editing" (reopen to draft). **Fold review into the finish
confirmation** ("these 12 items will be marked Well-Stocked → Confirm"). **SHOPPING
renders the shop-mode surface in place** (not a separate page). Retires Start/Stop/
Shop-mode/Review-mode soup.

### Chunk 4 — One creation surface
Proposal §2.3. Collapse the **5 buttons** into one "New list" form mapped onto the
existing `/auto-generate` (`sources` + a "create new / add to ▾" switch =
`merge_into_list_id`). Pure frontend consolidation; backend already supports it.

### Chunk 5 — Merge overview into detail
Proposal §2.3 + feedback L403-409. Remove the standalone overview; the **detail is
the surface**, with a list selector (desktop: right panel ordered by planned/
finalised shop date then creation; mobile: top dropdown), **archived lists in the
same list**, and the **list picked on navigation keyed to today's date**.

### Chunk 6 — In-store polish
Proposal §2.5 + feedback. **Persistent skip** (real saved reorder, not client-only);
**tap-to-type quantity**; **whole-list peek**; **group-by-aisle as a view that
never overwrites `sequence`**; **pricing-as-you-go** (the list *becomes the
receipt*, L419 — edit `actual_unit_price` inline during shopping). Fix the
**drag-and-drop off-by-one** (L414). Substitute-swap-in-store ties to C-7 §9.1 +
INV-8.

### Chunk 7 — Planned shop day + cleanup
- Add **`planned_shop_date`** (optional) + a **shopping-day alert** (feeds C-9's new
  alert types). (L401-402)
- Once `status` is proven, **drop `is_in_progress` / `is_archived` / `is_primary`**
  columns (the deferred-from-Chunk-1/2 cleanup migration).

---

## 2. First reviewable chunk — definition of done

**Chunk 1 (status model + server-owned finish/reopen).**
- `status` column + migration with the conversion table above; old booleans
  retained (dual-read).
- Finish writes a **stock-delta audit row**; **reopen** (`done→draft`) reverses
  from it.
- Tests: migration converts existing rows correctly; finish→reopen restores exact
  prior stock levels with **no client-supplied snapshot**; a list is always in
  exactly one status.
- DTOs expose `status`; queries that meant "active" now read `status != done`.

---

## 3. Risks & open decisions

**Risks** (proposal §3):
- **Migration is the crux** — it touches every shopping-list query + the summary/
  detail DTOs + overview/membership sorting. Dual-write + keep old columns until
  proven.
- **`is_primary` removal ripples** to 7 consumers — the inference resolver is the
  single replacement; test 0/1/2+ draft cases.
- **Risk concentrates in finish/restock** (the one place a state change ripples
  into stock levels) — own transaction + audit row; that *is* the reliable-undo
  mechanism.
- Net **less** surface area (5 auto-gen wrappers, Start/Stop, Review-mode all go).

**Open decisions** (proposal §5):
1. DONE lists permanently deletable, or archived-then-purged on a schedule?
2. "Remember the pick" — reset per session, or persist until the chosen draft goes
   DONE? (Shared with the C-7 cart button's session-default decision.)
3. Two lists in SHOPPING at once (two shoppers / two stores)? The model assumes one
   resume target — confirm.

**Cross-refs:** C-7 (quick-add inference = the cart button's Axis B resolver),
state-ownership Chunk 6 (offer snapshot at add), C-9 (shopping-day alert).

---

## 4. Feedback coverage

Maps SHOPPING LISTS / DETAILS / MODE (L401-422).

| Bullet (line) | Summary | Where |
|---|---|---|
| L401 | Planned shopping day per list (optional) | Chunk 7 |
| L402 | Shopping-day alert | Chunk 7 (→ C-9) |
| L403 | Combine overview into detail | Chunk 5 |
| L405 | Desktop right panel, ordered by shop/creation date | Chunk 5 |
| L406 | Mobile: list dropdown at top | Chunk 5 |
| L407 | Primary detail → top info area of current list | Chunk 5 |
| L408 | Archived lists in the same list | Chunk 5 |
| L409 | Picked list keyed to today's date | Chunk 5 |
| L410 | "Primary list" feels not quite right | Chunk 2 (inference replaces stored primary) |
| L414 | Drag-and-drop off-by-one | Chunk 6 |
| L418 | See substitutes in-store when unavailable | Chunk 6 (→ C-7 §9.1 / INV-8) |
| L419 | Pricing-as-you-go; list becomes the receipt | Chunk 6 |
| L420 | Close the loop: finish → restock-all + per-item level tweak (P2-01/02) | Chunk 1 (finish) + Chunk 3 (review-in-confirm) |
| L421 | Undo of done list is bad; only certain situations; no bad data | Chunk 1 (server audit + reopen replaces brittle client undo) |
