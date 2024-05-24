<template>
    <router-view />
</template>

<script setup lang="ts">
    import { useMerchantStore } from './stores/MerchantStore'
    import { useProductStore } from './stores/ProductStore'
    import { useStockItemStore } from './stores/stockItemStore'
    import { useStockLevelStore } from './stores/stockLevelStore'

    // TODO: Maybe want to move these to boot files too?
    // TODO: Check if API online and report online/offline in UI?
    const merchantStore = useMerchantStore()
    const productStore = useProductStore()
    const stockItemStore = useStockItemStore()
    const stockLevelStore = useStockLevelStore()

    await merchantStore.getMerchantsAsync()
    await productStore.getProductsAsync()
    await stockItemStore.getStockItemsAsync()
    await stockLevelStore.getStockLevelsAsync()
</script>
