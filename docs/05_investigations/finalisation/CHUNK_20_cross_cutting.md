# Chunk 20 — Cross-cutting concerns

**Session:** 2026-10-23 overnight (solo, no subagents) · **Stage:** 1 (analysis only — no code changed)
**Surface:** the layers every page stands on — the **formatting authorities** (`useMoney` + `useDateFormat` → `/health.locale_policy`; `formatQuantity`/`scaleQuantity` ↔ `domain/units.py`; FU-043 Layers A/B), the **theme system** (`css/tokens.scss` 127 tokens, `css/themes.scss` 7 families × light/dark, `themeService`, `useThemePalette`, `boot/theme.ts`, `boot/fonts.ts`, text-size scale — FU-025/13-D4), **colour usage** (FU-224, FU-671, FU-674 — recorded here as the consolidated sweep list), the **error layer** (`boot/globalErrorHandler.ts`, `useClientLogger`, `ErrorBoundary`/`PageErrorState`/`ErrorServer`/`ErrorPageNotFound`, `rollbackRegistry`, `apiErrorHandler` + `useFormErrors`/`FormErrorSummary`; server `submit_client_log.py`, `error_translation.py`, `api_response.py`), **toasts** (`notifyTypeRegistration.ts`, B7/D-009), **skeletons** (`AppSkeleton`, D-007), **keyboard shortcuts** (`useShortcut`, `ShortcutsCheatsheet`, 21 registered keys), **help primitives** (`HelpHint`, `InfoTip`, the `?q=` deep link), the dormant **vue-i18n** boot, and the **Base\*** primitives whose adoption is still partial (`BaseSegmented`/`DoraSegmented` FU-848, `BaseSelect` FU-675, raw `q-btn`/`q-dialog`). It also **collects the app-wide sweeps earlier chunks deferred here**: `useConfirm` (13-R26/16-R22/18-R9), the two focus-ring tokens (13-R40), the image-cap literal ×9 (16-R11), the `.settings-*` CSS copies (13-R9/18-R13), FU-654's session-key sweep (15-R14), FU-923's raw-table list.
**Boundaries:** PWA shortcuts/manifest → chunk 17 (done); security headers + CSRF → chunk 15; the Help *page* content per surface → each chunk's §B; `DoraBot` feedback → chunk 11; `units.py` conversion maths → chunk 1/11 (only the two duplicated lists are examined here); FU-010/FU-224 themselves stay the owner's late-game visual review — this chunk hands them a verified inventory, not a verdict.

---

## 0. Reading list + files walked

**Governing docs read:** `DESIGN_STYLE_GUIDE.md` A1–A8, B1–B12, D-001…D-025 (headings + D-002/003/004/006/007/008/009/014/015/016/017/019 bodies); `DESIGN_REMEDIATION_PLAN.md` (DR-1 ➗ — DR-1b component spots remain; DR-13 P3 open; DR-16 P3 owner call; the rest ✅/➗); `PROPOSAL_LOCALE_I18N.md` (§3 **closed** 2026-07-06: install-wide currency+locale; vue-i18n "adopt-lite"; Layer C deferred); `FINALISATION_PLAN.md` §3 (hand-rolled-vs-library list), §4 row 20; feedback `# NO AREA / MISC` (21), `# HELP` (5), `# MOBILE VIEW` (0). Open FUs: FU-010, FU-224, FU-671, FU-674, FU-675, FU-692, FU-848, FU-836, FU-841, FU-663, FU-632 (#7b theme mechanism), FU-844, FU-920, FU-923. Resolved and consulted: FU-043/368 (locale), FU-025?→ not in the ledger (text-size feedback is tracked as 13-D4), FU-099 (error shape), FU-370 (support channel), FU-539 (resilience specs), FU-578 (DR-14), FU-824/833 (theme palette reactivity), FU-614 (font prefs), FU-027.

**Files walked in full (SPA 2,082 · styles 1,599 · backend 449 + `units.py` head/outline):**

| File | Lines | Role |
|---|---|---|
| `web_app/src/boot/{theme,i18n,fonts,notifyTypeRegistration,globalErrorHandler,quasarScreen}.ts` | 28·41·10·49·74·8 | boot layer |
| `web_app/src/composables/{useMoney,useMoneyEnabled,useDateFormat,useThemePalette,useShortcut,useClientLogger,useFormErrors}.ts` | 145·25·118·133·139·127·80 | authorities + infra composables |
| `web_app/src/components/{ErrorBoundary,PageErrorState,ShortcutsCheatsheet,AppSkeleton,FormErrorSummary,BaseSegmented,BaseToggleGroup}.vue`, `pages/errors/{ErrorPageNotFound,ErrorServer}.vue`, `components/help/{HelpHint,InfoTip}.vue` | 60·207·81·71·21·124·165·16·24·35·72 | primitives |
| `web_app/src/services/errorHandling/{apiErrorHandler,rollbackRegistry}.ts`, `helpers/{formatQuantity,scaleQuantity}.ts` | 137·26·51·96 | — |
| `web_app/src/css/{tokens,themes,colours,quasar.variables}.scss` (+ `app.scss` outline) | 1,599 | token + theme layer |
| `dora_api/features/client_logs/submit_client_log.py`, `infrastructure/{error_translation,api_response}.py`, `domain/units.py` (:1–80, outline, :483–507, :617–642) | 125·90·231·823 | — |
| `web_app/src/services/themeService.ts:318–330`, `pages/settings/PreferencesSettings.vue:139–152`, `AdminSystemRegionSettings.vue` (outline), `layouts/MainLayout.vue:75–85, 204–223`, `pages/HelpPage.vue` (filter/`?q=`) | — | consumers |

**Tests read (names):** vitest `formatQuantity`, `scaleQuantity`, `useThemePalette`, `globalErrorHandler`, `errorBoundary`, `rollbackRegistry`, `useUnsavedChangesGuard`, `cardLoadError`, `baseSelect` (9), `weekDates`; pytest `test_client_logs` (13), `test_error_translation` (6), `test_locale_currency` (6), `test_security_headers` (3), `test_api_fuzz` (7 — every mutating route × malformed body never 500s). **No** spec for `useMoney`, `useDateFormat` (the D-006 authority), `useShortcut`, `notifyTypeRegistration`.

**Verification greps run (the app-wide counts Stage 2 will work from):**

| Pattern | Count | Note |
|---|---|---|
| `installGlobalErrorReporting(` callers | **0** | second global installer in `useClientLogger.ts:97–127` is dead; `boot/globalErrorHandler.ts` is the live one |
| `useI18n\|$t(\|i18n.global` | **0** | `vue-i18n` (^11) + `boot/i18n.ts` + `src/i18n` (12 lines) have no consumer; `useMoney.ts:13` says values "are fed into vue-i18n's numberFormats" — `boot/i18n.ts` sets none |
| `_NO_SPACE_UNITS` (`units.py:483–484`) vs `NO_SPACE_UNITS` (`formatQuantity.ts:9`) | 2 copies | comment: "MUST stay in sync … over there" — a declared two-language duplicate; `units_table.ts` is already codegen'd from this module |
| `SUB_ITEM_UNITS` (`units.py:617`) vs `COUNTABLE_UNITS` (`scaleQuantity.ts:20`) | 2 lists, overlapping (clove, sprig, slice, knob) but **different** (server: rasher/stalk/floret/leaf/wedge/splash/drizzle/handful; client: egg/scoop/piece/stick/can/bunch/pinch) | two answers to "is this a countable unit" |
| `$q.dialog(` | **50 sites / 26 files**; `html: true` ×4; `persistent: true` ×5 | no `useConfirm` composable exists |
| `text-color="white"` | **24 / 16 files** | FU-671 (17 sites when raised; grew) |
| bare icon strings `name="…"`/`icon="…"` not via `ICONS` | **48 sites**; **12 of them in shared primitives** (`SettingsSection` 3, `SettingsRow` 2, `SettingsPageHeader` 2, `BaseDialog` 2, `CollapsibleCard` 2, `DashboardCard` 2, `FilterBar` 3, `MealPlanRailDisclosure` 2) + `PageErrorState` 4 | A7 |
| hex literals in `.vue` | 55 / 16 files; outside the DEC-2 auth ladder (chunks 14/15): `RecipeNutriScore` (official grade colours — legit), `ScanOverlay:403,436,440,496`, `ImageEditTile:163`, `DoraModeSlider:142`, `VoicePicker:484–485` (`--negative` is not a token name), `DashboardPage:998–1000` + `ReportsPage:288–293` (`paletteToken` fallbacks) | D-017/R-002 |
| `var(--focus-ring)` / `var(--ring-focus)` | 25 / 8 | both defined at `tokens.scss:153–154`; `--ring-focus` overridden in **5 of 14** theme blocks only → 9 themes inherit the Pesto-green halo (13-R40) |
| `--text-on-primary` | 14 definitions; **5 themes set pure white** (pesto, blueberry, cherry-cola, salt-pepper + one more) | FU-674 measured pesto 3.88, blueberry 4.21, midnight 2.86 |
| `outline: none` | **21 sites / 15 files** | A6 / D-016 (FU-841 is one) |
| `position: '…'` on toasts | `bottom-right` 269 · `top` 23 · `bottom` 2; no default in `quasar.config` | D-009 placement budget: two conventions |
| `<q-select` raw / `<BaseSelect` | 47 / 30 | FU-675 backlog |
| `<q-btn` raw / `<BaseButton` | 10 / 542 | 4 are wrappers; stray: `DoraChat`, `SortControl`, `HelpPage` ×3, `StocktakeRunner` |
| `<q-dialog` raw / `<BaseDialog` | 9 / 66 | 1 wrapper; stray: `AlertsBell`, `MealPlanPickerSheet`, `ScanOverlay`, `SwapSuggestionsPanel`, `PutAwayDialog`, `RecipeCookModeImageView`, `MarkOpenExpiryDialog`, `NutritionFoodPicker` |
| `DoraSegmented` / `BaseSegmented` consumers | 9 / 13 | FU-848 |
| `col-lg-*` | 2 (`MyProductsPage:336`, `RecipesOverview:456`) | FU-836 |
| `credentials: 'include'` raw fetch | 21 | 18-R7 (17) + `useClientLogger` (1, deliberate) + FU-647 (3) |
| `toFixed(2)` | 7 | money: `MealPlanBuilderDialog.vue:697` `$${n.toFixed(2)}` (**bypasses `formatMoney`** — hard-coded `$`); the rest are sizes/quantities |
| raw `.toLocaleDateString(` | 1 (`ReportsPage.vue:369`) | bypasses `useDateFormat` (D-006) |
| `new Intl.Collator('en', …)` | 5 (`useStockFilters`, 4 stores) | sort collation hard-codes `'en'` while display locale is the household's |
| `SESSION_USER_ID_KEY` literal `"user_id"` | `submit_client_log.py:63` (+15-R14's 4) | FU-654 class |
| shortcuts registered | Global 7 (`?`, `/`, `g s/l/r/d/h`) · Stock overview 9 · Shopping list 5 | `useShortcut` callers: 3; no Help entry mentions shortcuts (grep `shortcut\|keyboard` in `HelpPage.vue`: 0) |
| `HelpHint` / `InfoTip` consumers | 3 / 10 | the chips earlier chunks propose (≈25) would be the first real adoption of `HelpHint` |

---

## A. Full Systems Test — cross-cutting

### A1. Preconditions
- Every theme family × light/dark (14) available from Settings → Preferences; `prefers-reduced-motion` and `prefers-color-scheme: dark` at the OS; text size each of the four steps.
- Install locale set to `en-AU` then `en-US` (Settings → Admin → System → Region), currency `AUD` → `USD` → `JPY`.
- A way to break a page (DevTools: throw in a component) and to make the API return 500 / go away.
- Phone (360×640) + 1920 desktop; a hardware keyboard.

### A2. Golden path (persona: a household member, any page)
| # | Step | Expect |
|---|---|---|
| G1 | Switch theme in Preferences | Every surface recolours live, including SVG/charts (donut, price chart, Reports) — `useThemePalette` version bump; no reload. Quasar palette (`--q-primary` etc.) follows. |
| G2 | Switch text size Small → Extra large | Root font-size 14 → 16.5 → 20.5 → 23 px; every rem-based text scales; icon-only controls keep 44 px targets; no page gains a horizontal scroll at 360 px. |
| G3 | Change locale to `en-US` and currency to `USD` | Within one health refresh every money render reads `$1,234.56` US-style and every date `7/17/2026`; the Region page preview matches; dates stay the **same calendar day** west of Greenwich (local-midnight parse). |
| G4 | `JPY` | Still renders 2 decimals (`¥1,234.00`) — documented limitation in `useMoney.ts:45–48`. |
| G5 | Press `?` | Cheatsheet lists Global + the current page's scope; `/` focuses search; `g s` navigates; keys are ignored while typing in an input. |
| G6 | Submit a form with a bad field | Inline `error-message` on the field (friendly copy from `error_translation`), `FormErrorSummary` for general errors, toast caption "Couldn't save. Check the highlighted fields. · ref: abcd1234". |
| G7 | Force a render error on a page | `ErrorBoundary` → `PageErrorState` ("Something went wrong on this screen.") with Reload / Go to dashboard / Report this (when a support channel is set); the layout shell + Dora bubble survive; navigating away clears it; one `oopsie` toast; one `POST /api/client-logs` (rate-limited 10/min). |
| G8 | API 500 on a list | Global toast once; the card shows its error state (DR-8), not an empty state. |
| G9 | Any list loading | Skeletons mimic the layout (`AppSkeleton`), never the word "Loading…" or placeholder titles (D-007). |
| G10 | Trigger 5 toasts quickly | They stack bottom-right (the 269-site convention); offline/online and PWA toasts come in at `top` (the 23-site convention) — two conventions visible at once (20-R10). |
| G11 | Tap a `(?)` chip | `HelpHint` deep-links to Help with `?q=<title>` and the matching guide expanded; `InfoTip` shows its tooltip instantly (0 ms). |

### A3. Edge cases
- Browser locale ≠ install locale → install wins for money and dates; **sorting** still collates with `'en'` (20-R7).
- `/health` unreachable at boot → money renders AUD/en-AU defaults, dates en-AU, flags false → gated cards hide (FU-844's race class).
- Theme set to a dark family + OS light, and vice versa; `system-*` keys follow the OS; signed-out → brand default light (`boot/theme.ts`).
- A toast fired while another theme is applying → `.dora-toast--info` keeps reading tokens (VERIFY 2026-08-28 bullet still open).
- Error in a boot file before `globalErrorHandler` loads → console only (documented).
- `ResizeObserver loop` notice → filtered (no toast, no rollback).
- Shortcut sequence `g` then a pause > 1 s → prefix dropped; `g` then `s` while an input is focused → ignored.
- Focus-visible ring on a button in `sourdough-dark` → ring halo is Pesto-green (20-R8) because `--ring-focus` isn't overridden there.
- `Esc` with the cheatsheet open closes it; with a `persistent: true` confirm open does nothing (5 sites).
- Text at `sm` (14 px root): captions at `--font-size-xs` ratio drop below the 12 px floor? (`0.75 × 14 = 10.5 px` — D-003 check, 20-R12).

### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (defaults) | ✓ (skeletons, toast stacking) | – | ✓ (shortcuts) | ✓ (Region/locale) | ✓ (per-user theme/text size) | ✓ (support channel → Report this) | ✓ |

### A5. Load-bearing conditions
- **All 14 themes × light/dark** (G1, FU-674/671 contrast); **reduced-motion** (skeleton pulse off, motion tokens); **360×640** at `xl` text (G2); **1920+**; **bad network** (G8, client-log rate limit); **keyboard** (G5).

### A6. Release-gate rows
1. G1 + G2 on every theme at `xl` text, phone width — no clipped labels, no h-scroll, focus ring visible and brand-matched.
2. G3 locale flip — no `$`/`toFixed`/US-date leaks (20-R6, R7 fixed).
3. G6–G8 error path end-to-end with a `ref:` id that matches a server log line.
4. Contrast spot-check of `warning`/`negative` chips and segmented active labels in pesto, blueberry, midnight (FU-671/674).

---

## B. Help content — cross-cutting

### B1. Current help audit
- `HelpPage.vue` has a search filter and the `?q=` deep link (navigable — feedback `# HELP` #4 ✓), 28 entries across 6 groups; after chunks 1–19 there are **~105 new entries + 8 rewords** proposed, which outgrows a flat list (20-D4). There is **no FAQ/Q&A section** (`# HELP` #3) — the *Dora itself* group already uses question-shaped titles, so the shape exists. No screenshots or diagrams anywhere (`# HELP` #5 — owner offered to provide).
- **Keyboard shortcuts** have a cheatsheet (`?`) but no Help entry — the only discoverability is knowing `?`.
- Theme / text size / fonts: one entry ("Theme, font, and text size", chunk 13 rewords it); nothing about what "System" means or why the login page is always light.
- Locale/currency: no entry (admin Region page has inline help; members have nothing explaining why dates look the way they do).
- Error toasts and the `ref:` id: nothing tells a user what the eight-character reference is for.

### B2. Help entries

#### Keyboard shortcuts
- **Group:** Getting around
- **What it does:** Press `?` anywhere to see every shortcut that works on the screen you're on. Always: `/` focuses search, `g` then `s`/`l`/`r`/`d`/`h` jumps to Stock, Lists, Cookbook, Dashboard, Help. Stock Overview and a shopping list add their own (`n` new, arrows to move, `Space` to tick, `u` untick last, `Enter` open).
- **When it fires / how to trigger it:** Any time you're not typing in a field. Two-key sequences give you a second to press the second key.
- **What controls it:** Always on — no setting; shortcuts never use Ctrl/Cmd so they can't collide with the browser's.
- **What it costs / might get wrong:** Nothing on a phone (no keyboard). The command palette is gone on purpose; `?` is the one place to look.
- **Related:** —
- **Chip:** none (`?` is the surface).
- **Source:** `useShortcut.ts`, `MainLayout.vue:204–223`, `StockOverview.vue:1010–1018`, `ShoppingListDetail.vue:2166–2170`.

#### How Dora shows dates, money and units
- **Group:** Getting around
- **What it does:** Every date, price and unit in the app follows the **household's** region (Settings → Admin → System → Region), not your browser's: `17/07/2026` and `$12.50` on an Australian install, `7/17/2026` on a US one. Metric or US units drive which units the pickers offer. A calendar date is always the day it names, whatever your timezone.
- **When it fires / how to trigger it:** Automatically, everywhere, after the admin saves the region.
- **What controls it:** Admin only; members can't override it per account (a household shares one format).
- **What it costs / might get wrong:** Prices always show two decimals, even for currencies that don't use them. If Dora can't reach the server at startup it falls back to Australian formatting until it can.
- **Related:** Region settings (chunk 13) · Where Dora keeps your data (chunk 19).
- **Chip:** `AdminSystemRegionSettings.vue:4` (page header) → `<HelpHint topic="How Dora shows dates, money and units">`.
- **Source:** `useMoney.ts`, `useDateFormat.ts`, `/health.locale_policy`, `units_for_system`.

#### Themes, dark mode and text size
- **Group:** Settings & admin *(extends the existing "Theme, font, and text size" entry — chunk 13 rewords it; this is the fuller version)*
- **What it does:** Pick a colour family (Pesto, Lemon Tart, Blueberry, Cherry Cola, Sourdough, Salt & Pepper, …) and whether it follows your device's light/dark setting or stays fixed; pick a font and one of four text sizes. Every page, chart and toast follows.
- **When it fires / how to trigger it:** Settings → Preferences; per account, remembered across devices.
- **What controls it:** `/settings/preferences`.
- **What it costs / might get wrong:** The sign-in page is always the light brand look (nobody is signed in yet). "System" follows the OS only after you've chosen a theme once.
- **Related:** Keyboard shortcuts.
- **Chip:** none.
- **Source:** `themeService.ts`, `boot/theme.ts`, `themes.scss`.

#### "Something went wrong" and the reference code
- **Group:** Dora itself
- **What it does:** When a save fails, Dora highlights the field and says why. When a screen breaks, it shows a recovery page with **Reload**, **Go to dashboard** and (if the operator set one up) **Report this**. A short code like `ref: 3f9a2c1b` on an error is the id of that exact request in the server log — quote it when you report a problem.
- **When it fires / how to trigger it:** Automatically.
- **What controls it:** Always on. Browser-side crashes are also sent to the server log (a few per minute at most).
- **What it costs / might get wrong:** Reloading loses unsaved typing. If the server itself is down you'll see the red connection strip instead (chunk 17).
- **Related:** Reporting a problem (chunk 19) · Use Dora when the connection drops (chunk 17).
- **Chip:** none.
- **Source:** `PageErrorState.vue`, `apiErrorHandler.ts`, `log_context.py`, `submit_client_log.py`.

### B3. DoraBot corpus delta
Add to `APP_OVERVIEW`:
> - Keyboard: `?` shows the shortcuts for the current screen; `/` focuses search; `g` then `s`/`l`/`r`/`d`/`h` jumps between the main areas.
> - Formatting: dates, prices and units follow the household region the admin set, not the browser.
> - Errors: a `ref:` code on an error identifies that request in the server log — include it when reporting.

---

## C. Senior review — cross-cutting

### C1. Bugs (verified or high-confidence latent)

**20-R1 — A second global error installer is dead code, and the live one's twin claims it is "called from boot".** class: verified · where: `useClientLogger.ts:93–127` `installGlobalErrorReporting(app)` — **no caller** (grep); its docstring (:10–13) says "`install()` (called from boot) wires global error handlers"; the real wiring is `boot/globalErrorHandler.ts` (toast + rollbacks + `clientLog.error`). If anyone *did* call it, every error would ship twice. · exact change: delete `installGlobalErrorReporting` + the stale docstring block; `useClientLogger.ts` becomes the logger only. · blast: S · guard: `globalErrorHandler.spec.ts` · verdict: **execute**.

**20-R2 — `vue-i18n` is installed, booted and unused; a comment in the money authority claims an integration that doesn't exist.** class: verified · where: `boot/i18n.ts` (41 lines, `createI18n` with a 12-line `src/i18n` message tree), `package.json:44` `"vue-i18n": "^11.0.0"`, `useMoney.ts:13–15` ("values are also fed into vue-i18n's `numberFormats` in `boot/i18n.ts`" — there are none); zero `useI18n`/`$t` consumers. PROPOSAL_LOCALE_I18N §3-2 chose "adopt-lite" (keep as the home for Intl wrappers) but the wrappers were built in `useMoney`/`useDateFormat` without it. · exact change: remove the boot file, `src/i18n`, the dependency and the `quasar.config` boot entry; fix the `useMoney` comment; record in the proposal that §3-2 resolved to (b) in practice. ~60 KB less bundle. · blast: S · guard: `vue-tsc` + build · verdict: **execute** (20-D1 asks the owner only whether Layer C is still a someday; the dead code goes either way).

**20-R3 — The "no space before the unit" list lives in two languages with a comment asking humans to keep them in sync.** class: verified (R-003) · where: `units.py:483–484` `_NO_SPACE_UNITS` ("Inclusion list MUST stay in sync with `NO_SPACE_UNITS` over there") ↔ `formatQuantity.ts:9–11`; the module already codegens `units_table.ts` via `scripts/dump_units.py`. · exact change: emit `NO_SPACE_UNITS` (and `SUB_ITEM_UNITS`, 20-R4) in `dump_units.py`; `formatQuantity.ts` imports from `generated/units_table.ts`; delete the comment. · blast: S · guard: `formatQuantity.spec.ts` + a pytest that the generated file is current (does one exist? — D2) · verdict: **execute**.

**20-R4 — Two different "countable unit" lists answer the same question on the two sides.** class: verified · where: `scaleQuantity.ts:20–32` `COUNTABLE_UNITS` (egg, clove, scoop, slice, piece, sprig, stick, knob, can, bunch, pinch) vs `units.py:617–632` `SUB_ITEM_UNITS` (clove, sprig, rasher, slice, stalk, floret, leaf, wedge, knob, splash, drizzle, handful) + `is_sub_item_unit`. Cook-mode scaling rounds "2 rashers" as continuous (→ "2.5") while the server treats a rasher as a sub-item; "1 can" rounds to whole on the client while the server has no opinion. · exact change: one server list (`units.py`) with the union, tagged per purpose if the purposes genuinely differ (`countable` for scaling vs `sub_item` for pricing), exported through the codegen; `scaleQuantity.isCountableUnit` reads it. · blast: S · guard: `scaleQuantity.spec.ts` · verdict: **execute** (owner may want to confirm "pinch" and "can" semantics — note in D2 of chunk 4's cook-mode help).

**20-R5 — `MealPlanBuilderDialog.vue:697` formats money by hand (`$${n.toFixed(2)}`).** class: verified (R-003/D-006; the one `formatMoney` bypass) · exact change: `formatMoney(n)`. · verdict: **execute**.

**20-R6 — `ReportsPage.vue:369` formats a date with `toLocaleDateString(undefined, …)` (browser locale).** class: verified (D-006; the one `useDateFormat` bypass after DR-14) · exact change: `formatDate(iso, opts)`. · verdict: **execute**.

**20-R7 — Sorting collates in `'en'` while display follows the household locale.** class: latent (R-003) · where: `new Intl.Collator('en', { sensitivity: 'base' })` ×5 — `useStockFilters.ts:341`, `recipeStore.ts:20`, `stockItemStore.ts:20`, `stockLocationStore.ts:20`, `storesStore.ts:20`. Harmless for `en-*` locales (the only shipped ones), but it is five copies of a collator that should come from the locale authority. · exact change: `useMoney.ts` (or a renamed `useLocalePolicy`) exports `nameCollator()` built from `currentLocale()` and cached; five call sites. · blast: S · verdict: **execute**.

**20-R8 — `--ring-focus` is overridden in 5 of 14 theme blocks; the other 9 inherit Pesto's green halo.** class: verified (13-R40 widened) · where: `tokens.scss:153–154` (`--focus-ring: var(--brand-primary)`; `--ring-focus: hsla(150,76%,39%,.35)` — a literal), `themes.scss:77–78, 128–129, 195–196, 267–268, 334–335` only. · exact change: define `--ring-focus: color-mix(in srgb, var(--brand-primary) 35%, transparent)` **once** at `:root` (it then follows every theme automatically) and delete the five per-theme copies; then rename to one token (`--focus-ring` solid, `--focus-ring-soft` halo) and update the 33 call sites. · blast: S · guard: visual (A6.1) · verdict: **execute**.

**20-R9 — `submit_client_log._buckets` never evicts keys.** class: latent · where: `submit_client_log.py:44–77` — one `deque` per session-id/IP, created on first sight, never removed; anonymous crawlers over a long uptime grow the dict without bound (each key ~100 B — slow, but it is a leak). Also `:63` literal `"user_id"` (FU-654/15-R14), `:9–11` docstring says the audit persist is "a follow-up round" (it exists at `:105–124`), `:92–95` comment says "429" while the code returns 204 (deliberately — the comment lies). · exact change: drop empty buckets after the window sweep; `SESSION_USER_ID_KEY`; fix the two comments. · blast: S · guard: `test_client_logs` (13) · verdict: **execute**.

**20-R10 — Toasts use two placement conventions.** class: verified vs D-009 · where: `position: 'bottom-right'` ×269 vs `'top'` ×23 (network/PWA/install toasts) vs `'bottom'` ×2; `quasar.config` sets no default, so 322 call sites each restate it. · exact change: set `framework.config.notify.position = 'bottom-right'` once in `quasar.config.ts`, remove the 269 restatements (mechanical), and decide whether the 23 `top` toasts are a deliberate second budget (connection/system notices) — D-009 allows one floating layer per edge; recommend keep `top` for *system* toasts only and document it in `notifyTypeRegistration.ts`. · blast: M (mechanical) · verdict: **execute** (the default) + **decision** (the `top` set).

### C2. Redundancy / DRY (R-001, R-003)

**20-R11 — No `useConfirm`; 50 hand-rolled `$q.dialog` confirms in 26 files.** tracked: 13-R26, 16-R22, 18-R9 · exact change: `composables/useConfirm.ts` → `confirm({ title, message, okLabel, destructive?: boolean, persistent?: boolean }): Promise<boolean>` wrapping `$q.dialog` with: `cancel: { flat: true, noCaps: true }`, `ok: { noCaps: true, color: destructive ? 'negative' : 'primary' }`, **never `html: true`** (18-R5; 4 sites today), copy suffix "This can't be undone." when `destructive`, Esc = cancel. Migrate the 50 sites (several already wrap it in a Promise by hand — `AdminDataBackupRestore.confirmAsync`). · blast: M (mechanical; copy stays) · guard: a Vitest for the composable · verdict: **execute**.

**20-R12 — Text-size scale vs the type floor.** where: `themeService.ts:321–326` roots at 14/16.5/20.5/23 px; `--font-size-xs` is a ratio token — at `sm` a `0.75` ratio yields 10.5 px, under D-003's 12 px floor for captions. · exact change: either floor `sm` at 16 px (and make the steps 16/18/20/23) or clamp caption tokens with `max(12px, …)` in `tokens.scss`. The owner's feedback asked for 75/100/150 % steps — 13-D4 recorded 87.5–125 % as the question; this finding is the floor interaction, not the range. · blast: S · verdict: **execute** the clamp; **decision** 13-D4 for the range.

**20-R13 — Shared primitives still carry bare Material icon strings** (`SettingsSection` ×3, `SettingsRow` ×2, `SettingsPageHeader` ×2, `BaseDialog` ×2, `CollapsibleCard` ×2, `DashboardCard` ×2, `FilterBar` ×3, `MealPlanRailDisclosure` ×2, `PageErrorState` ×4, `ShortcutsCheatsheet` uses `ICONS` ✓). Fixing the 12 primitive sites fixes them on every page at once; the remaining ~30 page sites (`StockItemDetailPage` 8, `HelpPage` 3, `ScanOverlay` 3, …) are a mechanical sweep. · verdict: **execute** (A7).

**20-R14 — Image-cap literal `6_000_000` ×9 in `dora_api`** (16-R11) → `infrastructure/images.py: MAX_IMAGE_DATA_URL_LEN` + a shared `ImageField`. · **execute**.

**20-R15 — `.settings-page` / `.settings-divider` / `.settings-actions` / `.settings-list` scoped CSS copied across settings pages** (13-R9, 18-R13) → `SettingsShell`-level global classes or a `settings.scss` partial. · **execute under 13-R9**.

**20-R16 — Two segmented controls** (FU-848: `BaseSegmented` 13 consumers, `DoraSegmented` 9) — the FU's own plan (merge onto the hand-rolled radiogroup, since `q-btn-toggle` fights the active ink with `!important`) stands. · **execute** (FU-848).

**20-R17 — `FONT_SIZE_PX`, the font list, and the theme families are already single-sourced in `themeService`** ✓ (FU-614). No finding; noted so Stage 2 doesn't look.

### C3. Dead code / unused fields / unread endpoints

**20-R18 — `ShortcutsCheatsheet.vue:74` `var(--q-grey-5, var(--border-strong))`** — a Quasar palette variable as the *primary* value with the token as fallback; R-002 inverted. · exact change: `var(--border-strong)`. · **execute**.
**20-R19 — `useShortcut` is consumed by 3 files; `'/'` is registered twice (Global + Stock overview, same handler intent)** — the page registration is redundant (newest-first lookup makes it win, but Global already does the same thing). · exact change: drop `StockOverview.vue:1012`. · **execute** (tiny).
**20-R20 — `rollbackRegistry.registerRollback` has one producer** (`stockItemStore`) — the "undo cross-app" feedback (MISC #2) is about the *undo* feature (chunk 6/7), not this registry; the registry is correct and small. **waive**.
**20-R21 — `PageErrorState` `style="max-width: 480px"` inline + the four bare icons + `travel_explore`/`cloud_off`/`block`/`error_outline` not in `ICONS`.** · **execute** with 20-R13.
**20-R22 — `api_response.endpoint_not_found` returns a bare tuple (plain JSON) while every sibling returns `application/problem+json`** — documented as deliberate (FU-167) at `:184–189`; keep, but the function is the only one not returning `Response` (type drift). **explain in place** (already is).

### C4. Componentisation opportunities (R-001)

**20-R23 — `useConfirm`** (20-R11) is the one new primitive this chunk adds. **20-R24 — `ShellBanner`** (17-R12) and **`CountBadge`** (FU-920 rename of `MealPlanRailCount`) are the two component renames/merges inherited here. · **execute** (S each).

### C5. Placement / layering (R-003, R-005)

**20-R25 — The locale authority lives in `useMoney.ts`** (`currentLocale`, `ensureLocalePolicy` consumed by `useDateFormat`; 20-R7 would add a collator). The file is named for one consumer of the policy. · exact change: `composables/useLocalePolicy.ts` owns `policy`/`load`/`currentLocale`/`currencySymbol`/`nameCollator`; `useMoney` and `useDateFormat` become thin consumers. · blast: S (re-exports keep call sites stable) · **execute**.

**20-R26 — `formatQuantity`/`scaleQuantity` are `helpers/`, `useDateFormat`/`useMoney` are `composables/`** — all four are pure formatting authorities (D-006); the non-reactive two don't need the composable shape, the reactive two don't need `helpers/`. Fine as is; **waive** (naming only).

**20-R27 — FU-923 raw-table sweep list (consolidated):** `products/get_products.py` (10-R12), `app_settings` readers (13-R32), `get_ingestable_products.py:81,89`, `get_ingest_stores.py:49`, `ingestion_auth.py:43` (16-R24), `import_spreadsheet.py:510,616,647` (18-R20 — fix), `backup_library.py:268` (18-R20), the dump/restore engine (18-R20 — **explain**), `audit_retention.py:40`, `health_check.py:67` (`alembic_version` — explain). · **FU-923** owns it.

**20-R28 — FU-654 / 15-R14 session-key sweep list (consolidated):** `logout.py:15`, `middleware.py:79,233`, `submit_client_log.py:63` + the assistant/budget/users/onboarding prologues chunks 11–14 listed. · **execute** (one helper, one import).

### C6. Naming & idiom
- **20-R29** — `clientLog.debug/info` carry blank-line gaps where an `eslint-disable-next-line no-console` used to be (`useClientLogger.ts:70, 74, 78, 83`) — tidy. **execute** (trivial).
- **20-R30** — `FormErrorSummary.vue:9` `v-slot:avatar` vs `#avatar` everywhere else. **execute** (trivial).
- **20-R31** — `error_translation.py:19–21` says "the map mirrors the small client-side translation file (FU-097 pattern for `format_quantity`)" — the client has no translation file; delete the sentence. **execute**.

### C7. Efficiency
- **20-R32** — `useDateFormat.getFormatter` keys the cache by `JSON.stringify(opts)` per call — fine (small objects). **waive**.
- **20-R33** — `paletteToken` runs `getComputedStyle` per token per computed re-run; Reports resolves 6 per theme change. **waive** (theme changes are rare).
- **20-R34** — 322 `Notify.create` sites each pass `position` — after 20-R10 the bundle loses ~269 object literals. Cosmetic.

### C8. Design-level findings — out of Stage-2 scope
- **20-D1 — Layer C (multi-language UI).** PROPOSAL_LOCALE_I18N §2.5 defers it; 20-R2 removes the dormant scaffold. If the owner wants to keep the *option* visibly open, keep the proposal line, not the dependency.
- **20-D2 — Toast placement budget (D-009):** keep `top` for connection/system notices and `bottom-right` for everything else, or one edge for all? Recommend the two-tier rule, written into `notifyTypeRegistration.ts`.
- **20-D3 — Text-size range** = 13-D4 (owner asked 75/100/150 %; shipped 85/100/125/140 %). 20-R12 handles the floor either way.
- **20-D4 — Help page shape.** ~105 proposed entries across 20 chunks will not fit six expandable groups; recommend one page per group (route per group, same `?q=` filter across all), a top-level **FAQ** group built from the question-shaped titles (`# HELP` #3), and an owner-supplied screenshot slot per entry (`# HELP` #5) — the HelpPage entry type gains an optional `image`. Design-level because it changes the Help IA; the per-surface content is ready.
- **20-D5 — FU-010 / FU-224 inputs (handed over, not decided):** `--text-on-primary` pure white in 5 themes (FU-674 measurements); `text-color="white"` on `warning`/`negative` chips in 16 files (FU-671); `color="secondary"` usage audit (FU-224) — `grep -c 'color="secondary"'` in Stage 2; the `--ring-focus` halo (20-R8); `AuthShell`'s private DEC-2 ladder vs theme tokens (15-R10/R6); `offline.html`/manifest brand hex (17); the `.backup-row:hover` `color-mix` pattern → a `--surface-hover` token (18-C11); `DemoBanner`/`OfflineBanner`/`UpdateBanner` accent-on-primary pairs (17/19 C11). These are the colour-system facts the holistic review needs; none is a Stage-2 change on its own beyond the token fixes already listed.
- **20-D6 — Usage analytics (MISC #17)** — answered **no** in chunk 19 §F (privacy posture; error telemetry only).
- **20-D7 — "UI should feel more unique / Quasar base customisation" (MISC #16, #15)** — this *is* FU-010's remit; the token system (127 tokens, 14 themes, Base\* primitives at 542/66/30 adoption) is the mechanism; what remains is the owner's visual pass.

### C9. Hand-rolled-vs-library verdicts (the plan §3.3 list for this chunk)
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `useMoney` / `useDateFormat` | `Intl.*` wrappers + one cache | `vue-i18n` `n()`/`d()` | **keep; remove vue-i18n** (20-R2) | S | The wrappers are 260 lines and already the authority; vue-i18n would re-wrap the same `Intl` calls. |
| `useShortcut` | 139-line registry with sequences | `@vueuse/core` `useMagicKeys` / `tinykeys` | **keep** | — | Sequences (`g s`), typing-target guard and the cheatsheet registry are the value; tinykeys would still need the registry. |
| `rollbackRegistry` | 26 lines | undo/redo libs | **keep** | — | It is not an undo stack; it reverts optimistic UI on crash. |
| `AppSkeleton` | 71 lines | `q-skeleton` | **keep** | — | Quasar's is per-type and not token-aware; this one reads `--surface-sunken`/`--text-muted`. |
| Toast layer | Quasar Notify + 2 registered types | — | keep; **set one default position** (20-R10) | S | — |
| `apiErrorHandler` + `error_translation` | FU-099 shape | — | keep | — | Server-authoritative copy is the right call; 6 + tests pin it. |
| Theme tokens + `themeService` | hand-rolled CSS-var system, 14 themes | Quasar's `setCssVar` only / a design-token build | **keep** | — | The `themeService` already re-points Quasar's palette; a token build step would add tooling for no new capability. |
| `formatQuantity`/`scaleQuantity` | 150 lines | `Intl.NumberFormat` unit style / fraction libs | **keep; single-source the lists** (20-R3/R4) | S | Fraction glyph snapping and the DEC-3 spacing rule are domain, not formatting. |
| `useFormErrors` | 80 lines | VeeValidate / vuelidate | **keep** | — | Server-side validation is the authority (R-020); a client validator would duplicate it. |
| `submit_client_log` rate limit | in-memory sliding window | `flask-limiter` | **keep** (fix eviction, 20-R9) | — | Same single-worker constraint as 15-R1 notes. |

### C10. Standards drift (R-0NN)
- **R-003** — unit lists ×2 (20-R3/R4); money/date bypasses (20-R5/R6); collator ×5 (20-R7); image cap ×9 (20-R14); confirm pattern ×50 (20-R11); toast position ×322 (20-R10); session key literal (20-R28); dead i18n claim (20-R2); `_buckets` (20-R9).
- **R-001** — `useConfirm` missing (20-R11); FU-848 (20-R16); FU-920 (20-R24).
- **R-002 / D-017** — `--q-grey-5` (20-R18); hex outside the ladder: `ScanOverlay:403,436,440,496` (camera frame — `#000` is arguably legitimate for a viewfinder; the green/red/pink are semantic → `--semantic-*`), `ImageEditTile:163` + `DoraModeSlider:142` `#fff` → `--text-on-primary`, `VoicePicker:484–485` `var(--negative, #c10015)` → `--semantic-negative`; `RecipeNutriScore` keeps the official grade colours (comment the carve-out); `paletteToken` fallbacks in `DashboardPage`/`ReportsPage` are documented pre-paint fallbacks — move them beside `CHART_RAMP_FALLBACKS` so there is one fallback table (R-003).
- **R-035 / D-002** — FU-671 (16 files), FU-674 (5 themes) — the sweep lists above.
- **A6 / D-016** — `outline: none` ×21 in 15 files (FU-841 is one); each needs a `:focus-visible` replacement ring (`--focus-ring`). **execute** as one sweep.
- **A7** — 48 bare icons (20-R13).
- **A8 / FU-836** — `col-lg-*` ×2 → `col-md-*`. **execute**.
- **D-003** — text-size floor (20-R12).
- **D-006** — 20-R5/R6/R7.
- **D-008 / B6** — `html: true` ×4 (20-R11 kills them); `persistent: true` ×5 (keep where destructive).
- **D-009 / B7** — 20-R10.
- **R-045** — raw `fetch` ×21 (18-R7 + FU-647; `useClientLogger`'s is explained in place ✓).
- **R-052** — `offline.html` (17-R2) ✓ handled there.

### C11. Ride-along signals for FU-010 / FU-224 (theme / colour) — consolidated hand-over
See 20-D5. Plus the raw numbers: 14 theme blocks; 127 root tokens; `--text-on-primary` white ×5; `--ring-focus` literal at root; `text-color="white"` ×24; `color="warning"`+white badges in chunks 16/18; `--q-negative`/`--q-accent` banners in chunk 17; hex outside the ladder ×8 files (above).

---

## D. Test plan — cross-cutting

| # | Test | Layer | Priority | Trigger to write it |
|---|---|---|---|---|
| D1 | `useDateFormat.spec.ts` — `formatDate('2026-09-03')` renders 3 Sept in `America/New_York`; `formatDateTime` medium+short; `formatRelativeDay` Today/Tomorrow/weekday/short; locale switch re-keys the formatter cache | vitest (fake timers + `Intl` locale) | **must-write-before-ship** | the D-006 authority has zero tests and is the kind of stable contract the owner's test stance wants pinned |
| D2 | `useMoney.spec.ts` — `formatMoney` null → `–`, 2 decimals, `currencySymbol` for AUD/USD/EUR under `en-AU`; `refreshMoneyPolicy` rebuilds the formatter | vitest | nice-to-have | with 20-R25 |
| D3 | `test__units_table_generated_is_current` — regenerate via `scripts/dump_units.py` into a temp path and diff against `web_app/src/generated/units_table.ts` (pins 20-R3/R4's single source) | pytest | **must-write-before-ship** | with 20-R3 (check whether one exists first — `grep dump_units tests/`) |
| D4 | `useConfirm.spec.ts` — resolves true on OK / false on cancel+dismiss; never passes `html`; destructive adds the suffix and `negative` colour | vitest | nice-to-have | with 20-R11 |
| D5 | `useShortcut.spec.ts` — typing-target guard, sequence timeout, newest-first precedence, Escape closes the cheatsheet | vitest | nice-to-have | opportunistic (139 lines, no tests) |
| D6 | `test__client_logs__bucket_keys_are_evicted` | pytest | nice-to-have | with 20-R9 |
| D7 | Structural: `grep` guard that no `.vue` sets `position:` on `Notify.create` except an allow-list of system toasts | vitest (fs scan, like `test_compose_env_coverage`) | nice-to-have | with 20-R10 — cheap drift pin |
| — | Visual contrast checks (FU-671/674) | manual, per theme | — | owner's FU-010 walk |

---

## E. Proposed follow-ups (orchestrator allocates ids)

- **finding (verified)** — dead second global-error installer with a stale "called from boot" docstring (20-R1). **now**.
- **finding (verified)** — `vue-i18n` + `boot/i18n.ts` + `src/i18n` unused; `useMoney` comment claims a numberFormats hook that doesn't exist (20-R2). **now**; amend PROPOSAL_LOCALE_I18N §3-2 to record the de-facto (b).
- **finding (R-003)** — unit lists duplicated across languages (20-R3/R4). **now**, via the existing codegen.
- **bug (D-006)** — one money bypass, one date bypass (20-R5/R6). **now**.
- **finding (R-003)** — `'en'` collators ×5 (20-R7). **now** with 20-R25.
- **finding (13-R40 widened)** — `--ring-focus` theme-inconsistent; two focus tokens (20-R8). **now**.
- **finding** — `_buckets` leak + stale comments + session-key literal in `submit_client_log.py` (20-R9). **now**.
- **finding (D-009)** — toast position restated ×322; no default (20-R10). **now** (default) · **decision** 20-D2.
- **sweep FUs to open (one each, with the counted site lists above):** `useConfirm` adoption (50 sites); bare-icon sweep (48, start with the 12 primitive sites); `outline: none` A6 sweep (21); FU-671 `text-color="white"` (24/16 files — **append** the list to FU-671); hex-outside-ladder (8 files — classify as listed); `col-lg` (2 — **append to FU-836**, then close it).
- **decision** — 20-D3 text-size range (= 13-D4); 20-D4 Help IA (one page per group + FAQ + screenshot slot) — needed before the ~105 entries from chunks 1–19 can land; 20-D1 Layer C.
- **hand-over** — 20-D5's inventory appended to **FU-010** and **FU-224** so the owner's visual review starts from measured facts.
- **resolve FU-920** (`CountBadge` rename) and **FU-848** (segmented merge) in Stage 2 — both are mechanical with the lists in hand.

---

## F. Feedback coverage — `# NO AREA / MISC` (21) + `# HELP` (5) + `# MOBILE VIEW` (0)

| # | Bullet | Status | Where |
|---|---|---|---|
| M1 | 404 page not in theme | ✅ shipped | fullscreen `ErrorNotFound` (chunk 15; 15-R6 dedupes its palette) + in-layout `ErrorPageNotFound` → `PageErrorState`. |
| M2 | Undo cross-app seems off (dashboard push expiry → detail clear) | → chunk 6/7 | undo/rollback semantics per surface; the shared registry is correct (20-R20). |
| M3 | Loading skeletons instead of placeholder words | ✅ shipped | `AppSkeleton`, DR-8 (D-007). |
| M4 | Main menu hover double outline | → chunk 13 (nav) | — |
| M5 | Settings in both main menu and user dropdown | ✅ shipped | `MainLayout.vue:75–83` — one direct nav entry, no dropdown. |
| M6 | Full systems QA document, do this last | 🟡 this plan | `FULL_SYSTEMS_TEST.md` assembled from §A of chunks 1–20 at close. |
| M7 | Text size too small in places; 75/100/150 % expected | ➗ | four steps 85/100/125/140 % shipped; range = **13-D4**; floor interaction = 20-R12. |
| M8 | Pesto button colours too bright / unreadable text | 🟡 | FU-674 (measured) + FU-010 — token facts handed over (20-D5). |
| M9 | Dora logo in QR codes | ✅ shipped | VERIFY 2026-08-28 "QR logo" (owner walk pending). |
| M10 | Real ALDI/IGA logos | ⚪ owner | Stores page accepts uploads; no shipped logos by design (FU-190). |
| M11 | Rename everywhere to Dashy Dora | ➗ | leftovers listed in 19-R4. |
| M12 | Main menu without bottom border? | 🔴 owner | FU-010 visual pass. |
| M13 | Command palette usefulness | ✅ cut | CLAUDE.md "Removed features". |
| M14 | QR scan → quick-actions modal | ✅ shipped (shape changed) | FU-378 action-first scan mode (`scanActions.ts`; chunk 5). |
| M15 | UI design consistent | ✅ mechanism / 🟡 remainder | token system + Base\* adoption (542/66/30); remaining raw `q-select` 47 (FU-675), `q-btn` 6, `q-dialog` 8, segmented ×2 (FU-848). |
| M16 | Feel more unique; Quasar base customisation | 🟡 | FU-010's remit; 14 themes + 127 tokens exist (20-D7). |
| M17 | Usage tracking | 🔴 answered no | privacy posture (19 §F / 20-D6). |
| M18 | `.local` folder messy | ✅ answered | chunk 19 §F. |
| M19 | Logs rolling? | ✅ shipped | chunk 19 §F. |
| M20 | Text invisible in light/dark | ➗ | DR-1 ramp done; DR-1b component spots + FU-671/674 remain. |
| M21 | Command palette doesn't work with create stock item | ✅ moot | palette cut; `n` shortcut on Stock Overview. |
| H1 | Detailed help for every part of the app | 🟡 | chunks 1–20 §B: ~105 entries + 8 rewords drafted; needs 20-D4's IA to land. |
| H2 | Detailed guides | 🟡 | same; cook-mode / stocktake / meal-plan runner guides extended (chunks 2, 4, 5). |
| H3 | Q&A / FAQ section | 🔵 designed | 20-D4 (FAQ group from question-shaped titles). |
| H4 | Help navigable, sections obvious | ✅ / 🟡 | filter + `?q=` deep link shipped; grouping change in 20-D4. |
| H5 | Screenshots / diagrams | 🔵 designed | 20-D4 image slot; owner supplies images. |

### Register summary
- **FST rows:** 11 golden + 10 edges · **Help entries:** 4 (new 3 / extended 1) + DoraBot 3 lines · **Review findings:** 34 (execute 27 / waive 4 / explain 1 / decision 2) + 7 design notes · **Tests:** 7 (must-write 2) · **Bugs:** 10 (20-R1…R10; R5/R6 are D-006 bypasses, R8 is the focus-ring token, R9 a slow leak)
- **One line:** the authorities exist and are right (locale, dates, money, tokens, error shape) — the drift is at the edges: a dead second error installer, a dead i18n dependency with a comment describing an integration that was never built, two unit lists kept in sync by comment, one `$`+`toFixed` and one browser-locale date, five `'en'` collators, a focus halo that only four themes recolour, 322 toasts each restating a position, and 50 hand-rolled confirms waiting for the `useConfirm` three earlier chunks asked for; the Help content from all twenty chunks now needs an information-architecture decision before it can ship.
