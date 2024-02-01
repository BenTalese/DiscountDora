<script setup lang="ts">
import type { StockItem } from '@/models/StockItem';
import type { StockLevel } from '@/models/StockLevel';
import StockItemApiService from '@/services/api/StockItemApiService';
import StockLevelApiService from '@/services/api/StockLevelApiService';
import type { Ref } from 'vue';
import { onMounted, reactive, ref } from 'vue';

const stockItems: Ref<StockItem[]> = ref([]);
const stockLevels: Ref<StockLevel[]> = ref([]);

const stockItemApiService = new StockItemApiService();
const stockLevelApiService = new StockLevelApiService();

onMounted(async () => {
    stockItems.value = await stockItemApiService.getAll();
    stockLevels.value = await stockLevelApiService.getAll();
    console.log(stockItems.value[0])
    console.log(stockLevels.value)
    form.stock_level_id = stockLevels.value[0].stock_level_id
})

const test = async () => await stockItemApiService.create(form);
// const test2 = () => {
//     stockItemApiService.create({ name: "X", stock_level_id: "", stock_location_id: "" });
// }

//    <button class="btn" @click="test">Add/Save to 'My Products' / + </button>
const form = reactive({
    name: "",
    stock_level_id: "stockLevels.value[0].stock_level_id",
    stock_location_id: null
});

// TODO: Loading text using fallback
// TODO: Loading spinner for API call (e.g. while scraping results) (or any loading at all)
</script>

<template>
    <form @submit.prevent="test">
        <label for="name">Name</label>
        <input id="name" v-model="form.name" />

        <br />

        <label for="stockLevel">Stock Level</label>
        <select id="stockLevel" v-model="form.stock_level_id">
            <option v-for="stockLevel in stockLevels" :key="stockLevel.stock_level_id" :value="stockLevel.stock_level_id">
                {{ stockLevel.description }}
            </option>
        </select>

        <br />

        <!-- <input type="email" v-model="form.a" />

        <label>Message is: {{ message }}</label>
        <input v-model="message" placeholder="edit me" />


        <textarea v-model="form.b" />


        <select v-model="form.c">
            <option value="new-york">New York</option>
            <option value="moscow">Moscow</option>
        </select>

        <input type="checkbox" v-model="form.d" />

        <input type="radio" value="weekly" v-model="form.e" />
        <input type="radio" value="monthly" v-model="form.f" /> -->

        <button type="submit">Submit</button>
    </form>
    <!-- <button type="button" class="btn btn-success" @click="testApi">{{ test }}</button> -->
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
                        <button type="button" class="btn btn-warning btn-sm">Edit</button>
                        <button type="button" class="btn btn-danger btn-sm">Delete</button>
                    </div>
                </td>
            </tr>
        </tbody>
    </table>
</template>
