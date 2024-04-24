<template>
    <div class="no-wrap q-pa-md row min-width-100 full-width">
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
                <q-btn round dense flat icon="tune" @click="toggleShowFiltersContainer" />
                <q-btn round dense flat icon="search" @click="search" />
            </template>
        </q-input>
    </div>

    <div v-show="showFiltersContainer" class="no-wrap row q-pa-sm scroll scrollbar-none">

        <select-component
            label="Stores"
            :multiple="true"
            :options="merchantStore.merchants"
            :option-label="(merchant: Merchant) => merchant.name"
            :model-value="productStore.productSearchOfferFilters.stores"
            @update:model-value="productStore.setProductSearchStoresFilter"
            :optionIconName="(isSelected: boolean): string => isSelected ? 'check_box' : 'check_box_outline_blank'"
        />

        <select-component
            label="Sort By"
            :options="OfferSortByOptions"
            :option-label="optionLabelSelector"
            :model-value="productStore.productSearchOfferFilters.sortBy"
            @update:model-value="productStore.setProductSearchSortByFilter"
        />

        <q-btn
            type="button"
            @click="toggleSearchFilter(nameof<IProductSearchFilters>(src => src.showOnlyAvailable))"
            no-caps
            no-wrap
            size="md"
            :stretch="false"
            :class="productStore.productSearchOfferFilters.showOnlyAvailable ? 'bg-blue': 'bg-white'"
            class="q-ma-sm"
            square
        >
            <template v-slot>
                <span class="font-weight-400">In Stock</span>
            </template>
        </q-btn>

        <q-btn
            type="button"
            @click="toggleSearchFilter(nameof<IProductSearchFilters>(src => src.showOnlyFavourites))"
            no-caps
            no-wrap
            size="md"
            :stretch="false"
            text-color="black"
            :class="productStore.productSearchOfferFilters.showOnlyFavourites ? 'bg-blue': 'bg-white'"
            class="q-ma-sm"
            square
        >
            <template v-slot>
                <span class="font-weight-400">Favourites</span>
            </template>
        </q-btn>

        <q-btn
            type="button"
            @click="toggleSearchFilter(nameof<IProductSearchFilters>(src => src.showOnlySpecials))"
            no-caps
            no-wrap
            size="md"
            :stretch="false"
            text-color="black"
            :class="productStore.productSearchOfferFilters.showOnlySpecials ? 'bg-blue': 'bg-white'"
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
import { nameof } from 'src/helpers/Nameof';
import { IOfferSortByOption, OfferSortByOptions } from 'src/helpers/OfferSortByOptions';
import { getOfferFullName, getOfferSize, isOfferFavourited } from 'src/helpers/ScrapedProductOfferLogic';
import { Merchant } from 'src/models/Merchant';
import ImageService from 'src/services/files/ImageService';
import { useMerchantStore } from 'src/stores/MerchantStore';
import { IProductSearchFilters, useProductStore } from 'src/stores/ProductStore';
import { ref, watch } from 'vue';

const merchantStore = useMerchantStore();
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

const showFiltersContainer = ref(true);

const toggleShowFiltersContainer = (): boolean =>
    showFiltersContainer.value = !showFiltersContainer.value;

const toggleSearchFilter = (filterName: string): void =>
    productStore.toggleProductSearchFilter(filterName as keyof IProductSearchFilters);

const optionLabelSelector = (option: IOfferSortByOption): string =>
    option.description;

/**
 * Initialises filters requiring merchants, once they exist.
 */
const unwatchMerchants = watch(() => merchantStore.merchants, async (newValue: Merchant[]) => {
    productStore.addStoresToProductSearchFilter(newValue);
    unwatchMerchants();
});

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

<style scoped>

.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
}

.h-px-20 {
    height: 20px;
}

.h-px-32 {
    height: 32px;
}

.w-px-32 {
    width: 32px;
}

.w-px-48 {
    width: 48px;
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

</style>
