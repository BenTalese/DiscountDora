<template>
    <input v-model="searchTerm" />
    <button class="btn btn-success" @click="search">Search</button>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));">
        <!-- TODO: Check with Ben.
            Removed offer.brand because all offer names seem to have the brand in there -->
            <div
            class="q-pa-md"
            v-for="offer in productStore.scrapedProductOffers" :key="offer.merchant_stockcode">
            <CardComponent
                :body-main-text="offer.name"
                :body-subtitle-text="offer.price_now.toString()"
                :chip-label="offer.merchant"
                :img="imageService.decodeBase64Image(offer.image)"
            />
        </div>
    </div>
</template>

<script setup lang="ts">
import CardComponent from 'src/components/CardComponent.vue';
import ImageService from 'src/services/files/ImageService';
import { useProductStore } from 'src/stores/ProductStore';
import { ref } from 'vue';

const imageService = new ImageService();
const productStore = useProductStore();
const searchTerm = ref('');

let currentPage = 1;

const search = () => productStore.searchByTerm({
    search_term: searchTerm.value,
    start_page: currentPage
});

</script>
