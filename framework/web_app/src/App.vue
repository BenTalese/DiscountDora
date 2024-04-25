<template>
  <router-view />
</template>

<script setup lang="ts">
import { useMerchantStore } from './stores/MerchantStore';
import { useProductStore } from './stores/ProductStore';

  const merchantStore = useMerchantStore();
  const productStore = useProductStore();

  merchantStore.getMerchantsAsync();
  productStore.getProductsAsync();

</script>
