# SUBSTITUTE_SWAP_ASSESSMENT — INV-8

**Date:** 2026-06-06 · **Type:** Read-only, no code changes · One-page memo.  
**Question:** The user said "swap into list for substitutes feels like a weird
feature. Would it even get used?" Assess the list-level substitute swap.

---

## How the list-level swap works today

- **Affordance:** a "Swap with substitute…" item in the per-line three-dot menu
  on the full shopping-list view (`ShoppingListDetail.vue:756-763`).
- **Flow** (`onSwapSubstitute`, ~1345-1424): fetch the line's stock-item detail
  to read its `substitutes[]`, filter out ones already on the list, show a
  radio dialog, then **add a new line for the chosen substitute** (`addLineAsync`)
  and **delete the original** (`deleteLineAsync`), preserving quantity. New
  `line_id` minted. Toast: "Swapped with substitute."

So it's a permanent line replacement, driven off the same per-item substitutes
list curated on the stock-item detail page.

## How it relates to the other two substitute surfaces

1. **Per-item substitutes list** (detail page) — the curated source data. Kept.
2. **B8 cook-mode temporary swap** (`RecipeCookMode.vue:386-421`) —
   session-only (`sessionSwaps` in RAM); on finish it decrements the
   *substitute's* stock, never edits the saved recipe. Ephemeral. Kept.
3. **This list-level swap** — permanent edit to a shopping-list line.

No functional overlap with cook-mode (ephemeral vs persistent). **But there's a
labelling collision:** Shop Mode has its own "Substitute" button
(`ShoppingListShopMode.vue:176-182`) that swaps the **merchant offer**, not the
stock item — same word, different action.

## The mental-model problem

The intuitive use case is "I'm at the shelf, planned item is out — swap it here."
That moment happens in **Shop Mode**, but Shop Mode's "Substitute" only changes
the offer. The stock-item swap lives back in the full list view, three menu
levels deep, so serving the real moment means exiting shop mode, swapping, and
re-entering. The list-level swap reads as **leftover from before B8** rather than
something positioned for when it'd actually be used. No telemetry exists to
confirm usage either way.

## Recommendation: **REWORK** (cut only if confirmed unused)

- The feature *concept* (swap an out-of-stock planned item for a known
  substitute) is legitimate — but it's in the wrong place and collides with Shop
  Mode's offer-swap label.
- **Rework:** surface the stock-item substitute swap **inside Shop Mode** at the
  moment of "this is out," and disambiguate the two "Substitute" buttons (e.g.
  list/shop = "Swap item" vs offer = "Pick another offer"). Then it serves the
  real in-shop moment instead of being buried.
- **Cut** only if you'd rather lean entirely on cook-mode swaps + manual
  add/remove and a quick check shows no one uses the list-level path. Given it's
  cheap to keep and the rework is modest, rework is the safer call.
- **Confirm-in-browser** flag: whether Shop Mode's "Substitute" truly only swaps
  the offer (static read says yes) — verify before acting.

---

## Feedback coverage

| User-flagged item | Finding |
|---|---|
| "swap into list for substitutes feels weird — would it get used?" | Works, but buried in the full-list menu and mispositioned vs the real in-shop moment; collides with Shop Mode's offer "Substitute". **Recommend REWORK** (move into Shop Mode + disambiguate), cut only if confirmed unused. |
