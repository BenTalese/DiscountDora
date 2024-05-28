<template>

    <div class="no-wrap q-pa-md row min-width-100 full-width">
        <q-btn type="button" no-caps no-wrap size="md" :stretch="false" square>
            <template v-slot>
                <span class="font-weight-400">Add</span>
            </template>
        </q-btn>
    </div>

    <div class="card-grid">

        <div v-for="product in productStore.products" :key="product.merchant_stockcode" class="q-pa-md">

            <card-component :img="imageService.decodeBase64Image(product.image)" icon="favorite"
                @icon-click="OnIconClick(product)" :icon-class="product.is_active ? 'text-red-12' : 'text-grey'">
                <template v-slot:body>
                    <q-card-section class="flex-1 q-py-none">
                        <div class="column full-height no-wrap justify-between">
                            <div class="text-body2 text-weight-regular q-pb-sm">
                                {{ `${product.name} | ${product.size}` }}
                            </div>
                        </div>
                    </q-card-section>
                </template>

                <template v-slot:footer>
                    <q-card-actions align="right" class="bg-off-white">
                        <component :is="MerchantLogoOptions[product.merchant_name]" />
                    </q-card-actions>
                </template>
            </card-component>

        </div>
    </div>
</template>

<script setup lang="ts">

import CardComponent from 'src/components/CardComponent.vue';
import MerchantLogoOptions from 'src/helpers/MerchantLogoOptions';
import { Product } from 'src/models/Product';
import ImageService from 'src/services/files/ImageService';
import { useProductStore } from 'src/stores/ProductStore';

const productStore = useProductStore();

//#region Offers

const imageService = new ImageService();

/**
 * Toggles the is_active state of the product and if it exists,
 * the is_product active state of the corresponding product offer.
 * @param product to activate/deactivate
 */
const OnIconClick = (product: Product): void => {
    const { is_active, merchant_name, merchant_stockcode, product_id } = product;

    productStore.updateProductAsync({
        is_active: !is_active,
        product_id
    })
        .then(() => productStore.updateProductOffer({
            is_saved_product_active: !is_active,
            merchant_name,
            merchant_stockcode
        }));
};

//#endregion Offers

</script>

<style scoped>
.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
}
</style>
