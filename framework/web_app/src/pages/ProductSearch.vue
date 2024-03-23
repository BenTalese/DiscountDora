<template>
    <div class="row no-wrap q-pa-md" style="min-width: 100px; width: 100%;">
        <!-- TODO: Disable until results are rendered, expensive operation -->
        <q-input
            @keydown.enter="search"
            dense outlined square v-model="searchTerm" placeholder="Search"
            class="bg-white col">
            <template v-slot:append>
                <q-btn round dense flat icon="search" @click="search" />
                <q-btn round dense flat icon="tune" @click="toggleShowFilters" />
            </template>
        </q-input>
    </div>

    <div class="row q-pa-sm" v-show="showFilters">

        <select-component
            label="Stores"
            :multiple="true"
            :options="productStore.merchants ?? []"
            :option-label="(merchant: Merchant) => merchant.name"
            :model-value="productStore.filterOptions.stores"
            @update:model-value="productStore.setStoresFilter"
            :icon-name="(isSelected: boolean): string => isSelected ? 'check_box' : 'check_box_outline_blank'"
        />

        <select-component
            label="Sort By"
            :options="OfferSortByOptions"
            :option-label="optionLabelSelector"
            :model-value="productStore.filterOptions.sortBy"
            @update:model-value="productStore.setSortByFilter"
        />

        <q-btn
            type="button"
            @click="productStore.toggleIsAvailableFilter"
            no-caps
            no-wrap
            size="md"
            :stretch="false"
            :class="productStore.filterOptions.showOnlyAvailable ? 'bg-blue': 'bg-white'"
            class="q-ma-sm"
        >
            <template v-slot>
                <span style="font-weight:400">In Stock</span>
            </template>
        </q-btn>

        <q-btn
            type="button"
            @click="productStore.toggleIsSavedFilter"
            no-caps
            no-wrap
            size="md"
            :stretch="false"
            text-color="black"
            :class="productStore.filterOptions.showOnlySaved ? 'bg-blue': 'bg-white'"
            class="q-ma-sm"
        >
            <template v-slot>
                <span style="font-weight:400">Saved</span>
            </template>
        </q-btn>

    </div>

    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));">

        <div
            v-for="offer in productStore.filteredProductOffers" :key="offer.merchant_stockcode"
            class="q-pa-md">

            <card-component
                :img="imageService.decodeBase64Image(offer.image)"
                icon="favorite"
                @icon-click="productStore.saveProduct(offer)"
                :chip-label="offer.merchant"
                :chip-colour="getMerchantColour(offer.merchant)"
                :body-main-text="getOfferFullName(offer.brand, offer.name)"
                :body-subtitle-text="`$${offer.price_now?.toFixed(2).toString()}`"
                :icon-class="isOfferSaved(offer, productStore.products) ? 'text-red-12' : 'text-grey'"
            />

        </div>

    </div>
</template>

<script setup lang="ts">

import CardComponent from 'src/components/CardComponent.vue';
import SelectComponent from 'src/components/SelectComponent.vue';
import { OfferSortByOption, OfferSortByOptions } from 'src/helpers/OfferSortByOptions';
import { getOfferFullName, isOfferSaved } from 'src/helpers/ProductLogic';
import { Merchant } from 'src/models/Merchant';
import ImageService from 'src/services/files/ImageService';
import { useProductStore } from 'src/stores/ProductStore';
import { ref } from 'vue';

const imageService = new ImageService();
const productStore = useProductStore();

const searchTerm = ref('');
const showFilters = ref(true);

let currentPage = 1;

const search = (): void =>
    productStore.searchByTerm({
        search_term: searchTerm.value,
        start_page: currentPage
    });

const toggleShowFilters = (): boolean =>
    showFilters.value = !showFilters.value;

const optionLabelSelector = (option: OfferSortByOption): string =>
    option.Description;

const colourByMerchant: { [key: string]: string } = {
    Coles: 'red',
    Woolworths: 'green'
};

const getMerchantColour = (merchantName: string): string =>
    colourByMerchant[merchantName];

</script>
