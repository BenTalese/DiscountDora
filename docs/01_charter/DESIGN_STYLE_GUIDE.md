# Dashy Dora — Design Style Guide (D-rules)

**Status:** authoritative — adopted 2026-07-18 (owner directive, following the
FU-578 UX audit + `docs/05_investigations/UX_DESIGN_CRITIQUE_2026-07-18.md`).
**Scope:** every task that adds or changes anything a user sees. This is the
*usage* companion to `ENGINEERING_STANDARDS.md` R-002 (which owns the tokens-only
mechanics): R-002 says colours come from tokens; this doc says which token, when,
and what the result must look like.

**How to use (agents):** on any UI-affecting task, check the change against the
D-rules the same way you check R-rules — fix, explain in place (`// D-00N
carve-out: …`), or log a `DORA_FOLLOWUPS.md` finding. Enforced via R-035 at the
standards close-gate. When a design decision recurs that this doc doesn't cover,
propose a new D-rule at close-gate (same promotion path as ADRs).

The remediation backlog that brings existing screens up to these rules is
`docs/04_proposals/DESIGN_REMEDIATION_PLAN.md` — new work must comply from the
start; old violations are tracked there, not silently copied.

---

## Foundations (already built — consume, never fork)

- **Colour:** `tokens.scss` + `themes.scss` (5 families × light/dark). Semantic
  colours (positive/warning/negative/info) encode meaning, not aesthetics.
- **Spacing:** `--space-1..12` (4→48px). **Radius:** `--radius-xs..pill`.
- **Type:** `--font-size-xs..3xl` ratios against the user-adjustable base.
- **Motion:** `motion.scss` — `--motion-fast|normal|slow` + easings + reduced-motion
  kill-switch. Never a literal `ms` value in a component.

---

## D-rules

### D-001 — Stock-level colour semantics: green → amber → red; grey = unknown only
- **Rule:** Level/status colour escalates with urgency: Stocked = positive green,
  Low = warning amber, Out of stock = negative red. Grey/muted is reserved for
  "no data / unknown / disabled" and must never represent a real level.
- **Why:** The audit found Out rendering grey — the worst state read *calmer* than
  Low (red), and grey level squares were indistinguishable from disabled rows
  (FU-578 #33). Alerts and buy-verdict already escalate amber→red; rows were the
  outlier. One scale everywhere or the colours stop carrying meaning.
- **Check:** any new status→colour mapping goes through `stock_status`-derived
  semantics; screenshot both themes.

### D-002 — Contrast floors are non-negotiable
- **Rule:** Body/secondary text ≥ 4.5:1 against its resolved background; large
  text (≥18.5px, or ≥14px bold) ≥ 3:1; text on tinted "soft" chips uses the
  full-strength semantic colour (the tint is for the *background* only). Never
  put text below 4.5:1 on interactive elements.
- **Why:** the light-mode muted ramp measured 3.0–3.7:1 across footer stats,
  chips, and captions; BUY badge 2.5:1 at 11px (FU-578 #7). "Muted" must mean
  de-emphasised, not illegible.
- **Check:** compute the ratio (the drive.mjs eval probe in the 2026-07-18 session
  is a reusable recipe) for any new text/background pair in BOTH modes.

### D-003 — Type floor: 12px is the minimum, and it's rare
- **Rule:** No text below `--font-size-xs` (0.75 × base ≈ 12px). Anything at the
  floor must be non-essential (captions, timestamps) — never a value the user
  acts on (prices, counts, button labels, badges).
- **Why:** the audit found 11px acting labels (BUY badges) and floor-size text
  used as the *default* for secondary UI. The floor is a boundary, not a style.

### D-004 — Tap targets: 44px minimum on touch surfaces
- **Rule:** Interactive elements on primary surfaces are ≥44×44px effective
  target (visual size + padding). Dense 32–36px icon buttons are allowed only in
  desktop-only chrome or where the row itself is the target. The in-store tick
  checkbox (50×50) is the reference for "gesture that matters".
- **Why:** the app's charter audience is pantry/mobile; the audit measured
  32–36px across stock rows and toolbars (FU-578 #19).

### D-005 — Every icon-only control has an accessible name AND a tooltip; icon metaphors match the domain
- **Rule:** Icon-only buttons ship `aria-label` + `<q-tooltip>` — no exceptions.
  Icon choice must read in the food domain: never security/system metaphors for
  domain states (the padlock-as-sealed/open toggle is the canonical violation —
  use an open/closed jar or seal metaphor). Two glyphs may not share a meaning
  axis (cart vs cart-plus) without an explicit state cue (colour + tooltip).
- **Why:** FU-578 #3 (unlabelled open-toggle), 15c (padlock), #34 (cart glyphs).

### D-006 — One date/number formatting authority
- **Rule:** All user-facing dates/times/currency format through the single shared
  formatter (household locale + timezone aware). Components never call
  `toLocaleDateString`/hand-format directly. Relative phrases ("3 days ago")
  come from the same module. No "(s)" pluralisation — write both forms.
- **Why:** three simultaneous date formats observed ("7/17/2026", ISO, "Mon,
  Jul 13") and "(s)" plurals in alerts (FU-578 #9/10/32/51). R-021 owns *which*
  day it is; this rule owns *how it reads*.

### D-007 — Loading states: skeletons, not words; reserve space for late content
- **Rule:** Any async surface >150ms shows a skeleton shaped like its content —
  never the literal string "Loading…", never a blank pane. Content that arrives
  after first paint (belief chips, verdict badges) renders into *reserved space*
  or fades in without reflowing neighbours.
- **Why:** dashboard cards show "Loading totals…" text while list pages have
  proper skeletons; belief chips pop in and shift rows (FU-578 #15/52).

### D-008 — Button & dialog conventions
- **Rule:** Sentence case everywhere ("Restock & finish", "Update expiry") —
  set `no-caps`; never Quasar's default UPPERCASE. Every dialog has an explicit
  escape hatch (Cancel button or ✕) AND closes on Escape; dismissing a dialog
  must never leave a half-applied mutation (mutate on confirm, not on open —
  the open-toggle trap, FU-578 #2, is the canonical violation). Destructive
  confirms are red and never the default-focused action.
- **Why:** casing drift ("SKIP / UPDATE EXPIRY" vs "Restock & finish") and the
  no-cancel expiry dialog came straight from unstyled Quasar defaults.

### D-009 — Toasts & floating chrome respect a placement budget
- **Rule:** Bottom-right is a single-occupancy zone: one toast column, and the
  helper mascot docks *below/behind* it, never overlapping page content,
  interactive controls, or other floating chrome. Toasts auto-dismiss ≤5s
  (except ones carrying Undo, ≤8s) and never survive a route change. Floating
  elements honour safe-areas on mobile.
- **Why:** the audit found toasts + tip bubble + mascot + badge quadruple-booked,
  the bubble covering Level controls/calendar cells/ingredient lists on five
  surfaces, and a toast persisting across navigation (FU-578 #6/31/41).

### D-010 — Micro-feedback on high-frequency actions; motion tokens or nothing
- **Rule:** The repeated gestures (level change, tick, add-to-list, chip toggle)
  give ≤`--motion-fast` visual feedback (settle/scale/count-bump). All animation
  reads `--motion-*` tokens (no literal durations); no animation on
  per-keystroke/scroll churn; anything gating *dismissal* of a blocking surface
  (splash!) must have a non-animation fallback (timeout/event), never rely on
  paint having happened.
- **Why:** motion tokens exist but the most-touched interactions have zero
  feedback; the splash wedges when paint is throttled (FU-578 #23/26).

### D-011 — Page composition: no stranded half-cards, no non-wrapping toolbars
- **Rule:** Two-column card grids must define collapse behaviour — a lone card in
  a row goes full-width (or the grid packs); no card sits beside dead air.
  Toolbar/action rows wrap (or collapse into a More menu) — content may never
  force horizontal page scroll at any supported viewport (375px+). Page titles
  never collide with actions.
- **Why:** dashboard/reports dead zones; the 930px shopping-list toolbar
  overflowing mobile and colliding with its own title at 1280px (FU-578 #4/30/40).

### D-012 — Data-dense widgets earn their area
- **Rule:** A visualisation must carry information proportional to its footprint.
  Calendars show labels/counts on cells, not bare 4px dots; charts with <2
  distinct values render as a stat/list instead; long uniform event streams
  group repeats ("×50 over 3 months") behind expansion.
- **Why:** the alerts 14-day calendar, meal-plans mini-month, "Meals cooked"
  solid-block chart, and the 6,500px history wall (FU-578 #28/29/32/50).

### D-013 — Colour-coded states get a legend
- **Rule:** Any surface using colour/edge/tint coding for row states (on-list
  edge, attention outline, expiring tint…) exposes the mapping in-UI — a legend
  in the filter panel or tooltips on the coded element. A state with styling but
  no discoverable meaning is a defect.
- **Why:** the stock rows speak a consistent private colour language nobody is
  told (FU-578 #44), and one undecodable state (dimmed row) read as a bug.

### D-014 — Copy voice: Dora's, everywhere
- **Rule:** User-facing copy is warm, concrete, first-person-Dora where natural —
  the register of the onboarding scenes and empty states ("Nothing's been added
  to a list while out of stock — nicely played."). No dev leakage: no raw UUIDs,
  usernames used as display names without casing, "(file)"-style parentheticals,
  or internal jargon (say "batch cooking covers several days", not "cook-pool
  controls"). Personalisation uses the display name.
- **Why:** the app has a distinctive voice in its best surfaces; the tells
  ("Add (file)", raw UUID, "Good afternoon, dora") are where it lapsed
  (FU-578 #12/13/21/38).

### D-015 — Pattern reuse: one anatomy per job
- **Rule:** New surfaces reuse the established pattern for their job rather than
  inventing a sibling: card-runner (stocktake/reconcile) for queue-walking;
  colour-dot level picker for level selection; labelled-sidebar (settings) for
  section nav; read-view + explicit edit mode for detail pages (don't ship
  always-editable forms as "detail"). If a pattern must diverge, the divergence
  is a design decision — record it.
- **Why:** the runner reuse is the app's consistency high-water mark; the
  recipe-detail form-as-page is the counterexample (FU-578 critique §8.1).

---

## Exemplars (the bar — protect these)

Cook mode (step type, per-step ingredient highlight) · stocktake/reconcile
runners · onboarding story + all-set hub · Stock-locations settings page ·
Draft-my-shop flow · Add-item dialog · instant search with re-scoping stats ·
404/splash art + empty-state copy.

## Change process

D-rules follow the same lifecycle as R-rules: propose at close-gate, record the
decision (ADR if it constrains architecture; otherwise note here + worklog),
newest rules appended. This doc is indexed from `ENGINEERING_STANDARDS.md`
(R-035) so it is checked on every task.
