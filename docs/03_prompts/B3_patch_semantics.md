# B3 — "Can't save unless I change the name" (partial-update semantics)

**Wave:** B · **Risk:** medium (touches update handlers) · **Depends on:** none

## Impact & decisions (read first)
- Symptom: editing a stock item or recipe and saving **without changing the name** fails with "a <thing> with the name 'X' already exists." You correctly diagnosed it as PUT-style full-object update tripping the uniqueness check against itself.
- Two valid fixes — **confirm which** (or both):
  1. **Exclude-self in the uniqueness check** (smallest change): "name exists AND id != this id."
  2. **True PATCH** (only send/apply changed fields): cleaner, but you warned "be careful" — must not accidentally null unspecified fields.
- Recommended: do **both** — exclude-self now (fixes the bug safely) and move updates to partial-field semantics where feasible. The merged recipes area means verify recipe update against your current code.

---

## PROMPT

Fix self-collision on update for stock items and recipes (and audit for the same pattern elsewhere) in a Python backend + Vue frontend.

### 1. Locate (read current code)
- Find the stock-item and recipe **update** handlers and their uniqueness validation. Confirm whether the request is full-object (PUT-like) and whether the name-uniqueness check excludes the current entity.

### 2. Fix
- **Uniqueness check:** exclude the current entity id (`name == X AND id != current_id`). This alone fixes the reported bug.
- **Partial update (preferred where safe):** use the request's set/provided fields only (e.g. Pydantic `model_fields_set`) so unspecified fields are left untouched, not overwritten/nulled. Mirror on the frontend by sending only changed fields. Be careful not to clear fields the user didn't touch.

### 3. Sweep
- Grep other update handlers for the same "uniqueness check that doesn't exclude self" pattern and fix consistently.

### 4. Verify
- Edit a stock item changing only (say) expiry → saves fine, name untouched. Same for a recipe. Changing a name to a *different existing* name still correctly errors.

Output: handlers changed, the approach used (exclude-self and/or partial), other endpoints found with the same flaw, and verification notes.
