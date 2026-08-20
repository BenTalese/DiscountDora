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
};
