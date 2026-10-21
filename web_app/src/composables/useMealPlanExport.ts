/**
 * Meal-plan export — print-view (weekly calendar) only. CSV export was removed
 * (FU-168): a meal plan is a calendar, not a tabular dataset, so print-view
 * (→ browser "Save as PDF") is the export path.
 */
import { resolveBaseURL } from 'src/services/api/axiosHttpClient';

export function useMealPlanExport() {
    const baseUrl = resolveBaseURL();

    function openPrintView(planId: string): void {
        const url = `${baseUrl}/meal-plans/${encodeURIComponent(planId)}/print-view`;
        window.open(url, '_blank', 'noopener');
    }

    return { openPrintView };
}

