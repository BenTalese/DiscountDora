// View shape for a recipe ingredient's recorded substitutes.
//
// `inStock` is resolved by the caller against the stock-item store, so the
// component renders a verdict it was handed rather than reaching for a second
// source of truth about stock (R-003).

import type { Substitute } from 'src/models/stockItemDetail';

export type SubstituteOption = {
    sub: Substitute;
    /** False when the substitute is itself out of stock or untracked. */
    inStock: boolean;
    /** Level-dot sequence, resolved by the caller against the stock-item
     *  store so the menu shows the *same* dot + tooltip the rest of the app
     *  uses for a pantry item (owner feedback 2026-08-27: one presentation
     *  and iconography for stock level everywhere). Null when untracked. */
    levelSequence: number | null;
    /** Human label behind the dot — the item's own level name where it has
     *  one, else a plain out-of-stock reading. */
    levelLabel: string;
};
