# B1 — "Extra inputs are not permitted" (product save/link/quick-add/inactive)

**Wave:** B · **Risk:** low-medium (API contract) · **Depends on:** none

## Impact & decisions (read first)
- Symptom on Product Search + My Products: saving a product, quick-add to list, link to stock item, and mark-inactive all fail with **"Extra inputs are not permitted"** (repeated).
- Root cause (confirmed in my copy; verify in yours): request models use Pydantic `ConfigDict(extra="forbid")`, and the frontend sends fields the schema rejects (computed/display fields, or wrong field names).
- **Decision — fix direction:** prefer **aligning the frontend payload** to the request contract (keeps `extra="forbid"` as a guardrail). Only relax a specific schema if a field legitimately belongs. Do NOT blanket-remove `extra="forbid"`.
- "Link to a stock item" should **also save the product** in the same action (you flagged this) — handle as part of the fix.

---

## PROMPT

Fix the "Extra inputs are not permitted" failures in a Vue 3 + Quasar SPA (`web_app/`) with a Python backend.

### 1. Reproduce & locate (read current code)
- For each failing action — save product, quick-add product to list, link product to stock item, mark product inactive — find the frontend call (`src/services/api/…`) and the backend request model (`dora_api/features/products/…`, shopping list line/add handlers).
- Diff the JSON the frontend sends against each request model. The offending extra fields / mismatched names are the cause (models use `extra="forbid"`).

### 2. Fix (prefer frontend alignment)
- Make the frontend send exactly the fields each endpoint accepts (strip computed/display-only fields; correct any renamed fields). Keep `extra="forbid"`.
- If a sent field genuinely belongs on the endpoint, add it to that specific request model instead.
- **Link action:** ensure linking a product to a stock item also persists/saves the product if not already saved (single user action, ideally one transaction or safely sequenced).

### 3. Verify
- All four actions succeed end-to-end. No "extra inputs" error. Link also saves the product. Check the mark-inactive path actually toggles `is_active`.

Output: per action — the field mismatch found and the fix applied (frontend strip vs schema add), and confirmation each works.
