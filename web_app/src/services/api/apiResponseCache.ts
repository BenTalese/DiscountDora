// Service-worker cache of API GET responses — eviction on user change.
//
// `quasar.config.ts` registers a Workbox `NetworkFirst` rule over every
// `/api/**` GET into the `dora-api` cache. That is what makes the app
// read-only-usable when Dora is unreachable (owner decision 2026-08-23:
// offline is read-only, so this cache IS the offline story).
//
// The cache is keyed by URL alone, with no notion of who was signed in when
// the response was stored. On a multi-user install that means the next person
// to sign in on the same device can be served the previous user's pantry,
// lists and recipes out of cache. Sign-out is a soft router push, not a
// reload, so nothing else clears it.
//
// Same reasoning as FU-355's `clearAllListState()`, but the stakes are higher:
// that leaked filter shapes, this would leak content. Called on explicit
// logout and on a 401 (which can mean "someone else's session started").
//
// Matches on substring rather than an exact name because Workbox may decorate
// a runtime cache name with its own prefix/suffix depending on version and
// registration scope — a rename or an upgrade must not silently turn this into
// a no-op.
const API_CACHE_NAME_FRAGMENT = 'dora-api';

/** Delete the cached API GET responses. Best-effort and never throws: the
 *  Cache API is absent in some contexts (Capacitor's WebView with no service
 *  worker, private-mode quirks, non-secure origins) and a failed eviction must
 *  not break signing out. */
export async function clearApiResponseCache(): Promise<void> {
    try {
        if (typeof caches === 'undefined') return;
        const names = await caches.keys();
        await Promise.all(
            names
                .filter((name) => name.includes(API_CACHE_NAME_FRAGMENT))
                .map((name) => caches.delete(name)),
        );
    } catch (err) {
        console.warn('[apiResponseCache] could not clear cached API responses', err);
    }
}
