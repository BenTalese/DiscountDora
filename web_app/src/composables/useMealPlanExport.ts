/**
 * Meal-plan export actions — CSV (entries) + print-view (weekly calendar).
 * Same shape as useShoppingListExport / useRecipeExport.
 */
import { Notify } from 'quasar';
import { resolveBaseURL } from 'src/services/api/axiosHttpClient';
import { parseFilename, triggerSave } from 'src/services/files/downloadHelpers';

export function useMealPlanExport() {
    const baseUrl = resolveBaseURL('dora');

    async function downloadCsv(planId: string): Promise<void> {
        try {
            const response = await fetch(
                `${baseUrl}/meal-plans/${encodeURIComponent(planId)}/export?format=csv`,
                { method: 'GET', credentials: 'include' },
            );
            if (!response.ok) throw new Error(`Export failed (${response.status})`);
            const filename =
                parseFilename(response.headers.get('content-disposition'))
                ?? `meal-plan-${planId}.csv`;
            const blob = await response.blob();
            triggerSave(blob, filename);
        } catch (err) {
            Notify.create({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't export the meal plan.",
                caption: err instanceof Error ? err.message : String(err),
            });
        }
    }

    function openPrintView(planId: string): void {
        const url = `${baseUrl}/meal-plans/${encodeURIComponent(planId)}/print-view`;
        window.open(url, '_blank', 'noopener');
    }

    return { downloadCsv, openPrintView };
}

