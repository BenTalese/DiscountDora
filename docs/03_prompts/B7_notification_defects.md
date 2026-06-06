# B7 — Notification / toast defects

**Wave:** B · **Risk:** low · **Depends on:** none

## Impact & decisions (read first)
- Two issues:
  1. **Placeholder text in production:** the "Generate shopping list" toast on Meal Plans showed subtitle **"I'm a notification!"**. Unacceptable for a polished app — purge ALL placeholder/demo/example strings app-wide.
  2. **Duplicate/contradictory toasts:** stocktake shopping-list action fires **two at once** — "0 added, 1 already on list" AND "brazil nuts added to your primary list." Conflicting and confusing.
- Low risk; mostly string + notification-logic cleanup. The deeper "shopping-list button should know the item's list state" is part of the cart-button big rock (C7) — here just fix the duplicate/contradiction.

---

## PROMPT

Fix notification/toast defects in a Vue 3 + Quasar SPA (`web_app/`).

### 1. Purge placeholders
- Grep for placeholder/demo strings in notifications and UI: "I'm a notification", "example", "placeholder", "lorem", "demo" (and similar). Replace each with the correct real message or remove. Report every hit.

### 2. Fix duplicate/contradictory toasts
- Find the stocktake "add to shopping list" action. It emits two toasts that contradict ("0 added, 1 already" + "added to primary"). Determine the true outcome and emit **one** accurate toast (e.g. "Already on your primary list" OR "Added to your primary list"). Remove the redundant emit.
- Sweep for other double-toast patterns (an action both showing a per-item result and a generic success).

### 3. Verify
- No placeholder text anywhere in notifications; the stocktake add emits exactly one correct toast for each case (already-on-list vs added).

Output: list of placeholder strings fixed, the stocktake toast logic corrected, and any other duplicate-toast sites found.
