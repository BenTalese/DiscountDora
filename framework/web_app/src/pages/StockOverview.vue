<template>
    <q-btn
        color="green"
        class="q-ma-sm"
        @click="shouldDisplayCreateStockItemModal = true"
    >
        <q-icon
            name="add"
            size="30px"
            color="dark-green"
        />
    </q-btn>

    <q-card
        v-for="item in stockItemStore.stockItems"
        :key="item.stock_item_id"
        class="no-shadow q-ma-sm"
        bordered
        vertical="false"
    >
        <q-card-section
            horizontal
            class="row justify-between"
        >
            <q-card-actions class="col">
                <!-- style="border-right: 3px black solid;" /> -->
                <q-btn-dropdown
                    class="q-mx-sm"
                    :color="getStockLevelColour(item.stock_level_id)"
                    :items="stockLevelStore.stockLevels"
                    style="width: 28px"
                    dense
                    rounded
                    dropdown-icon="none"
                    push
                    no-caps
                >
                    <q-item
                        clickable
                        v-close-popup
                        v-for="level in stockLevelStore.stockLevels"
                        :key="level.sequence"
                        @click="
                            updateStockLevelAsync(
                                item.stock_item_id,
                                level.stock_level_id,
                            )
                        "
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
                            <q-item-label>{{ level.description }}</q-item-label>
                        </q-item-section>
                    </q-item>
                </q-btn-dropdown>
                <q-btn
                    class="q-mx-sm"
                    flat
                    rounded
                    icon="shopping_cart"
                    @click="shouldDisplayAddToShoppingCartModal = true"
                />

                <q-separator
                    class="q-ml-sm q-mr-md"
                    vertical
                />
                <p class="text-bold q-ma-sm">{{ item.name }}</p>
            </q-card-actions>

            <!-- Possibly want to group all cols together under one parent, and have buttons their own parent -->
            <!-- <q-card-section class="col">
                <p class="text-bold">{{ item.name }}</p>
            </q-card-section> -->

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

    <q-dialog v-model="shouldDisplayCreateStockItemModal">
        <q-card class="q-pa-md">
            <p class="text-h4">Add a new stock item</p>
            <q-form
                @submit="createStockItemAsync(createStockItemForm)"
                class="q-gutter-md"
            >
                <q-input
                    label="Name"
                    filled
                    lazy-rules
                    :rules="[
                        (val) =>
                            (val && val.length > 0) || 'Please type something',
                    ]"
                    v-model="createStockItemForm.name"
                />

                <q-input
                    filled
                    type="number"
                    label="Days Until Stocktake Alert"
                />

                <q-select
                    label="Stock Level"
                    :option-label="nameof<StockLevel>((src) => src.description)"
                    option-value="stock_level_id"
                    :options="stockLevelStore.stockLevels"
                    v-model="createStockItemForm.stock_level_id"
                >
                    <template v-slot:option="scope">
                        <q-item v-bind="scope.itemProps">
                            <q-item-section avatar>
                                <q-avatar
                                    :color="
                                        getStockLevelColour(
                                            scope.opt.stock_level_id,
                                        )
                                    "
                                    size="25px"
                                />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>
                                    {{ scope.opt.description }}
                                </q-item-label>
                            </q-item-section>
                        </q-item>
                    </template>
                </q-select>

                <!-- TODO: IMPLEMENT -->
                <q-select label="Stock Group"></q-select>

                <!-- TODO: IMPLEMENT -->
                <q-select label="Stock Location"></q-select>

                <q-btn
                    label="Submit"
                    type="submit"
                    color="primary"
                />
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
                    flat
                    label="Cancel"
                    color="primary"
                    v-close-popup
                />
                <q-btn
                    flat
                    label="Add to list"
                    color="primary"
                    v-close-popup
                />
            </q-card-actions>
        </q-card>
    </q-dialog>
</template>

<script setup lang="ts">
    import { nameof } from 'src/helpers/Nameof'
    import { StockLevel } from 'src/models/StockLevel'
    import { CreateStockItemCommand } from 'src/services/api/StockItemApiService'
    import { useStockItemStore } from 'src/stores/stockItemStore'
    import { useStockLevelStore } from 'src/stores/stockLevelStore'
    import { Ref, ref } from 'vue'

    const shouldDisplayAddToShoppingCartModal = ref(false)
    const shouldDisplayCreateStockItemModal = ref(false)
    const stockItemStore = useStockItemStore()
    const stockLevelStore = useStockLevelStore()

    const { createStockItemAsync, updateStockLevelAsync } = stockItemStore

    // TODO: Not sure if this is the best type to use here
    const createStockItemForm: Ref<CreateStockItemCommand> = ref({
        days_until_stocktake_alert: 0,
        name: '',
        stock_group_id: '',
        stock_level_id: '',
        stock_location_id: '',
    })

    // TODO: Move to logic file
    // TODO: Look into PartialWithRequired tht atif uses
    // TODO: Look into "...offer" and how it works
    function getStockLevelColour(stockLevelID: string) {
        let stock_level = stockLevelStore.stockLevels.find(
            (sl) => sl.stock_level_id == stockLevelID,
        )

        if (stock_level?.description == 'Well-Stocked') {
            return 'green'
        }

        if (stock_level?.description == 'Sufficient Stock') {
            return 'yellow'
        }

        if (stock_level?.description == 'Low Stock') {
            return 'red'
        }

        if (stock_level?.description == 'Out of Stock') {
            return 'grey'
        }

        throw new Error(
            `Colour not configured for stock level '${stock_level?.description}'.`,
        )
    }
</script>
