// Column classes for the dashboard's zone grid, so no card ever sits beside
// dead air (D-011 / B4: "no lone half-width card beside dead air"; a lone card
// in a 2-col row goes full-width).
//
// ## The defect this fixes
//
// `DASHBOARD_PAGE_REVIEW.md` §4.6 counted dead regions on the default desktop
// dashboard. **Measured** with the old classes re-applied in a real browser
// (chunk 2, 2026-09-02):
//
//   1920px  5 dead regions      1280px  2 dead regions
//   1440px  5                   1024px  2      768px  2
//
// The review said "five on a default desktop", which is right at **≥1440px** and
// wrong below it — it assumed `col-lg-*` engaged at the app's own ≥1024
// "desktop" breakpoint (A8) when Quasar's `lg` is ≥1440. Corrected in §4.6.
//
// Two separate causes. **Mixed widths:** `meal_plan` was `col-lg-8` inside a zone
// of `col-lg-6`s, so above 1440 it could not share a row and stranded a card
// above it *and* a third beside it; the Kitchen zone was three `col-lg-4`s of
// which one (`reconcile_pending`) is hide-when-empty, so it rendered 4+4 and
// left a third empty. **Odd counts:** a zone with an odd number of half-width
// cards always strands its last one — that is the pair that showed up at every
// width, including 768px.
//
// FU-631 #3 called for "per-zone odd-count logic" rather than a pure-CSS rule,
// because the widths are static classes while the order is dynamic (users
// reorder within a zone, and gates/data hide cards). This is that logic.
//
// ## Why runs, not zones
//
// The naive rule — "if the zone has an odd number of cards, widen the last one"
// — is wrong as soon as a genuinely full-width card sits *inside* a zone. A
// full-width card takes its own row, so it splits the zone into independent
// runs of half-width cards, and each run needs its own parity fix:
//
//   [A, B, FULL, C, D]  →  A+B · FULL · C+D                    already clean
//   [A, FULL, B, C]     →  A alone beside dead air unless A widens
//
// So: partition the zone's rendered cards into runs of consecutive half-width
// cards, and widen the last card of any run with an odd length.

/** Quasar column classes for a half-width card: full-width on phone, half from
 *  the `sm` breakpoint (600px) up.
 *
 *  ⚠️ **Do not add `col-lg-*` here.** Quasar's breakpoints are xs <600 ·
 *  sm ≥600 · **md ≥1024** · **lg ≥1440** · xl ≥1920, while the app's own design
 *  guide (A8) calls **≥1024 "desktop"**. Those two do not line up, and the
 *  dashboard was the one surface in the app that reached for `col-lg-*` to mean
 *  "desktop": measured, its `col-lg-6` / `col-lg-4` / `col-lg-8` classes did
 *  nothing at all below 1440px, so on an ordinary 1280px laptop "Needs your
 *  attention" and "The week ahead" rendered **full-width** (they carried no
 *  `col-sm-*` step) while everything else was already half. Almost certainly not
 *  what their author intended. The rest of the app uses `col-md-*` for the
 *  desktop tier — 14 usages against 2 for `col-lg-*`. See FU-836. */
export const CARD_COL_HALF = 'col-12 col-sm-6';

/** Full width at every breakpoint. */
export const CARD_COL_FULL = 'col-12';

/**
 * Decide each card's column classes for one zone.
 *
 * @param renderedInOrder  the cards this zone actually renders, in render
 *   order. Must reflect what the template will really show — a card hidden by
 *   its own data guard (an empty reconcile queue, a null budget) is *not* in
 *   this list, or the parity maths pads for a card that isn't there.
 * @param alwaysFull  cards that are full-width by design regardless of parity
 *   (the fortnight calendar's 14-day grid, for instance).
 */
export function zoneColClasses(
    renderedInOrder: readonly string[],
    alwaysFull: ReadonlySet<string> = new Set(),
): Record<string, string> {
    const classes: Record<string, string> = {};
    // The half-width cards seen since the last full-width card — i.e. the run
    // currently being accumulated.
    let run: string[] = [];

    const closeRun = () => {
        if (run.length % 2 === 1) {
            // Odd run: its last card would sit beside dead air, so give it the
            // whole row. Widening the *last* one (rather than the first) keeps
            // the pairs above it stable as cards are added or hidden.
            classes[run[run.length - 1]!] = CARD_COL_FULL;
        }
        run = [];
    };

    for (const id of renderedInOrder) {
        if (alwaysFull.has(id)) {
            closeRun();
            classes[id] = CARD_COL_FULL;
            continue;
        }
        classes[id] = CARD_COL_HALF;
        run.push(id);
    }
    closeRun();

    return classes;
}
