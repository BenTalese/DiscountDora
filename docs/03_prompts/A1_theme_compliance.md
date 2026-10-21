# A1 — Theme token-compliance (audit + chunked fixes)

**Wave:** A (foundations) · **Risk:** wide but shallow (styling only) · **Depends on:** nothing

## Impact & decisions (read first)
- Touches **nearly every `.vue` file** — low logic risk, but every screen needs a quick light+dark eyeball after.
- Swapping a hardcoded hex for a token can **slightly shift light mode** where the old hex didn't match the token. Usually desirable (consistency), but "light mode unchanged" is not guaranteed.
- **Separate, do NOT do here:** token *value* tuning (too-bright greens) → `A1b`. The theme-*picker* UX split (system/light/dark × family) → lives in Settings (deferred).
- Decision already made: **one audit, then chunked fixes.**

---

## STEP 1 — AUDIT PROMPT (no code changes)

You are auditing a Vue 3 + Quasar SPA (`web_app/`) for **hardcoded colours that bypass the design-token system**. AUDIT ONLY — change nothing except creating `web_app/THEME_AUDIT.md`.

### Background — read first, treat as source of truth
- `web_app/src/css/tokens.scss` — semantic tokens (text/surface/brand/semantic/border/overlay/chart/spacing/radius/font-size).
- `web_app/src/css/themes.scss` — `[data-theme="…"]` overrides (5 families × light/dark).
- `web_app/src/css/quasar.variables.scss`, `app.scss`, `colours.scss`; `src/services/themeService.ts`, `src/boot/theme.ts` for activation.
Build a map of the **actual** semantic token names before scanning; propose only tokens that exist.

### Offenders to flag (scan `web_app/src/**` `.vue`/`.scss`/`.css`/`.ts`)
1. Raw colour literals: hex, `rgb()/rgba()`, `hsl()/hsla()`, CSS named colours used as colour values.
2. Quasar palette classes: `text-white`, `bg-green-6`, `text-red-5`, `text-grey-7`, etc.
3. Quasar `color="…"` / `text-color="…"` props using palette names.
4. Inline `:style`/`style=""` colour values.
5. SCSS `$colour` vars defined outside the token files; `setCssVar` writing literal colours.

### Exclude
- The token definition files themselves; intentional brand/logo colours (note + mark `intentional?`); non-colour `transparent`. DO flag raw-black shadows/overlays if `--overlay-*` / `--elevation-*` tokens exist.

### Capture per offender
`file:line` · snippet · **proposed token** (best guess; if intent ambiguous set `needs_decision: yes` + reason) · **mode risk** (`dark-broken` vs `consistency`; prioritise dark-broken) · **light-shift** (`yes/no/maybe`).

### Output `web_app/THEME_AUDIT.md`
1. Summary counts (by type; dark-broken vs consistency).
2. Token cheat-sheet (actual tokens found, one-line "use for…" each).
3. Findings grouped into **reviewable CHUNKS** by page-group (auth/shell; stock; products; recipes+cook; meal-plans+shopping; dora+shared; other) — each a table of the columns above + chunk gotchas.
4. `needs_decision` section (all ambiguous intents in one place).
5. "Out-of-scope but spotted": token-*value* problems for A1b (note, don't fix).

End by printing summary counts + the chunk list.

---

## STEP 2 — FIX PROMPT TEMPLATE (run once per chunk)

Use `web_app/THEME_AUDIT.md` as the work list. Fix **only the chunk named `<CHUNK NAME>`**.

- Read each offender in the chunk and replace the hardcoded colour with the proposed semantic token (`var(--…)` in styles; for Quasar `color=` props prefer a brand/semantic mapping or a tokenised class).
- Where the audit marked `needs_decision`, use the resolution I give you here: `<paste resolved intents, or "use your best judgment and list what you assumed">`.
- Do **not** change token *values* (that's A1b). Do not touch files outside this chunk.
- After editing, verify by reasoning through **both** `pesto` (light) and `pesto-dark` for each changed surface: text must meet contrast, no white-on-white / invisible text, semantic colours still read as their meaning.
- Output: the diff for this chunk + a short list of any offenders you skipped and why, and any new `needs_decision` items discovered.
