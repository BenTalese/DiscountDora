<template>
    <div class="no-wrap q-pa-md row min-width-100 full-width">
        <q-input autofocus @keydown.enter="search" v-model="searchTerm" :disable="Loading.isActive" placeholder="Search"
            dense outlined square class="bg-white col">
            <template v-slot:prepend>
                <q-btn round dense flat icon="tune" @click="toggleShowFiltersContainer" />
                <q-btn round dense flat icon="search" @click="search" />
            </template>
        </q-input>
    </div>

    <div v-show="showFiltersContainer" class="no-wrap row q-pa-sm scroll scrollbar-none">

        <select-component label="Stores" :multiple="true" :options="merchantStore.merchants"
            :option-label="getStoresOptionLabel" :model-value="productStore.productSearchOfferFilters.stores"
            @update:model-value="productStore.setProductSearchStoresFilter" :optionIconName="getStoresOptionIcon" />

        <select-component label="Sort By" :options="OfferSortByOptions" :option-label="getSortByOptionLabel"
            :model-value="productStore.productSearchOfferFilters.sortBy"
            @update:model-value="productStore.setProductSearchSortByFilter" />

        <q-btn type="button" @click="toggleFilterFlag(nameof<IProductSearchFilters>('showOnlyAvailable'))" no-caps
            no-wrap size="md" :stretch="false"
            :class="getFilterBttnClass(productStore.productSearchOfferFilters.showOnlyAvailable)" class="q-ma-sm"
            square>
            <template v-slot>
                <span class="font-weight-400">In Stock</span>
            </template>
        </q-btn>

        <q-btn type="button" @click="toggleFilterFlag(nameof<IProductSearchFilters>('showOnlySpecials'))" no-caps
            no-wrap size="md" :stretch="false" text-color="black"
            :class="getFilterBttnClass(productStore.productSearchOfferFilters.showOnlySpecials)" class="q-ma-sm" square>
            <template v-slot>
                <span class="font-weight-400">Specials</span>
            </template>
        </q-btn>

    </div>

    <div class="card-grid">

        <div v-for="offer in productStore.filteredProductOffers" :key="offer.merchant_stockcode" class="q-pa-md">

            <card-component :img="imageService.decodeBase64Image(offer.image)"
                :img-caption="offer.is_available ? undefined : 'OUT OF STOCK'" icon="favorite"
                @icon-click="onIconClick(offer)" :icon-class="offer.is_saved && offer.is_saved_product_active ? 'text-red-12' : 'text-grey'">
                <template v-slot:body>
                    <q-card-section class="flex-1 q-py-none">
                        <div class="column full-height no-wrap justify-between">
                            <div class="text-body2 text-weight-regular q-pb-sm">
                                {{ `${offer.name} | ${offer.size}` }}
                            </div>
                            <div>
                                <div class="items-center no-wrap row text-body2 text-weight-medium">

                                    <template v-if="offer.price_now > 0">
                                        <span>
                                            {{ `$${offer.price_now}` }}
                                        </span>

                                        <q-badge v-if="offer.price_difference > 0" class="q-mx-sm" color="yellow-6"
                                            text-color="black">
                                            SAVE ${{ offer.price_difference }}
                                        </q-badge>
                                    </template>
                                    <span v-else>
                                        Price Unavailable
                                    </span>
                                </div>

                                <div class="h-px-20 text-caption text-weight-regular">
                                    <span v-if="isOfferOnSpecial(offer)">
                                        <s>{{ `$${offer.price_was}` }}</s>
                                        &nbsp;
                                    </span>
                                    <span>
                                        {{ offer.price_per_cup }}
                                    </span>
                                </div>

                            </div>
                        </div>
                    </q-card-section>
                </template>

                <template v-slot:footer>
                    <q-card-actions align="right" class="bg-off-white">
                        <component :is="MerchantLogoOptions[offer.merchant_name]" />
                    </q-card-actions>
                </template>
            </card-component>

        </div>
    </div>
    <div v-if="!Loading.isActive && previousSearchTerm && !productStore.productOffers?.length"
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
import MerchantLogoOptions from 'src/helpers/merchantLogoOptions';
import nameof from 'src/helpers/nameOf';
import { IOfferSortByOption, OfferSortByOptions } from 'src/helpers/offerSortByOptions';
import { isOfferOnSpecial } from 'src/helpers/scrapedProductOfferLogic';
import { Merchant } from 'src/models/merchant';
import { ScrapedProductOffer } from 'src/models/scrapedProductOffer';
import ImageService from 'src/services/files/imageService';
import { useMerchantStore } from 'src/stores/merchantStore';
import { IProductSearchFilters, useProductStore } from 'src/stores/productStore';
import { ref } from 'vue';

const merchantStore = useMerchantStore();
const productStore = useProductStore();

//#region Search

const searchTerm = ref('');
const previousSearchTerm = ref<undefined | string>();

let currentPage = 1; // TODO: What to do with this now?

const search = (): Promise<string> =>
    productStore.searchByTermAsync({
        search_term: searchTerm.value,
        merchants_to_search: productStore.productSearchOfferFilters.stores.map(merchant => merchant.name)
    })
    .then(() => previousSearchTerm.value = searchTerm.value);

//#endregion Search

//#region Filters

const showFiltersContainer = ref(true);

const toggleShowFiltersContainer = (): boolean =>
    showFiltersContainer.value = !showFiltersContainer.value;

const toggleFilterFlag = (filterName: string): void =>
    productStore.toggleProductSearchFilter(filterName as keyof IProductSearchFilters);

const getFilterBttnClass = (isSelected: boolean) => isSelected ? 'bg-blue' : 'bg-white';

const getSortByOptionLabel = (option: IOfferSortByOption): string =>
    option.description;

const getStoresOptionLabel = (merchant: Merchant) =>
    merchant.name;

const getStoresOptionIcon = (isSelected: boolean): string =>
    isSelected ? 'check_box' : 'check_box_outline_blank';

//#endregion Filters

//#region Offers

const imageService = new ImageService();

/**
 * Updates the offer and its matching saved product.
 * Creates the saved product if it does not exist.
 * @param offer the product offer
 */
const onIconClick = (offer: ScrapedProductOffer): void => {

    const { is_saved_product_active, merchant_name, merchant_stockcode } = offer;

    const product = productStore.products?.find(p =>
        p.merchant_name === offer.merchant_name
        && p.merchant_stockcode === offer.merchant_stockcode);

    if (product)
        productStore.updateProductAsync({
            is_active: !is_saved_product_active,
            product_id: product.product_id
        })
        .then(() => productStore.updateProductOffer({
            is_saved_product_active: !is_saved_product_active,
            merchant_name,
            merchant_stockcode
        }));

    else
        productStore.createProductAsync({
            ...offer,
            is_active: true
        })
        .then(() => productStore.updateProductOffer({
            is_saved: true,
            is_saved_product_active: true,
            merchant_name,
            merchant_stockcode
        }));
}

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
