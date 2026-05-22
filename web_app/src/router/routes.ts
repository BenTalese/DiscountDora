import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
    // Login lives outside MainLayout so the drawer/header don't render while
    // the user is signed out.
    {
        path: '/login',
        component: () => import('pages/LoginPage.vue')
    },
    // First-run wizard. Uses its own minimal layout so the nav drawer /
    // dashboard chrome don't peek through while the user is still being
    // set up. Router guard forces incomplete users here.
    {
        path: '/welcome',
        component: () => import('layouts/WelcomeLayout.vue'),
        children: [
            { path: '', component: () => import('pages/onboarding/WelcomeWizard.vue') },
        ],
    },
    {
        path: '/',
        component: () => import('layouts/MainLayout.vue'),
        children: [
            // Dashboard is the landing page; stock overview moves to /stock.
            { path: '', component: () => import('pages/DashboardPage.vue') },
            { path: 'stock', component: () => import('pages/StockOverview.vue') },
            { path: 'stock/:id', component: () => import('pages/StockItemDetailPage.vue') },
            { path: 'locations', component: () => import('pages/LocationsOverview.vue') },
            { path: 'locations/:id', component: () => import('pages/LocationDetail.vue') },
            { path: 'product-search', component: () => import('pages/ProductSearch.vue') },
            { path: 'my-products', component: () => import('pages/MyProductsPage.vue') },
            { path: 'help', component: () => import('pages/HelpPage.vue') },
            { path: 'recipes', component: () => import('pages/RecipesOverview.vue') },
            { path: 'recipes/:id', component: () => import('pages/RecipeDetailPage.vue') },
            { path: 'recipes/:id/cook', component: () => import('pages/RecipeCookMode.vue') },
            { path: 'meals', component: () => import('pages/MealsOverview.vue') },
            { path: 'meal-plans', component: () => import('pages/MealPlansOverview.vue') },
            { path: 'shopping-lists', component: () => import('pages/ShoppingListsOverview.vue') },
            { path: 'shopping-lists/templates', component: () => import('pages/ShoppingListTemplates.vue') },
            { path: 'shopping-lists/:id', component: () => import('pages/ShoppingListDetail.vue') },
            // In-layout error pages (F3). These keep the header/drawer
            // around so the user can navigate away without a full reload.
            // The bare-URL catch-all at the bottom of this file still
            // renders the fullscreen ErrorNotFound page for typo'd routes.
            {
                path: 'errors/not-found',
                component: () => import('pages/errors/ErrorPageNotFound.vue'),
            },
            {
                path: 'errors/server',
                component: () => import('pages/errors/ErrorServer.vue'),
            },
            // Settings shell hosts sub-routes via its own <router-view>.
            // Personal sections live at /settings/*, admin/global sections at
            // /settings/admin/* (gated by the global router guard).
            {
                path: 'settings',
                component: () => import('pages/SettingsShell.vue'),
                redirect: '/settings/preferences',
                children: [
                    {
                        path: 'preferences',
                        component: () => import('pages/settings/PreferencesSettings.vue')
                    },
                    {
                        path: 'stock-locations',
                        component: () => import('pages/settings/StockLocationsSettings.vue')
                    },
                    {
                        path: 'stock-groups',
                        component: () => import('pages/settings/StockGroupsSettings.vue')
                    },
                    {
                        path: 'account',
                        component: () => import('pages/settings/AccountSettings.vue')
                    },
                    {
                        path: 'about',
                        component: () => import('pages/settings/AboutSettings.vue')
                    },
                    {
                        path: 'admin/merchants',
                        component: () => import('pages/settings/MerchantsSettings.vue')
                    },
                    {
                        path: 'admin/users',
                        component: () => import('pages/settings/UsersAdminSettings.vue')
                    },
                    {
                        path: 'admin/system',
                        component: () => import('pages/settings/SystemSettings.vue')
                    }
                ]
            }
        ]
    },

    // Always leave this as last one,
    // but you can also remove it
    {
        path: '/:catchAll(.*)*',
        component: () => import('pages/ErrorNotFound.vue')
    }
];

export default routes;
