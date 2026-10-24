// @vitest-environment jsdom
// Finalisation 17-R1 — push must attach to the registration that already
// controls the page, never register `/push-sw.js` beside it. A registration
// is keyed by scope, so registering a second script at `/` *replaces* the
// Workbox worker (offline cache gone) and fires `controllerchange`, which the
// PWA lifecycle layer reads as "a new version is ready".
import { describe, expect, it, vi } from 'vitest';

vi.mock('src/services/api/alertApiService', () => ({ default: class {} }));

import { resolvePushRegistration } from 'src/composables/usePushSubscription';

function fakeContainer(existing: object | undefined) {
    const registered = { scope: '/', tag: 'push-only' };
    const container = {
        getRegistration: vi.fn(() => Promise.resolve(existing)),
        register: vi.fn(() => Promise.resolve(registered)),
        ready: Promise.resolve(existing ?? registered),
    };
    return { container: container as unknown as ServiceWorkerContainer, registered, calls: container };
}

describe('resolvePushRegistration', () => {
    it('attaches to the registration that already controls the page and registers nothing', async () => {
        const workbox = { scope: '/', tag: 'workbox sw.js' };
        const { container, calls } = fakeContainer(workbox);

        const result = await resolvePushRegistration(container);

        expect(result).toBe(workbox);
        expect(calls.register).not.toHaveBeenCalled();
    });

    it('registers the push-only worker only when nothing is registered (SPA / dev)', async () => {
        const { container, calls, registered } = fakeContainer(undefined);

        const result = await resolvePushRegistration(container);

        expect(result).toBe(registered);
        expect(calls.register).toHaveBeenCalledTimes(1);
        expect(calls.register).toHaveBeenCalledWith('/push-sw.js');
    });
});
