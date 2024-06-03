<template>
    <q-btn
        class="q-ma-sm"
        @click="onCreateStockItemButtonClick"
        color="green"
    >
        <q-icon
            name="add"
            color="dark-green"
            size="30px"
        />
    </q-btn>

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
                    :color="getStockLevelColour(item.stock_level_id)"
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
                                :color="
                                    getStockLevelColour(level.stock_level_id)
                                "
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

    <q-dialog
        @hide="clearCreateStockItemForm"
        v-model="shouldDisplayCreateStockItemModal"
    >
        <q-card
            class="q-pa-md"
            style="width: 700px; max-width: 80vw"
        >
            <p class="text-h4">Add a new stock item</p>
            <q-form
                class="q-gutter-md"
                @submit="createStockItemAsync(createStockItemForm)"
            >
                <q-input
                    :rules="nameInputRules"
                    autofocus
                    filled
                    label="Name"
                    v-model="createStockItemForm.name"
                />

                <q-input
                    type="number"
                    filled
                    hint="Alerts disabled if set to zero"
                    label="Days Until Stocktake Alert"
                    v-model="createStockItemForm.days_until_stocktake_alert"
                />

                <q-select
                    :option-label="getStockLevelName"
                    :option-value="getStockLevelID"
                    :options="stockLevelStore.stockLevels"
                    :rules="stockLevelSelectRules"
                    emit-value
                    label="Stock Level"
                    map-options
                    v-model="createStockItemForm.stock_level_id"
                >
                    <template v-slot:option="scope">
                        <q-item v-bind="scope.itemProps">
                            <q-item-section avatar>
                                <q-avatar
                                    :color="
                                        getStockLevelColour(
                                            scope.opt.stock_level_id
                                        )
                                    "
                                    size="25px"
                                />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>
                                    {{ scope.opt.name }}
                                </q-item-label>
                            </q-item-section>
                        </q-item>
                    </template>
                </q-select>

                <!-- TODO: IMPLEMENT -->
                <q-select
                    label="Stock Group"
                    v-model="createStockItemForm.stock_group_id"
                ></q-select>

                <!-- TODO: IMPLEMENT -->
                <q-select
                    label="Stock Location"
                    v-model="createStockItemForm.stock_location_id"
                ></q-select>

                <q-card-actions align="right">
                    <q-btn
                        type="submit"
                        align="right"
                        color="cyan"
                        label="Save & Continue"
                        size="lg"
                    />
                    <q-btn
                        type="submit"
                        align="right"
                        color="green"
                        label="Save & Close"
                        size="lg"
                        v-close-popup
                    />
                </q-card-actions>
            </q-form>
        </q-card>
    </q-dialog>

    <q-dialog v-model="shouldDisplayAddToShoppingCartModal">
        <q-card style="width: 700px; max-width: 80vw">
            <q-card-section class="row items-center">
                <span class="q-ml-sm">
                    Add {{ 'stock item' }} to a shopping list.
                </span>
            </q-card-section>

            <q-card-actions align="right">
                <q-btn
                    color="primary"
                    flat
                    label="Cancel"
                    v-close-popup
                />
                <q-btn
                    color="primary"
                    flat
                    label="Add to list"
                    v-close-popup
                />
            </q-card-actions>
        </q-card>
    </q-dialog>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import { ValidationRule } from 'quasar';
    import { StockLevel } from 'src/models/StockLevel';
    import { CreateStockItemCommand } from 'src/services/api/StockItemApiService';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { reactive, ref } from 'vue';

    //#region Common

    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();

    const { stockItems } = storeToRefs(stockItemStore);
    const { createStockItemAsync, updateStockLevelAsync } = stockItemStore;

    const { stockLevels } = storeToRefs(stockLevelStore);
    const { getStockLevelColour } = stockLevelStore;

    //#endregion Common

    //#region Create Stock Item

    const shouldDisplayCreateStockItemModal = ref(false);

    const defaultCreateStockItemForm = {
        days_until_stocktake_alert: 0,
        name: '',
        stock_group_id: null,
        stock_level_id: stockLevels.value[0]?.stock_level_id,
        stock_location_id: null
    };

    const createStockItemForm: CreateStockItemCommand = reactive({
        ...defaultCreateStockItemForm
    });

    function clearCreateStockItemForm() {
        Object.assign(createStockItemForm, defaultCreateStockItemForm);
    }

    const onCreateStockItemButtonClick = () =>
        (shouldDisplayCreateStockItemModal.value = true);

    //#endregion Create Stock Item

    //#region Create Stock Item Rules

    const nameInputRules: ValidationRule[] = [
        (val: string) => (val && val.length > 0) || 'Please type something'
    ];

    const stockLevelSelectRules: ValidationRule[] = [
        (val: string) => !!val || 'Please select a stock level'
    ];

    //#endregion Create Stock Item Rules

    //#region Shopping List

    const shouldDisplayAddToShoppingCartModal = ref(false);

    const onShoppingListButtonClick = () =>
        (shouldDisplayAddToShoppingCartModal.value = true);

    //#endregion Shopping List

    //#region Stock Level

    const getStockLevelID = (stockLevel: StockLevel) =>
        stockLevel.stock_level_id;

    const getStockLevelName = (stockLevel: StockLevel) => stockLevel.name;

    //#endregion Stock Level
</script>
