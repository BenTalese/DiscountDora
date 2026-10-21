// The cookbook filters, searches and sorts entirely over the collection the
// recipe store holds, so "the store loaded every recipe" is a correctness
// contract, not a performance detail: a truncated first page made recipes
// past the 50th invisible on the overview while still appearing on the meal
// planner (which fetches its own entries). This pins the paging loop that
// closes that gap — the same contract stock items got under FU-035.
//
// Mocking sits at the http-client boundary so the real service code (query
// encoding + the loop's stop conditions) runs.
import { beforeEach, describe, expect, it, vi } from 'vitest';

import RecipeApiService from 'src/services/api/recipeApiService';

const m = vi.hoisted(() => ({ get: vi.fn() }));

vi.mock('src/services/api/axiosHttpClient', () => ({
    AxiosHttpClient: class {
        get = m.get;
    },
    default: class {
        get = m.get;
    },
}));

/** `count` recipes named r0..r(count-1), served as pages of `limit`. */
function servePages(count: number, limit: number) {
    m.get.mockImplementation((url: string) => {
        const page = Number(new URL(url, 'http://x').searchParams.get('page') ?? 1);
        const start = (page - 1) * limit;
        return Promise.resolve({
            items: Array.from({ length: Math.max(0, Math.min(limit, count - start)) }, (_, i) => ({
                recipe_id: `r${start + i}`,
                name: `Recipe ${start + i}`,
            })),
            total: count,
            page,
            limit,
        });
    });
}

describe('RecipeApiService.getAllPagesAsync', () => {
    beforeEach(() => {
        m.get.mockReset();
    });

    it('collects every recipe when the cookbook spans multiple pages', async () => {
        servePages(1150, 500);
        const items = await new RecipeApiService().getAllPagesAsync();

        expect(items).toHaveLength(1150);
        expect(items.at(-1)?.recipe_id).toBe('r1149');
        expect(m.get).toHaveBeenCalledTimes(3);
    });

    it('stops after one request when the first page is short', async () => {
        servePages(68, 500);
        const items = await new RecipeApiService().getAllPagesAsync();

        expect(items).toHaveLength(68);
        expect(m.get).toHaveBeenCalledTimes(1);
    });

    it('stops on an exactly-full final page rather than looping forever', async () => {
        servePages(1000, 500);
        const items = await new RecipeApiService().getAllPagesAsync();

        expect(items).toHaveLength(1000);
        expect(m.get).toHaveBeenCalledTimes(2);
    });

    it('carries the caller filters onto every page', async () => {
        servePages(600, 500);
        await new RecipeApiService().getAllPagesAsync({ expiring_within_days: 5 });

        for (const [url] of m.get.mock.calls) {
            expect(url).toContain('expiring_within_days=5');
        }
    });
});
