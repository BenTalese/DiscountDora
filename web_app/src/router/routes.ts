import 'vue-router';
import type { RouteRecordRaw } from 'vue-router';

declare module 'vue-router' {
    interface RouteMeta {
        // Set on every navigable route; router afterEach writes
        // `${title} · Discount Dora` to document.title so browser tabs are
        // useful when several are open. Dynamic detail pages can override
        // at runtime by setting document.title in onMounted.
        title?: string;
    }
}

const routes: RouteRecordRaw[] = [
    // Login lives outside MainLayout so the drawer/header don't render while
    // the user is signed out.
    {
        path: '/login',
        component: () => import('pages/LoginPage.vue'),
        meta: { title: 'Sign in' }
    },
    // ── A1 out-of-band auth flows. Each one lives outside MainLayout so
    // signed-out users (or someone clicking a verify link in a fresh
    // browser) doesn't see the nav chrome.
    {
        path: '/verify-email',
        component: () => import('pages/VerifyEmailPage.vue'),
        meta: { title: 'Verify email' },
    },
    {
        path: '/forgot-password',
        component: () => import('pages/ForgotPasswordPage.vue'),
        meta: { title: 'Forgot password' },
    },
    {
        path: '/reset-password',
        component: () => import('pages/ResetPasswordPage.vue'),
        meta: { title: 'Reset password' },
    },
    {
        path: '/confirm-email-change',
        component: () => import('pages/ConfirmEmailChangePage.vue'),
        meta: { title: 'Confirm new email' },
    },
    // First-run wizard. Uses its own minimal layout so the nav drawer /
    // dashboard chrome don't peek through while the user is still being
    // set up. Router guard forces incomplete users here.
    {
        path: '/welcome',
        component: () => import('layouts/WelcomeLayout.vue'),
        children: [
            {
                path: '',
                component: () => import('pages/onboarding/WelcomeWizard.vue'),
                meta: { title: 'Welcome' }
            },
        ],
    },
    {
        path: '/',
        component: () => import('layouts/MainLayout.vue'),
        children: [
            // Dashboard is the landing page; stock overview moves to /stock.
            { path: '', component: () => import('pages/DashboardPage.vue'), meta: { title: 'Dashboard' } },
            { path: 'stock', component: () => import('pages/StockOverview.vue'), meta: { title: 'Stock' } },
            { path: 'stocktake', component: () => import('pages/StocktakePage.vue'), meta: { title: 'Stocktake' } },
            { path: 'stocktake/run', component: () => import('pages/StocktakeRunner.vue'), meta: { title: 'Stocktake · running' } },
            { path: 'stock/:id', component: () => import('pages/StockItemDetailPage.vue'), meta: { title: 'Stock item' } },
            { path: 'product-search', component: () => import('pages/ProductSearch.vue'), meta: { title: 'Product search' } },
            { path: 'price-history', component: () => import('pages/PriceHistoryPage.vue'), meta: { title: 'Price history' } },
            { path: 'my-products', component: () => import('pages/MyProductsPage.vue'), meta: { title: 'My products' } },
            { path: 'help', component: () => import('pages/HelpPage.vue'), meta: { title: 'Help' } },
            // B5 stopgap — minimal alerts list, reuses alertStore (same
            // data as the header bell). The full alerts control centre is
            // the C-wave design brief.
            { path: 'alerts', component: () => import('pages/AlertsPage.vue'), meta: { title: 'Alerts' } },
            { path: 'tts-test', component: () => import('pages/TtsTestPage.vue'), meta: { title: 'TTS test' } },
            { path: 'help/dora', component: () => import('pages/DoraHelpPage.vue'), meta: { title: 'About Dora' } },
            // A8 + 2026-06-12 migration — recipe routes all live under
            // `/cookbook` (the cookbook is the page; a recipe is an
            // item in it). Legacy `/recipes*` redirects were retired
            // 2026-06-12 — pre-release, no live bookmarks to preserve,
            // no external links written yet. A user that types
            // `/recipes/<id>` now hits the 404 page (which is fine).
            { path: 'cookbook', component: () => import('pages/RecipesOverview.vue'), meta: { title: 'Cookbook' } },
            { path: 'cookbook/:id', component: () => import('pages/RecipeDetailPage.vue'), meta: { title: 'Recipe' } },
            { path: 'cookbook/:id/cook', component: () => import('pages/RecipeCookMode.vue'), meta: { title: 'Cook mode' } },
            { path: 'meal-plans', component: () => import('pages/MealPlansOverview.vue'), meta: { title: 'Meal plans' } },
            { path: 'meal-plans/templates', component: () => import('pages/MealPlanTemplatesPage.vue'), meta: { title: 'Meal plan templates' } },
            {
                path: 'shopping-lists',
                component: () => import('pages/ShoppingListsOverview.vue'),
                meta: { title: 'Shopping lists' },
                // P6-01 Chunk 5 — the detail page is the canonical surface
                // (with a list-selector in its header). The landing's job is
                // to pick a target list and route there. We do it as a
                // **route-level `beforeEnter`** rather than an
                // in-component `router.replace` in `onMounted`: the
                // MainLayout wraps the router-view in <FadeTransition
                // mode="out-in">, and a mount-time redirect unmounts the
                // entering component mid-transition, which wedges the
                // global transition state and renders subsequent pages
                // blank. A route guard resolves before the component
                // mounts, so no transition is ever in flight to wedge.
                beforeEnter: async () => {
                    const { useShoppingListStore } = await import('src/stores/shoppingListStore');
                    const store = useShoppingListStore();
                    if (store.summaries.length === 0 && !store.loading) {
                        try {
                            await store.refreshAsync();
                        } catch {
                            // Fall through — Overview will render the
                            // empty / error state.
                        }
                    }
                    // UX-v2 §3.3 — the "next up" pick is a server-owned rule
                    // (live shop > first date-wise after the last completed >
                    // earliest pending > most recently completed). The guard
                    // just follows the flag; no date logic lives here.
                    const next = store.summaries.find((s) => s.is_next_up);
                    if (next) return `/shopping-lists/${next.shopping_list_id}`;
                    // No lists at all — render the empty state.
                    return;
                },
            },
            { path: 'shopping-lists/templates', component: () => import('pages/ShoppingListTemplates.vue'), meta: { title: 'Shopping list templates' } },
            // UX-v2: detail is the single shopping surface for every status
            // (S4: plural title; the old /shop route + page were merged in).
            { path: 'shopping-lists/:id', component: () => import('pages/ShoppingListDetail.vue'), meta: { title: 'Shopping lists' } },
            // P2-11 — PWA-shortcut landing page that redirects to whichever
            // list is live / next up. Lightweight stub; see
            // pages/ShopNowRedirect.vue.
            { path: 'shop-now', component: () => import('pages/ShopNowRedirect.vue'), meta: { title: 'Shop now' } },
            { path: 'reports', component: () => import('pages/ReportsPage.vue'), meta: { title: 'Reports' } },
            { path: 'waste', component: () => import('pages/WastePage.vue'), meta: { title: 'Waste' } },
            // In-layout error pages (F3). These keep the header/drawer
            // around so the user can navigate away without a full reload.
            // The bare-URL catch-all at the bottom of this file still
            // renders the fullscreen ErrorNotFound page for typo'd routes.
            {
                path: 'errors/not-found',
                component: () => import('pages/errors/ErrorPageNotFound.vue'),
                meta: { title: 'Not found' }
            },
            {
                path: 'errors/server',
                component: () => import('pages/errors/ErrorServer.vue'),
                meta: { title: 'Server error' }
            },
            // Data Management shell. Greenfield section (N1) — placeholder
            // sub-pages for now; N2-N5 fill them with backup/import/export
            // /barcode functionality. Pattern mirrors SettingsShell.
            {
                path: 'data',
                component: () => import('pages/DataManagement.vue'),
                redirect: '/data/backup',
                meta: { title: 'Data' },
                children: [
                    {
                        path: 'backup',
                        component: () => import('pages/data/BackupRestore.vue'),
                        meta: { title: 'Backup & restore' }
                    },
                    {
                        path: 'import',
                        component: () => import('pages/data/DataImport.vue'),
                        meta: { title: 'Import' }
                    },
                    {
                        path: 'export',
                        component: () => import('pages/data/ExportPrint.vue'),
                        meta: { title: 'Export & print' }
                    },
                    {
                        path: 'barcodes',
                        component: () => import('pages/data/BarcodesQR.vue'),
                        meta: { title: 'Barcodes & QR' }
                    }
                ]
            },
            // Settings shell hosts sub-routes via its own <router-view>.
            // Personal sections live at /settings/*, admin/global sections at
            // /settings/admin/* (gated by the global router guard).
            {
                path: 'settings',
                component: () => import('pages/SettingsShell.vue'),
                redirect: '/settings/preferences',
                meta: { title: 'Settings' },
                children: [
                    {
                        path: 'preferences',
                        component: () => import('pages/settings/PreferencesSettings.vue'),
                        meta: { title: 'Preferences' }
                    },
                    {
                        path: 'stock-locations',
                        component: () => import('pages/settings/StockLocationsSettings.vue'),
                        meta: { title: 'Stock locations' }
                    },
                    {
                        path: 'stock-groups',
                        component: () => import('pages/settings/StockGroupsSettings.vue'),
                        meta: { title: 'Stock groups' }
                    },
                    {
                        path: 'recipe-vocab',
                        component: () => import('pages/settings/RecipeVocabSettings.vue'),
                        meta: { title: 'Recipe tags & categories' }
                    },
                    {
                        path: 'account',
                        component: () => import('pages/settings/AccountSettings.vue'),
                        meta: { title: 'Account' }
                    },
                    {
                        path: 'about',
                        component: () => import('pages/settings/AboutSettings.vue'),
                        meta: { title: 'About' }
                    },
                    {
                        path: 'admin/merchants',
                        component: () => import('pages/settings/MerchantsSettings.vue'),
                        meta: { title: 'Merchants' }
                    },
                    {
                        path: 'admin/users',
                        component: () => import('pages/settings/UsersAdminSettings.vue'),
                        meta: { title: 'Users' }
                    },
                    {
                        path: 'admin/system',
                        component: () => import('pages/settings/SystemSettings.vue'),
                        meta: { title: 'System' }
                    },
                    {
                        path: 'admin/audit-log',
                        component: () => import('pages/settings/AuditLogSettings.vue'),
                        meta: { title: 'Audit log' }
                    }
                ]
            }
        ]
    },

    // Always leave this as last one,
    // but you can also remove it
    {
        path: '/:catchAll(.*)*',
        component: () => import('pages/ErrorNotFound.vue'),
        meta: { title: 'Not found' }
    }
];

export default routes;
