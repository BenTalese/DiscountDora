<script setup lang="ts">
import { StockItem } from 'src/models/StockItem';
import { StockLevel } from 'src/models/StockLevel';
import StockItemApiService from 'src/services/api/StockItemApiService';
import StockLevelApiService from 'src/services/api/StockLevelApiService';
import type { Ref } from 'vue';
import { onMounted, reactive, ref } from 'vue';

const stockItems: Ref<StockItem[]> = ref([]);
const stockLevels: Ref<StockLevel[]> = ref([]);

const stockItemApiService = new StockItemApiService();
const stockLevelApiService = new StockLevelApiService();

onMounted(async () => {
    stockItems.value = await stockItemApiService.getAll();
    stockLevels.value = await stockLevelApiService.getAll();
    console.log(stockItems.value[0])
    console.log(stockLevels.value)
    form.stock_level_id = stockLevels.value[0].stock_level_id
})

// const test = async () => await stockItemApiService.create(form);
// const test2 = () => {
//     stockItemApiService.create({ name: "X", stock_level_id: "", stock_location_id: "" });
// }

//    <button class="btn" @click="test">Add/Save to 'My Products' / + </button>
const form = reactive({
    name: "",
    stock_level_id: "stockLevels.value[0].stock_level_id",
    stock_location_id: null
});

const model = ref(null)

// TODO: Need to order these in the UI
const stockLevelTestData = ref([
    { name: 'Out of Stock', colour: 'grey' },
    { name: 'Sufficient Stock', colour: 'yellow' },
    { name: 'Low Stock', colour: 'red' },
    { name: 'Well-Stocked', colour: 'green' },
])

const stockItemTestData = ref([
    { name: 'Bananas', stock_item_id: '1', stock_level_id: '4', stock_level_colour: 'green', stock_location_id: '7' },
    { name: 'Apples', stock_item_id: '2', stock_level_id: '5', stock_level_colour: 'yellow', stock_location_id: '8' },
    { name: 'Watermelon', stock_item_id: '3', stock_level_id: '6', stock_level_colour: 'red', stock_location_id: '9' },
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

    <q-card v-for="item in stockItemTestData" :key="item.stock_item_id" class="no-shadow" bordered>
        <q-btn-dropdown :color="item.stock_level_colour" :items="stockLevelTestData" dropdown-icon="none"
            class="q-pa-xs" push no-caps>
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
    </q-card>

    <q-card v-for="item in stockItemTestData" :key="item.stock_item_id" class="no-shadow q-ma-sm" bordered>
        <q-card-section class="q-pa-sm">
            <!-- <q-avatar :color="item.stock_level_colour" size="25px" style="border: 2px solid rgb(126, 126, 126);"
                    class="q-mr-xs"></q-avatar> -->
            <!-- <q-btn-dropdown icon="check" :label="item.selectedStatus"
                    :items="statusOptions.map(status => ({ label: status, value: status }))" dense /> -->
            <q-btn-dropdown :color="item.stock_level_colour" :items="stockLevelTestData" dense rounded dropdown-icon="none"
                class="q-pa-xs" push no-caps>
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
        </q-card-section>

        <q-card-actions>
            <q-btn flat rounded icon=""/>
        </q-card-actions>
    </q-card>

    <!-- <form @submit.prevent="test">
        <label for="name">Name</label>
        <input id="name" v-model="form.name" />

        <br />

        <label for="stockLevel">Stock Level</label>
        <select id="stockLevel" v-model="form.stock_level_id">
            <option v-for="stockLevel in stockLevels" :key="stockLevel.stock_level_id" :value="stockLevel.stock_level_id">
                {{ stockLevel.description }}
            </option>
        </select>

        <br />

        <input type="email" v-model="form.a" />

        <label>Message is: {{ message }}</label>
        <input v-model="message" placeholder="edit me" />


        <textarea v-model="form.b" />


        <select v-model="form.c">
            <option value="new-york">New York</option>
            <option value="moscow">Moscow</option>
        </select>

        <input type="checkbox" v-model="form.d" />

        <input type="radio" value="weekly" v-model="form.e" />
        <input type="radio" value="monthly" v-model="form.f" />

        <button type="submit">Submit</button>
    </form>
    <table class="table table-hover">
        <thead>
            <tr>
                <th scope="col">Name</th>
                <th scope="col">Action</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="stockItem in stockItems" :key="stockItem.stock_item_id">
                <td>{{ stockItem.name }}</td>
                <td>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-warning btn-sm">Edit</button>
                        <button type="button" class="btn btn-danger btn-sm">Delete</button>
                    </div>
                </td>
            </tr>
        </tbody>
    </table> -->
</template>
