import 'vue-router';
import type { RouteRecordRaw } from 'vue-router';

declare module 'vue-router' {
    interface RouteMeta {
        // Set on every navigable route; router afterEach writes
        // `${title} · Dashy Dora` to document.title so browser tabs are
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
    // fresh-install first-admin setup. Lives outside MainLayout
    // for the same reason as /login. The router guard sends visitors here
    // when bootstrapRequired is true, and bounces them away once an admin
    // exists.
    {
        path: '/setup',
        component: () => import('pages/SetupAdminPage.vue'),
        meta: { title: 'Set up Dashy Dora' },
    },
    // native app first-run instance picker. Only reachable when
    // Capacitor.isNativePlatform() is true and no backend URL is stored
    // yet; the router guard bounces web visitors to /settings/about.
    {
        path: '/setup/backend',
        component: () => import('pages/setup/BackendSetupPage.vue'),
        meta: { title: 'Choose your instance' },
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
            // PROPOSAL_STOCKTAKE_MODE §5.1 — no landing page. Tapping
            // Stocktake drops straight into the focused runner; empty-
            // queue state is handled inside the runner itself. The
            // legacy `/stocktake/run` sub-route is redirected below for
            // any bookmark / deep link that predates this change.
            { path: 'stocktake', component: () => import('pages/StocktakeRunner.vue'), meta: { title: 'Stocktake' } },
            { path: 'stocktake/run', redirect: '/stocktake' },
            { path: 'stock/:id', component: () => import('pages/StockItemDetailPage.vue'), meta: { title: 'Stock item' } },
            // Phase D / FU-186 — the in-app `/product-search` route is gone.
            // The Product Search nav entry now opens `AppSetting.product_search_url`
            // in a new tab when product data is present. No route remains here.
            { path: 'price-history', component: () => import('pages/PriceHistoryPage.vue'), meta: { title: 'Price history' } },
            { path: 'my-products', component: () => import('pages/MyProductsPage.vue'), meta: { title: 'My products' } },
            { path: 'help', component: () => import('pages/HelpPage.vue'), meta: { title: 'Help' } },
            // minimal alerts list, reuses alertStore (same
            // data as the header bell). The full alerts control centre is
            // the C-wave design brief.
            { path: 'alerts', component: () => import('pages/AlertsPage.vue'), meta: { title: 'Alerts' } },
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
            // FU-304 closed 2026-07-07 — Direction A won the A/B experiment;
            // `/meal-plans/board` (Direction B) is retired. Redirect any
            // deep-links / bookmarks back to the surviving planner surface.
            { path: 'meal-plans/board', redirect: '/meal-plans' },
            // FU-308 (2026-07-07) — page repurposed to Rotating template
            // sets only; per-template CRUD moved to the planner's drawer.
            // Route path kept for existing deep-links / bookmarks.
            { path: 'meal-plans/templates', component: () => import('pages/MealPlanTemplatesPage.vue'), meta: { title: 'Rotating template sets' } },
            // FU-317 Chunk 5 — reconcile page (single-runner-style, one
            // entry at a time, five verbs). Empty state is handled by the
            // runner itself; no separate landing.
            { path: 'meal-plans/reconcile', component: () => import('pages/MealReconcilePage.vue'), meta: { title: 'Reconcile past meals' } },
            {
                path: 'shopping-lists',
                component: () => import('pages/ShoppingListsOverview.vue'),
                meta: { title: 'Shopping lists' },
                // the detail page is the canonical surface
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
            // PWA-shortcut landing page that redirects to whichever
            // list is live / next up. Lightweight stub; see
            // pages/ShopNowRedirect.vue.
            { path: 'shop-now', component: () => import('pages/ShopNowRedirect.vue'), meta: { title: 'Shop now' } },
            { path: 'reports', component: () => import('pages/ReportsPage.vue'), meta: { title: 'Reports' } },
            // C-waste W6 — the standalone /waste page is gone. Capture
            // moved to a row action on the stock-item expiry dropdown;
            // expiry rescue surfaces via Needs-your-attention on the
            // dashboard. Bookmarks 404 by design (no redirect — pre-
            // release, per PROPOSAL_WASTE_MINIMISATION §2 D10).
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
            // the `/data` shell + its DataManagement.vue host are
            // retired. Backup + Import now live under Settings → Admin →
            // Data (see the settings route tree below). Every child path
            // that used to hang off `/data` is preserved as a redirect so
            // stale bookmarks, prior emails, and the retired PWA shortcut
            // still land somewhere useful; the parent `/data` redirect
            // catches direct visits to the shell URL itself.
            {
                path: 'data',
                redirect: '/settings/admin/data/backup'
            },
            {
                path: 'data/backup',
                redirect: '/settings/admin/data/backup'
            },
            {
                path: 'data/import',
                redirect: '/settings/admin/data/import'
            },
            {
                path: 'data/barcodes',
                redirect: '/settings/kitchen-setup/qr-labels'
            },
            {
                // The redirect points at Backup so a stale bookmark lands
                // on the closest sibling rather than 404. Print now lives
                // in-context on each printable surface.
                path: 'data/export',
                redirect: '/settings/admin/data/backup'
            },
            // Settings shell hosts sub-routes via its own <router-view>.
            // Three top-level groups (IMPL_PLAN_SETTINGS_REBUILD §2.1):
            //   Account — identity + per-user preferences
            //   Kitchen setup — user-curated reference data (stock taxonomy,
            //     stores, recipe taxonomies)
            //   Admin · global — install-wide concerns (gated by the router
            //     guard in `router/index.ts`)
            // Phase 1 = routing structure only; Phase 2 splits the monoliths
            // (Preferences, RecipeVocab, System) into focused pages.
            {
                path: 'settings',
                component: () => import('pages/SettingsShell.vue'),
                redirect: '/settings/account',
                meta: { title: 'Settings' },
                children: [
                    // Account group ────────────────────────────────────────
                    {
                        path: 'account',
                        component: () => import('pages/settings/AccountSettings.vue'),
                        meta: { title: 'Account' }
                    },
                    {
                        // Phase 2: Appearance-only after the split below.
                        path: 'preferences',
                        component: () => import('pages/settings/PreferencesSettings.vue'),
                        meta: { title: 'Preferences' }
                    },
                    {
                        path: 'notifications',
                        component: () => import('pages/settings/NotificationsSettings.vue'),
                        meta: { title: 'Notifications' }
                    },
                    {
                        path: 'money',
                        component: () => import('pages/settings/MoneySettings.vue'),
                        meta: { title: 'Money' }
                    },
                    {
                        path: 'voice',
                        component: () => import('pages/settings/VoiceSettings.vue'),
                        meta: { title: 'Voice' }
                    },
                    {
                        path: 'nutrition',
                        component: () => import('pages/settings/NutritionSettings.vue'),
                        meta: { title: 'Nutrition' }
                    },
                    {
                        // per-user Assistant config (provider +
                        // URL/model/API key). Sibling to MoneySettings /
                        // NutritionSettings; the install-wide master flag lives
                        // separately on AdminSystemAssistantSettings.
                        path: 'assistant',
                        component: () => import('pages/settings/AssistantSettings.vue'),
                        meta: { title: 'Assistant' }
                    },
                    {
                        path: 'about',
                        component: () => import('pages/settings/AboutSettings.vue'),
                        meta: { title: 'About' }
                    },
                    // Kitchen setup group ──────────────────────────────────
                    {
                        path: 'kitchen-setup/stock-locations',
                        component: () => import('pages/settings/StockLocationsSettings.vue'),
                        meta: { title: 'Stock locations' }
                    },
                    {
                        path: 'kitchen-setup/stock-groups',
                        component: () => import('pages/settings/StockGroupsSettings.vue'),
                        meta: { title: 'Stock groups' }
                    },
                    // Stores moved out of Admin per §2.1 — it's user-curated
                    // retail data, not install governance.
                    {
                        path: 'kitchen-setup/stores',
                        component: () => import('pages/settings/StoresSettings.vue'),
                        meta: { title: 'Stores' }
                    },
                    // Phase 2: Recipe vocab splits 1 → 5 focused pages. The
                    // first four share TaxonomyManagerPage; dietary tags keeps
                    // its bespoke editor (grouping field).
                    {
                        path: 'kitchen-setup/recipe-cuisines',
                        component: () => import('pages/settings/RecipeCuisinesSettings.vue'),
                        meta: { title: 'Recipe cuisines' }
                    },
                    {
                        path: 'kitchen-setup/recipe-categories',
                        component: () => import('pages/settings/RecipeCategoriesSettings.vue'),
                        meta: { title: 'Recipe categories' }
                    },
                    {
                        path: 'kitchen-setup/recipe-tools',
                        component: () => import('pages/settings/RecipeToolsSettings.vue'),
                        meta: { title: 'Recipe tools' }
                    },
                    {
                        path: 'kitchen-setup/recipe-meal-slots',
                        component: () => import('pages/settings/RecipeMealSlotsSettings.vue'),
                        meta: { title: 'Recipe meal slots' }
                    },
                    {
                        path: 'kitchen-setup/recipe-dietary-tags',
                        component: () => import('pages/settings/RecipeDietaryTagsSettings.vue'),
                        meta: { title: 'Recipe dietary tags' }
                    },
                    // QR labels (Print sheet). Relocated from
                    // `/data/barcodes`; the old page's Scan tab was retired
                    // (duplicative with Stock Overview's scan button). Still
                    // gated by the install-wide `scanning_enabled` flag; the
                    // sidebar hides the entry when off, the page itself shows
                    // an "ask an admin to enable it" banner if reached by URL.
                    {
                        path: 'kitchen-setup/qr-labels',
                        component: () => import('pages/settings/QrLabels.vue'),
                        meta: { title: 'QR labels' }
                    },
                    // Backwards-compat redirects for moved/split routes.
                    // Bookmarks, email deep-links and HelpPage entries that
                    // shipped under the old paths keep working. Drop these
                    // only when there's no surface still referencing them.
                    {
                        path: 'stock-locations',
                        redirect: '/settings/kitchen-setup/stock-locations'
                    },
                    {
                        path: 'stock-groups',
                        redirect: '/settings/kitchen-setup/stock-groups'
                    },
                    {
                        // Old single recipe-vocab page → first of the five.
                        path: 'recipe-vocab',
                        redirect: '/settings/kitchen-setup/recipe-cuisines'
                    },
                    {
                        path: 'kitchen-setup/recipe-vocab',
                        redirect: '/settings/kitchen-setup/recipe-cuisines'
                    },
                    {
                        path: 'admin/stores',
                        redirect: '/settings/kitchen-setup/stores'
                    },
                    // Admin · global group ─────────────────────────────────
                    {
                        path: 'admin/users',
                        component: () => import('pages/settings/UsersAdminSettings.vue'),
                        meta: { title: 'Users' }
                    },
                    // Phase 2: System splits 1 → 4 focused admin pages.
                    {
                        path: 'admin/system/timezone',
                        component: () => import('pages/settings/AdminSystemTimezoneSettings.vue'),
                        meta: { title: 'System: Timezone' }
                    },
                    // install-wide currency + display locale.
                    {
                        path: 'admin/system/locale',
                        component: () => import('pages/settings/AdminSystemLocaleSettings.vue'),
                        meta: { title: 'System: Currency & locale' }
                    },
                    {
                        path: 'admin/system/alerts',
                        component: () => import('pages/settings/AdminSystemAlertsSettings.vue'),
                        meta: { title: 'System: Alert thresholds' }
                    },
                    {
                        path: 'admin/system/assistant',
                        component: () => import('pages/settings/AdminSystemAssistantSettings.vue'),
                        meta: { title: 'System: AI assistant' }
                    },
                    {
                        path: 'admin/system/features',
                        component: () => import('pages/settings/AdminSystemFeaturesSettings.vue'),
                        meta: { title: 'System: Features' }
                    },
                    // four focused System pages carrying the
                    // operational config that used to live in DORA_* env vars.
                    {
                        path: 'admin/system/email',
                        component: () => import('pages/settings/AdminSystemEmailSettings.vue'),
                        meta: { title: 'System: Email' }
                    },
                    {
                        path: 'admin/system/push',
                        component: () => import('pages/settings/AdminSystemPushSettings.vue'),
                        meta: { title: 'System: Push notifications' }
                    },
                    {
                        path: 'admin/system/voice',
                        component: () => import('pages/settings/AdminSystemVoiceSettings.vue'),
                        meta: { title: 'System: Voice' }
                    },
                    {
                        path: 'admin/system/hosting',
                        component: () => import('pages/settings/AdminSystemHostingSettings.vue'),
                        meta: { title: 'System: Hosting' }
                    },
                    // PROPOSAL_STOCKTAKE_MODE §8 — new focused page for the
                    // two global stocktake dials (default cadence + Auto
                    // self-tuning). The old "Default stocktake reminder"
                    // section on the Alerts page is superseded by this.
                    {
                        path: 'admin/system/stocktake',
                        component: () => import('pages/settings/AdminSystemStocktakeSettings.vue'),
                        meta: { title: 'System: Stocktake' }
                    },
                    // FU-511 — install-wide auto-add mode
                    // (off / essential-only / all). Collapsed here from the
                    // retired per-item `StockItem.auto_add_when_low` toggle.
                    {
                        path: 'admin/system/stock',
                        component: () => import('pages/settings/AdminSystemStockSettings.vue'),
                        meta: { title: 'System: Stock' }
                    },
                    {
                        // Old single System page → first of the four.
                        path: 'admin/system',
                        redirect: '/settings/admin/system/timezone'
                    },
                    {
                        path: 'admin/audit-log',
                        component: () => import('pages/settings/AuditLogSettings.vue'),
                        meta: { title: 'Audit log' }
                    },
                    {
                        path: 'admin/api-access',
                        component: () => import('pages/settings/ApiAccessSettings.vue'),
                        meta: { title: 'API access' }
                    },
                    // Data sub-group under Admin: relocated
                    // Backup/Restore + Import from the retired `/data`
                    // shell. Admin-only via the same isAdmin router
                    // guard that covers the rest of `admin/*`; the
                    // backend endpoints these pages call carry the
                    // shared @require_admin dep (FU-198 closure).
                    {
                        path: 'admin/data/backup',
                        component: () => import('pages/settings/AdminDataBackupRestore.vue'),
                        meta: { title: 'Backup & restore' }
                    },
                    {
                        path: 'admin/data/import',
                        component: () => import('pages/settings/AdminDataImport.vue'),
                        meta: { title: 'Import' }
                    },
                    // IMPL_PLAN_RECIPE_IMPORTER §Chunk 6 — bulk-linker
                    // for paste-imported ingredients that landed unlinked.
                    // Lives under Data because it's a data-cleanup surface
                    // shaped like Backup / Import, not a per-recipe editor.
                    {
                        path: 'admin/data/unlinked-ingredients',
                        component: () => import('pages/settings/AdminDataUnlinkedIngredients.vue'),
                        meta: { title: 'Unlinked ingredients' }
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
