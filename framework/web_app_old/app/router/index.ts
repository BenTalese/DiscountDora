import ProductSearchView from '@/views/ProductSearchView.vue'
import StockOverviewView from '@/views/StockOverviewView.vue'
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'StockOverview',
            component: StockOverviewView
        },
        {
            path: '/productSearch',
            name: 'ProductSearch',
            component: ProductSearchView
        }
    ]
})

export default router
