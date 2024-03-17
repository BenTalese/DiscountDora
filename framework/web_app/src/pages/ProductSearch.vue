<template>
    <div class="row no-wrap q-pa-md" style="min-width: 100px; width: 100%;">
        <!-- TODO: Disable until results are rendered, expensive operation -->
        <q-input
            @keydown.enter="search"
            dense outlined square v-model="searchTerm" placeholder="Search"
            class="bg-white col">
            <template v-slot:append>
                <q-btn round dense flat icon="search" @click="search" />
                <q-btn round dense flat icon="tune" @click="toggleFilter" />
            </template>
        </q-input>
    </div>
        <!-- TODO: research ordering convention of component props -->
        <!-- TODO: Transition on filter section toggle -->
        <!-- loader -->
        <!-- unsave product -->
            <div class="row q-pa-sm" v-show="showFilter">
                <select-component
                    label="Stores"
                    :icon-name="(isSelected: boolean): string => isSelected ? 'check_box' : 'check_box_outline_blank'"
                    :multiple="true"
                    :options="productStore.merchants ?? []"
                    :option-label="(merchant: Merchant) => merchant.name"
                    v-model="productStore.filterOptions.stores"
                />
                <select-component
                    label="Sort By"
                    :options="ProductSearchSortByOptions"
                    :option-label="optionLabelSelector"
                    v-model="productStore.filterOptions.sortBy"
                />
                <q-btn
                    class="q-ma-sm"
                    :class="productStore.filterOptions.isAvailable ? 'bg-blue': 'bg-white'"
                    no-caps
                    no-wrap
                    size="md"
                    :stretch="false"
                    type="button"
                    @click="() => productStore.toggleIsAvailableFilter()"
                >
                    <template v-slot>
                        <span style="font-weight:400">In Stock</span>
                    </template>
                </q-btn>
                <q-btn
                    class="q-ma-sm"
                    :class="productStore.filterOptions.isSaved ? 'bg-blue': 'bg-white'"
                    no-caps
                    no-wrap
                    size="md"
                    :stretch="false"
                    type="button"
                    text-color="black"
                    @click="() => productStore.toggleIsSavedFilter()"
                >
                    <template v-slot>
                        <span style="font-weight:400">Saved</span>
                    </template>
                </q-btn>
                <!-- TODO: mock has 'specials', do we want this? should it be a filter rather than sort? -->
            </div>

        <!-- TODO: PRICE NOW comes as null sometimes, encountered in Woolies response.
            What should we display instead?-->
    <div
        style="display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));">
        <div
            class="q-pa-md"
            v-for="offer in productStore.filteredProductOffers" :key="offer.merchant_stockcode">
            <card-component
                :body-main-text="getOfferFullName(offer.brand, offer.name)"
                :body-subtitle-text="`$${offer.price_now?.toFixed(2).toString()}`"
                :chip-label="offer.merchant"
                icon="favorite"
                :icon-class="isSavedProduct(offer) ? 'text-red-12' : 'text-grey'"
                :img="imageService.decodeBase64Image(offer.image)"
                @icon-click="productStore.saveProduct(offer)"
            />
            <!-- TODO: 0 search results found or a display if productStore.filteredProductOffers is empty
                , may be able to do per component too-->
        </div>
    </div>
</template>

<script setup lang="ts">
import CardComponent from 'src/components/CardComponent.vue';
import SelectComponent from 'src/components/SelectComponent.vue';
import { ProductSearchSortByOption } from 'src/helpers/ProductSearchSortByOption';
import { ProductSearchSortByOptions } from 'src/helpers/ProductSearchSortByOptions';
import { Product } from 'src/models/Product';
import { Merchant } from 'src/models/Merchant';
import { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';
import ImageService from 'src/services/files/ImageService';
import { useProductStore } from 'src/stores/ProductStore';
import { ref } from 'vue';

const imageService = new ImageService();
const productStore = useProductStore();

const searchTerm = ref('');
const showFilter = ref(true);

let currentPage = 1;

// TODO: Need somewhere to load initial states. Could... load it just in this component...maybe
productStore.getProducts();
productStore.getMerchants();

/// <Summary>
/// Retrieves a product offer's name, including the brand name.
/// E.g., the Coles offers don't always contain the brand in the name.
/// </Summary>
const getOfferFullName = (brand: string, name: string): string =>
    name.includes(brand) ? name : `${brand} ${name}`;

const isSavedProduct = (offer: ScrapedProductOffer): boolean => {
    let savedProduct = productStore.products?.find((product: Product) =>
        product.merchant_stockcode == offer.merchant_stockcode &&
        product.merchant_name === offer.merchant)

    return savedProduct != undefined;
};

const search = (): Array<ScrapedProductOffer> => productStore.searchByTerm({
    search_term: searchTerm.value,
    start_page: currentPage
}) as Array<ScrapedProductOffer>;

const optionLabelSelector = (option: ProductSearchSortByOption) => {
    return option.Description;
};

const toggleFilter = (): void => {
    showFilter.value = !showFilter.value;
};

</script>
