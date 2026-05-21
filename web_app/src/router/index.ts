import { defineRouter } from '#q-app/wrappers';
import { Notify } from 'quasar';
import { useAuthStore } from 'src/stores/authStore';
import { createMemoryHistory, createRouter, createWebHashHistory, createWebHistory } from 'vue-router';

import routes from './routes';

const PUBLIC_ROUTES = new Set<string>(['/login']);

export default defineRouter(function (/* { store, ssrContext } */) {
    const createHistory = process.env.SERVER
        ? createMemoryHistory
        : process.env.VUE_ROUTER_MODE === 'history'
          ? createWebHistory
          : createWebHashHistory;

    const Router = createRouter({
        scrollBehavior: () => ({ left: 0, top: 0 }),
        routes,

        // Leave this as is and make changes in quasar.conf.js instead!
        // quasar.conf.js -> build -> vueRouterMode
        // quasar.conf.js -> build -> publicPath
        history: createHistory(process.env.VUE_ROUTER_BASE)
    });

    Router.onError((err) => {
        console.error('Vue Router Error: ' + err.message);
        Notify.create({ type: 'oopsie' });
    });

    // Global auth guard. Bootstraps the session on first navigation, then
    // either lets the request through, redirects to /login (when a protected
    // route needs a session), or redirects to / (when an already-logged-in
    // user lands on /login).
    Router.beforeEach(async (to) => {
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

        // Block non-admins from the global/admin settings tree. They get
        // bounced to the personal Preferences page so they don't end up on a
        // blank screen if they navigated by URL.
        if (to.path.startsWith('/settings/admin') && !authStore.currentUser?.is_admin) {
            return { path: '/settings/preferences' };
        }
        return true;
    });

    return Router;
});
