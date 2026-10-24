/* C-9.8 — Push handlers.
 *
 * In the PWA build this file is pulled INTO the Workbox worker (`sw.js`)
 * via `importScripts` (quasar.config.ts) — one worker, one registration.
 * It used to be registered on its own, and because a registration is keyed
 * by scope (both default to `/`) that replaced the Workbox worker every
 * time Settings → Notifications opened (finalisation 17-R1). In SPA / dev
 * mode, where there is no `sw.js`, `usePushSubscription` still registers
 * this file standalone, so the `install` / `activate` handlers below stay:
 * inside the Workbox worker they are harmless duplicates of what Workbox
 * already does (`skipWaiting` / `clientsClaim`). Handles two events:
 *
 *   - `push`              show a notification from the payload
 *   - `notificationclick` focus an existing tab on the right route or
 *                         open a new one
 *
 * Deliberately no fetch handler, no caching — this SW exists only so
 * the browser is willing to deliver push payloads to us. The payload
 * shape is fixed by `dora_api/features/alerts/send_alerts_push.py`'s
 * `_payload_for`; see that function before changing field reads here.
 */

self.addEventListener('install', (_event) => {
    // Skip waiting so an updated SW activates on the next page load
    // rather than waiting for every Dora tab to close.
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    // Claim open clients immediately so newly-subscribed tabs route
    // through us without a reload.
    event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
    if (!event.data) return;
    let payload = {};
    try {
        payload = event.data.json();
    } catch (_err) {
        // Some push services deliver empty/non-JSON pings (e.g. as
        // wake-up signals). Render a generic notification rather than
        // dropping it silently.
        payload = { title: 'Dashy Dora', body: 'You have new alerts.' };
    }
    const title = payload.title || 'Dashy Dora';
    const options = {
        body: payload.body || '',
        // The 192px PWA icon doubles as the notification badge; mobile
        // platforms downscale automatically.
        icon: '/icons/web-app-manifest-192x192.png',
        badge: '/icons/web-app-manifest-192x192.png',
        // Tag dedupes when the same alert key is pushed twice (e.g. a
        // user with two devices both online) — the second one replaces
        // the first on the system tray rather than stacking.
        tag: payload.alert_id || undefined,
        renotify: false,
        data: {
            url: payload.url || '/#/?alerts=open',
            alert_id: payload.alert_id || null,
        },
    };
    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const targetUrl = (event.notification.data && event.notification.data.url) || '/#/?alerts=open';
    event.waitUntil((async () => {
        const allClients = await self.clients.matchAll({
            type: 'window',
            includeUncontrolled: true,
        });
        // Reuse an existing tab on the same origin if there is one;
        // navigating it is less jarring than spawning a new window.
        for (const client of allClients) {
            try {
                const url = new URL(client.url);
                if (url.origin === self.location.origin) {
                    await client.focus();
                    if ('navigate' in client) {
                        await client.navigate(targetUrl);
                    }
                    return;
                }
            } catch (_err) { /* fall through to openWindow */ }
        }
        await self.clients.openWindow(targetUrl);
    })());
});
