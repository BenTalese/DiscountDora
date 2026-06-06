# Shopping List Redesign Proposal

**Status:** Draft for discussion
**Date:** 2026-06-04
**Scope:** Conceptual redesign of the shopping-list lifecycle, list creation, the in-store experience, and the "primary list" concept. Touches the data model and API, not just the UI.

---

## 1. Why

The shopping-list feature works, but it *feels* like friction — and that feeling has concrete causes. The functionality accreted over many iterations (the code even contains comments like *"map the legacy two-source quick-pick to the new multi-source endpoint"*), and old surfaces were never removed when better ones arrived. The result is feature accumulation without consolidation.

Three root problems:

### 1.1 Too many overlapping "modes"

To go shopping, a user navigates **five** concepts that sound related but mean different things:

| Concept | What it actually is | Where |
|---|---|---|
| **Primary list** | The "default" list quick-add and the PWA shortcut point at | `is_primary` flag |
| **Start / Stop shopping** | Sets `is_in_progress`; *locks editing* on the detail page | `ShoppingListDetail.vue` |
| **Shop mode** | A separate full-screen page, one item at a time | `ShoppingListShopMode.vue` |
| **Review mode** | Previews which items will get restocked | `ShoppingListDetail.vue` |
| **Finish shopping** | The real checkout — archives + bumps stock levels | `manage_shopping_list.py` |

"Start shopping" *sounds* like it should take you shopping — but it just locks the list. The thing that actually takes you shopping is a different button ("Shop mode"). "Stop shopping" finishes nothing; it just unlocks. There are three verbs (Start / Stop / Finish) and two nouns (Shop mode / Review mode) for what is really one linear journey.

The data model is the source: four independent booleans (`is_primary`, `is_in_progress`, `is_archived`, plus client-side `reviewMode`), each surfaced as its own control. Independent flags can also combine into nonsense (in-progress *and* archived?), so every query that wants "active lists" has to express it as a mushy combination of negations.

> The model's own comment already describes an informal state machine — `planning -> in_progress -> archived` — it just isn't formalized. (`shopping_list.py:84-91`)

### 1.2 Five doors to the same room

List creation / auto-generation has fragmented into near-duplicate entry points:

- "From flagged items"
- "From all low/out stock"
- "Advanced auto-generate…" (the superset of the two above)
- "Top up the primary list"
- "Append low + essentials" (same thing, on the detail page)

The **backend is already clean**: one `/auto-generate` endpoint with a `sources` object and an optional `merge_into_list_id` (`auto_generate.py:104,156`). The frontend just wraps that single endpoint in five differently-labeled buttons. This is a UI consolidation problem, not an architecture one.

### 1.3 "Primary list" is load-bearing but unexplained

Quick-add, the "Shop now" PWA shortcut, and finish-promotion all depend on a designated primary list, yet the only hint a user gets is a warning banner with no button to fix it. It's jargon for "the list things default to," and it forces the user to maintain a setting the system could infer.

---

## 2. The redesign

### 2.1 One status, not four flags

Replace `is_in_progress` + `is_archived` (+ implicit "active") with a single `status` enum. A list is in exactly one phase at a time:

```
DRAFT  →  SHOPPING  →  DONE
  ↑__________↓ (reopen)        DONE → DRAFT (reopen)
```

- **DRAFT** — building/editing. Add, remove, reorder, auto-fill, set quantities. The only phase where structural editing is unlocked.
- **SHOPPING** — in the store. Structural edits locked; you tick items off. **This phase _is_ Shop Mode** — not a separate page you navigate to.
- **DONE** — checked out. Stock levels bumped, list filed away. Reopen-able.

`is_primary` is intentionally **not** folded into this enum — *which* list is active is a separate question from *what phase* a list is in. (And §2.4 removes it as a stored flag entirely.)

### 2.2 One primary action button

A single button that always reads as the next step:

```
DRAFT:     [ Start shopping ]        (→ SHOPPING)
SHOPPING:  [ Finish & restock ]      (→ DONE)   + secondary: "← back to editing" (→ DRAFT)
DONE:      [ Reopen ]                (→ DRAFT)
```

This dissolves the mode soup:

- **Start / Stop / Finish / Shop mode / Review mode → gone.** "Start shopping" and "Shop mode" were always the same intent (begin the in-store flow) — now they're the same thing.
- **"Stop shopping"** becomes "← back to editing" (reopen to DRAFT), framed as going back a step rather than a separate verb.
- **"Review mode"** was only ever a *preview of what DONE will do*. Fold it into the Finish confirmation: tapping "Finish & restock" shows *"These 12 items will be marked well-stocked → [Confirm]"*. The review appears exactly when relevant, never as a mode to discover.

### 2.3 One creation surface

Collapse the five creation/auto-fill buttons into a single "New list" surface whose controls mirror the one `/auto-generate` endpoint that already underlies them:

```
New shopping list
  Start from:  ◉ Empty   ○ Template ▾   ○ Recipe / meal plan ▾
  Auto-fill:   ☑ Low / out of stock
               ☐ Flagged essentials
               ☐ Stuff I buy often
  [ Create ]
```

"Top up an existing list" is the **same surface** with a "create new / add to ▾" switch at the bottom — which the API already supports via `merge_into_list_id`. Five buttons → one composable form mapped onto the one endpoint.

### 2.4 No stored "primary" — infer the target per entry point

Drop `is_primary` as a maintained setting. Resolve the target contextually, and only ask when there's genuine ambiguity. The cost of a decision appears only in proportion to the actual ambiguity.

**Quick-add** (counts DRAFT lists — the only valid add targets):

| Draft lists | Behavior |
|---|---|
| 0 | Create one, drop the item in it |
| 1 | Use it, silently — no prompt (the common case) |
| 2+ | Ask which; **remember the pick** as a soft default for the rest of the session |

The "remember the pick" sticky default recreates the *ergonomics* of an active list — subsequent quick-adds go there silently with a small "adding to Groceries ▾" affordance to switch — but as a **transient, inferred** default the user never sets up, not a stored property with a config banner.

**"Shop now" PWA shortcut** asks a different question — not "where do I add?" but "what do I shop?" — so it keys off a different phase:

| Condition | Behavior |
|---|---|
| 1 list in SHOPPING | Open it (resume the trip) |
| else 1 DRAFT | Offer to start shopping it |
| else (0, or 2+) | Land on the overview |

Same *pattern* — infer when unambiguous, fall back to neutral when not — keyed to the relevant phase for each entry point.

> **Why this is reliable only now:** "count the draft lists" is a trivial, exact query when a list is in exactly one phase. Under today's flag soup ("active" = not-archived-and-not-in-progress, roughly) that count is mushy. The status model (§2.1) is what makes contextual inference dependable — the two ideas reinforce each other.

### 2.5 Fix the in-store experience (now that it's a first-class phase)

Because SHOPPING is no longer a side-trip you navigate into, the in-store flow deserves to be solid:

- **Skip persists.** Today "skip" reorders locally and silently reverts on refresh (client-only). Make it a real, saved reorder.
- **Quantity is tap-to-type**, not click `+` ten times.
- **Whole-list peek.** A peek/expand to see the full remaining list — you're no longer "leaving" a separate mode to check it.
- **Group-by-aisle stops destroying manual order.** Keep it as a view; never overwrite the stored `sequence`.

---

## 3. Trade-offs & risks (the honest part)

- **Migration is the crux.** Collapse `is_in_progress` / `is_archived` (+ implicit active) into a single `status` enum (`draft` / `shopping` / `done`). Mechanical, but it touches every shopping-list query, the summary/detail DTOs, and the overview/membership sorting.
- **`is_primary` removal ripples.** Quick-add, the PWA shortcut, and the finish auto-promote logic (`manage_shopping_list.py:244`) all reference it today. Removing the stored flag means rewriting those to the inference rules in §2.4.
- **Reopen replaces "unfinish," and gets more robust.** Today undo-finish has the client snapshot pre-finish stock levels and POST them back (`unfinish_shopping_list.py`) — brittle: lose the snapshot, lose the undo. With explicit states, "reopen" is a server-side `done → draft` transition. Record the stock-level deltas **server-side at finish time** so reopen reverses them without trusting the client.
- **Risk concentrates in the finish/restock path** — the one place a state change ripples into another domain (stock levels). Treat it as its own transaction with an audit row; that also yields free, reliable undo and removes today's inconsistency where "Clear all items" has *no* undo but "Finish" has a *fragile* one.
- **Net less surface area.** We delete the five auto-gen wrappers, the Start/Stop pair, and the Review-mode toggle. Fewer buttons, fewer flags, fewer nonsense states — that's the point.

---

## 4. Suggested sequencing

1. **Data model + API:** introduce `status`, migrate existing rows (`is_archived → done`, `is_in_progress → shopping`, else `draft`), add the `done → draft` reopen transition with server-side stock-level delta tracking.
2. **Inference rules:** implement quick-add and Shop-now target resolution; remove `is_primary` reads. Keep `is_primary` column temporarily for rollback safety, drop in a follow-up migration.
3. **UI — lifecycle:** single primary-action button; fold review into the finish confirmation; SHOPPING phase renders the shop-mode surface in place.
4. **UI — creation:** one creation surface mapped to `/auto-generate`; retire the five entry points.
5. **In-store polish:** persistent skip, tap-to-type quantity, whole-list peek, non-destructive group-by.

---

## 5. Open questions

- Should DONE lists be permanently deletable, or only archived-then-purged on a schedule?
- Does "remember the pick" reset per session, or persist until the chosen draft becomes DONE?
- Is there ever a reason to have **two** lists in SHOPPING at once (two shoppers, two stores)? The model above assumes at most one resume target — worth confirming.
