# B8 — Recipe detail dead/wrong actions

**Wave:** B · **Risk:** medium (in the merged recipes area — re-ground first) · **Depends on:** none

## Impact & decisions (read first)
- **Your code has merged meals into recipes** — this area drifted most from my copy. The executing agent MUST read the current recipe detail page + recipe API before changing anything; my references are hints only.
- Reported defects:
  - Remove-from-favourites does nothing.
  - Clicking a related recipe fails / dumps you on the Cookbook overview instead of that recipe.
  - All recipe actions inert **except** Cook.
  - **Substitute selection permanently swaps/edits the recipe** — wrong; substituting should be **temporary** (and ideally cook-mode-only).
  - References the **deleted substitutes-graph** feature.
- **Decision — substitutes behaviour:** confirm the intended model: a substitute is a *temporary* swap for a single cook session, never mutating the saved recipe. (This aligns with your feedback.)

---

## PROMPT

Fix broken actions on the recipe detail page in a Vue 3 + Quasar SPA (`web_app/`) with a Python backend. **Read the current recipe detail page, recipe store/API, and substitutes handling first — the meals→recipes merge means structure has changed.**

### 1. Inventory the actions
- List every action/button on recipe detail and test what each does. Identify the inert ones (favourite toggle, related-recipe navigation, others) vs working (Cook).

### 2. Fixes
- **Remove from favourites:** wire the toggle to the real favourite mutation; reflect state.
- **Related-recipe navigation:** route to the specific recipe id, not the overview.
- **Other inert actions:** wire each to its handler; if an action is obsolete post-merge, remove it (note which).
- **Substitutes:** make substitute selection a **temporary, non-destructive** swap that does NOT edit the saved recipe. Prefer applying it for the cook session only. Remove/replace any reference to the deleted **substitutes-graph** feature.

### 3. Verify
- Favourite toggles + persists; related recipes navigate correctly; previously-inert actions work or are removed; choosing a substitute leaves the saved recipe unchanged; no mention of substitutes-graph remains.

Output: action inventory (before/after), the substitutes behaviour implemented, removed obsolete actions, and verification.
