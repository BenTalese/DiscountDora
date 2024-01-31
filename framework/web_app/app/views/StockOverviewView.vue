<script setup lang="ts">
import type { StockItem } from '@/models/StockItem';
import StockItemApiService from '@/services/api/StockItemApiService';
import type { Ref } from 'vue';
import { onMounted, ref } from 'vue';

const stockItems: Ref<StockItem[]> = ref([])

const stockItemApiService = new StockItemApiService()
onMounted(async () => (stockItems.value = await stockItemApiService.getAll()))


// TODO: Loading text using fallback
// TODO: Loading spinner for API call (e.g. while scraping results) (or any loading at all)
</script>

<template>
    <table class="table table-hover">
        <thead>
            <tr>
                <th scope="col">Name</th>
                <th scope="col">Action</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="stockItem in stockItems" :key="stockItem.stock_item_id">
                <td>{{ stockItem.name }}</td>
                <td>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-warning btn-sm">Update</button>
                        <button type="button" class="btn btn-danger btn-sm">Delete</button>
                    </div>
                </td>
            </tr>
        </tbody>
    </table>
</template>
