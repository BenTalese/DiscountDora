<template>
    <div class="row no-wrap q-pa-md" style="min-width: 100px; width: 100%;">
        <!-- TODO: Disable until results are rendered, expensive operation -->
        <q-input
            @keydown.enter="search"
            dense outlined square v-model="searchTerm" placeholder="Search" class="bg-white col">
            <template v-slot:append>
                <q-btn round dense flat icon="search" @click="search" />
                <q-btn round dense flat icon="tune" @click="toggleFilter" />
            </template>
        </q-input>
    </div>
        <!-- TODO: research ordering convention of component props -->
        <!-- TODO: props position, loading -->
        <!-- TODO: Vue set prop to bool without binding, :persistent="false"-->
        <!-- Transition is likely redundant, may be worth Ben testing on Linux (doc says known windows issues) -->
        <!-- loader -->
        <!-- unsave product -->
        <Transition appear :duration="300"
            enter-active-class="animated fadeIn"
            leave-active-class="animated fadeOut">
            <div class="row q-pa-sm" v-show="showFilter">
                <SelectComponent
                    label="Stores"
                    :icon-name="(isSelected: boolean): string => isSelected ? 'check_box' : 'check_box_outline_blank'"
                    :multiple="true"
                    :options="productStore.merchants ?? []"
                    :option-label="(merchant: Merchant) => merchant.name"
                    v-model="productStore.filterOptions.stores"
                />
                <SelectComponent
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
                        <!-- OG 500 WEIGHT -->
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

                <!-- TODO: Binding the state directly to components which modify it may be bad -->
            </div>
        </Transition>

        <!-- TODO: PRICE NOW comes as null sometimes, encountered in Woolies response -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));">
        <!-- TODO: COLES, Add offer.brand back in, not all names contain the brand -->
            <div
            class="q-pa-md"
            v-for="offer in productStore.filteredProductOffers" :key="offer.merchant_stockcode">
            <CardComponent
                :body-main-text="getOfferFullName(offer.brand, offer.name)"
                :body-subtitle-text="offer.price_now?.toFixed(2).toString()"
                :chip-label="offer.merchant"
                icon="favorite"
                :icon-class="isSavedProduct(offer) ? 'text-red-12' : 'text-grey'"
                :img="imageService.decodeBase64Image(offer.image)"
                @icon-click="productStore.saveProduct(offer)"
            />
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
