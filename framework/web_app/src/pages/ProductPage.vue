<template>
    <div
        v-if="product"
        class="row"
        style="padding: 10%; margin: 0 auto"
    >
        <div class="col-12 q-pb-sm">
            <span class="text-h6">{{ product.name }}</span>
        </div>
        <div class="col-12">
            <card-component
                :img="imageService.decodeBase64Image(product.image)"
                :img-caption="product.is_available ? undefined : 'OUT OF STOCK'"
                :row="$q.screen.gt.xs"
            >
                <template v-slot:body>
                    <q-card-section class="flex-1 q-py-none q-mt-sm">
                        <div class="column full-height no-wrap justify-between">
                            <div class="items-start column no-wrap">
                                <div
                                    class="row q-my-sm full-width"
                                    style="padding: 8px 16px"
                                >
                                    <q-item-label
                                        class="product-header-item-label"
                                        header
                                        style="padding: 0px; align-self: end"
                                    >
                                        Brand:
                                    </q-item-label>
                                    <q-item-label class="product-item-label">
                                        {{ product.brand }}
                                    </q-item-label>
                                </div>
                                <div
                                    class="row q-mb-sm full-width"
                                    style="padding: 8px 16px"
                                >
                                    <q-item-label
                                        class="product-header-item-label"
                                        header
                                        style="padding: 0px; align-self: end"
                                    >
                                        Store:
                                    </q-item-label>
                                    <q-item-label class="product-item-label">
                                        <component
                                            :is="
                                                MerchantLogoOptions[
                                                    product.merchant_name
                                                ]
                                            "
                                        />
                                    </q-item-label>
                                </div>
                                <div
                                    class="row q-mb-sm full-width"
                                    style="padding: 8px 16px"
                                >
                                    <q-item-label
                                        class="product-header-item-label"
                                        header
                                        style="padding: 0px; align-self: end"
                                    >
                                        Size:
                                    </q-item-label>
                                    <q-item-label class="product-item-label">
                                        {{ product.size }}
                                    </q-item-label>
                                </div>
                                <div
                                    class="row q-mb-sm full-width"
                                    style="padding: 8px 16px"
                                >
                                    <q-item-label
                                        class="product-header-item-label"
                                        header
                                        style="padding: 0px; align-self: end"
                                    >
                                        Stock Code:
                                    </q-item-label>
                                    <q-item-label class="product-item-label">
                                        {{ product.merchant_stockcode }}
                                    </q-item-label>
                                </div>

                                <div
                                    class="row q-mb-sm full-width"
                                    style="padding: 8px 16px"
                                >
                                    <q-item-label
                                        class="product-header-item-label"
                                        header
                                        style="padding: 0px; align-self: end"
                                    >
                                        Online Stock:
                                    </q-item-label>
                                    <q-item-label class="product-item-label">
                                        <q-badge
                                            class="pa-xs fw-500"
                                            color="green-6"
                                            text-color="black"
                                            v-if="product.is_available"
                                        >
                                            IN STOCK
                                        </q-badge>
                                        <q-badge
                                            class="pa-xs fw-500"
                                            color="red-6"
                                            text-color="black"
                                            v-else
                                        >
                                            OUT OF STOCK
                                        </q-badge>
                                    </q-item-label>
                                </div>

                                <div
                                    class="row q-mb-sm full-width"
                                    style="padding: 8px 16px"
                                >
                                    <q-item-label
                                        class="product-header-item-label"
                                        header
                                        style="
                                            margin-top: 4px;
                                            padding: 0px;
                                            align-self: start;
                                        "
                                    >
                                        Current Offer:
                                    </q-item-label>
                                    <div class="product-item-label">
                                        <q-item-label
                                            class="flex no-wrap items-center text-body2 fw-600"
                                            style="margin-top: 4px"
                                        >
                                            <template v-if="product.price_now">
                                                {{ `$${product.price_now}` }}

                                                <q-badge
                                                    class="pa-xs q-mx-sm fw-500"
                                                    color="yellow-6"
                                                    text-color="black"
                                                    v-if="
                                                        isCurrentOfferOnSpecial(
                                                            product
                                                        )
                                                    "
                                                >
                                                    SAVE ${{
                                                        product.price_difference
                                                    }}
                                                </q-badge>
                                            </template>
                                            <span v-else>
                                                Price Unavailable
                                            </span>
                                        </q-item-label>
                                        <q-item-label
                                            class="h-px-20 text-caption text-weight-regular"
                                        >
                                            <span
                                                v-if="
                                                    isCurrentOfferOnSpecial(
                                                        product
                                                    )
                                                "
                                            >
                                                <s>
                                                    {{
                                                        `$${product.price_was}`
                                                    }}
                                                </s>
                                                &nbsp;
                                            </span>
                                            <span v-if="product.price_now">
                                                {{ product.price_per_cup }}
                                            </span>
                                        </q-item-label>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </q-card-section>
                </template>
            </card-component>
        </div>
        <div class="col-12 q-mt-md">
            <q-card>
                <q-tabs
                    class="text-grey"
                    active-color="primary"
                    align="justify"
                    indicator-color="primary"
                    narrow-indicator
                    v-model="tab"
                >
                    <q-tab
                        name="linkedStockItem"
                        label="Linked Stock Item"
                    />
                </q-tabs>

                <q-separator />

                <q-tab-panels
                    animated
                    v-model="tab"
                >
                    <q-tab-panel
                        name="linkedStockItem"
                        style="padding: 0px"
                    >
                        <select-component
                            :dense="false"
                            :model-value="selectedStockItemModel"
                            :option-label="(si) => (si as StockItem).name"
                            :options="stockItems"
                            :stack-label="true"
                            @update:model-value="onUpdateLinkedStockItem"
                            clearable
                            filter
                            placeholder="Search for stock items"
                            style="margin: 0px"
                        />
                    </q-tab-panel>
                </q-tab-panels>
            </q-card>
        </div>
    </div>
    <div v-else class="row text-h3 q-ma-sm items-center">
        <img
            class="q-pa-sm round-img-230"
            src="../../src/assets/banana-peel.jpg"
        />

        <span class="text-h5 q-pa-sm">
            Product not found.
        </span>
    </div>
</template>

<script lang="ts" setup>
    import CardComponent from 'src/components/CardComponent.vue';
    import SelectComponent from 'src/components/SelectComponent.vue';
    import MerchantLogoOptions from 'src/helpers/merchantLogoOptions';
    import { isCurrentOfferOnSpecial } from 'src/helpers/productLogic';
    import { Product } from 'src/models/product';
    import { StockItem } from 'src/models/stockItem';
    import ImageService from 'src/services/files/imageService';
    import { useProductStore } from 'src/stores/productStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { computed, ref, watch } from 'vue';
    import { useRouter } from 'vue-router';

    //#region Common

    const { products } = useProductStore();
    const { productStockItems, stockItems, updateStockItemAsync } = useStockItemStore();

    const imageService = new ImageService();
    const router = useRouter();

    // TODO: check route value type, impacts .Find below
    const { productId } = router.currentRoute.value.params;

    // read on route changes
    // https://router.vuejs.org/guide/essentials/dynamic-matching

    //#endregion Common

    //#region Product

    // TODO Undefined products
    const product = products?.find(
        (p) => p.product_id === productId
    ) as Product;

    //#endregion Product

    //#region Linked Stock Item

    const stockItem: Readonly<StockItem> | undefined = computed(() =>
        productStockItems.find((psi) => psi.product.product_id === productId)
    ).value?.stockItem;


    let previousSelectedStockItemModel: StockItem | undefined = stockItem;
    const selectedStockItemModel = ref(stockItem);
    const tab = ref('linkedStockItem');

    watch(selectedStockItemModel, (value, oldValue) => {
        previousSelectedStockItemModel = oldValue
    })

    const onUpdateLinkedStockItem = (value: unknown): void => {
        const stockItem = value as StockItem;

        if(previousSelectedStockItemModel){
            updateStockItemAsync({
                product_ids_to_remove: [product.product_id],
                stock_item_id: previousSelectedStockItemModel.stock_item_id
            });
        }

        if(stockItem){
            updateStockItemAsync({
                product_ids_to_add: [product.product_id],
                stock_item_id: stockItem.stock_item_id
            });
        }

    };

    //#endregion Linked Stock Item
</script>
