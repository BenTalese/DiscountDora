<template>
    <!-- #region Toolbar -->
    <AddToolbarButton @click="onAddButtonClick" />
    <!-- #endregion Toolbar -->

    <q-card
        class="no-shadow q-ma-sm"
        :key="item.stock_item_id"
        bordered
        v-for="item in stockItems"
        vertical="false"
    >
        <q-card-section
            class="row justify-between"
            horizontal
        >
            <q-card-actions class="col">
                <q-btn-dropdown
                    class="q-mx-sm"
                    :color="
                        getStockLevelColour(stockLevels.find((sl) => sl.stock_level_id === item.stock_level_id)!.name)
                    "
                    :items="stockLevelStore.stockLevels"
                    dense
                    dropdown-icon="none"
                    no-caps
                    push
                    rounded
                    style="width: 28px"
                >
                    <q-item
                        :key="level.sequence"
                        @click="
                            updateStockLevelAsync({
                                stock_item_id: item.stock_item_id,
                                stock_level_id: level.stock_level_id
                            })
                        "
                        clickable
                        v-close-popup
                        v-for="level in stockLevelStore.stockLevels"
                    >
                        <q-item-section avatar>
                            <q-avatar
                                :color="getStockLevelColour(level.name)"
                                size="25px"
                            />
                        </q-item-section>

                        <q-item-section>
                            <q-item-label>{{ level.name }}</q-item-label>
                        </q-item-section>
                    </q-item>
                </q-btn-dropdown>
                <q-btn
                    class="q-mx-sm"
                    @click="onShoppingListButtonClick"
                    flat
                    icon="shopping_cart"
                    rounded
                />

                <q-separator
                    class="q-ml-sm q-mr-md"
                    vertical
                />
                <p class="text-bold q-ma-sm">{{ item.name }}</p>
            </q-card-actions>

            <q-card-section class="col">
                <p class="text-weight-bold q-ma-none">Location</p>
                <p class="q-ma-none">{{ 'item.stock_location' }}</p>
            </q-card-section>

            <q-card-section class="col">
                <p class="text-weight-bold q-ma-none">Stock Group</p>
                <p class="q-ma-none">{{ 'item.stock_group' }}</p>
            </q-card-section>
        </q-card-section>
    </q-card>

    <!-- #region Modals -->
    <CreateStockItemModal v-model="shouldDisplayCreateStockItemModal" />
    <AddToShoppingCartModal v-model="shouldDisplayAddToShoppingCartModal" />
    <!-- #endregion Modals -->
</template>

<script lang="ts" setup>
    //#region Imports
    import { storeToRefs } from 'pinia';
    import AddToShoppingCartModal from 'src/components/modal/AddToShoppingCartModal.vue';
    import CreateStockItemModal from 'src/components/modal/CreateStockItemModal.vue';
    import AddToolbarButton from 'src/components/toolbar/AddToolbarButton.vue';
    import { getStockLevelColour } from 'src/helpers/stockLevelLogic';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { ref } from 'vue';
    //#endregion Imports

    //#region Store Initialisation
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);
    const { updateStockLevelAsync } = stockItemStore;
    //#endregion Store Initialisation

    //#region State
    const shouldDisplayCreateStockItemModal = ref(false);
    const shouldDisplayAddToShoppingCartModal = ref(false);
    //#endregion State

    //#region Methods
    const onAddButtonClick = () => (shouldDisplayCreateStockItemModal.value = true);
    const onShoppingListButtonClick = () => (shouldDisplayAddToShoppingCartModal.value = true);
    //#endregion Methods
</script>
