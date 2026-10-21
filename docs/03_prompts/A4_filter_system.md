# A4 — Filter system standardisation + "empty = off" bug

**Wave:** A · **Risk:** medium (shared behaviour across data-heavy pages) · **Depends on:** A1, A2

## Impact & decisions (read first)
- Fixes a **real bug on every filtered screen**: clearing a filter input filters *everything out* instead of behaving as "filter off." Empty MUST equal off.
- Standardises filter UX you flagged everywhere: show/hide toggle, active-state indication, a consistent Clear that styles when filters are active, and multi-select pattern.
- **Decisions:**
  1. **Default visibility** — you suggested filters shown by default on desktop, hidden on mobile. Confirm.
  2. **Search bar** — keep the free-text search **separate** from the collapsible filter panel (you said so). Confirm.
  3. **Numeric filters** (e.g. per-unit max price): reject non-numeric input; empty = off. Confirm.
- Affects: stock overview, product search, my products, recipes (Cookbook). NOT the deferred pages.

---

## PROMPT

Standardise filtering across the data-list pages of a Vue 3 + Quasar SPA (`web_app/`) and fix the empty-input bug.

### 1. Discover (read current code)
- Find each page's filter implementation (stock overview, product search, my products, recipes). Identify how empty inputs are handled — the bug is that empty string is treated as a non-matching predicate instead of "no filter."
- Note differences in: filter panel show/hide, active indication, clear button behaviour, multi-select handling.

### 2. Core rule (fix the bug everywhere)
- An empty/blank filter value (text, number, or empty multi-select) means **filter disabled** — it must not exclude any rows. Apply this uniformly. Numeric inputs: ignore non-numeric, treat blank as off.

### 3. Shared filter UX
- A reusable filter-bar component: collapsible panel (default **shown on desktop, hidden on mobile** — confirm), a **separate** persistent search box, an "active filters" indicator (count of active / styled Clear button only when ≥1 active), and a consistent multi-select control.
- Standard "Clear filters" label/behaviour identical on every screen (replace one-off variants like "Clear ranges").

### 4. Migrate each page to the shared component
- Preserve each page's specific filter fields; only the *mechanics/skin* are shared.

### 5. Verify
- On each page: blank input shows all rows; non-numeric rejected; clear resets; active indicator correct; mobile hides panel by default. Light + dark.

Output: the shared filter component, per-page migration list, and explicit confirmation the empty-input bug is fixed on each page.
