<template>
  <router-view />
</template>

<script setup lang="ts">
import { useProductStore } from './stores/ProductStore';

  const productStore = useProductStore();

  //TODO: If initial load up fails.
  // E.g., user has no connection, fetch fails then user gets connection but no re-fetch
  //  (no data for some components, partially working pages)
  // Solution is likely to conditionally re-fetch in the store as Ben suggested
  // or to re fetch on pages that require it if there is no data
  productStore.getMerchants();
  productStore.getProducts();

</script>
