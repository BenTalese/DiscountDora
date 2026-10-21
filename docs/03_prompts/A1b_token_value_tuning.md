# A1b — Token *value* tuning (do AFTER A1)

**Wave:** A · **Risk:** low (values only) · **Depends on:** A1 complete (everything on tokens)

## Impact & decisions (read first)
- Once components consume tokens (A1), specific "too bright / unreadable" complaints become **one-line fixes to token values** that propagate everywhere.
- Known targets from feedback: green "add" buttons too bright in pesto; recipe "cookable" green too bright; pesto-dark green chips (connections/stores) hard to read; well-stocked chip; any contrast flagged by the A1 audit's "out-of-scope but spotted" section.
- Pure value tuning — no component changes. If a colour still looks wrong after this, it means a component is still bypassing tokens (kick back to A1).

---

## PROMPT

Tune theme **token values** in `web_app/src/css/themes.scss` (and `tokens.scss` defaults) — values only, no component edits.

### 1. Gather
- Read the "out-of-scope but spotted" section of `web_app/THEME_AUDIT.md` (from A1) plus these reported issues: bright greens on add/positive buttons (pesto), bright "cookable"/well-stocked greens, pesto-dark green chips unreadable.

### 2. Adjust
- For each, adjust the relevant semantic/brand token *value* (lower lightness/saturation, or fix the paired `*-soft` / text-on colour) so contrast is comfortable in the affected theme+mode. Keep meaning intact (positive stays green-ish, etc.). Check both light and dark of each affected family.

### 3. Verify
- For every changed token, reason through each theme that uses it (esp. pesto + pesto-dark): text on the colour meets contrast; chips/buttons readable; no regressions to other themes.

Output: a table of token → old value → new value → themes affected → reason. If any reported issue can't be fixed by value alone, flag it as a remaining component-compliance gap for A1.
