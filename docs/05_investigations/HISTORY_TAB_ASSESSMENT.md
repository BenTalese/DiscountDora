# HISTORY_TAB_ASSESSMENT — INV-7

**Date:** 2026-06-06 · **Type:** Read-only, no code changes · One-page memo.  
**Question:** Does the Stock Item Detail "History" tab earn its surface? The user
said it "feels unuseful… maybe if it had a bit more data/info. I'd need to be
convinced."

---

## What it shows today

A bare Quasar timeline of **stock-level changes only**
(`StockItemDetailPage.vue:412-425`), backed by `level_history` from the detail
endpoint (`get_stock_item_detail.py:213-225`) — up to 20 `StockLevelChange`
rows, each with just `changed_at` + `stock_level_name`:

> "Low — 3 days ago" · "Well-Stocked — 1 week ago" · …

No reason, no cost, no link to anything else. It's a read-only record that
doesn't tell you *why* a level changed or *what else* happened — so it drives no
decision. That matches the user's "unuseful" read.

## What already exists that could make it useful (no new logging)

The model already records per-item lifecycle events that are not surfaced here:

| Event | Source (already in model) |
|---|---|
| Opened / in-use | `StockItem.opened_on`, `is_open` |
| Last stock-take check | `StockItem.last_checked_at` |
| Waste / spoilage | `StockItemWasteEvent` (`occurred_at`, `reason`, `quantity`, `estimated_value`) |
| Added to a list (why) | `ShoppingListLine.added_at` + `added_via` (manual / auto_low_stock / auto_recipe / auto_essential…) |
| Expiry set/cleared | `StockItem.expiry_date` |

Of these, `StockItemWasteEvent` and the list-add provenance are the highest-value
and are completely absent from the detail DTO today.

## Sketch — a unified "item lifecycle" timeline

```
● Opened — 10 Jun
● Added to Primary list (auto: low stock) — 8 Jun
● Wasted ~30% (spoiled) — 3 Jun · ≈$0.85
● Level → Low — 3 Jun
● Level → Well-Stocked (restocked) — 27 May
● Created — 15 May
```

Same timeline component, more event types merged in and sorted by date. Level
changes can be labelled with inferred context by comparing their timestamp to
`opened_on` / `last_checked_at` already in the detail payload.

## Charter check

- **P5 closed loop:** a multi-event timeline makes the purchase→use→waste→restock
  loop visible per item — the level-only view severs it.
- **P6 insight→action:** "wasted twice this month" / "never checked in 30 days"
  are each one tap from an action (adjust cadence, quick stocktake).
- **P10 anti-creep:** uses data that already exists; no new capture, no new page —
  it *replaces* a weak tab rather than adding surface.

## Recommendation: **REWORK** (don't cut, don't keep as-is)

The tab is worth keeping **only** if it earns the space — merge waste events and
list-add provenance into the existing timeline and label level changes with
context. Medium effort, no schema change (mainly: add `StockItemWasteEvent` +
recent list-adds to the detail DTO and render them). If that's not on the table
soon, it stays a weak surface — but cutting loses the one place item history
could live, so rework beats cut. Folds naturally into a future Stock Item Detail
polish chunk.

---

## Feedback coverage

| User-flagged item | Finding |
|---|---|
| "History tab feels unuseful as-is" | Confirmed — level-changes-only, no context/action (`StockItemDetailPage.vue:412-425`). |
| "maybe if it had more data/info" | Rework sketch: merge waste events + list-add provenance + open/checked context, all from existing model data. **Recommend REWORK.** |
