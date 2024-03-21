<script setup lang="ts">
import { useStockItemStore } from 'src/stores/stockItemStore';
import { useStockLevelStore } from 'src/stores/stockLevelStore';
import { onMounted, ref } from 'vue';

const stockItemStore = useStockItemStore();
const stockLevelStore = useStockLevelStore();

onMounted(async () => {
    stockItemStore.getStockItems();
    stockLevelStore.getStockLevels();
})

// const test = async () => await stockItemApiService.create(form);
// const test2 = () => {
//     stockItemApiService.create({ name: "X", stock_level_id: "", stock_location_id: "" });
// }

//    <button class="btn" @click="test">Add/Save to 'My Products' / + </button>
// const form = reactive({
//     name: "",
//     stock_level_id: "stockLevels.value[0].stock_level_id",
//     stock_location_id: null
// });

// const model = ref(null)

const addToShoppingCartModal = ref(false)

// TODO: Need to order these in the UI
const stockLevelTestData = ref([
    { name: 'Out of Stock', colour: 'grey' },
    { name: 'Sufficient Stock', colour: 'yellow' },
    { name: 'Low Stock', colour: 'red' },
    { name: 'Well-Stocked', colour: 'green' },
])

const stockItemTestData = ref([
    { name: 'Bananas', stock_item_id: '1', stock_level_id: '4', stock_level_colour: 'green', stock_location: 'Pantry', stock_group: 'Fruit' },
    { name: 'Apples', stock_item_id: '2', stock_level_id: '5', stock_level_colour: 'yellow', stock_location: 'Kitchen Bench', stock_group: 'Fruit' },
    { name: 'Watermelon', stock_item_id: '3', stock_level_id: '6', stock_level_colour: 'red', stock_location: 'Fridge', stock_group: 'Not Not Fruit' }
])

const updateStockLevel = (stockItemID: string, stockLevelColour: string) => {
    const foundItem = stockItemTestData.value.find(e => e.stock_item_id === stockItemID);
    if (foundItem)
        foundItem.stock_level_colour = stockLevelColour;
}

// TODO: Loading text using fallback
// TODO: Loading spinner for API call (e.g. while scraping results) (or any loading at all)
</script>

<template>
    <q-btn-toggle v-model="model" toggle-color="primary" :options="[
        { label: 'Compact', value: 'Compact' },
        { label: 'Expanded', value: 'Expanded' }
    ]" />

    <!-- <q-card v-for="item in stockItemTestData" :key="item.stock_item_id" class="no-shadow" bordered>
        <q-btn-dropdown :color="item.stock_level_colour" :items="stockLevelTestData" dropdown-icon="none" class="q-pa-xs"
            push no-caps>
            <q-item clickable v-close-popup v-for="level in stockLevelTestData" :key="level.name"
                @click="updateStockLevel(item.stock_item_id, level.colour)">
                <q-item-section avatar>
                    <q-avatar :color="level.colour" size="25px" />
                </q-item-section>
                <q-item-section>
                    <q-item-label>{{ level.name }}</q-item-label>
                </q-item-section>
            </q-item>
        </q-btn-dropdown>
        {{ item.name }}
    </q-card> -->

    <q-btn color="green" class="q-ma-sm">
        <q-icon name="add" size="30px" color="dark-green" />
    </q-btn>

    <q-card v-for="item in stockItemTestData" :key="item.stock_item_id" class="no-shadow q-ma-sm" bordered vertical="false">
        <q-card-section horizontal class="row justify-between">

            <!-- <q-card-actions class="col" style="border-right: 3px black solid;"> -->
            <q-card-actions class="col">
                <q-btn-dropdown class="q-mx-sm" :color="item.stock_level_colour" :items="stockLevelTestData"
                    style="width: 28px;" dense rounded dropdown-icon="none" push no-caps>
                    <q-item clickable v-close-popup v-for="level in stockLevelTestData" :key="level.name"
                        @click="updateStockLevel(item.stock_item_id, level.colour)">
                        <q-item-section avatar>
                            <q-avatar :color="level.colour" size="25px" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>{{ level.name }}</q-item-label>
                        </q-item-section>
                    </q-item>
                </q-btn-dropdown>
                <q-btn class="q-mx-sm" flat rounded icon="shopping_cart" @click="addToShoppingCartModal = true" />

                <q-separator class="q-ml-sm q-mr-md" vertical />
                <p class="text-bold q-ma-sm">{{ item.name }}</p>
            </q-card-actions>

            <!-- Possibly want to group all cols together under one parent, and have buttons their own parent -->
            <!-- <q-card-section class="col">
                <p class="text-bold">{{ item.name }}</p>
            </q-card-section> -->

            <q-card-section class="col">
                <p class="text-weight-bold q-ma-none">Location</p>
                <p class="q-ma-none">{{ item.stock_location }}</p>
            </q-card-section>

            <q-card-section class="col">
                Stock Group: {{ item.stock_group }}
            </q-card-section>

        </q-card-section>
    </q-card>

    <!-- <q-dialog>
        <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">
        </q-form>
    </q-dialog> -->

    <q-dialog v-model="addToShoppingCartModal">
        <q-card style="width: 700px; max-width: 80vw;">
            <q-card-section class="row items-center">
                <span class="q-ml-sm">Add {{ "stock item" }} to a shopping list.</span>
            </q-card-section>

            <q-card-actions align="right">
                <q-btn flat label="Cancel" color="primary" v-close-popup />
                <q-btn flat label="Add to list" color="primary" v-close-popup />
            </q-card-actions>
        </q-card>
    </q-dialog>
</template>
