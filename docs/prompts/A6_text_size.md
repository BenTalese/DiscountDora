# A6 — Text-size scale + global application

**Wave:** A · **Risk:** low-medium (global typography) · **Depends on:** A1

## Impact & decisions (read first)
- Two issues: the small/medium/large steps are **too close** (you expected ~75% / 100% / 150%), and the setting **isn't applied everywhere** (some hovers/areas ignore it).
- The token system already has a font-size scale driven by `--dora-base-font-size` (set by `themeService.ts` from the user's `font_size` pref). So this is: (1) re-space the steps, (2) find text that uses fixed px instead of the scale.
- **Decision:** confirm the three steps map to **0.875 / 1.0 / 1.25** of base, or your preferred **0.75 / 1.0 / 1.5**. (Bigger spread = more visible difference but more layout shift to test.)

---

## PROMPT

Fix and globally apply the text-size preference in a Vue 3 + Quasar SPA (`web_app/`).

### 1. Discover
- Read `src/services/themeService.ts` + `tokens.scss` for how `--dora-base-font-size` and the font-size scale work and how the `font_size` user pref maps to it.
- Find text using **fixed px font sizes** (or Quasar `text-*` sizing) that bypass the scale — especially small text, hovers/tooltips, captions.

### 2. Re-space the steps
- Set the three preference steps to a clearly distinct spread (confirm with me: `0.875 / 1.0 / 1.25` vs `0.75 / 1.0 / 1.5`). Ensure the base value drives the unitless `--font-size-*` ratios already defined.

### 3. Apply globally
- Migrate fixed-px text to the scale tokens so the preference affects them. Tooltips/hovers included.

### 4. Verify
- Switching the preference visibly changes text app-wide including hovers; no broken layouts at the largest step (spot-check dense screens: stock overview, recipe detail, meal plans). Light + dark.

Output: the changed scale, list of migrated text sites, and any deliberately-fixed text (with reason).
