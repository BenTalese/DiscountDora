# A7 — Componentised sticky footer for page counts

**Wave:** A · **Risk:** low-medium (layout) · **Depends on:** A1, A2

## Impact & decisions (read first)
- You want page-level **counts moved out of the cluttered top area into a consistent sticky footer**, with spacing between footer and scroll area, and **more counts** where useful (well-stocked, sufficient, flagged, auto-add, needs-attention…).
- Applies to: stock overview, my products, recipes (Cookbook). The top-area teardown itself is part of the **Stock Overview big rock (C)** — A7 just provides the reusable footer they'll use.
- **Decision:** footer counts should reflect **filtered** results or **totals**? (You said export should follow the filtered set — suggest counts do too. Confirm.)

---

## PROMPT

Create a reusable sticky page-footer for counts in a Vue 3 + Quasar SPA (`web_app/`).

### 1. Discover
- Find where stock overview / my products / recipes render their page-level counts today (currently top, cramped/hidden).

### 2. Build
- A `PageCountsFooter` component: sticky to the viewport bottom of the page content, visually separated from the scroll area (gap/elevation, tokenised), responsive wrap, each count a labelled stat. Accepts a list of `{label, value, tone?}`.

### 3. Wire up
- Stock overview: well-stocked, sufficient, low, out, flagged, auto-add, needs-attention, total (confirm the set). Counts reflect the **filtered** view (confirm).
- My products & recipes: the equivalent useful counts, moved from the top into the footer.

### 4. Verify
- Footer visible without overlapping content; counts update with filters; consistent across the three pages; light + dark; mobile sensible.

Output: the component + per-page wiring. Note: do not rebuild the stock-overview top toolbar here (that's the Stock Overview design brief).
