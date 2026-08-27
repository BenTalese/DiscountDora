// Owner feedback 2026-08-27 — "a common component and flow is forming… we
// should ensure this common component and flow is actually the same on these
// areas." `AddToListDialog.vue` is that component; this is the one shape every
// surface feeds it (R-001/R-003), so recipes and meal plans can't drift apart.
//
// Callers map their own domain rows into `AddToListRow` and know nothing about
// shopping-list membership, stock levels, or target-list selection — the
// dialog owns all three.

/** Where the surface's `sourceLabel` sentence comes from — kept out of the
 *  dialog so it can't invent copy about a domain it doesn't know. */
export type AddToListRow = {
    stockItemId: string;
    name: string;
    /** Out of stock or untracked. Drives the default tick + "Select missing". */
    isMissing: boolean;
    isLowStock: boolean;
    /** Filed into the Optional section; never ticked by default (cookbook
     *  revision §1.9 — opt-in only, regardless of stock level). */
    isOptional: boolean;
    /** How much is needed, already formatted ("500 g"). `null` when the
     *  source didn't say — a recipe row with no quantity, for instance. */
    quantityLabel: string | null;
    /** What requires this item. Recipe names on a meal plan (an item can be
     *  pulled in by several meals); empty on a single recipe, where the answer
     *  is the page you're already looking at. */
    sources: string[];
};

/** An ingredient that can't become a line because it was never linked to a
 *  pantry item (FU-505). Surfaced in the dialog's footer so a picker-driven
 *  add still says what it couldn't take. */
export type AddToListUnlinked = {
    /** The recipe the row came from. */
    sourceName: string;
    ingredientName: string;
};

/** `targetListId: null` means "the new list named by `newListName`" — the
 *  dialog offers that option, the caller creates it. */
export type AddToListConfirm = {
    stockItemIds: string[];
    targetListId: string | null;
};
