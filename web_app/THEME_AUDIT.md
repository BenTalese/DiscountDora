# Theme token-compliance audit (A1, STEP 1)

**Date:** 2026-06-04
**Scope:** `web_app/src/**` — `.vue`, `.scss`, `.css`, `.ts`.
**Excluded files** (legitimately hold raw colour values): `css/tokens.scss`,
`css/themes.scss`, `css/colours.scss`, `css/quasar.variables.scss`,
`services/themeService.ts`, `css/motion.scss`.

**What this is:** an offender map + chunk plan for STEP 2 fix work. **No code
changed.** Token *value* tuning (too-bright greens etc.) is **out of scope** — it
lives in A1b. The theme-picker UX split is in Settings (deferred).

---

## 1. Summary counts

| Offender type | Count (non-token files) | Mode-risk profile |
|---|---:|---|
| Quasar palette **classes** in templates — `text-grey`, `bg-red-1`, `text-red-9`, … | 325 | mostly **dark-broken** (fixed greys/light pastels) |
| Quasar palette **props** — `color="white"`, `text-color="grey-9"`, … | 128 | mixed — `"white"` on coloured surfaces usually OK; greys are dark-broken |
| **Hex** literals (raw `#rrggbb` / `#rgb`) | ~36 | mixed — many are intentional brand logos or canvas fallbacks |
| **`rgb()` / `rgba()` / `hsl()` / `hsla()`** literals | 65 | mostly **dark-broken** — pinned light pastels & ink-on-light shadows |
| Inline `:style` colour expressions | 5 | data-vis swatches (chart colours from a JS palette) |
| Bare CSS named colours (`color: white`, …) | 8 | logo/branding intentional in most cases |
| SCSS `$colour` vars outside token files | 0 | clean |
| `setCssVar` writes from non-`themeService` code | 0 | clean |

**Headline:** the dark-mode breakage the feedback (C1) flags is overwhelmingly
two patterns: (a) `text-grey` and `text-grey-N` classes that resolve to a fixed
mid-grey regardless of theme, and (b) `bg-grey-1` / `bg-red-1` / `bg-amber-2`
etc. — Quasar's light pastels that stay light even when `data-theme="*-dark"`
is active.

Dark-broken (high priority) vs consistency (light-only nudge):

| Bucket | ~Count | Notes |
|---|---:|---|
| **Dark-broken** (literally unreadable / wrong surface in any `-dark` theme) | ~430 | All palette classes + `rgba(255,255,255,…)` panels + light-pastel score colours |
| **Consistency** (works in both modes but bypasses tokens) | ~50 | Canvas/EChart hex fallbacks, intentional brand logos, login splash `--lp-*` tokens |
| **Intentional** (brand assets / logo files) | ~15 | Aldi/Coles/IGA/Merchant logos — keep |

---

## 2. Token cheat-sheet

The token map below is what STEP 2 will replace into. Sourced from
`css/tokens.scss` + `css/themes.scss` (5 families × light/dark) +
`services/themeService.ts`.

### Text
| Token | Use for |
|---|---|
| `var(--text-primary)` | Body text, headings — replaces `text-grey-9/10`, `text-black` |
| `var(--text-secondary)` | Secondary copy — replaces bare `text-grey`, `text-grey-7/8` |
| `var(--text-muted)` | Captions, hints, timestamps — replaces `text-grey-5/6` + `text-grey` on captions |
| `var(--text-on-primary)` | Text over brand-primary surface — replaces `text-white` on a brand bg |
| `var(--text-on-toolbar)` | Text on the top header — replaces `text-white` in the toolbar |
| `var(--text-on-accent)` | Text over the brand accent (yellow etc.) |
| `var(--text-inverse)` | Text on dark scrims / chips |

### Surfaces
| Token | Use for |
|---|---|
| `var(--surface-page)` | Page background — replaces `bg-grey-2` page wrappers |
| `var(--surface-component)` | Cards, sheets, dialogs — replaces `bg-white`, `color="white"` cards |
| `var(--surface-elevated)` | Hovered/raised card — replaces `bg-grey-1` elevated rows |
| `var(--surface-sunken)` | Insets, "wells", read-only blocks — replaces `bg-grey-2/3` |
| `var(--surface-toolbar)` + `var(--text-on-toolbar)` | The top header. Theme-defined; do **not** hardcode |

### Brand
`var(--brand-primary[-soft])`, `var(--brand-secondary[-soft])`,
`var(--brand-accent[-soft])`. `*-soft` is the pastel-bg variant.

### Semantic (meaning-bearing)
| Token | Use for | Replaces (typical) |
|---|---|---|
| `var(--semantic-positive)` / `-soft` | OK / done / on-track | `text-green-*`, `bg-green-1`, `#21ba45` |
| `var(--semantic-warning)` / `-soft` | Watch / nudge / low-stock | `text-orange-*`, `text-amber-*`, `bg-orange-1`, `bg-amber-1/2`, `#f2c037` |
| `var(--semantic-negative)` / `-soft` | Error / out / blocked | `text-red-*`, `bg-red-1/2`, `#c10015` |
| `var(--semantic-info)` / `-soft` | Info / hint / explainer | `text-blue-*`, `bg-blue-1` |

### Borders, overlays, focus
`--border-default`, `--border-strong`, `--divider`,
`--overlay-hover`, `--overlay-active`, `--overlay-dim`, `--overlay-scrim`,
`--ring-focus`, `--focus-ring`,
`--elevation-1/2/3`, `--elevation-card`, `--elevation-card-hover`.

### Chart / data-vis
`--chart-1` … `--chart-6` (categorical, theme-defined). Replaces the JS hex
array in `composables/usePriceHistoryPalette.ts` and the `read('--chart-N',
'#…')` canvas fallbacks in `pages/ReportsPage.vue`.

### Hero
`--hero-gradient` (3-stop, per theme) — only consumer is the Dashboard hero
band. Don't compose your own dashboard backgrounds; use this.

### Quasar-compat shim
`css/colours.scss` exposes `--q-page`, `--q-component`, `--q-text`,
`--q-disabled`, `--q-border`, `--q-divider`, `--q-focus`. Prefer the
DS-semantic tokens for new work; the `--q-*` aliases exist for older Quasar
plugins and should be considered legacy.

### What is NOT yet a token (don't invent one — raise it as needs_decision)
- A "danger-ink-on-pastel" token (the exact ink used inside `bg-red-1`).
  Right now components reach for `text-red-9` — see DEC-1.
- A "dora chat gradient" surface. The DoraChat / Dora bubble files compose
  their own `linear-gradient(...rgba(23,176,115,…)…)` — that's the
  Pesto-primary green pinned in. **No theme-aware token for "Dora glow"
  exists.** See DEC-3.
- A "scan overlay state" semantic — green-good / red-bad rings in
  `ScanOverlay.vue` are pinned. Could ride on `--semantic-positive` /
  `--semantic-negative` at low alpha — see DEC-4.
- A login-splash brand-y token set (`LoginPage.vue`'s `--lp-*`). It's
  intentionally its own brand moment — see DEC-2.

---

## 3. Findings — grouped into CHUNKS

Each chunk is a runnable STEP-2 unit. Order chunks A→I roughly by ripple
narrowness. Within a chunk, prioritise the **dark-broken** column.

> Convention: `file:line` followed by the offender pattern. Where a single file
> has many hits of the same shape they're collapsed into a count.

### Chunk A — Auth / shell / always-on chrome (~32 hits + some hex/rgba)

Files: `pages/LoginPage.vue`, `pages/ForgotPasswordPage.vue`,
`pages/ResetPasswordPage.vue`, `pages/VerifyEmailPage.vue`,
`pages/ConfirmEmailChangePage.vue`, `pages/ErrorNotFound.vue`,
`pages/SettingsShell.vue`, `layouts/WelcomeLayout.vue`,
`components/OfflineBanner.vue`, `components/PageErrorState.vue`,
`components/CommandPalette.vue`, `components/AlertsBell.vue`,
`components/menu/MainMenuButton.vue` + `MainMenuButtonStrip.vue`,
`components/PwaInstallPrompt.vue`, `components/ShortcutsCheatsheet.vue`,
`components/FormErrorSummary.vue`.

| Where | Offender | Proposed token | Mode-risk | Light-shift |
|---|---|---|---|---|
| `pages/LoginPage.vue:226-385` | Whole `--lp-*` ladder (`#1f2647`, `#ff7ad9`, `#f5c462`, `#4cd5b7`, `rgba(255,255,255,0.94)`, `rgba(20,12,50,…)`, …) + `color: #fff` | **needs_decision** — DEC-2 | n/a (own splash) | n/a |
| `pages/ErrorNotFound.vue` | `text-grey` (caption) | `var(--text-muted)` | dark-broken | no |
| `components/OfflineBanner.vue:63` | `color: white` (in `.cant-connect` banner) | `var(--text-on-primary)` | consistency | no |
| `components/OfflineBanner.vue:70` | `box-shadow: 0 1px 4px rgba(0,0,0,0.15)` | `var(--elevation-1)` | consistency | no |
| `components/PageErrorState.vue:5,10` | `text-grey` (body2/caption) | `var(--text-muted)` | dark-broken | no |
| `components/PageErrorState.vue:179` | `background: rgba(0,0,0,0.05)` (chip) | `var(--overlay-active)` | dark-broken | maybe |
| `components/CommandPalette.vue:404,428,458,462` | `rgba(255,255,255,0.05/0.08)` & yellow highlight `rgba(255,235,59,…)` | DEC-5 — palette has no "yellow highlight at α" token; closest is `--brand-accent-soft` | dark-broken | no |
| `components/CommandPalette.vue:425` | `rgba(var(--q-primary-rgb), 0.12)` | already token-driven via Quasar var — leave |  |  |
| `components/AlertsBell.vue` (~6 palette classes incl. `text-grey`) | `text-grey` → `var(--text-muted)`; `bg-red-1`/`text-red-9` for "missed" badge → `var(--semantic-negative-soft)` + `var(--semantic-negative)` | dark-broken | no |
| `components/menu/MainMenuButton.vue:39` | `background: rgba(255,255,255,0.08)` (hover state) | `var(--overlay-hover)` | dark-broken | maybe |
| `components/menu/MainMenuButtonStrip.vue:111` | `box-shadow: rgba(242,192,55,0.55)` (amber glow) | DEC-6 — brand-accent glow; could be `0 0 8px var(--brand-accent-soft)` or kept as intentional glow | consistency | no |
| `components/PwaInstallPrompt.vue` | `text-grey-*` | `var(--text-secondary/muted)` | dark-broken | no |
| `components/ShortcutsCheatsheet.vue:85` | `background: rgba(255,255,255,0.06)` (kbd cap) | `var(--overlay-active)` | dark-broken | maybe |
| `components/FormErrorSummary.vue` | `text-red-9` + likely `bg-red-1` | `var(--semantic-negative)` + `-soft` | dark-broken | no |
| `pages/SettingsShell.vue` (2 hits) | grey nav text | `var(--text-secondary)` | dark-broken | no |
| Other auth pages (`ForgotPassword`, `Reset`, `VerifyEmail`, `ConfirmEmailChange`) | misc `text-grey` captions | `var(--text-muted)` | dark-broken | no |

Chunk gotcha: LoginPage's `--lp-*` ladder is wired as a *separate* tiny brand
system; resolve DEC-2 before touching it. Don't blindly substitute global
tokens or you lose the splash treatment that feedback C19 wants to keep.

---

### Chunk B — Stock (~67 hits)

Files: `pages/StockOverview.vue`, `pages/StockItemDetailPage.vue`,
`pages/StocktakePage.vue`, `pages/StocktakeRunner.vue`,
`components/stock/*` (chips/cards), `components/QuickAddSheet.vue`,
`components/ScanOverlay.vue`.

| Where | Offender | Proposed token | Mode-risk | Light-shift |
|---|---|---|---|---|
| `pages/StockItemDetailPage.vue` (17 palette-class hits) | mix: `text-grey-*`, `bg-grey-2` (panel bg), `text-red-9` / `bg-red-1` (danger sections), `text-orange-9` (warning row), `color="grey-7"`/`"grey-3"` props on q-btn / q-icon | `--text-secondary`/`-muted`; `--surface-sunken`; `--semantic-negative` + `-soft`; `--semantic-warning` + `-soft`; `--text-secondary`/`--text-muted` for icon colours | dark-broken | minor |
| `pages/StockOverview.vue` (12 hits) | `text-grey`, `bg-grey-1` row hover, dose chip colours; **`rgba(245,196,98,0)` keyframe at L714** (the lemon-yellow "just-added" pulse) | text → `--text-secondary`; row hover → `--overlay-hover`; pulse keyframe → `var(--brand-accent)` at α 0 (or DEC-7: introduce `--motion-pulse-from`) | dark-broken (pulse is theme-pinned to yellow) | minor |
| `pages/StocktakePage.vue`, `pages/StocktakeRunner.vue` | `text-grey-*`, `bg-grey-1`, stocktake outcome chips | text → `--text-secondary`; bg → `--surface-elevated`; outcome chips → semantic tokens | dark-broken | no |
| `components/stock/*` (chips/cards — small) | bare `text-grey` | `var(--text-muted)` | dark-broken | no |
| `components/QuickAddSheet.vue` (3 hits) | grey captions | `var(--text-muted)` | dark-broken | no |
| `components/ScanOverlay.vue:308,335-346,363-381,387` | `background: #000`, `border-color: #4caf50` / `#ef5350`, `rgba(255,255,255,0.85)`, `rgba(0,80,0,0.45)` / `rgba(80,0,0,0.45)`, `rgba(76,175,80,0.92)`, error `color: #ffb4ab` | DEC-4: introduce or reuse — green/red rings → `var(--semantic-positive)`/`-negative` at low α; black scrim → `var(--overlay-scrim)`; white viewfinder → `var(--text-on-primary)`; success bar → `var(--semantic-positive)`; error tint `#ffb4ab` → `var(--semantic-negative-soft)` | dark-broken (the camera overlay always overlays a video feed though, so contrast is OK; lower priority) | n/a |

Chunk gotcha: Stock's "stock-level chip" is on the C6 *remove* list in the
feedback. **Don't repaint a chip you're about to delete.** If a hit lives on
the chip component, mark it skipped-pending-C6 in the STEP-2 diff rather than
re-themed.

---

### Chunk C — Products / price history / merchant logos (~53 hits + hex)

Files: `pages/ProductSearch.vue`, `pages/MyProductsPage.vue`,
`pages/PriceHistoryPage.vue`, `components/ProductSearchCard.vue`,
`components/PriceHistoryChart.vue`, `components/MerchantLogo.vue`,
`components/AldiLogo.vue`, `components/ColesLogo.vue`,
`components/IgaLogo.vue`, `components/TrendSparkline.vue`,
`composables/usePriceHistoryPalette.ts`.

| Where | Offender | Proposed token | Mode-risk | Light-shift |
|---|---|---|---|---|
| `composables/usePriceHistoryPalette.ts:12-16` | `['#1e88e5','#43a047','#ef5350','#ab47bc','#fb8c00']` categorical palette | `[var(--chart-1), … --chart-5]` (read at runtime from CSS) | dark-broken | maybe |
| `components/TrendSparkline.vue:40` | `last <= first ? '#21ba45' : '#c10015'` | `var(--semantic-positive)` / `var(--semantic-negative)` (read via CSS var) | dark-broken | no |
| `components/PriceHistoryChart.vue:19-77` | SVG `stroke="#eee"`, `fill="#888"`, `stroke="#bbb"` (axis/grid) | `var(--divider)` / `var(--text-muted)` / `var(--border-default)` | dark-broken | minor |
| `components/PriceHistoryChart.vue:307` | `background: rgba(255,255,255,0.97)` tooltip | `var(--surface-component)` (with optional drop-shadow `var(--elevation-2)`) | dark-broken | no |
| `pages/PriceHistoryPage.vue` (8 palette classes + inline `:style` swatch) | `text-grey-*`, `bg-grey-1` graph row hover; swatch `:style="{ background: seriesColour(i) }"` — pulls from JS palette | text → `--text-secondary/muted`; row → `--overlay-hover`; swatch — depends on `usePriceHistoryPalette` fix above | dark-broken | no |
| `pages/ProductSearch.vue` (14 hits) | `text-grey-*`, `bg-grey-1/2`, `color="grey-7"` filter chips | `--text-secondary/muted`, `--surface-elevated/sunken`, `--text-muted` props | dark-broken | minor |
| `pages/MyProductsPage.vue` (11 hits) | same pattern | same mappings | dark-broken | minor |
| `components/ProductSearchCard.vue:138,156-173` | inline `hsl(${hue},90%,${light}%)` (deterministic category bg), `rgba(0,0,0,0.65)` veil, `rgba(255,255,255,0.85)` ribbon, `color: white` | DEC-8: deterministic-category-hash is *intentional* and dark-pinned; the white-on-dark veil/ribbon is also intentional over product imagery (no theme need). Keep but document. Veil → could ride on `--overlay-scrim` | consistency | no |
| `components/AldiLogo.vue:39-41` | `linear-gradient(#f7a600 → #0e306f)` + `text-shadow rgba(0,0,0,0.25)` + `color: white` | **intentional** (Aldi brand) — leave; mark with `intentional?: yes` comment | n/a | n/a |
| `components/ColesLogo.vue:17` | `fill="#E01A22"` | **intentional** (Coles brand) — leave | n/a | n/a |
| `components/IgaLogo.vue:38-39` | `#d61f25` + `color: white` | **intentional** (IGA brand) — leave | n/a | n/a |
| `components/MerchantLogo.vue:66-67` | `#ece1c9` / `#2e2820` initials placeholder | DEC-9: generic merchant placeholder. Could be `--surface-sunken` + `--text-secondary` to ride the theme | consistency | maybe |

Chunk gotcha: anything in this chunk that lives on **product search / merchant
search / comparison** UI is moving to the *companion app* per master Decision
1 — so any rework here is short-lived for Dora-core. **Run minimal-touch
re-theming only** (just fix dark-broken cases); don't refactor structure.

---

### Chunk D — Recipes + cook (~30 hits) — ✅ DONE (2026-06-06)

The ~30 figure was stale: most `text-grey-*` captions/breadcrumbs had already been
migrated to `var(--text-*)` tokens before this chunk ran. The re-verify found only
**4 genuine survivors** (palette literals as `:color` fallbacks), now fixed by
routing the neutral branch through `dora-bg-sunken dora-text-secondary` (chips) /
`dora-text-muted` (icon btn) while keeping the saturated semantic branch (`negative`/
`positive`) on its `color=`/`text-color="white"` props — the theme-stable
white-on-saturated pattern kept since Chunk A:

- `pages/RecipesOverview.vue` — ingredient chip `'grey-3'` → neutral helper class. ✅
- `pages/RecipeDetailPage.vue` — untracked-level chip `'grey-4'` → neutral helper
  class (also fixes the white-on-light-grey contrast bug). `levelColourFor(…)` is
  data-driven stock-level colour, left as-is. ✅
- `components/RecipeCard.vue` — fav heart `'grey'` → `dora-text-muted`; **`'red'`
  kept by user decision** (brand-agnostic favourited affordance, like a like-button).
  Available-meals chip `'grey-7'` → neutral helper class. ✅

`RecipeCookMode.vue` and `RecipeEditDialog.vue` were already clean. The remaining
`text-color="white"` hits sit on saturated semantic surfaces — kept, not offenders.

Files: `pages/RecipesOverview.vue`, `pages/RecipeDetailPage.vue`,
`pages/RecipeCookMode.vue`, `components/RecipeCard.vue`,
`components/RecipeEditDialog.vue`.

| Where | Offender | Proposed token | Mode-risk | Light-shift |
|---|---|---|---|---|
| `pages/RecipeDetailPage.vue` (10 hits — many `text-grey` on captions and breadcrumb router-link) | `var(--text-muted)` for captions, `var(--text-secondary)` for breadcrumb | dark-broken | no |
| `pages/RecipesOverview.vue` (6 hits) | `text-grey-*`, `color="grey-7"` filter glyphs | `--text-secondary/muted` | dark-broken | no |
| `pages/RecipeCookMode.vue` (6 hits) | step counters `text-grey-*`, completed-step row `bg-grey-1` | `--text-muted`, `--surface-elevated` | dark-broken | no |
| `components/RecipeCard.vue`, `components/RecipeEditDialog.vue` | small palette-class set | per-row | dark-broken | no |

Chunk gotcha: feedback B8 says some recipe-detail actions are dead /
substitute swap is broken — that's a **logic** bug (Wave B), don't try to fix
it inside the theme chunk. Just paint.

---

### Chunk E — Meal plans + shopping (~77 hits)

Files: `pages/MealPlansOverview.vue`, `pages/ShoppingListsOverview.vue`,
`pages/ShoppingListDetail.vue`, `pages/ShoppingListShopMode.vue`,
`pages/ShoppingListTemplates.vue`, `pages/ShopNowRedirect.vue`.

| Where | Offender | Proposed token | Mode-risk | Light-shift |
|---|---|---|---|---|
| `pages/ShoppingListDetail.vue` (16 palette classes + `rgba(23,176,115,0.12)` highlight at L2251) | text → `--text-secondary/muted`; row hover `bg-grey-1` → `--overlay-hover`; checked-line `bg-red-1`/`text-red-9` → `--semantic-negative-soft`/`--semantic-negative`; the green hi-light → DEC-3 ("Dora-touched" surface token; closest existing = `var(--brand-primary-soft)`) | dark-broken | no |
| `pages/ShoppingListsOverview.vue` (11 hits + `rgba(0,0,0,0.025)` row at L1136) | text → secondary/muted; bg → `--overlay-active`; "primary list" highlight chip → `--brand-accent-soft` | dark-broken | no |
| `pages/ShoppingListShopMode.vue` (10 hits + `rgba(0,0,0,0.04/0.06)` × 3 panels) | text → muted; surfaces → `--surface-elevated` / `--overlay-active`; **already uses fallback chains `var(--surface-elevated, rgba(0,0,0,0.04))` — drop the literal fallback**, the token always exists in this codebase | dark-broken | no |
| `pages/ShoppingListTemplates.vue` (7 hits) | `text-grey-*` + `bg-grey-1` | `--text-secondary/muted`, `--surface-elevated` | dark-broken | no |
| `pages/MealPlansOverview.vue` (11 hits) | calendar header `bg-grey-2`, day-cell `text-grey-*`, "haven't had recently" tag `bg-amber-1`/`text-amber-9` | bg → `--surface-sunken`; tag → `--semantic-warning-soft`/`--semantic-warning` | dark-broken | minor |

Chunk gotcha: the **Shopping list redesign** (P6-01) is the next phase up from
this — repainting now is fine because the surfaces survive the redesign, but
*don't refactor structure* in a theme-only pass.

---

### Chunk F — Dora + shared widgets (~42 hits incl. hex/rgba)

Files: `components/dora/DoraBubble.vue`, `components/dora/DoraChat.vue`,
`pages/DoraHelpPage.vue`, `pages/HelpPage.vue`, `components/chips/*`,
`components/SelectComponent.vue`, `components/CardComponent.vue`,
`components/settings/*` (shared settings widgets).

| Where | Offender | Proposed token | Mode-risk | Light-shift |
|---|---|---|---|---|
| `components/dora/DoraBubble.vue:396-423,504` | warm-paper gradient `rgba(247,243,234,…)`, Pesto-green halo `rgba(23,176,115,…)`, `box-shadow rgba(23,176,115,0.35)`, `background: white` | **DEC-3** — introduce a "Dora glow" theme-aware token set (`--dora-disc-bg`, `--dora-halo`) | dark-broken (the green halo is pinned to Pesto; other themes look off-brand) | n/a |
| `components/dora/DoraChat.vue:1450,1458-1459,1486-1610` | many `rgba(23,176,115,…)` / `rgba(254,210,36,…)` for chat surfaces + `--c-accent`/`--c-ink-mute` private fallbacks + `background: white` + `border-left: var(--q-warning, #f2c037)` etc. | Same as DEC-3 — Dora-glow token set; private `--c-*` vars should be retired in favour of real tokens | dark-broken | n/a |
| `pages/DoraHelpPage.vue` (6 hits) | grey body, grey caption | `--text-secondary/muted` | dark-broken | no |
| `pages/HelpPage.vue` (7 hits + `rgba(23,176,115,0.06)` / `rgba(254,210,36,0.08)` hero gradient L433-434) | text → secondary/muted; hero gradient → `var(--hero-gradient)` (already exists per theme) | dark-broken | maybe |
| `components/chips/*` | small `text-grey` usage | `--text-muted` | dark-broken | no |
| `components/SelectComponent.vue`, `components/CardComponent.vue` | grey scaffolding | `--text-secondary/muted`, `--border-default` | dark-broken | no |
| `components/settings/*` shared widgets | `text-grey-*` | `--text-secondary/muted` | dark-broken | no |

Chunk gotcha: Dora has the most *aesthetic* dark-mode breakage in the app
(the green glow + warm-paper bubble pinned to Pesto). Resolving DEC-3 is the
prerequisite for this chunk.

---

### Chunk G — Settings (~50 hits)

Files: `pages/settings/AccountSettings.vue`,
`pages/settings/PreferencesSettings.vue`,
`pages/settings/SystemSettings.vue`,
`pages/settings/MerchantsSettings.vue`,
`pages/settings/UsersAdminSettings.vue`,
`pages/settings/AuditLogSettings.vue`,
`pages/settings/AboutSettings.vue`,
`pages/settings/StockLocationsSettings.vue`,
`pages/settings/StockGroupsSettings.vue`.

| Where | Offender | Proposed token | Mode-risk | Light-shift |
|---|---|---|---|---|
| `pages/settings/PreferencesSettings.vue:65,73` | `:style="{ background: hex }"` swatches — this is the **theme picker** rendering each `THEMES[k].swatch[i]` hex | **intentional / DEC-10** — picker *must* show the actual hex of the theme it picks; leave as-is, mark as expected | n/a | n/a |
| `pages/settings/PreferencesSettings.vue` (9 palette classes) | label `text-grey-*`, helper `text-grey-7` | `--text-secondary/muted` | dark-broken | no |
| `pages/settings/SystemSettings.vue`, `…/AccountSettings.vue` (8 + 5 hits) | grey scaffolding | `--text-secondary/muted` | dark-broken | no |
| `pages/settings/MerchantsSettings.vue` (7 hits) | merchant-row `text-grey-*`, `bg-grey-1` zebra | `--text-secondary/muted`, `--surface-elevated` | dark-broken | no |
| `pages/settings/UsersAdminSettings.vue`, `…/AuditLogSettings.vue` (4 + 4 hits) | grey scaffolding | `--text-secondary/muted` | dark-broken | no |
| `pages/settings/AboutSettings.vue` (2 hits) | grey label | `--text-muted` | dark-broken | no |
| `pages/settings/StockLocationsSettings.vue`, `…/StockGroupsSettings.vue` (3 + 3 hits) | grey + small chips | `--text-secondary/muted` | dark-broken | no |

Chunk gotcha: the **theme picker swatches** in `PreferencesSettings.vue` are
the only legitimate "hex in a Vue template" in the app. STEP 2 must **not**
touch them.

---

### Chunk H — Dashboard / reports / waste / data (~95 hits)

Files: `pages/DashboardPage.vue`, `pages/ReportsPage.vue`,
`pages/WastePage.vue`, `pages/DataManagement.vue`, `pages/data/*`,
`pages/TtsTestPage.vue`.

| Where | Offender | Proposed token | Mode-risk | Light-shift |
|---|---|---|---|---|
| `pages/DashboardPage.vue:982-984` | EChart fallbacks `'#6ba368'`, `'#e89a45'`, `'#c85a4f'` — `getPropertyValue(...).trim() \|\| '#…'` | **consistency only** — the `getPropertyValue` *is* the canonical read; the hex is a defensive cold-paint fallback. Leave **but** consider unifying with `ReportsPage.vue`'s read-via-canvas dance | consistency | no |
| `pages/DashboardPage.vue:1620-1621` | `border-left-color: #c10015` (high-priority suggest), `#f2c037` (medium) | `var(--semantic-negative)` / `var(--semantic-warning)` | dark-broken | no |
| `pages/DashboardPage.vue:1360,1401,1886` | `box-shadow rgba(74,56,26,0.25/0.4/0.5)` (Lemon-Tart ink colour pinned in) | DEC-11: should be `var(--elevation-card)` / `--elevation-card-hover` (already theme-defined) | dark-broken | maybe |
| `pages/DashboardPage.vue` (7 palette classes) | mostly `text-grey` body | `--text-secondary/muted` | dark-broken | no |
| `pages/ReportsPage.vue:307-336` | `colourCanvas.fillStyle = '#000'` + `read('--brand-primary','#17b073')`, `read('--chart-1','#17b073')`, etc. | **consistency only** — these are canvas defaults if the CSS var read fails. Leave; consider adding a code comment. The `#000` fillStyle is *just* normalising HSL → RGB through a canvas, not a paint colour | consistency | no |
| `pages/ReportsPage.vue` (≈4 palette classes) | `text-grey-*` | `--text-secondary/muted` | dark-broken | no |
| `pages/WastePage.vue` (11 hits) | grey + `bg-red-1` "wasted" markers | `--text-secondary/muted`, `--semantic-negative-soft` | dark-broken | no |
| `pages/DataManagement.vue`, `pages/data/*` (BackupRestore, BarcodesQR, DataImport, ExportPrint) (~32 hits) | grey scaffolding, danger-styled destructive buttons, `bg-amber-1` warnings | `--text-secondary/muted`; `--semantic-negative` + `-soft`; `--semantic-warning-soft` | dark-broken | no |
| `pages/TtsTestPage.vue` (7 hits) | grey + chip colours | `--text-secondary/muted`, semantic tokens | dark-broken | no |

Chunk gotcha: Dashboard + Reports do *both* CSS-token reads **and** raw-hex
fallbacks for canvas/EChart. Treat the fallback hexes as
**consistency-only** — they're never the painted colour at runtime if the
token exists, which it always does in this codebase. Don't churn them just
because grep flagged them.

---

### Chunk I — Onboarding (~11 hits) — ✅ ALREADY COMPLIANT (2026-06-06)

**No code change needed.** This row is stale: `WelcomeWizard.vue` was rewritten
after the 2026-06-04 audit (the colour-coded step-list became a single
`q-linear-progress` bar), so the 11 palette offenders below no longer exist. A
fresh grep of the current file finds zero palette classes / hex / `rgb(a)` /
palette `color=` props — every colour reference is a semantic theme token
(`dora-text-secondary/muted`, `text-negative` on `dora-bg-negative-soft`,
`color="primary"`, `var(--overlay-active)`, `var(--q-primary)`). Chunk closed.

Files: `pages/onboarding/WelcomeWizard.vue`.

| Where | Offender | Proposed token | Mode-risk | Light-shift |
|---|---|---|---|---|
| `pages/onboarding/WelcomeWizard.vue` (11 palette classes) | step `text-grey-*`, completed-step `bg-green-1` / `text-green-9` checkmark, current-step `bg-amber-2` / `text-amber-9` highlight | text → `--text-secondary/muted`; complete → `--semantic-positive[-soft]`; current → `--brand-accent-soft` / `--text-on-accent` (the on-accent text token is precisely for amber/yellow surfaces) | dark-broken | minor |

Chunk gotcha: feedback `B5` calls out dead nav buttons in onboarding — same
"don't fix structure during paint" rule as the other chunks.

---

## 4. `needs_decision`

These are the design calls STEP 2 needs resolved before it can pick a token.
Group them together so you can answer them in one sitting; each chunk
references the DEC- IDs above.

- **DEC-1 — "danger ink on pastel" pair.** Components reach for `text-red-9`
  on top of `bg-red-1`. The semantic token pair is `--semantic-negative` (ink)
  + `--semantic-negative-soft` (bg). Is the existing `--semantic-negative` ink
  readable on `--semantic-negative-soft` in **every** theme, esp. the dark
  ones? If not, we need a `--semantic-negative-on-soft` token. *Same question
  applies to positive / warning / info pairs.* (Recommendation: assume yes,
  spot-check during STEP 2's per-chunk light+dark eyeball, file findings to A1b.)
- **DEC-2 — LoginPage `--lp-*` ladder.** Three options:
  (a) **Keep it as-is** (intentional separate splash brand — feedback C19
  wants a shared *auth-shell style* but doesn't say the colours must come from
  the main token system).
  (b) **Fold into tokens** (`--lp-bg-base` → `--surface-page`, etc.) — losing
  the deep-midnight blob aesthetic.
  (c) **Promote `--lp-*` into themes.scss** so each theme can override its own
  splash (the right answer if you want themed splashes long-term).
  Recommendation: **(a) — keep**, mark `intentional?: yes`, revisit when C19's
  shared auth-shell is designed.
- **DEC-3 — Dora glow / chat surfaces.** Today: pinned to Pesto-green
  (`rgba(23,176,115,…)`) and warm-paper (`rgba(247,243,234,…)`). Options:
  (a) Introduce `--dora-disc-bg`, `--dora-halo`, `--dora-halo-strong` per
  theme (probably best — Dora's vibe should breathe with the theme).
  (b) Lock Dora visually to Pesto regardless of theme (current effect; not
  ideal — Dora looks alien in Cherry Cola / Blueberry).
  (c) Hand the chat panel `var(--brand-primary-soft)` (close enough, no new
  tokens — but loses the deliberate halo gradient).
  Recommendation: **(a)** — small, isolated addition; let A1b tune values.
- **DEC-4 — ScanOverlay state rings.** Options:
  (a) Reuse `--semantic-positive`/`-negative` at low α (token expressions
  with `color-mix(in srgb, var(--semantic-positive) 45%, transparent)` if
  acceptable, or via `hsl(from var(--semantic-positive) h s l / 0.45)`).
  (b) Add explicit `--scan-state-good` / `--scan-state-bad` tokens.
  (c) Leave hard-coded (the camera fills the background, contrast is fine).
  Recommendation: **(c)** — lowest priority dark-broken case; revisit only
  if QR/scan surfaces become more prominent.
- **DEC-5 — CommandPalette search highlight.** `rgba(255,235,59,0.4)` for the
  matched-substring highlight. Token? Closest existing is `--brand-accent-soft`
  (yellow-ish in Pesto/Lemon-Tart, but not in Cherry/Blueberry — those would
  highlight in red/blue, which arguably is *better* than fixed yellow).
  Recommendation: use `--brand-accent-soft`; flag for A1b value tuning.
- **DEC-6 — Amber accent glow.** `MainMenuButtonStrip` uses
  `box-shadow: 0 0 8px rgba(242,192,55,0.55)` — the Lemon-Tart accent glow.
  Same shape as DEC-5: use `var(--brand-accent)` at low α, or `--brand-accent-soft`.
- **DEC-7 — "Just-added pulse" keyframe colour.** `StockOverview:714` —
  `rgba(245,196,98,0)` (Lemon-Tart amber) inside a `@keyframes pulse`. Options:
  (a) `var(--brand-accent)` — pulses in theme colour.
  (b) Add `--motion-pulse-accent` token. Recommendation: **(a)**.
- **DEC-8 — ProductSearchCard category swatch.** Deterministic hash → HSL.
  Intentional — gives products stable category colours independent of theme.
  Recommendation: **leave**; mark `intentional?: yes`. *But* the
  `rgba(0,0,0,0.65)` veil over the product image could ride
  `var(--overlay-scrim)` — low priority since the card is moving to the
  companion app (master Decision 1).
- **DEC-9 — Merchant placeholder colours.** Generic `#ece1c9` / `#2e2820`
  initials block in `MerchantLogo`. Should it shift with the theme
  (`--surface-sunken` + `--text-secondary`) or stay stable (current —
  intentional kraft-paper aesthetic)? Recommendation: stable. Low priority.
- **DEC-10 — Theme-picker swatches.** Hex inline in
  `PreferencesSettings.vue`. **Always leave.** Documented here so STEP 2 doesn't
  trip over it.
- **DEC-11 — Dashboard box-shadow ink.** Pinned to Lemon-Tart's warm brown
  `rgba(74,56,26,…)`. Replace with `var(--elevation-card)` /
  `--elevation-card-hover` (already exists per theme). High-priority dark fix.

---

## 5. Out-of-scope but spotted (A1b — token value tuning)

These are things to remember when token *values* get tuned. **Not part of
A1.**

- The feedback complains about "too-bright greens." Inspect:
  - `--semantic-positive` defined as `hsl(140 50% 45%)` in `tokens.scss`;
    each theme also redefines positive — Pesto Dark and Cherry Cola Dark go
    `hsl(150 75% 55%)` / `hsl(98 60% 60%)`, which read very saturated.
  - Pesto Dark's `--brand-primary: hsl(150 75% 55%)` is the brightest green
    in the app and probably the "too bright" complaint.
- `--semantic-warning` is `hsl(33 95% 55%)` (Pesto/light) but Lemon-Tart Dark
  overrides to `hsl(46 100% 55%)` (pure yellow); may clash with text-on-it.
- `--text-muted` in Pesto is `hsl(168 8% 50%)` — borderline AA against
  `--surface-page` `hsl(168 38% 94%)`. Worth a contrast pass.
- Pesto Dark's `--surface-page: hsl(165 60% 5%)` is *very* dark (deep forest
  black) — visually striking but text-muted may need lifting.
- The `--ring-focus` value is hardcoded to a Pesto-green α; not redefined
  per theme — focus rings flash Pesto green even on Cherry Cola Dark.
- LoginPage `--lp-shadow` `rgba(20,12,50,0.55)` is Lemon-Tart brown'd; if
  DEC-2 resolves to (c) "promote to themes", tune per theme.

---

## 6b. Discovered during STEP 2 — token-system gaps (file for A1b)

These came up while running Chunk A and can't be fixed by template rewrites
alone; they need additions to `tokens.scss` / `themes.scss` which are out of
scope for A1. **Not blockers** for further chunks — same patterns will recur
and same deferral applies.

- **DEC-A-1 — Hover overlay on dark/toolbar surfaces.** `--overlay-hover` is
  defined as a *dark* veil (`hsla(168,30%,10%,0.04)`) which is invisible on
  dark surfaces. Components currently work around it with `.body--dark`
  blocks pinning `rgba(255,255,255,0.05-0.08)`. Residuals:
  `components/menu/MainMenuButton.vue:39`,
  `components/CommandPalette.vue:404`, `:428`,
  `components/ShortcutsCheatsheet.vue:85`.
  **Fix path:** add `--overlay-hover` overrides in each `[data-theme="*-dark"]`
  block (white-veil at low α) **and** add a new
  `--overlay-hover-on-coloured` token for hover states that sit on saturated
  brand surfaces (toolbar). Then delete the `body--dark` overrides.
- **DEC-A-2 — Search-result highlight.** `CommandPalette.vue:458,462` paints
  matched substrings with `rgba(255,235,59,0.4)` light / `0.25` dark.
  DEC-5 mapped this to `--brand-accent-soft` but that's a *solid* pastel — it
  shades the line rather than highlighting the substring. **Fix path:** add
  a `--highlight-search` token, theme-defined at low α (so text still reads
  through it). Until then the existing rgba reads correctly in both modes.

---

## 6a. Resolved decisions (2026-06-04)

All 11 DEC items resolved by the user. STEP 2 chunks should be filled in with
these answers when the per-chunk fix prompt is run.

| DEC | Resolution |
|---|---|
| DEC-1 (semantic ink-on-soft contrast) | **Assume OK; verify per-chunk during light+dark eyeball.** Any failures get filed to A1b. |
| DEC-2 (LoginPage `--lp-*`) | **(a) Keep as-is — intentional splash brand.** Do not touch in STEP 2 Chunk A. Revisit when feedback C19 (shared auth-shell) is designed. |
| DEC-3 (Dora glow) | **(a) Introduce theme-aware Dora tokens.** Add `--dora-disc-bg`, `--dora-halo`, `--dora-halo-strong` to `tokens.scss` defaults + per-theme overrides in `themes.scss`. Chunk F is **blocked on this token addition** — do it as a prerequisite step at the start of Chunk F. A1b tunes the values per theme. |
| DEC-4 (ScanOverlay rings) | **(c) Leave hardcoded.** Lowest priority; camera fills the bg so contrast is fine. |
| DEC-5 (CommandPalette highlight) | Use `var(--brand-accent-soft)`. Flag for A1b value tuning if Cherry Cola / Blueberry highlight reads weirdly. |
| DEC-6 (Amber menu glow) | Use `var(--brand-accent)` at low α (`box-shadow: 0 0 8px color-mix(in srgb, var(--brand-accent) 55%, transparent)`, or equivalent). |
| DEC-7 ("just-added" pulse) | Use `var(--brand-accent)` in the keyframe. |
| DEC-8 (ProductSearchCard category hash) | **Leave** — deterministic-hash swatch is intentional. The `rgba(0,0,0,0.65)` veil over the image stays too (low priority; surface is companion-bound). |
| DEC-9 (Merchant placeholder) | **Leave** — kraft-paper aesthetic stable across themes. |
| DEC-10 (Theme-picker swatches) | **Always leave.** STEP 2 must not touch `pages/settings/PreferencesSettings.vue:65,73`. |
| DEC-11 (Dashboard box-shadow) | Replace pinned `rgba(74,56,26,…)` with `var(--elevation-card)` / `var(--elevation-card-hover)`. |

---

## 6. How STEP 2 should be run

For each chunk A→I:

1. **Confirm decisions.** Read §4. STEP 2's per-chunk prompt template should
   be filled with the resolved DEC values.
2. **Run STEP 2 fix prompt scoped to that chunk only.** Do not let it touch
   files outside the chunk's named list.
3. **Eyeball both `pesto` (light) and `pesto-dark`** (and ideally a third,
   non-default theme — Cherry Cola Dark catches Pesto-pinned ink fastest)
   for each chunk before moving on.
4. **Log per-chunk completion in `DORA_WORKLOG.md`** with: chunk, files
   touched, decisions applied, any new `needs_decision` discovered.

Chunks are roughly ordered narrowest-ripple → widest:
A (auth/shell) → I (onboarding) → D (recipes) → G (settings) → C
(products — minimal-touch, companion-bound) → B (stock) → E (meal-plans +
shopping) → H (dashboard + reports + data) → F (Dora — gated on DEC-3).
