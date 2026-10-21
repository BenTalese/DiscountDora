# A5 — One loading / skeleton component everywhere

**Wave:** A · **Risk:** low · **Depends on:** A1

## Impact & decisions (read first)
- You want the **same loading treatment everywhere**, using the first-app-load pulse animation, and **skeleton (layout-mimicking) placeholders** instead of literal text like "Stock Item" while detail views load.
- **Decision:** two patterns — (a) a **spinner/pulse** for short waits, (b) a **skeleton** that mirrors the page layout for list/detail loads. Confirm you want both, or skeleton-only.
- Low risk; purely presentational.

---

## PROMPT

Unify loading states in a Vue 3 + Quasar SPA (`web_app/`).

### 1. Discover
- Find the first-app-load pulse animation (the one shown while the SPA boots). Find all ad-hoc loading states (`q-spinner`, `loading` flags rendering placeholder text like "Stock Item", `q-inner-loading`, etc.).

### 2. Build shared components
- `AppSpinner` (or reuse the boot pulse) for short/inline waits.
- `Skeleton` blocks (line, card, row, detail) that mimic the real layout, animated with the same pulse, tokenised colours (`--surface-sunken`/shimmer).

### 3. Migrate
- Replace placeholder-text loading (esp. stock item detail showing "Stock Item") with skeletons that match that view's layout.
- Replace inconsistent spinners with `AppSpinner`. Product-search loading area must be theme-aware (currently isn't).

### 4. Verify
- No raw placeholder text during load; skeletons match layout; consistent animation; light + dark correct.

Output: the components, list of replaced loading sites, and any spot left on a spinner deliberately (with reason).
