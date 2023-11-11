<script setup lang="ts">
import type { StockItem } from '@/models/StockItem';
import StockItemApiService from '@/services/api/StockItemApiService';
import axios from 'axios';
import { onMounted, Ref, ref } from 'vue';

const stockItems: Ref<StockItem[]> = ref([])
const products = ref([])

const test = ref("Turtles!!")

const itemApiService = new StockItemApiService()
onMounted(async () => (stockItems.value = await itemApiService.getAll()))

const testApi = async () => {
    try {
        // Make a GET request to your Flask API endpoint
        const response = await axios.post("http://127.0.0.1:5000/api/webScraper/doTheThing", { "searchTerm": "Hazelnut Chocolate Bar", "startPage": 1 });

        if (response.status === 200) {
            // Assuming the API returns an array of stock items in JSON format
            products.value = response.data;
        } else {
            console.error("API request failed with status code:", response.status);
        }
    } catch (error) {
        console.error("An error occurred:", error);
    }
};

function decodeBase64Image(encodedImage) {
    // Decode the base64-encoded image and return the data URI
    return `data:image/jpeg;base64,${encodedImage}`;
}

// TODO: Loading text using fallback
</script>

<template>
    <main>
        <button type="button" class="btn btn-success" @click="testApi">{{ test }}</button>
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
        <table class="table table-hover">
            <thead>
                <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Action</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="stockItem in products" :key="stockItem.stock_item_id">
                    <td>{{ stockItem.name }}</td>
                    <td><img :src="decodeBase64Image(stockItem.image)" alt="Product Image" :style="{ width: '100%', maxWidth: '200px', height: 'auto' }" /></td>
                    <td>
                        <div class="btn-group" role="group">
                            <button type="button" class="btn btn-warning btn-sm">Update</button>
                            <button type="button" class="btn btn-danger btn-sm">Delete</button>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>
    </main>
</template>
