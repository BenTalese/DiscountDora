import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
    {
        path: '/',
        component: () => import('layouts/MainLayout.vue'),
        children: [
            {
                path: 'stock',
                component: () => import('pages/StockOverview.vue'),
                meta: { title: 'Stock Overview' }
            },
            {
                path: 'product-search',
                component: () => import('pages/ProductSearch.vue'),
                meta: { title: 'Product Search' }
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
