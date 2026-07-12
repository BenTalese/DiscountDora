// @vitest-environment jsdom
// FU-539 resilience layer — globalErrorHandler boot module. It is the single
// place that turns a crash (Vue render error, window.onerror, an unhandled
// promise rejection) into: run the optimistic-rollback registry, tell the user,
// ship the error to the backend log stream. If executeRollbacks doesn't fire, an
// optimistic UI update is stranded showing a value the server never accepted.
//
// The rollback registry is deliberately REAL — the wiring under test is
// "a global error → executeRollbacks". The module registers window listeners at
// import time, so it is imported ONCE at the top (re-importing would stack
// duplicate listeners on the shared jsdom window).
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const h = vi.hoisted(() => ({
    notify: vi.fn(),
    clientError: vi.fn(),
}));

vi.mock('quasar', () => ({ Notify: { create: h.notify } }));
// boot() normally wraps a callback for Quasar's boot pipeline; unwrap it so the
// module's default export is the plain callback we can invoke with a fake app.
vi.mock('quasar/wrappers', () => ({ boot: (fn: unknown) => fn }));
vi.mock('src/composables/useClientLogger', () => ({
    clientLog: { error: h.clientError },
}));

import bootErrorHandler from 'src/boot/globalErrorHandler';
import {
    clearRollbacks,
    registerRollback,
} from 'src/services/errorHandling/rollbackRegistry';

const originalOnError = window.onerror;

beforeEach(() => {
    vi.clearAllMocks();
    clearRollbacks();
});

afterEach(() => {
    window.onerror = originalOnError;
});

describe('globalErrorHandler — unhandledrejection', () => {
    it('fires the rollback registry exactly once, notifies, and logs origin=promise', () => {
        const rollback = vi.fn();
        registerRollback(rollback);

        window.dispatchEvent(
            new PromiseRejectionEvent('unhandledrejection', {
                reason: new Error('kaboom'),
                promise: Promise.resolve(),
            }),
        );

        expect(rollback).toHaveBeenCalledTimes(1);
        expect(h.notify).toHaveBeenCalledWith({ type: 'oopsie' });
        expect(h.clientError).toHaveBeenCalledWith(
            'kaboom',
            expect.objectContaining({ origin: 'promise' }),
        );
    });
});

describe('globalErrorHandler — window.onerror', () => {
    it('runs executeRollbacks and reports origin=window', () => {
        const rollback = vi.fn();
        registerRollback(rollback);

        window.onerror!('boom', 'app.js', 1, 2, new Error('boom'));

        expect(rollback).toHaveBeenCalledTimes(1);
        expect(h.notify).toHaveBeenCalledWith({ type: 'oopsie' });
        expect(h.clientError).toHaveBeenCalledWith(
            'boom',
            expect.objectContaining({ origin: 'window' }),
        );
    });
});

describe('globalErrorHandler — Vue app.config.errorHandler', () => {
    it('installs a handler that runs rollbacks, notifies, and logs origin=vue', () => {
        const app = { config: {} as { errorHandler?: (...a: unknown[]) => void } };
        // Default export is the (unwrapped) boot callback.
        (bootErrorHandler as unknown as (ctx: { app: typeof app }) => void)({ app });

        const rollback = vi.fn();
        registerRollback(rollback);

        app.config.errorHandler!(new Error('render fail'), null, 'render');

        expect(rollback).toHaveBeenCalledTimes(1);
        expect(h.notify).toHaveBeenCalledWith({ type: 'oopsie' });
        expect(h.clientError).toHaveBeenCalledWith(
            'render fail',
            expect.objectContaining({ origin: 'vue' }),
        );
    });
});
