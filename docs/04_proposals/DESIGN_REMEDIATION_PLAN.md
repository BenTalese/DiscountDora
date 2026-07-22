# Design Remediation Plan — actioning the 2026-07-18 UX/design audit

**Status:** 🔵 approved-to-action (owner directive 2026-07-18: "add all this to a
report to be actioned"). Work units below are sized for one agent session each
unless noted. **Sources:** `DORA_FOLLOWUPS.md` FU-578 (54 itemised findings) +
FU-582, and `docs/05_investigations/UX_DESIGN_CRITIQUE_2026-07-18.md` (synthesis).
**Standing rules:** every unit must land compliant with
`docs/01_charter/DESIGN_STYLE_GUIDE.md` (D-rules) — that doc is the contract;
this plan is the backlog that brings existing screens up to it.

**Verification vehicle:** each unit re-runs the relevant `web_app/e2e/drive.mjs`
screenshot plan (session scratchpad plans are the recipes; store new plans under
`web_app/e2e/plans/` as they're recreated) + the existing Vitest/Playwright
suites. Contrast checks use the ratio-probe eval from the audit session.

---

## Wave 1 — token & convention passes (small diffs, app-wide lift)

### DR-1 · Contrast token pass (D-002) — P1
Retune `--text-muted` / `--text-secondary` (light variants especially) and
soft-chip text colours to AA; fix the alerts-badge (3.0:1), "New item" button
(3.6:1), Essential footer stat (2.3:1), BUY badge (2.5:1@11px), and audit the
wordmark treatment (2.8:1). **Files:** `tokens.scss`, `themes.scss` (all 10
variants), `colours.scss`. **Accept:** ratio probe passes D-002 floors on stock
overview, dashboard, shopping list detail in all 5 families × light/dark.
**Refs:** FU-578 #7/43.

### DR-2 · Stock-level scale + row legend (D-001, D-013) — P1
Out of stock → negative red; Low → warning amber; grey reserved for
unknown/disabled. Add the row-state legend (filter panel section or edge
tooltips): on-list edge, attention outline, expiring tint, open/sealed. Explain
or remove the undecodable states (dimmed row, cream tint — first *identify*
them in code). **Accept:** every row visual state is either self-labelled or in
the legend; both-theme screenshots. **Refs:** FU-578 #33/44, critique §3.1.

### DR-3 · De-Quasar detail audit (D-005, D-008) — P1
`no-caps` app-wide (audit every dialog for casing); replace the padlock
open/sealed glyph with a domain metaphor; aria-label + tooltip sweep over
icon-only buttons (the open-toggle first); disambiguate the two cart glyphs;
style the bulk-bar disabled state. **Accept:** zero uppercase dialog buttons;
no icon-only control without name+tooltip (axe/a11y spec extended to pin).
**Refs:** FU-578 #3/15c/34/53, critique §9.

### DR-4 · Copy & leakage sweep (D-014, D-006) — P1
Fix "expires expired" (`generators.py:113`); "(s)" plurals in alerts; "Add
(file)" labels; raw UUID off the Account page; display-name greeting
("Good afternoon, dora"); "$1 saves vs rrp"; dedupe "Dessert · Dessert" chips;
batch-cook onboarding explainer in plain words. **Accept:** grep-able tells
gone; copy reads in Dora's register. **Refs:** FU-578 #1/10/12/13/14/21/22/38.

## Wave 2 — interaction correctness

### DR-5 · Open-toggle mutation trap (D-008) — P1
Defer the `is_open` PATCH until dialog resolution (Skip/Update both confirm;
add Cancel + Escape close = no mutation), or keep eager-mutate but add Cancel
that reverts + an Undo toast. Pick the defer option unless code archaeology
shows a reason. **Accept:** backdrop/Escape dismissal leaves server state
untouched (extend the FU-507 e2e spec to pin). **Refs:** FU-578 #2.

### DR-6 · Finish-modal restock review (FU-582) — ✅ CLOSED 2026-07-22, cut confirmed
**Do not build the per-item level picker.** Owner cut it deliberately in commit
`a3b82644` (2026-07-13); FU-582 only existed because that removal went
undocumented. Rationale: someone who just bought an item would never mark it
anything but Stocked, so the picker was ceremony over a foregone conclusion (a
part-used item is corrected on the stock item itself). The `level_overrides`
contract has since been removed server-side too, and a test now pins that a
stale override body is rejected rather than ignored. **Refs:** FU-582 (resolved,
see `DORA_FOLLOWUPS_RESOLVED.md`).

### DR-7 · Toast & helper-bubble placement budget (D-009) — P2
Single toast column; toasts die on route change; dock the mascot/tip bubble so
nothing overlaps content (safe-area aware on mobile); explain or remove the
"6" badge; tip auto-dismisses. **Accept:** screenshots on stock/detail/reports/
alerts/cook-mode show zero overlap; toast gone after navigation.
**Refs:** FU-578 #6/31/35/41.

### DR-8 · Loading-state unification (D-007) — P2
Dashboard cards get skeletons (kill "Loading…" strings); reserve belief-chip /
verdict-badge space (or reflow-free fade-in); investigate the >2s warm splash
(what does it await?) + give splash dismissal a non-paint-gated fallback
(fixes the background-tab wedge risk). **Refs:** FU-578 #15/23/26/52.

## Wave 3 — layout

### DR-9 · Toolbar & grid composition pass (D-011) — P2
Shopping-list toolbar wraps/collapses to More (fixes the 255px mobile overflow
AND the 1280px title collision); dashboard + reports grids stop stranding
half-width cards; mobile stock rows: collapse the three trailing icons into an
overflow menu so names stop truncating at ~10 chars; belief chip placement on
chip-bearing rows. Tap-target pass to D-004 on stock rows/toolbars.
**Accept:** no horizontal scroll at 375px anywhere; no lone card beside dead
air; row names readable on mobile. **Refs:** FU-578 #4/19/30/40/15b.

### DR-10 · Nav labelling (D-005) — P2, needs owner taste call
Give the icon strip labels (under-icon at desktop, keep hamburger on mobile) or
at minimum active-page label + tooltips. **Refs:** FU-578 #5, critique §4.

## Wave 4 — surface redesigns (one session each, design-first)

### DR-11 · Recipe detail read-mode (D-015) — P2
Read view (hero/meta chips/ingredients/instructions) + explicit Edit mode;
fix the "0 unallocated of 1 cooked" vs "Last cooked: Never" contradiction while
in there. **Refs:** FU-578 #11, critique §8.1.

### DR-12 · Alerts page order + calendar diet (D-012) — P2
Actionable list first; calendar becomes a labelled 14-day strip (counts on
cells) or moves below; same treatment for the meal-plans mini-month.
**Refs:** FU-578 #28/50.

### DR-13 · History timeline grouping (D-012, D-006) — P3
Collapse repeated kinds ("Pushed expiry ×50 over 3 months"), per-kind filter
chips, one date format via the DR-14 formatter. **Refs:** FU-578 #32.

### DR-14 · Locale/format authority (D-006) — P2
Single date/currency formatter module (household locale+tz); replace direct
`toLocaleDateString` calls; onboarding SETUP gains the one-line "Use this
device" region derivation (backend already has the endpoint + admin override).
Also reconcile the two theme mechanisms (`body--dark` vs raw media queries) —
same "one authority" principle, fixes the split render. **Refs:** FU-578
#9/48/51, 7b.

### DR-15 · Micro-motion pass (D-010) — P3
`--motion-fast` feedback on level change / tick / add-to-list / chip toggles;
meal-planner wizard dedupe (one selectable instance per recipe, FU-578 #47) can
ride along. **Refs:** critique §6.

### DR-16 · Onboarding activation step — P3, needs owner product call
A "get food in" step (add first items / import / start with the starter list)
in SETUP, and drop Price history from the all-set hub for data-empty accounts
(R-012/R-014 tension — reveal-and-disable may prefer a "collects as you shop"
caption instead of removal). Register-form eager validation fix (#37) rides
along. **Refs:** FU-578 #37/39.

---

## Coverage table (audit → action)

| Audit item (FU-578 # / critique §) | Unit | Note |
|---|---|---|
| 1, 10, 12, 13, 14, 21, 22, 38 (copy/leakage) | DR-4 | |
| 2 (open-toggle trap) | DR-5 | |
| 3, 15c, 34, 53 (icons/casing/disabled) | DR-3 | |
| 4, 19, 30, 40, 15b (toolbars/grids/targets) | DR-9 | |
| 5 (nav labels) | DR-10 | owner taste call |
| 6, 31, 35, 41 (bubble/toasts) | DR-7 | |
| 7, 43 (contrast) + wordmark | DR-1 | |
| 7b, 9, 48, 51 (theme split + locale) | DR-14 | |
| 11 (cook-count contradiction) | DR-11 | |
| 15, 23, 26, 52 (loading/splash) | DR-8 | |
| 16 (meal-plans stat confusion) | DR-12 | rides the redesign |
| 17 (bell advice/action mismatch) | DR-4 | copy-level fix |
| 18 (rows not real links) | DR-9 | stretch: `href` on rows |
| 20 (kitchen-health scores unused feature) | DR-16 | skip-component like Budget |
| 24/25 (superseded/console error) | — | 25 stays FU-578 verify item |
| 27 (stocktake change-button affordance) | DR-3 | wording/affordance tweak |
| 28, 29, 50 (calendars/charts) | DR-12 | reports charts included |
| 32 (history wall) | DR-13 | |
| 33, 44 (level colours/legend) | DR-2 | |
| 36, 42, 45, 46, 54 (keep-as-is / cross-refs) | — | protected exemplars |
| 37, 39 (register validation, activation) | DR-16 | |
| 47 (wizard dupes) | DR-15 | |
| 49 (missing route alias) | DR-4 | one-line ride-along |
| FU-582 (finish pickers) | DR-6 | ✅ closed — cut confirmed, do not build |
| Critique §6 (micro-motion) | DR-15 | |
| Critique §8.1 (recipe detail) | DR-11 | |

**Open decisions — spawned, not dangling:** DR-6 scope (build vs cut), DR-10
(labels vs tooltips), DR-16 (activation step shape) are flagged `needs owner
sign-off/call` inline above; they block only their own units. Everything else
is approved-to-action per the owner's 2026-07-18 directive.

**Suggested order:** DR-1..DR-5 first (small, compounding, unblock screenshots
that look right), then DR-7/8/9/14, then the redesigns.
