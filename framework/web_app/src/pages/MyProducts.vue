<template>
  <div class="no-wrap q-pa-md row min-width-100 full-width">
    <q-btn type="button" no-caps no-wrap size="md" :stretch="false" square>
      <template v-slot>
        <span class="font-weight-400">Add</span>
      </template>
    </q-btn>
  </div>

  <div class="card-grid">
    <div
      v-for="product in productStore.products"
      :key="product.merchant_stockcode"
      class="q-pa-md"
    >
      <!-- TODO: Look into improving reusability -->
      <!-- TODO: highlighting name triggers click event -->
      <!-- TODO: change cursor to 'click' -->
      <card-component
        :img="imageService.decodeBase64Image(product.image)"
        icon="favorite"
        @icon-container-click="openProductModal(product)"
        @icon-click="OnIconClick(product, $event)"
        :icon-class="product.is_active ? 'text-red-12' : 'text-grey'"
      >
        <template v-slot:body>
          <q-card-section
            class="flex-1 q-py-none"
            @click="openProductModal(product)"
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
            align="right"
            class="bg-off-white"
            @click="openProductModal(product)"
          >
            <component :is="MerchantLogoOptions[product.merchant_name]" />
          </q-card-actions>
        </template>
      </card-component>
    </div>
  </div>

  <q-dialog
    v-model="shouldDisplayProductModal"
    position="bottom"
    full-width
    maximized
    :no-esc-dismiss="false"
  >
    <q-card style="height: 75vh; scrollbar-width: 0px">
      <q-card-section class="row justify-around">
        <div class="col-9">
          <div class="q-mx-sm items-center column">
            <div class="text-weight-bold">{{ selectedProduct?.name }}</div>
          </div>
          <div
            class="q-ma-sm bg-off-white items-start column no-wrap"
            style="border: 1px solid rgba(0, 0, 0, 0.12)"
          >
            <template v-for="(value, key) in selectedProduct">
              <div class="q-pa-sm">
                <div class="text-grey-10">{{ key }}</div>
                <div class="text-weight-bold">{{ value }}</div>
              </div>
            </template>
          </div>
          <div
            class="q-ma-sm bg-off-white items-start column no-wrap"
            style="border: 1px solid rgba(0, 0, 0, 0.12)"
          >
            <div class="q-pa-sm">
              <div class="text-weight-bold">Graph</div>
            </div>
          </div>
          <div
            class="q-ma-sm bg-off-white items-start column no-wrap"
            style="border: 1px solid rgba(0, 0, 0, 0.12);"
          >
            <div class="q-pa-sm" style="width: 100%;">
              <div class="text-weight-bold">Linked Stock Items</div>
              <LinkedItemsTable />
            </div>
          </div>
        </div>
        <div class="col-3 items-center column no-wrap">
          <div class="column" style="position: fixed">
            <div class="text-weight-bold">Nav</div>
            <q-chip label="Product Details" />
            <q-chip label="Price History" />
            <q-chip label="Linked Stock" />
            <q-separator />
            <div class="text-weight-bold">Quick Actions</div>
            <q-chip label="Current Deal" />
          </div>
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import CardComponent from "src/components/CardComponent.vue";
import LinkedItemsTable from "src/components/LinkedItemsTable.vue";
import MerchantLogoOptions from "src/helpers/MerchantLogoOptions";
import { Product } from "src/models/Product";
import { StockItem } from "src/models/StockItem";
import ImageService from "src/services/files/ImageService";
import { useProductStore } from "src/stores/ProductStore";
import { ref } from "vue";

const productStore = useProductStore();

//#region Offers

//TODO: move onIconClick offer update here

//#endregion Offers

//#region Products

const imageService = new ImageService();

/**
 * Toggles the is_active state of the product and if it exists,
 * the is_product active state of the corresponding product offer.
 * @param product to activate/deactivate
 */
const OnIconClick = (product: Product, event?: Event): void => {
  //TODO: make stop propagation built in behaviour to CardComponent
  console.log("icon-click");
  return;

  const { is_active, merchant_name, merchant_stockcode, product_id } = product;

  //TODO: consider moving this out into another method too
  productStore
    .updateProductAsync({
      is_active: !is_active,
      product_id,
    })
    .then(() =>
      productStore.updateProductOffer({
        is_saved_product_active: !is_active,
        merchant_name,
        merchant_stockcode,
      }),
    );
};

const OnIconContainerClick = (product: Product, event: Event): void => {
  console.log("icon-container-click");
  openProductModal(product);
};

//#endregion Products

//#region Product Details Form

const shouldDisplayProductModal = ref(false);

let selectedProduct: Product | null = null;

const openProductModal = (product: Product) => {
  selectedProduct = product;
  shouldDisplayProductModal.value = true;
};

const dummyLinkedStockModel: StockItem[] = [];

//#endregion Product Details Form
</script>

<style scoped>
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
}
</style>
