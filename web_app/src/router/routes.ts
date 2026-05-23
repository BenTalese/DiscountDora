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
            { path: 'stock/:id', component: () => import('pages/StockItemDetailPage.vue'), meta: { title: 'Stock item' } },
            { path: 'locations', component: () => import('pages/LocationsOverview.vue'), meta: { title: 'Locations' } },
            { path: 'locations/:id', component: () => import('pages/LocationDetail.vue'), meta: { title: 'Location' } },
            { path: 'product-search', component: () => import('pages/ProductSearch.vue'), meta: { title: 'Product search' } },
            { path: 'my-products', component: () => import('pages/MyProductsPage.vue'), meta: { title: 'My products' } },
            { path: 'help', component: () => import('pages/HelpPage.vue'), meta: { title: 'Help' } },
            { path: 'recipes', component: () => import('pages/RecipesOverview.vue'), meta: { title: 'Recipes' } },
            { path: 'recipes/:id', component: () => import('pages/RecipeDetailPage.vue'), meta: { title: 'Recipe' } },
            { path: 'recipes/:id/cook', component: () => import('pages/RecipeCookMode.vue'), meta: { title: 'Cook mode' } },
            { path: 'meals', component: () => import('pages/MealsOverview.vue'), meta: { title: 'Meals' } },
            { path: 'meal-plans', component: () => import('pages/MealPlansOverview.vue'), meta: { title: 'Meal plans' } },
            { path: 'shopping-lists', component: () => import('pages/ShoppingListsOverview.vue'), meta: { title: 'Shopping lists' } },
            { path: 'shopping-lists/templates', component: () => import('pages/ShoppingListTemplates.vue'), meta: { title: 'Shopping list templates' } },
            { path: 'shopping-lists/:id', component: () => import('pages/ShoppingListDetail.vue'), meta: { title: 'Shopping list' } },
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
