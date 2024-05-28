import { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', redirect: 'my-products' },

      { path: 'my-products', component: () => import('pages/MyProducts.vue') },
      { path: 'product-search', component: () => import('pages/ProductSearch.vue') },
      { path: 'stock', component: () => import('pages/StockOverview.vue') }
    ],
  },
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;
