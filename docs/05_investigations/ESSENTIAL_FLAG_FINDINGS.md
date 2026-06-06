# ESSENTIAL_FLAG_FINDINGS — INV-10

**Date:** 2026-06-06 · **Type:** Read-only, no code changes.  
**Question:** The user said "no way to set 'essential' that I can see. Might be
missing it?" Trace where "essential" lives, how it's read, and whether it's the
right primitive.

---

## The headline: "essential" = `StockItem.is_flagged` (a labelling gap, not a missing feature)

There is **no `is_essential` column.** "Essential" is the product-language name
for the existing `is_flagged` boolean (`stock_item.py`, column
`table_mappings.py:123`, TS `stockItem.ts:8`). The user's confusion is justified
because **the one place to set it doesn't use the word "essential."**

### Where it's SET (today)
- **Stock Item Detail** (`StockItemDetailPage.vue:205-220`): a toggle labelled
  **"Always include in auto-generated lists"** — *not* "Essential." Its tooltip
  is the only on-screen text linking it to "essentials." Saved as `is_flagged`.
- **Reports page** (`ReportsPage.vue:501-518`): a bulk `markAllEssential()` for
  the "keeps running out" set — discoverable only if you're on that report.

### Where it's READ
- **Auto-generate** (`auto_generate.py:80-82, ~289-295`): `essentials_only_for_low`
  counts only `is_flagged` items for low/out picks; tagged `ADDED_VIA_AUTO_ESSENTIAL`.
  Plus a convenience `append-low-stock-essentials` endpoint.
- **Alerts** (`get_alerts.py:123-150`): flagged + low/out → `essential_low`,
  `SEVERITY_HIGH`.
- **Stock overview** (`useStockFilters.ts:52,149,182,278`): an "Essentials"
  filter chip + counts.
- **Assistant** + chips surface it too.

So the concept is fully wired on the read side and consistently *called*
"essential" everywhere **except the toggle that sets it.**

## Is "essential" the right primitive?

Yes — an explicit, user-set "always restock this staple" flag is the right
lightweight primitive, and it's Charter-aligned (Effortless, explicit, single
purpose). A *derived* alternative ("you buy this every shop") would lean on
purchase history and the existing `auto_frequently_added` provenance, but that's
a fuzzier, harder-to-trust signal and the app already exposes
`frequently_added` separately in auto-generate. **Keep essential explicit; don't
auto-derive it.**

Note it's distinct from `auto_add_when_low` (silently adds to the primary list on
a low/out transition) — different trigger, both legitimate. Their labels just
don't make the distinction obvious.

## Recommendation

1. **Rename the detail toggle** from "Always include in auto-generated lists" to
   **"Essential — always include when restocking"** (keep the tooltip explaining
   it only matters on explicit auto-generate, vs `auto_add_when_low`). This alone
   resolves the user's "can't find it."
2. **Add a quick-set where users already triage** — an "Essential" toggle in the
   stock-overview row context menu / multi-select, so it doesn't require opening
   each item or finding the Reports button. The "Essentials" filter chip already
   lives there, so set + filter are co-located.
3. **Leave the primitive as `is_flagged`** (explicit boolean). No data-model
   change; this is a labelling + discoverability fix.

---

## Feedback coverage

| User-flagged item | Finding |
|---|---|
| "no way to set 'essential' that I can see" | It IS settable — `is_flagged`, but the toggle reads "Always include in auto-generated lists," not "Essential." **Rename it** + add a stock-overview quick-toggle. |
| `essentials_only_for_low` criterion exists | Confirmed — it filters auto-generate low/out picks to `is_flagged` items (`auto_generate.py:80-82`). The flag is the essential flag. |
| Is "essential" the right primitive? | Yes — keep it explicit (`is_flagged`); don't auto-derive. Distinct from `auto_add_when_low`. |
