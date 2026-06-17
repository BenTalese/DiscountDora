/**
 * Shopping-list export actions — print-view open.
 *
 * Single source for these actions so every caller shares the code path;
 * keep new export formats here rather than scattering `${baseUrl}/...`
 * literals. The CSV download was removed in the UX-v2 pass — print is the
 * only take-it-with-you export for a shopping list
 * (PROPOSAL_SHOPPING_LIST_UX_V2.md §12 Q1); the endpoint is gone too.
 */
import { resolveBaseURL } from 'src/services/api/axiosHttpClient';

export function useShoppingListExport() {
    const baseUrl = resolveBaseURL();

    /** Open the server-rendered print view in a new tab and fire the
     *  browser's print dialog. User can hit "Save as PDF" from there. */
    function openPrintView(listId: string): void {
        const url = `${baseUrl}/shopping-lists/${encodeURIComponent(listId)}/print-view`;
        // _blank lets the user keep working in Dora; the floating toolbar
        // in the print view triggers window.print() on click, and the
        // browser remembers to re-open the print dialog on Ctrl/Cmd-P.
        window.open(url, '_blank', 'noopener');
    }

    return { openPrintView };
}

