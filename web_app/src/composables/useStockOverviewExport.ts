/**
 * Stock-overview (install-wide) export. Sibling to the per-entity
 * composables — no id, just CSV + print-view of every stock item grouped
 * by location.
 */
import { Notify } from 'quasar';
import { resolveBaseURL } from 'src/services/api/axiosHttpClient';
import { parseFilename, triggerSave } from 'src/services/files/downloadHelpers';

export function useStockOverviewExport() {
    const baseUrl = resolveBaseURL('dora');

    async function downloadCsv(): Promise<void> {
        try {
            const response = await fetch(
                `${baseUrl}/stock-items/export?format=csv`,
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

    function openPrintView(): void {
        window.open(`${baseUrl}/stock-items/print-view`, '_blank', 'noopener');
    }

    function openQrSheet(ids: string[]): void {
        if (ids.length === 0) return;
        const url =
            `${baseUrl}/stock-items/qr/sheet` +
            `?layout=a4-21up&ids=${encodeURIComponent(ids.join(','))}`;
        window.open(url, '_blank', 'noopener');
    }

    return { downloadCsv, openPrintView, openQrSheet };
}

