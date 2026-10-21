# Design critique — look & feel analysis (2026-07-18)

**Origin:** owner-requested design-level critique after the seven FU-578 UX passes.
**Method:** real-pixel review via `web_app/e2e/drive.mjs` screenshots (~40 captures:
every major surface, Pesto light + dark, desktop/tablet/mobile) cross-read against
the token sources (`tokens.scss`, `themes.scss`, `motion.scss`). Companion to the
itemised FU-578 findings — this doc is the synthesis: what the design *system* is,
where execution diverges from it, and what deserves redesign.

---

## 1. Verdict

The bones are unusually good: a real token system (spacing/radius/type/motion),
five paired theme families with a documented philosophy, semantic colours held
constant across themes, and a proper reduced-motion kill-switch. This is NOT a
cookie-cutter codebase at the architecture level. The gap is between the system
and the screens: Quasar defaults leak through (button casing, toast placement,
stock Material glyphs), the semantic colour scale misfires at its most important
point (Out of stock reads *calmer* than Low), secondary text is tuned below AA in
light mode, and a handful of surfaces (recipe detail, alerts calendar, history
timeline, meal-plans right rail) read as data dumps rather than designed pages.
The personality layer (mascot, copy voice) is distinctive and worth keeping —
but its floating-bubble implementation undermines it by squatting on content.

## 2. Colour palette — the system

Pesto (default): primary `hsl(150 60% 36%)` garden green, secondary deep teal,
accent `hsl(50 99% 56%)` golden yellow, warm-tinted neutral surfaces (168-hue
greys). Dark variant: forest-teal surfaces (`hsl(165 60% 5%)` page) with a
blue-tinted text ramp (`#D8E4FF`). Assessment:

- **The family idea is strong.** Food-adjacent theme names, paired variants,
  chart palettes per theme, hero gradient stops — this is designed, not sampled.
- **The accent is underemployed.** The golden yellow appears in the wordmark and
  active-tab underline and almost nowhere else. Meanwhile primary green is doing
  five jobs: brand, CTA, success, active state, and "stocked" level. When one hue
  means everything it stops meaning anything — the "Theme updated." success toast,
  the New item CTA, the active nav tab, and a Stocked square are all the same green.
- **Yellow-on-green wordmark** measures ~2.8:1 — brand lockups get latitude, but
  it's the first thing on every screen and it shimmers at small sizes.

## 3. Colour usage — where it misfires

1. **The stock-level scale is semantically inverted at the extreme.** Observed:
   Stocked = green, Low = coral red, **Out of stock = grey**. The worst state gets
   the least alarming colour; grey conventionally means "no data / disabled", which
   is why the dimmed-Parmesan mystery (FU-578 #33) is even possible — grey-square
   rows and genuinely-disabled rows are neighbours in the same visual space.
   Redesign: Stocked green → Low amber → Out red, reserving grey for "unknown".
   (The alerts bell and buy-verdict already use amber/red escalation — the row
   squares are the outlier.)
2. **Secondary/muted text is tuned below AA in light mode** (~3.0–3.7:1 across
   footer stats, chips, captions; the `--text-muted` ramp). One token nudge fixes
   dozens of instances — this is the single highest-leverage colour change.
3. **Soft-tint badges** (BUY = green-on-20%-green) land at 2.5–3.5:1 at 11px. The
   tint-chip pattern is fine; the text needs the full-strength colour with the
   tint reserved for the background.
4. **Two theme mechanisms disagree** — Quasar `body--dark` classes vs raw
   `prefers-color-scheme` media queries produce the split header/body render on a
   live OS scheme change (FU-578 7b). Whatever CSS still reads the media query
   directly should read the token instead (R-002 spirit: tokens are the single
   source).
5. **Row-edge colour language is real but private** — blue edge = on a list,
   amber = attention, red = out, cream tint = (?). It's consistent enough to be a
   feature; without a legend it's decoration users can't decode.

## 4. Sizes

- **Tap targets:** 32–36px icon buttons across stock rows/toolbars vs the 44–48px
  guideline; in-store checkboxes are a correct 50×50. The pattern: bespoke
  surfaces got sized deliberately, `dora-btn--icon` dense defaults everywhere else.
- **Type scale is well-formed** (0.75→1.875 ratios against a user-adjustable base —
  the text-size preference is a genuinely nice accessibility touch), but the
  *floor* gets used too often: 11–12px on BUY badges, belief-chip suffixes, nav
  labels, footer stat captions. The floor should be rare, not the default for
  secondary UI.
- **Icon-only main nav at every width** — six 24px glyphs carrying the whole IA
  with no labels. At desktop widths there is room for labels; on mobile the
  hamburger already exists. Icon-only top nav reads minimal but tests as
  unmemorable; at minimum, active-page label + tooltips.
- Cook mode's 28px+ step text is the right kind of size bravery — more of that
  confidence elsewhere (dashboard section headers are timid by comparison).

## 5. Spacing & layout

- **The spacing tokens (4→48px) are consistently applied inside components** —
  cards, dialogs, and settings pages feel evenly padded. The failures are at
  *page composition* level:
  - Dashboard/reports two-column grid leaves lone half-width cards beside dead
    air (Next to cook, Savings captured, You-keep-running-out) — the grid needs
    either masonry packing or full-width fallbacks.
  - Toolbar rows don't wrap: 930px of shopping-list actions overflowing mobile,
    and the page title colliding with Quick add at 1280px.
  - Bottom-right corner is quadruple-booked: toasts + tip bubble + mascot + badge.
  - Calendar widgets (alerts 14-day, meal-plans mini-month) spend enormous area
    on near-empty grids — space budget wildly out of line with information carried.
- Stock rows at 59px with clear internal rhythm are good; the belief chip
  crowding the location line on chip-bearing rows is the one density miss.

## 6. Motion & animation

`motion.scss` is textbook: three durations, Material easings, a documented
when-to-animate philosophy, Quasar's hardcoded 300ms overridden centrally, and a
reduced-motion collapse that keeps transitionend firing. Against that standard:

- **Observed motion is mostly Quasar stock** — dialog scale, menu jump, toast
  slide. Nothing wrong, but nothing owned either; the one bespoke signature bits
  (stocktake pulse halo, nav-slide flash token) are invisible in normal use.
  There's no micro-feedback on the app's most-repeated actions (level change,
  tick, add-to-list) — a 120ms `--motion-fast` settle on the level square or a
  chip count bump would make the app feel hand-made at exactly the moments users
  touch it most.
- **Missing transitions where they matter:** belief chips pop in with a reflow
  (should fade/slide within reserved space); dashboard cards swap "Loading…"
  text for content with no crossfade (and inconsistently — other pages have
  skeletons); route changes are instant swaps.
- **The splash is the riskiest animation in the app** — full-screen, z-9000,
  dismissal gated on a transition that assumes paint (wedge risk in
  background/throttled tabs) and >2s on a warm dev load.

## 7. Inconsistencies between pages

| Axis | Variants observed |
|---|---|
| Date format | "7/17/2026" (lists, meal grid) · "2026-10-08" ISO (history bodies) · "Mon, Jul 13" (reconcile card) — three formats, no single authority |
| Dialog button casing | "SKIP / UPDATE EXPIRY" (Quasar uppercase default) vs "Cancel / Restock & finish" (sentence case) vs "Create Account" (title case) |
| Loading states | Skeletons (lists, detail) · literal "Loading…" text (dashboard cards) · splash (boot) · nothing (belief chips) |
| Pluralisation | Proper singular/plural (stocktake caption) vs "3 day(s) ago" (alerts) |
| Cart glyphs | Filled cart vs cart-plus carry different meanings (on-list vs add) with no cue; two styles of BUY chip (solid row badge vs ghost) |
| Navigation affordance | Icon-only top nav (app) vs labelled sidebar (settings) — settings is the better pattern |
| Level pickers | Colour-dot picker pixel-consistent across overview/dialog/detail (good — deliberate) vs the finish modal having no picker at all (FU-582) |

The runner pattern (stocktake/reconcile) is the counter-example: the same card
anatomy, verb layout, and progress bar reused exactly. That's the consistency
bar the rest should meet.

## 8. Redesign candidates (in order)

1. **Recipe detail page** — an edit form wearing a detail page's clothes. Every
   field permanently editable, "Add (file)", empty Qty/Unit inputs as reading
   noise. Needs a read view (hero, meta chips, ingredient list, instructions)
   with an explicit edit mode; cook mode already proves the team can do a
   reading surface.
2. **Alerts page** — leads with the near-empty 14-day calendar while the
   actionable list is below the fold. Flip the order; shrink the calendar to a
   labelled strip.
3. **History timeline** — group repeated events, one date format, per-kind
   filter chips.
4. **Stock-level colour scale** — the green/red/grey → green/amber/red fix plus
   a row-state legend.
5. **Dashboard grid balance** — pack or full-width the lone cards; replace
   "Loading…" text with skeletons.
6. **Helper bubble placement** — dock it (FAB with safe-area, or collapse into
   the header) so the panel's genuinely good content stops being announced by
   an overlay that covers Level controls and calendar cells.

## 9. Cookie-cutter / unprofessional tells

- Quasar defaults leaking: uppercase dialog buttons, stacked default toasts,
  stock Material glyphs for load-bearing custom semantics (padlock = sealed/open
  is the worst — a security metaphor on a food-state toggle).
- Letter-avatar recipe cards (grey circle + initial) — fine as fallback, but the
  seed shows it as the dominant look; a food-category illustration set would
  transform the cookbook's first impression.
- "Add (file)", raw UUID on the Account page, "(s)" plurals, "Loading…" strings,
  US dates on an AU install — individually tiny, collectively the difference
  between "product" and "project".
- The 404 page, splash art, onboarding copy, and empty-state lines are the
  opposite: distinctive, confident, clearly authored. The app already knows its
  voice — the tells above are where nobody applied it.

## 10. What's already polished (protect these)

Cook mode (step type, location-grouped scaled ingredients, per-step highlight,
Finish ✓) · the runner pattern · onboarding story copy + all-set hub · Stock
locations settings page · Draft-my-shop flow · Add-item dialog · instant search
with re-scoping stats · token/motion architecture itself.

## 11. Priority order (design-only lens)

1. Muted-text + soft-badge contrast token pass (both modes) — hours, app-wide lift.
2. Stock-level scale green/amber/red + row legend.
3. Dialog casing + toast + icon audit (de-Quasar the details); replace the padlock.
4. Helper bubble docking.
5. Recipe detail read-mode redesign.
6. Alerts page order flip + calendar shrink.
7. Micro-motion on level change/tick/add (use the existing tokens).
8. Single date-format authority fed by household locale (overlaps FU-578 #48).

---

*Cross-refs: FU-578 (itemised findings, 54), FU-582 (finish-modal pickers),
FU-579 (dev overlay). Screenshots: session scratchpad `shots/` 01–41.*

*Actioned (same day): the standing rules extracted from this critique are
`docs/01_charter/DESIGN_STYLE_GUIDE.md` (D-001..D-015, enforced via
ENGINEERING_STANDARDS R-035/ADR-031); the work backlog is
`docs/04_proposals/DESIGN_REMEDIATION_PLAN.md` (DR-1..DR-16). This doc stays
the rationale record; those two are the operative documents.*
