// FU-520 workstream 1 — unit coverage for the A8 §3 nav-state cache.
//
// `useListState` is the session-scoped keep-alive for list-page filter state:
// first call per scope runs the factory, later calls return the SAME bag so
// values survive route changes; `clearAllListState` is the sign-out escape
// hatch. The caching contract is the whole feature — pin it.
//
// Vue refs only — no component lifecycle, runs in plain node.
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

import { clearAllListState, useListState } from 'src/composables/useListState';

describe('useListState — per-scope session cache', () => {
    beforeEach(() => {
        // Module-level cache — wipe between tests so cases stay independent.
        clearAllListState();
    });

    it('runs the factory on the first call for a scope', () => {
        const factory = vi.fn(() => ({ searchText: ref('') }));

        const state = useListState('stock-overview', factory);

        expect(factory).toHaveBeenCalledTimes(1);
        expect(state.searchText.value).toBe('');
    });

    it('returns the SAME bag on subsequent calls, preserving mutated values', () => {
        const first = useListState('stock-overview', () => ({ searchText: ref('') }));
        first.searchText.value = 'flour';

        // Simulates navigating away and back — a fresh useListState call.
        const second = useListState('stock-overview', () => ({ searchText: ref('') }));

        expect(second).toBe(first);
        expect(second.searchText.value).toBe('flour');
    });

    it('does not re-run the factory once a scope is cached', () => {
        const factory = vi.fn(() => ({ sortBy: ref('name_asc') }));
        useListState('recipes', factory);
        useListState('recipes', factory);
        useListState('recipes', factory);

        expect(factory).toHaveBeenCalledTimes(1);
    });

    it('keeps scopes independent of each other', () => {
        const stock = useListState('stock-overview', () => ({ searchText: ref('milk') }));
        const recipes = useListState('recipes', () => ({ searchText: ref('curry') }));

        stock.searchText.value = 'bread';

        expect(recipes.searchText.value).toBe('curry');
    });

    it('clearAllListState wipes every scope (sign-out / hard-reset UX)', () => {
        const before = useListState('stock-overview', () => ({ searchText: ref('') }));
        before.searchText.value = 'flour';

        clearAllListState();

        const after = useListState('stock-overview', () => ({ searchText: ref('') }));
        expect(after).not.toBe(before);
        expect(after.searchText.value).toBe('');
    });
});
