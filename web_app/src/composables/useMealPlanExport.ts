/**
 * Meal-plan export — print-view (weekly calendar) only. CSV export was removed
 * (FU-168): a meal plan is a calendar, not a tabular dataset, so print-view
 * (→ browser "Save as PDF") is the export path.
 *
 * FU-682 / finalisation 02-R36: fetched through the client (R-045) via
 * `openPrintDocument`, not `window.open(baseUrl…)`.
 */
import { openPrintDocument } from 'src/composables/usePrintDocument';

export function useMealPlanExport() {
    function openPrintView(planId: string): void {
        openPrintDocument(`/meal-plans/${encodeURIComponent(planId)}/print-view`, 'Meal plan');
    }

    return { openPrintView };
}
