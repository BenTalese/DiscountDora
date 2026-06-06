# A3 — Standard modal behaviour

**Wave:** A · **Risk:** low-medium · **Depends on:** A1 (tokens), helps from A2 (buttons)

## Impact & decisions (read first)
- Fixes a recurring complaint AND several bugs: modals that don't close on click-outside, and modals with **no Cancel** (new-recipe modal, recipe delete, cook-mode finish, unsaved-changes modal). Some currently *navigate away* on click-out — a bug.
- **Decision — destructive modals:** should click-outside dismiss a *destructive* confirm (delete)? Recommended: click-outside = cancel for **all** modals (safe default), destructive action requires an explicit button. Confirm.
- One subtlety: the **unsaved-changes** modal must NOT navigate on click-out (current bug) — click-out should mean "stay/cancel," not "discard and go."

---

## PROMPT

Standardise modal/dialog behaviour in a Vue 3 + Quasar SPA (`web_app/`).

### 1. Discover
- Find dialog usage (`q-dialog`) and any shared dialog wrapper. List dialogs that (a) lack a Cancel/close, (b) don't close on backdrop click, or (c) navigate/commit on backdrop click (bug).

### 2. Define the standard
- A `BaseDialog` wrapper (or normalise the existing one) where: backdrop click and Esc = **cancel** (no commit, no navigation); every dialog has an explicit Cancel/Close and a primary action; consistent header/footer/padding from tokens.
- Destructive dialogs: same dismissal rules, but the destructive button is `danger` variant and is the *only* way to commit. (Confirm this policy with me.)

### 3. Migrate the known offenders (verify against current code)
- New-recipe modal (make consistent with add-stock modal; click-out cancels).
- Recipe delete confirm (add Cancel; click-out cancels).
- Cook-mode "finished cooking" modal (click-out cancels → returns to cooking).
- Unsaved-changes modal: add Cancel; **click-out = stay** (do not discard/navigate).
- Any others surfaced in step 1.

### 4. Verify
- Each migrated dialog: Esc cancels, backdrop cancels, explicit buttons work, no accidental navigation/commit. Light + dark.

Output: the BaseDialog (or changes), list of dialogs migrated, and confirmation each no longer commits/navigates on dismiss.
