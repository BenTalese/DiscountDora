<template>
    <div class="row no-wrap q-pa-md" style="min-width: 100px; width: 100%;">
        <q-input dense outlined square v-model="searchTerm" placeholder="Search" class="bg-white col">
            <template v-slot:append>
                <q-btn round dense flat icon="search" @click="search" />
                <q-btn round dense flat icon="tune" @click="toggleFilter" />
            </template>
        </q-input>
    </div>
        <!-- style="min-width: 100px; width: 100%;" -->
        <!-- TODO: research ordering convention of component props -->
        <!-- TODO: props position, loading -->
        <!-- TODO: Vue set prop to bool without binding, :persistent="false"-->
        <!-- Transition is likely redundant, may be worth Ben testing on Linux (doc says known windows issues) -->
        <Transition appear :duration="300"
            enter-active-class="animated fadeIn"
            leave-active-class="animated fadeOut">
            <div class="row q-pa-sm bg-red" v-show="showFilter">
                <DropdownComponent label="Store" :list-items="stores" />
                <DropdownComponent label="In Stock" :list-items="stores" />
                <q-btn
                    class="bg-white q-ma-sm"
                    no-caps
                    no-wrap
                    size="md"
                    :stretch="false"
                    type="button"
                >
                    <template v-slot>
                        Saved
                    </template>
                </q-btn>
                <!-- <SelectComponent
                    label="Stores"
                    multiple
                    :options="stores"
                    :option-value="undefined"
                    v-model="selectModel"
                /> -->
                <!-- TODO: mock has 'specials', do we want this? should it be a filter rather than sort? -->
                <SelectComponent
                    label="Sort By"
                    :options="ProductSearchSortOptions"
                    :option-label="optionLabelSelector"
                    v-model="productStore.activeSortOption"
                />
                <!-- TODO: Binding the state directly to components which modify it may be bad -->
            </div>
        </Transition>

    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));">
        <!-- TODO: lighter shade of red on saved heart icon -->
        <!-- TODO: Add offer.brand back in, not all names contain the brand -->
            <div
            class="q-pa-md"
            v-for="offer in productStore.sortedProductOffers" :key="offer.merchant_stockcode">
            <CardComponent
                :body-main-text="offer.name"
                :body-subtitle-text="offer.price_now.toFixed(2).toString()"
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
import DropdownComponent from 'src/components/DropdownComponent.vue';
import SelectComponent from 'src/components/SelectComponent.vue';
import { ProductSearchSortOption, ProductSearchSortOptions } from 'src/helpers/ProductSearchFilter';
import { Product } from 'src/models/Product';
import { ScrapedProductOffer } from 'src/models/ScrapedProductOffer';
import ImageService from 'src/services/files/ImageService';
import { useProductStore } from 'src/stores/ProductStore';
import { computed, ref } from 'vue';

const imageService = new ImageService();
const productStore = useProductStore();

const searchTerm = ref('');
const showFilter = ref(true);

let currentPage = 1;

// TODO: Need somewhere to load initial states. Could... load it just in this component...maybe
productStore.getProducts()

// TODO: revise == vs ===
const isSavedProduct = (offer: ScrapedProductOffer): boolean => {
    let savedProduct = productStore.savedProducts?.find((product: Product) =>
        product.merchant_stockcode == offer.merchant_stockcode &&
        product.merchant_name == offer.merchant)

    return savedProduct != undefined;
};

const search = (): Array<ScrapedProductOffer> => productStore.searchByTerm({
    search_term: searchTerm.value,
    start_page: currentPage
}) as Array<ScrapedProductOffer>;

const stores = computed((): Array<string> => {
    return [...new Set(productStore.scrapedProductOffers?.map(offer => offer.merchant))].sort()
});

const optionLabelSelector = (option: ProductSearchSortOption) => {
    return option.Description;
};

const toggleFilter = (): void => {
    showFilter.value = !showFilter.value;
};

</script>
