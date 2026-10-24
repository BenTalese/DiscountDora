/**
 * Shopping-list export actions — print-view open.
 *
 * Single source for these actions so every caller shares the code path;
 * keep new export formats here rather than scattering path literals. The CSV
 * download was removed in the UX-v2 pass — print is the only take-it-with-you
 * export for a shopping list (PROPOSAL_SHOPPING_LIST_UX_V2.md §12 Q1); the
 * endpoint is gone too.
 *
 * FU-682 / finalisation 03: fetched through the client (R-045) via
 * `openPrintDocument`, not `window.open(baseUrl…)`.
 */
import { openPrintDocument } from 'src/composables/usePrintDocument';

export function useShoppingListExport() {
    /** Open the server-rendered print view in a new tab; the floating toolbar
     *  in the print view triggers window.print() and the user can "Save as
     *  PDF" from there. */
    function openPrintView(listId: string): void {
        openPrintDocument(`/shopping-lists/${encodeURIComponent(listId)}/print-view`, 'Shopping list');
    }

    return { openPrintView };
}
