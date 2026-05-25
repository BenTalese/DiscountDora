/**
 * Shopping-list export actions — CSV download + print-view open.
 *
 * The brief calls for this to be the single source for these actions so
 * both ExportPrint.vue and the ShoppingListDetail toolbar use the same
 * code path. Keep new export formats here too rather than scattering
 * `${baseUrl}/...` literals.
 */
import { Notify } from 'quasar';
import { resolveBaseURL } from 'src/services/api/axiosHttpClient';
import { parseFilename, triggerSave } from 'src/services/files/downloadHelpers';

export function useShoppingListExport() {
    const baseUrl = resolveBaseURL('dora');

    async function downloadCsv(listId: string): Promise<void> {
        try {
            const response = await fetch(
                `${baseUrl}/shopping-lists/${encodeURIComponent(listId)}/export?format=csv`,
                { method: 'GET', credentials: 'include' },
            );
            if (!response.ok) {
                throw new Error(`Export failed (${response.status})`);
            }
            const filename =
                parseFilename(response.headers.get('content-disposition'))
                ?? `shopping-list-${listId}.csv`;
            const blob = await response.blob();
            triggerSave(blob, filename);
        } catch (err) {
            Notify.create({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't export the shopping list.",
                caption: err instanceof Error ? err.message : String(err),
            });
        }
    }

    /** Open the server-rendered print view in a new tab and fire the
     *  browser's print dialog. User can hit "Save as PDF" from there. */
    function openPrintView(listId: string): void {
        const url = `${baseUrl}/shopping-lists/${encodeURIComponent(listId)}/print-view`;
        // _blank lets the user keep working in Dora; the floating toolbar
        // in the print view triggers window.print() on click, and the
        // browser remembers to re-open the print dialog on Ctrl/Cmd-P.
        window.open(url, '_blank', 'noopener');
    }

    return { downloadCsv, openPrintView };
}

