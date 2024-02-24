<template>
    <div class="row no-wrap q-pa-md" style="min-width: 100px; width: 100%;">
        <q-input dense outlined square v-model="searchTerm" placeholder="Search" class="bg-white col">
            <template v-slot:append>
                <q-btn round dense flat icon="search" @click="search" />
                <q-btn round dense flat icon="tune" @click="toggleFilter" />
            </template>
        </q-input>
    </div>
    <q-slide-transition>
        <div class="row q-pa-md bg-red" style="min-width: 100px; width: 100%;" v-show="showFilter">
        </div>
    </q-slide-transition>

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
                icon="favorite"
                :icon-class="isSavedProduct(offer) ? 'text-red' : 'text-grey'"
                :img="imageService.decodeBase64Image(offer.image)"
                @icon-click="productStore.saveProduct(offer)"
            />
        </div>
    </div>
</template>

<script setup lang="ts">
import CardComponent from 'src/components/CardComponent.vue';
import { Product } from 'src/models/Product';
import { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';
import ImageService from 'src/services/files/ImageService';
import { useProductStore } from 'src/stores/ProductStore';
import { ref } from 'vue';

const imageService = new ImageService();
const productStore = useProductStore();

const searchTerm = ref('');
const showFilter = ref(true)

let currentPage = 1;

const isSavedProduct = (offer: ScrapedProductOffer): boolean => {
    return productStore.savedProducts.find((product: Product) =>
        product.merchant_stockcode == offer.merchant_stockcode
        && product.merchant == offer.merchant)
    != null;
};

const search = () => productStore.searchByTerm({
    search_term: searchTerm.value,
    start_page: currentPage
});

const toggleFilter = () => showFilter.value = !showFilter.value;
</script>
