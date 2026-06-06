# B4 — Delete stock item → FOREIGN KEY constraint failed

**Wave:** B · **Risk:** medium (data integrity) · **Depends on:** none

## Impact & decisions (read first)
- Symptom: deleting a stock item → `sqlalchemy.exc.IntegrityError: FOREIGN KEY constraint failed`. It's referenced by other rows (recipe ingredients, shopping-list lines, products/links, locations, etc.). *(Substitutes graph and stock map are removed features — don't expect those tables.)*
- **Decision — delete policy (important, confirm):**
  - **(a) Cascade delete** dependents (removes the item and everything pointing at it). Simple but can silently destroy recipe ingredients / list lines.
  - **(b) Block with explanation** ("used by 3 recipes, on 1 list — remove there first / confirm"). Safest; matches your "dangling reference" worry.
  - **(c) Soft-delete** (mark inactive/archived, hide from lists). No data loss; needs UI filtering.
  - Recommended: **(b) for user-facing delete** (clear consequences), with cascade only for truly owned children. Tell me your preference.
- This also fixes the vague "dangling reference" warning copy you flagged on Stock Item Detail.

---

## PROMPT

Fix stock-item deletion failing on FK constraints in a Python/SQLAlchemy + SQLite backend with a Vue frontend.

### 1. Map references (read current code)
- Find every table/relationship referencing a stock item (recipe ingredients, shopping-list lines, product links, locations, stocktake, alerts, etc.). List FK constraints that block deletion. (Ignore substitutes/stock-map — removed.)

### 2. Implement the chosen policy
- I will tell you the policy: **(a) cascade / (b) block-with-explanation / (c) soft-delete.** Default to **(b)** if I haven't said.
- **(b):** before delete, count references; if any, return a structured response listing what references it; the UI shows a clear modal ("Used by N recipes, on M lists — these will lose this item / remove there first"). Only delete on explicit confirm, cascading only genuinely-owned children.
- **(a):** configure proper cascade on owned relationships; still warn in UI.
- **(c):** add an archived/inactive flag, exclude from normal queries, keep references intact.

### 3. Fix the warning copy
- Replace the vague "Recipes that use it will be left with a dangling reference" with accurate, specific text driven by the actual reference counts.

### 4. Verify
- Deleting a referenced item no longer 500s; behaviour matches the chosen policy; an unreferenced item still deletes cleanly.

Output: the reference map, the policy implemented, backend + frontend changes, and verification.
