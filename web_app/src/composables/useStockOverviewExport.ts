/**
 * Stock-overview (install-wide) export. Sibling to the per-entity
 * composables — no id, just CSV + print-view of every stock item grouped
 * by location.
 */
import { Notify } from 'quasar';
import { resolveBaseURL } from 'src/services/api/axiosHttpClient';
import { describeQrFailure, openQrSheetAsync } from 'src/composables/useQrLabels';
import { parseFilename, triggerSave } from 'src/services/files/downloadHelpers';

export function useStockOverviewExport() {
    const baseUrl = resolveBaseURL();

    /** C-1 Chunk 1 / L67 — when `ids` is provided, the server filters the
     *  export to that set so CSV mirrors the on-screen filtered list. An
     *  empty array intentionally exports zero rows (matches what the
     *  filter shows); pass `undefined` to export everything. */
    async function downloadCsv(ids?: string[]): Promise<void> {
        try {
            const idsParam =
                ids !== undefined
                    ? `&ids=${encodeURIComponent(ids.join(','))}`
                    : '';
            const response = await fetch(
                `${baseUrl}/stock-items/export?format=csv${idsParam}`,
                { method: 'GET', credentials: 'include' },
            );
            if (!response.ok) throw new Error(`Export failed (${response.status})`);
            const filename =
                parseFilename(response.headers.get('content-disposition'))
                ?? `stock-overview.csv`;
            const blob = await response.blob();
            triggerSave(blob, filename);
        } catch (err) {
            Notify.create({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't export the stock overview.",
                caption: err instanceof Error ? err.message : String(err),
            });
        }
    }

    /** C-1 Chunk 1 / L67 — print-view honours the same `ids` filter as
     *  the CSV export. Pass `undefined` to print everything. */
    function openPrintView(ids?: string[]): void {
        const idsParam =
            ids !== undefined
                ? `?ids=${encodeURIComponent(ids.join(','))}`
                : '';
        window.open(`${baseUrl}/stock-items/print-view${idsParam}`, '_blank', 'noopener');
    }

    // Stays sync-entry so the click's gesture reaches `window.open` (R-046);
    // the failure is caught rather than dropped, because the most likely one is
    // a blocked pop-up, and a print button that does nothing at all is the
    // worst version of that.
    function openQrSheet(ids: string[]): void {
        if (ids.length === 0) return;
        openQrSheetAsync({ layout: 'a4-21up', ids }).catch((err: unknown) => {
            Notify.create({
                type: 'negative',
                position: 'bottom-right',
                message: describeQrFailure(err),
            });
        });
    }

    return { downloadCsv, openPrintView, openQrSheet };
}

