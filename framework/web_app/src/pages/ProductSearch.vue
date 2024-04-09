<template>
    <div class="no-wrap q-pa-md row min-width-100 width-100">
        <q-input
            autofocus
            @keydown.enter="search"
            v-model="searchTerm"
            :disable="Loading.isActive"
            placeholder="Search"
            dense
            outlined
            square
            class="bg-white col">
            <template v-slot:prepend>
                <q-btn round dense flat icon="tune" @click="toggleShowFilters" />
                <q-btn round dense flat icon="search" @click="search" />
            </template>
        </q-input>
    </div>

    <div v-show="showFilters" class="no-wrap row q-pa-sm scroll scrollbar-none">

        <select-component
            label="Stores"
            :multiple="true"
            :options="productStore.merchants"
            :option-label="(merchant: Merchant) => merchant.name"
            :model-value="productStore.offerFilters.stores"
            @update:model-value="productStore.setStoresFilter"
            :optionIconName="(isSelected: boolean): string => isSelected ? 'check_box' : 'check_box_outline_blank'"
        />

        <select-component
            label="Sort By"
            :options="OfferSortByOptions"
            :option-label="optionLabelSelector"
            :model-value="productStore.offerFilters.sortBy"
            @update:model-value="productStore.setSortByFilter"
        />

        <q-btn
            type="button"
            @click="productStore.toggleShowOnlyAvailable"
            no-caps
            no-wrap
            size="md"
            :stretch="false"
            :class="productStore.offerFilters.showOnlyAvailable ? 'bg-blue': 'bg-white'"
            class="q-ma-sm"
            square
        >
            <template v-slot>
                <span class="font-weight-400">In Stock</span>
            </template>
        </q-btn>

        <q-btn
            type="button"
            @click="productStore.toggleShowOnlyFavourites"
            no-caps
            no-wrap
            size="md"
            :stretch="false"
            text-color="black"
            :class="productStore.offerFilters.showOnlyFavourites ? 'bg-blue': 'bg-white'"
            class="q-ma-sm"
            square
        >
            <template v-slot>
                <span class="font-weight-400">Favourites</span>
            </template>
        </q-btn>

        <q-btn
            type="button"
            @click="productStore.toggleShowOnlySpecials"
            no-caps
            no-wrap
            size="md"
            :stretch="false"
            text-color="black"
            :class="productStore.offerFilters.showOnlySpecials ? 'bg-blue': 'bg-white'"
            class="q-ma-sm"
            square
        >
            <template v-slot>
                <span class="font-weight-400">Specials</span>
            </template>
        </q-btn>

    </div>

    <div class="card-grid">

        <div
            v-for="offer in productStore.filteredProductOffers" :key="offer.merchant_stockcode"
            class="q-pa-md">

            <card-component
                :img="imageService.decodeBase64Image(offer.image)"
                icon="favorite"
                @icon-click="productStore.addOfferToFavouritesAsync(offer)"
                :chip-label="offer.merchant_name"
                :chip-colour="getMerchantColour(offer.merchant_name)"
                :icon-class="isOfferFavourited(offer, productStore.products) ? 'text-red-12' : 'text-grey'"
            >
                <template v-slot:body>
                    <q-card-section class="flex-1 q-py-none">
                        <div class="column full-height no-wrap justify-between">
                            <div class="text-body2 text-weight-regular q-pb-sm">
                                {{ `${getOfferFullName(offer.brand, offer.name)} | ${getOfferSize(offer.size_value, offer.size_unit)}` }}
                            </div>
                            <div>
                                <div class="text-body2 text-weight-medium">
                                    {{ `$${offer.price_now?.toFixed(2).toString()}` }}
                                </div>
                                <div class="text-caption text-weight-regular">
                                    {{
                                        `was $${offer.price_was
                                            ? offer.price_was?.toFixed(2).toString()
                                            : offer.price_now?.toFixed(2).toString()}`
                                    }}
                                </div>
                            </div>
                        </div>
                    </q-card-section>
                </template>
            </card-component>

        </div>
    </div>
    <div
        v-if="!Loading.isActive && previousSearchTerm && !productStore.productOffers?.length"
        class="row text-h3 q-ma-sm items-center">
        <img src="../../src/assets/banana-peel.jpg" class="q-pa-sm round-img" />
        <span class="text-h5 q-pa-sm">
            No products found for '{{ previousSearchTerm }}'.
        </span>
    </div>
</template>

<script setup lang="ts">

import { Loading } from 'quasar';
import CardComponent from 'src/components/CardComponent.vue';
import SelectComponent from 'src/components/SelectComponent.vue';
import { IOfferSortByOption, OfferSortByOptions } from 'src/helpers/OfferSortByOptions';
import { getOfferFullName, getOfferSize, isOfferFavourited } from 'src/helpers/ScrapedProductOfferLogic';
import { Merchant } from 'src/models/Merchant';
import ImageService from 'src/services/files/ImageService';
import { useProductStore } from 'src/stores/ProductStore';
import { ref } from 'vue';

const productStore = useProductStore();

//#region Search

const searchTerm = ref('');
const previousSearchTerm = ref<undefined | string>();

let currentPage = 1;

const search = (): Promise<string> =>
    productStore.searchByTermAsync({
        search_term: searchTerm.value,
        start_page: currentPage
    })
    .then(() => previousSearchTerm.value = searchTerm.value);

//#endregion Search

//#region Filters

const showFilters = ref(true);

const toggleShowFilters = (): boolean =>
    showFilters.value = !showFilters.value;

const optionLabelSelector = (option: IOfferSortByOption): string =>
    option.Description;

//#endregion Filters

//#region Offers

const imageService = new ImageService();

const colourByMerchant: { [key: string]: string } = {
    Coles: 'red-14',
    Woolworths: 'green-14'
};

const getMerchantColour = (merchantName: string): string =>
    colourByMerchant[merchantName];

//#endregion Offers

</script>

<!-- TODO: Move to global styling accessible by all componets -->
<style scoped>

.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
}

.flex-1 {
    flex: 1;
}

.font-weight-400 {
    font-weight: 400;
}

.round-img {
    border-radius: 50%;
    width: 230px;
}

.min-width-100 {
    min-width: 100px;
}

.scrollbar-none {
    scrollbar-width: none;
}

/* TODO: Quasar may already have this class */
.width-100 {
    width: 100%;
}

/* TODO: re-readup on mixins to make some of these styles more dynamic, possibly mixins */

</style>
