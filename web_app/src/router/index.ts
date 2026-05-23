import { defineRouter } from '#q-app/wrappers';
import { Notify } from 'quasar';
import { useAuthStore } from 'src/stores/authStore';
import { createMemoryHistory, createRouter, createWebHashHistory, createWebHistory } from 'vue-router';

import routes from './routes';

const PUBLIC_ROUTES = new Set<string>(['/login']);
// Routes we allow incomplete-onboarding users to visit without the redirect.
// /welcome is the wizard itself; the rest are safety hatches (sign out,
// error pages so a crash mid-wizard doesn't lock the user out).
const ONBOARDING_BYPASS = new Set<string>([
    '/welcome',
    '/errors/not-found',
    '/errors/server',
]);

export default defineRouter(function (/* { store, ssrContext } */) {
    const createHistory = process.env.SERVER
        ? createMemoryHistory
        : process.env.VUE_ROUTER_MODE === 'history'
          ? createWebHistory
          : createWebHashHistory;

    const ROUTER = createRouter({
        scrollBehavior: () => ({ left: 0, top: 0 }),
        routes,

        // Leave this as is and make changes in quasar.conf.js instead!
        // quasar.conf.js -> build -> vueRouterMode
        // quasar.conf.js -> build -> publicPath
        history: createHistory(process.env.VUE_ROUTER_BASE)
    });

    // Navigation errors (lazy-loaded chunk failed to fetch, etc) route the
    // user to /errors/server with a retry rather than leaving them on a
    // half-loaded screen. We tag with the error message so the report-this
    // link in PageErrorState carries useful context.
    ROUTER.onError((err) => {
        console.error('Vue Router Error: ' + err.message);
        Notify.create({
            type: 'negative',
            position: 'top',
            message: "Couldn't load that page. Pointing you somewhere safer.",
            timeout: 3500,
        });
        // Avoid an infinite loop if /errors/server itself fails to load.
        if (typeof window !== 'undefined' && window.location.pathname.endsWith('/errors/server')) {
            return;
        }
        try {
            void ROUTER.push({
                path: '/errors/server',
                query: { ref: err.message.slice(0, 80) },
            });
        } catch {
            if (typeof window !== 'undefined') {
                window.location.assign('/');
            }
        }
    });

    // Global auth guard. Bootstraps the session on first navigation, then
    // either lets the request through, redirects to /login (when a protected
    // route needs a session), or redirects to / (when an already-logged-in
    // user lands on /login).
    ROUTER.beforeEach(async (to) => {
        const authStore = useAuthStore();
        if (!authStore.isBootstrapped) {
            await authStore.bootstrapAsync();
        }

        const isPublic = PUBLIC_ROUTES.has(to.path);
        if (!isPublic && !authStore.isAuthenticated()) {
            return { path: '/login', query: { redirect: to.fullPath } };
        }
        if (to.path === '/login' && authStore.isAuthenticated()) {
            return { path: '/' };
        }

        // First-run onboarding (F1): authed users whose wizard isn't
        // finished get bounced to /welcome unless they're heading to a
        // bypass route. If we don't yet know the state (boot before the
        // backend grew the column, for instance), we let them through —
        // never trap the user in an opaque redirect loop.
        if (
            authStore.isAuthenticated()
            && !ONBOARDING_BYPASS.has(to.path)
            && authStore.currentUser?.onboarding_completed_at === null
        ) {
            return { path: '/welcome' };
        }
        // Conversely, an already-completed user landing on /welcome (e.g.
        // a stale tab) is bounced back to the dashboard.
        if (
            to.path === '/welcome'
            && authStore.isAuthenticated()
            && authStore.currentUser?.onboarding_completed_at !== null
        ) {
            return { path: '/' };
        }

        // Block non-admins from the global/admin settings tree. They get
        // bounced to the personal Preferences page so they don't end up on a
        // blank screen if they navigated by URL.
        if (to.path.startsWith('/settings/admin') && !authStore.currentUser?.is_admin) {
            return { path: '/settings/preferences' };
        }
        return true;
    });

    // Browser tab title — picks the nearest matched-route's meta.title so
    // nested settings pages get their leaf title (e.g. "Preferences"), not
    // the parent ("Settings"). Falls back to the app name if a route has
    // no title set.
    const APP_NAME = 'Discount Dora';
    ROUTER.afterEach((to) => {
        if (typeof document === 'undefined') return;
        const titled = [...to.matched].reverse().find((r) => r.meta?.title);
        const leaf = titled?.meta.title;
        document.title = leaf ? `${leaf} | ${APP_NAME}` : APP_NAME;
    });

    return ROUTER;
});
