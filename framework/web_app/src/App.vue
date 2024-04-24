<template>
  <router-view />
</template>

<script setup lang="ts">
import { onBeforeMount } from 'vue';
import { useMerchantStore } from './stores/MerchantStore';
import { useProductStore } from './stores/ProductStore';

  const merchantStore = useMerchantStore();
  const productStore = useProductStore();

  onBeforeMount(() => {
    merchantStore.getMerchantsAsync();
    productStore.getProductsAsync();
  })

</script>
