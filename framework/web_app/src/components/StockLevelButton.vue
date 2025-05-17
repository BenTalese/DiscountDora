<template>
    <q-btn-dropdown
        :color="getStockLevelColour(stockLevels.find((sl) => sl.stock_level_id === idOfSelectedStockLevel)!.name)"
        :items="stockLevelStore.stockLevels"
        @click.stop
        class="q-mx-sm"
        dense
        dropdown-icon="none"
        no-caps
        push
        rounded
        style="width: 30px"
    >
        <q-item
            :key="level.sequence"
            @click="onClick(level.stock_level_id)"
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
</template>

<script lang="ts" setup>
    //#region Imports
    import { storeToRefs } from 'pinia';
    import { getStockLevelColour } from 'src/helpers/stockLevelLogic';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    //#endregion Imports

    //#region Store Initialization
    const stockLevelStore = useStockLevelStore();
    const { stockLevels } = storeToRefs(stockLevelStore);
    //#endregion Store Initialization

    //#region Props and Events
    defineProps<{
        idOfSelectedStockLevel: string;
        onClick: (stockLevelID: string) => void;
    }>();
    //#endregion Props and Events
</script>
