<script setup lang="ts">
import { Product } from '@/models/Product';
import ProductApiService from '@/services/api/ProductApiService';
import ImageService from '@/services/files/ImageService';
import { Ref, ref } from 'vue';

const searchTerm = ref('')
const productApiService = new ProductApiService()
const imageService = new ImageService()
const products: Ref<Product[]> = ref([])

let currentPage = 1

const search = async () => {
    (await productApiService.searchByTerm(searchTerm.value, currentPage)).forEach(product => {
        products.value.push(product)
    });
};

// BUG: Can keep pressing search button and it will continue to append...not how pagination should work
// TODO: Order results by best match first (by default, sorting can be changed)
// TODO: Pressing enter should search
// TODO: Should it auto-search if input text changes? (with delay of course)
</script>

<template>
    <input v-model="searchTerm" />
    <button class="btn btn-success" @click="search">Search</button>
    <div class="row">
        <div class="col-sm-3" v-for="product in products" :key="product.merchant_stockcode"> <!-- col-sm-6??? -->
            <div class="card">
                <img :src="imageService.decodeBase64Image(product.image)" class="card-img-top" alt="product image">
                <div class="card-body">
                    <h5 class="card-title">{{ product.name }}</h5>
                    <p class="card-text">{{ product.brand }}</p>
                    <p class="card-text">Now: ${{ product.price_now }}</p>
                    <p class="card-text">Was: ${{ product.price_was }}</p>
                    <p class="card-text">{{ product.size_value }}{{ product.size_unit }}</p>
                    <button class="btn">Add? Link? Save to 'My Products'?</button>
                </div>
                <div :class="['card-footer', {
                    'text-white bg-success': product.merchant === 'Woolworths',
                    'text-white bg-danger': product.merchant === 'Coles'
                }]">
                    <p>{{ product.merchant }}</p>
                </div>
            </div>
        </div>
    </div>
    <!-- <table class="table table-hover">
        <thead>
            <tr>
                <th scope="col">Name</th>
                <th scope="col">Action</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="stockItem in products" :key="stockItem.stock_item_id">
                <td>{{ stockItem.name }}</td>
                <td><img :src="decodeBase64Image(stockItem.image)" alt="Product Image"
                        :style="{ width: '100%', maxWidth: '200px', height: 'auto' }" /></td>
                <td>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-warning btn-sm">Update</button>
                        <button type="button" class="btn btn-danger btn-sm">Delete</button>
                    </div>
                </td>
            </tr>
        </tbody>
    </table> -->
</template>
