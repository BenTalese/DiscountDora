<template>
    <div class="no-wrap q-pa-md row dora-minWidth-100 full-width">
        <q-input
            class="bg-white col"
            :disable="Loading.isActive"
            @keydown.enter="search"
            autofocus
            dense
            outlined
            placeholder="Search"
            square
            v-model="searchTerm"
        >
            <template v-slot:prepend>
                <q-btn
                    @click="toggleShowFiltersContainer"
                    dense
                    flat
                    icon="tune"
                    round
                />
                <q-btn
                    @click="search"
                    dense
                    flat
                    icon="search"
                    round
                />
            </template>
        </q-input>
    </div>

    <div
        class="no-wrap row q-pa-sm scroll dorascoped-scrollbar-none"
        v-show="showFiltersContainer"
    >
        <select-component
            :model-value="productStore.productSearchOfferFilters.stores"
            :multiple="true"
            :option-label="getStoresOptionLabel"
            :optionIconName="getStoresOptionIcon"
            :options="merchantStore.getEnabledMerchants"
            @update:model-value="productStore.setProductSearchStoresFilter"
            label="Stores"
        />

        <select-component
            :model-value="productStore.productSearchOfferFilters.sortBy"
            :option-label="getSortByOptionLabel"
            :options="OfferSortByOptions"
            @update:model-value="productStore.setProductSearchSortByFilter"
            label="Sort By"
        />

        <q-btn
            class="q-ma-sm"
            type="button"
            :class="
                getFilterBttnClass(
                    productStore.productSearchOfferFilters.showOnlyAvailable
                )
            "
            :stretch="false"
            @click="
                toggleFilterFlag(
                    nameof<IProductSearchFilters>('showOnlyAvailable')
                )
            "
            no-caps
            no-wrap
            size="md"
            square
        >
            <template v-slot>
                <span class="dora-fontWeight-400">In Stock</span>
            </template>
        </q-btn>

        <q-btn
            class="q-ma-sm"
            type="button"
            :class="
                getFilterBttnClass(
                    productStore.productSearchOfferFilters.showOnlySpecials
                )
            "
            :stretch="false"
            @click="
                toggleFilterFlag(
                    nameof<IProductSearchFilters>('showOnlySpecials')
                )
            "
            no-caps
            no-wrap
            size="md"
            square
            text-color="black"
        >
            <template v-slot>
                <span class="dora-fontWeight-400">Specials</span>
            </template>
        </q-btn>
    </div>

    <div class="dorascoped-card-grid">
        <div
            class="q-pa-md"
            :key="offer.merchant_stockcode"
            v-for="offer in productStore.filteredProductOffers"
        >
            <card-component
                :icon-class="
                    offer.is_saved && offer.is_saved_product_active
                        ? 'text-red-12'
                        : 'text-grey'
                "
                :img="imageService.decodeBase64Image(offer.image)"
                :img-caption="offer.is_available ? undefined : 'OUT OF STOCK'"
                @icon-click="onIconClick(offer)"
                icon="favorite"
            >
                <template v-slot:body>
                    <q-card-section class="dora-flex-1 q-py-none">
                        <div class="column full-height no-wrap justify-between">
                            <div class="text-body2 text-weight-regular q-pb-sm">
                                {{ `${offer.name} | ${offer.size}` }}
                            </div>
                            <div>
                                <div
                                    class="items-center no-wrap row text-body2 text-weight-medium"
                                >
                                    <template v-if="offer.price_now > 0">
                                        <span>
                                            {{ `$${offer.price_now}` }}
                                        </span>

                                        <q-badge
                                            class="q-mx-sm"
                                            color="yellow-6"
                                            text-color="black"
                                            v-if="offer.price_difference > 0"
                                        >
                                            SAVE ${{ offer.price_difference }}
                                        </q-badge>
                                    </template>
                                    <span v-else>Price Unavailable</span>
                                </div>

                                <div
                                    class="dora-height-20 text-caption text-weight-regular"
                                >
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
                    <q-card-actions
                        class="dora-bgc-offWhite"
                        align="right"
                    >
                        <component
                            :is="MerchantLogoOptions[offer.merchant_name]"
                        />
                    </q-card-actions>
                </template>
            </card-component>
        </div>
    </div>
    <div
        class="row text-h3 q-ma-sm items-center"
        v-if="
            !Loading.isActive &&
            previousSearchTerm &&
            !productStore.productOffers?.length
        "
    >
        <img
            class="q-pa-sm dorascoped-round-img"
            src="../../src/assets/banana-peel.jpg"
        />

        <span class="text-h5 q-pa-sm">
            No products found for '{{ previousSearchTerm }}'.
        </span>
    </div>
    <!-- TODO: Add v-if for all merchants filtered to have -->
</template>

<script lang="ts" setup>
    import { Loading, setCssVar } from 'quasar';
    import CardComponent from 'src/components/CardComponent.vue';
    import SelectComponent from 'src/components/SelectComponent.vue';
    import MerchantLogoOptions from 'src/helpers/merchantLogoOptions';
    import nameof from 'src/helpers/nameOf';
    import {
        IOfferSortByOption,
        OfferSortByOptions
    } from 'src/helpers/offerSortByOptions';
    import { isOfferOnSpecial } from 'src/helpers/scrapedProductOfferLogic';
    import { Merchant } from 'src/models/merchant';
    import { ScrapedProductOffer } from 'src/models/scrapedProductOffer';
    import ImageService from 'src/services/files/imageService';
    import { useMerchantStore } from 'src/stores/merchantStore';
    import {
        IProductSearchFilters,
        useProductStore
    } from 'src/stores/productStore';
    import { ref } from 'vue';

    import { colors } from 'quasar'

    const { getPaletteColor } = colors

    setCssVar('primary', getPaletteColor('test'))

    const merchantStore = useMerchantStore();
    const productStore = useProductStore();

    //#region Search

    const searchTerm = ref('');
    const previousSearchTerm = ref<undefined | string>();

    const search = (): Promise<string> =>
        productStore
            .searchByTermAsync({
                search_term: searchTerm.value,
                result_limit: 5, // TODO: NEEDS TO BE AN INPUT
                merchants_to_search:
                    productStore.productSearchOfferFilters.stores.map(
                        (merchant) => merchant.name
                    )
            })
            .then(() => (previousSearchTerm.value = searchTerm.value));

    //#endregion Search

    //#region Filters

    const showFiltersContainer = ref(true);

    const toggleShowFiltersContainer = (): boolean =>
        (showFiltersContainer.value = !showFiltersContainer.value);

    const toggleFilterFlag = (filterName: string): void =>
        productStore.toggleProductSearchFilter(
            filterName as keyof IProductSearchFilters
        );

    const getFilterBttnClass = (isSelected: boolean) =>
        isSelected ? 'bg-blue' : 'bg-white';

    const getSortByOptionLabel = (option: IOfferSortByOption): string =>
        option.description;

    const getStoresOptionLabel = (merchant: Merchant) => merchant.name;

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
        const { is_saved_product_active, merchant_name, merchant_stockcode } =
            offer;

        const product = productStore.products?.find(
            (p) =>
                p.merchant_name === offer.merchant_name &&
                p.merchant_stockcode === offer.merchant_stockcode
        );

        if (product)
            productStore
                .updateProductAsync({
                    is_active: !is_saved_product_active,
                    product_id: product.product_id
                })
                .then(() =>
                    productStore.updateProductOffer({
                        is_saved_product_active: !is_saved_product_active,
                        merchant_name,
                        merchant_stockcode
                    })
                );
        else
            productStore
                .createProductAsync({
                    ...offer,
                    is_active: true
                })
                .then(() =>
                    productStore.updateProductOffer({
                        is_saved: true,
                        is_saved_product_active: true,
                        merchant_name,
                        merchant_stockcode
                    })
                );
    };

    //#endregion Offers

</script>

<style scoped>
    .dorascoped-card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    }

    .dorascoped-round-img {
        border-radius: 50%;
        width: 230px;
    }

    .dorascoped-scrollbar-none {
        scrollbar-width: none;
    }
</style>
