<script setup lang="ts">
import type { StockItem } from '@/models/StockItem';
import StockItemApiService from '@/services/api/StockItemApiService';
import { onMounted, Ref, ref } from 'vue';

const stockItems: Ref<StockItem[]> = ref([])

const itemApiService = new StockItemApiService();
onMounted(async () => stockItems.value = await itemApiService.getAll())

// TODO: Loading text using fallback
</script>

<template>
  <main>
    <table>
      <thead>
        <tr>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="stockItem in stockItems" :key="stockItem.stock_item_id">
          <td>{{ stockItem.name }}</td>
        </tr>
      </tbody>
    </table>
  </main>
</template>
