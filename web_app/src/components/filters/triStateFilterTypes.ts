// Shared types for `TriStateFilter`. Extracted from the .vue SFC so
// consumers can import them as a plain TS module — type re-exports
// from .vue files don't always resolve cleanly (eslint sees them as
// error types and the intersection collapses to `any`).

export type TriStateOption = {
    value: string;
    label: string;
    category?: string;
    /** Quasar colour name; renders a 10px dot next to the +/- icon.
     *  Use for at-a-glance signals like stock level. */
    dotColour?: string;
    /** Opaque metadata blob the caller's sort compares can read.
     *  Not used by the component itself. */
    meta?: Record<string, unknown>;
};

/** Caller-supplied sort axis. When `sortOptions` is non-empty the
 *  component renders a small `q-btn-toggle` below the search bar
 *  with one entry per axis. The active axis's `compare` runs
 *  against the option list before grouping. */
export type TriStateSort = {
    value: string;
    label: string;
    compare: (a: TriStateOption, b: TriStateOption) => number;
};
