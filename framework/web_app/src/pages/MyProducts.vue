<template>
    <div class="no-wrap q-pa-md row min-width-100 full-width">
        <q-btn
            type="button"
            :stretch="false"
            no-caps
            no-wrap
            size="md"
            square
        >
            <template v-slot>
                <span class="font-weight-400">Add</span>
            </template>
        </q-btn>
    </div>

    <div class="card-grid">
        <div
            class="q-pa-md"
            :key="product.merchant_stockcode"
            v-for="product in productStore.products"
        >
            <card-component
                :icon-class="product.is_active ? 'text-red-12' : 'text-grey'"
                :img="imageService.decodeBase64Image(product.image)"
                @icon-click="OnIconClick(product)"
                @icon-container-click="OnIconContainerClick(product)"
                icon="favorite"
            >
                <template v-slot:body>
                    <q-card-section
                        class="flex-1 q-py-none"
                        @click="OnIconContainerClick(product)"
                    >
                        <div class="column full-height no-wrap justify-between">
                            <div class="text-body2 text-weight-regular q-pb-sm">
                                {{ `${product.name} | ${product.size}` }}
                            </div>
                        </div>
                    </q-card-section>
                </template>

                <template v-slot:footer>
                    <q-card-actions
                        class="bg-off-white"
                        @click="OnIconContainerClick(product)"
                        align="right"
                    >
                        <component
                            :is="MerchantLogoOptions[product.merchant_name]"
                        />
                    </q-card-actions>
                </template>
            </card-component>
        </div>
    </div>
</template>

<script lang="ts" setup>
    import CardComponent from 'src/components/CardComponent.vue';
    import MerchantLogoOptions from 'src/helpers/merchantLogoOptions';
    import { Product } from 'src/models/product';
    import ImageService from 'src/services/files/imageService';
    import { useProductStore } from 'src/stores/productStore';
    import { useRouter } from 'vue-router';

    //#region Common

    const productStore = useProductStore();

    const router = useRouter();

    //#endregion Common

    //#region Products

    const imageService = new ImageService();

    /**
     * Toggles the is_active state of the product and if it exists,
     * the is_product active state of the corresponding product offer.
     * @param product to activate/deactivate
     */
    const OnIconClick = (product: Product): void => {

        const { is_active, merchant_name, merchant_stockcode, product_id } =
            product;

        productStore
            .updateProductAsync({
                is_active: !is_active,
                product_id
            })
            .then(() =>
                productStore.updateProductOffer({
                    is_saved_product_active: !is_active,
                    merchant_name,
                    merchant_stockcode
                })
            );
    };

    const OnIconContainerClick = (product: Product): void => {
        router.push({
            path: `/products/${product.product_id}`
        });
    };

    //#endregion Products
</script>
