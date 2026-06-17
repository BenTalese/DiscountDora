/**
 * Recipe export actions — CSV (ingredients) + print-view (recipe card).
 * Sibling to useShoppingListExport; same shape so callers can swap.
 */
import { Notify } from 'quasar';
import { resolveBaseURL } from 'src/services/api/axiosHttpClient';
import { parseFilename, triggerSave } from 'src/services/files/downloadHelpers';

export function useRecipeExport() {
    const baseUrl = resolveBaseURL();

    async function downloadCsv(recipeId: string): Promise<void> {
        try {
            const response = await fetch(
                `${baseUrl}/recipes/${encodeURIComponent(recipeId)}/export?format=csv`,
                { method: 'GET', credentials: 'include' },
            );
            if (!response.ok) {
                throw new Error(`Export failed (${response.status})`);
            }
            const filename =
                parseFilename(response.headers.get('content-disposition'))
                ?? `recipe-${recipeId}.csv`;
            const blob = await response.blob();
            triggerSave(blob, filename);
        } catch (err) {
            Notify.create({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't export the recipe.",
                caption: err instanceof Error ? err.message : String(err),
            });
        }
    }

    function openPrintView(recipeId: string): void {
        const url = `${baseUrl}/recipes/${encodeURIComponent(recipeId)}/print-view`;
        window.open(url, '_blank', 'noopener');
    }

    return { downloadCsv, openPrintView };
}

