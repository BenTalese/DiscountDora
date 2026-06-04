# A2 — Standard button + toolbar + "create" placement

**Wave:** A · **Risk:** medium (visual + minor layout) · **Depends on:** A1 (tokens in use)

## Impact & decisions (read first)
- You want **one toolbar button standard** app-wide (same height/width/spacing), with purpose-built exceptions only (e.g. the stocktake glow). This will visibly re-style most toolbars.
- **Decision — button variants:** confirm the set before running. Proposed: `primary` (filled brand), `secondary` (outline), `ghost` (text-only), `danger` (filled negative), `icon` (square icon-only). Plus a `glow`/attention modifier.
- **Decision — "create X" placement:** confirm one rule, e.g. *top-right of the page toolbar, primary variant, label "New <thing>"*. Today placement varies per page.
- Ripple: the **stock-level quick-change button (C8)** and **shopping-cart button (C7)** are their own components built on this base — don't fold them in here; just ensure the base supports them.

---

## PROMPT

You are standardising buttons and page toolbars in a Vue 3 + Quasar SPA (`web_app/`).

### 1. Discover the current state (read first)
- Find existing button usage patterns and any current shared button/toolbar components (`grep` `q-btn`, look in `src/components/`). Note the inconsistencies (sizes, colours, icon vs text, placement of "create/new" actions).
- Read the design tokens (`src/css/tokens.scss`) for sizing/spacing/radius/colour tokens to build on.

### 2. Build the standard components
- Create a `BaseButton` (or extend the existing shared button if one exists) wrapping `q-btn`, exposing variants: `primary | secondary | ghost | danger | icon` and an `attention` modifier (the glow). Sizing/padding/radius/font from tokens — fixed height so all toolbar buttons align. Confirm the variant set with me if unsure.
- Create/normalise a `PageToolbar` layout component: left = title/back, right = action buttons in a consistent gap; the **primary "New <thing>" button sits top-right** with the `primary` variant.

### 3. Migrate
- Replace ad-hoc `q-btn` toolbar buttons across pages with the standard components. Keep purpose-built exceptions (stocktake glow → `attention`).
- Do NOT restyle the stock-level quick button or shopping-cart button here (separate components); just confirm the base supports an icon-only coloured variant they can use.

### 4. Verify
- Toolbars across stock / products / recipes / shopping / meal-plans look consistent (same button height, aligned, same "New" placement). Light + dark both fine.

Output: the new/updated components, a list of pages migrated, and any toolbar that needed a bespoke exception (with reason).
