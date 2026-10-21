// @vitest-environment jsdom
/**
 * FU-520 component/composable layer — useMealPlanExport.
 *
 * The composable is a thin print-view opener (CSV export was removed in
 * FU-168): it resolves the API base URL once and opens
 * `/meal-plans/<id>/print-view` in a new tab. We mock `resolveBaseURL` at
 * the module boundary and spy `window.open`, then assert the URL is built
 * (and the plan id encoded) correctly.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const m = vi.hoisted(() => ({ resolveBaseURL: vi.fn() }));

vi.mock('src/services/api/axiosHttpClient', () => ({
    resolveBaseURL: m.resolveBaseURL,
}));

import { useMealPlanExport } from 'src/composables/useMealPlanExport';

describe('useMealPlanExport', () => {
    let openSpy: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        m.resolveBaseURL.mockReturnValue('http://api.test/api');
        openSpy = vi.fn();
        vi.stubGlobal('window', { ...window, open: openSpy });
    });

    afterEach(() => {
        vi.unstubAllGlobals();
        vi.clearAllMocks();
    });

    it('opens the print-view URL in a new noopener tab', () => {
        useMealPlanExport().openPrintView('plan-1');

        expect(openSpy).toHaveBeenCalledWith(
            'http://api.test/api/meal-plans/plan-1/print-view',
            '_blank',
            'noopener',
        );
    });

    it('URL-encodes the plan id', () => {
        useMealPlanExport().openPrintView('a b/c?d');

        expect(openSpy).toHaveBeenCalledWith(
            'http://api.test/api/meal-plans/a%20b%2Fc%3Fd/print-view',
            '_blank',
            'noopener',
        );
    });

    it('resolves the base URL once at composable construction', () => {
        const exporter = useMealPlanExport();
        m.resolveBaseURL.mockReturnValue('http://changed/api');

        exporter.openPrintView('plan-2');

        // The base was captured on construction, so the later change is ignored.
        expect(openSpy).toHaveBeenCalledWith(
            'http://api.test/api/meal-plans/plan-2/print-view',
            '_blank',
            'noopener',
        );
    });
});
