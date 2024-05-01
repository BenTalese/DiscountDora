<template>
    <router-view />
</template>

<script setup lang="ts">
import { useMerchantStore } from './stores/MerchantStore';
import { useProductStore } from './stores/ProductStore';

// TODO: Maybe want to move these to boot files too?
// TODO: Check if API online and report online/offline in UI?
const merchantStore = useMerchantStore();
const productStore = useProductStore();

merchantStore.getMerchantsAsync();
productStore.getProductsAsync();

</script>
