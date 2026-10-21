// FU-539 resilience layer — rollbackRegistry, the module-level LIFO stack that
// backs every optimistic-mutation undo. A stranded or mis-ordered rollback is a
// silently-wrong UI (a row shows a value the server never accepted). These tests
// pin: LIFO execution order, that a run empties the registry, that clear discards
// without running, and — the FU fix — that one throwing rollback does not strand
// the rest.
import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
    clearRollbacks,
    executeRollbacks,
    registerRollback,
} from 'src/services/errorHandling/rollbackRegistry';

beforeEach(() => {
    // Module-global stack — isolate every test from leftover registrations.
    clearRollbacks();
    vi.restoreAllMocks();
});

describe('rollbackRegistry — ordering & lifecycle', () => {
    it('runs rollbacks in LIFO order (c, b, a for register a, b, c)', () => {
        const order: string[] = [];
        registerRollback(() => order.push('a'));
        registerRollback(() => order.push('b'));
        registerRollback(() => order.push('c'));

        executeRollbacks();

        expect(order).toEqual(['c', 'b', 'a']);
    });

    it('empties the registry after executing (a second run is a no-op)', () => {
        const fn = vi.fn();
        registerRollback(fn);

        executeRollbacks();
        executeRollbacks();

        expect(fn).toHaveBeenCalledTimes(1);
    });

    it('clearRollbacks discards without running any rollback', () => {
        const fn = vi.fn();
        registerRollback(fn);

        clearRollbacks();
        executeRollbacks();

        expect(fn).not.toHaveBeenCalled();
    });

    it('executeRollbacks on an empty registry is a harmless no-op', () => {
        expect(() => executeRollbacks()).not.toThrow();
    });

    it('rollbacks registered after a run are handled by the next run', () => {
        const first = vi.fn();
        registerRollback(first);
        executeRollbacks();

        const second = vi.fn();
        registerRollback(second);
        executeRollbacks();

        expect(first).toHaveBeenCalledTimes(1);
        expect(second).toHaveBeenCalledTimes(1);
    });
});

describe('rollbackRegistry — resilience (FU-539 fix)', () => {
    it('a throwing rollback does not strand the others; all run and the registry empties', () => {
        const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
        const order: string[] = [];
        // Registered a, b, c → executed c, b, a. Make the FIRST-executed (c)
        // throw and assert b and a still run.
        registerRollback(() => order.push('a'));
        registerRollback(() => order.push('b'));
        registerRollback(() => {
            order.push('c');
            throw new Error('undo failed');
        });

        expect(() => executeRollbacks()).not.toThrow();

        expect(order).toEqual(['c', 'b', 'a']);
        expect(consoleError).toHaveBeenCalled();
        // Registry drained even though one rollback threw.
        const later = vi.fn();
        registerRollback(later);
        executeRollbacks();
        expect(later).toHaveBeenCalledTimes(1);
    });

    it('survives multiple throwing rollbacks in one sweep', () => {
        vi.spyOn(console, 'error').mockImplementation(() => {});
        const ok = vi.fn();
        registerRollback(ok);
        registerRollback(() => { throw new Error('boom-1'); });
        registerRollback(() => { throw new Error('boom-2'); });

        expect(() => executeRollbacks()).not.toThrow();
        expect(ok).toHaveBeenCalledTimes(1);
    });

    it('a rollback that registers another rollback mid-sweep drains fully (re-entrancy sanity)', () => {
        const order: string[] = [];
        registerRollback(() => order.push('base'));
        registerRollback(() => {
            order.push('outer');
            // Re-entrant registration — the while-loop keeps popping until
            // the stack is empty, so this new one runs in the same sweep.
            registerRollback(() => order.push('inner'));
        });

        executeRollbacks();

        expect(order).toEqual(['outer', 'inner', 'base']);
    });
});
