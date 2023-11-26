<script setup lang="ts">
import type { Merchant } from '@/models/Merchant';
import type { ScrapedProductOffer } from '@/models/ScrapedProductOffer';
import MerchantApiService from '@/services/api/MerchantApiService';
import ProductApiService from '@/services/api/ProductApiService';
import ImageService from '@/services/files/ImageService';
import { onMounted, Ref, ref } from 'vue';

const productApiService = new ProductApiService()
const merchantApiService = new MerchantApiService()
const imageService = new ImageService()

const searchTerm = ref('')
const product_offers: Ref<ScrapedProductOffer[]> = ref([])
const merchants: Ref<Merchant[]> = ref([])

let currentPage = 1

const search = async () => {
    // (await productApiService.searchByTerm(searchTerm.value, currentPage)).forEach(product => {
    //     products.value.push(product)
    // });
    product_offers.value = await productApiService.searchByTerm({ search_term: searchTerm.value, start_page: currentPage })
};

const add = async (product_offer: ScrapedProductOffer) =>
    await productApiService.create({
        brand: product_offer.brand,
        image: product_offer.image,
        is_available: product_offer.is_available,
        merchant_id: merchants.value.find((merchant) => merchant.name === product_offer.merchant)?.merchant_id!,
        merchant_stockcode: product_offer.merchant_stockcode,
        name: product_offer.name,
        price_now: product_offer.price_now,
        price_was: product_offer.price_was,
        size_unit: product_offer.size_unit,
        size_value: product_offer.size_value,
        web_url: product_offer.web_url
    });

onMounted(async () => { (merchants.value = await merchantApiService.getAll()); console.log(merchants.value) })

// BUG: What if there's no internet? Need to handle this and say "you're offline!" or something
// BUG: Can keep pressing search button and it will continue to append...not how pagination should work
// TODO: Order results by best match first (by default, sorting can be changed)
// TODO: Pressing enter should search
// TODO: Should it auto-search if input text changes? (with delay of course)
// TODO: Enter key press doesn't search
</script>

<template>
    <input v-model="searchTerm" />
    <button class="btn btn-success" @click="search">Search</button>
    <div class="row">
        <div class="col-sm-3" v-for="offer in product_offers" :key="offer.merchant_stockcode"> <!-- col-sm-6??? -->
            <div class="card">
                <img :src="imageService.decodeBase64Image(offer.image)" class="card-img-top" alt="product image">
                <!-- TODO: Could put decode method in api service, will need to re-encode though -->
                <div class="card-body">
                    <h5 class="card-title">{{ offer.name }}</h5>
                    <p class="card-text">{{ offer.brand }}</p>
                    <p class="card-text">Now: ${{ offer.price_now }}</p>
                    <p class="card-text">Was: ${{ offer.price_was }}</p>
                    <p class="card-text">{{ offer.size_value }}{{ offer.size_unit }}</p>
                    <button class="btn" @click="add(offer)">Add? Link? Save to 'My Products'?</button>
                </div>
                <div :class="['card-footer', {
                    'text-white bg-success': offer.merchant === 'Woolworths',
                    'text-white bg-danger': offer.merchant === 'Coles'
                }]">
                    <p>{{ offer.merchant }}</p>
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
