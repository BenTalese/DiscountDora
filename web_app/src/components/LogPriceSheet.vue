<template>
    <!--
        FU-300 — dashboard quick-action "Log a price" surface. Two-step:
          1. Pick a stock item (same shortlist ordering as QuickAddSheet —
             frequently-added first, then low/out — so the muscle memory
             carries over).
          2. Log the price via the shared PriceEntry component (shelf mode,
             prefilled from the item's last observation).
        Mounted once in MainLayout; any screen pops it via
        useLogPrice().openLogPrice().
    -->
    <BaseDialog
        v-model="open"
        :title="selectedItem ? `Log a price · ${selectedItem.name}` : 'Log a price'"
        closable
        position="bottom"
        card-style="width: 520px; max-width: 96vw"
        @cancel="onHide"
    >
        <q-card-section>
            <!-- Step 1 — item picker. -->
            <template v-if="!selectedItem">
                <q-input
                    v-model="query"
                    outlined
                    dense
                    autofocus
                    clearable
                    debounce="150"
                    label="Search stock items"
                />
                <q-list separator class="q-mt-sm log-price-sheet__results">
                    <q-item
                        v-for="item in results"
                        :key="item.stock_item_id"
                        clickable
                        @click="selectItem(item)"
                    >
                        <q-item-section avatar>
                            <q-avatar
                                :color="levelColour(item.stock_level_id) ?? undefined"
                                :class="{ 'dora-bg-sunken dora-text-secondary': !levelColour(item.stock_level_id) }"
                                :text-color="levelColour(item.stock_level_id) ? 'white' : undefined"
                                size="28px"
                            >
                                <q-icon name="inventory_2" size="16px" />
                            </q-avatar>
                        </q-item-section>
                        <q-item-section>{{ item.name }}</q-item-section>
                        <q-item-section side>
                            <q-icon :name="ICONS.chevron_right" />
                        </q-item-section>
                    </q-item>
                    <q-item v-if="results.length === 0">
                        <q-item-section class="dora-text-muted">
                            {{ query ? 'No matches.' : 'No stock items yet.' }}
                        </q-item-section>
                    </q-item>
                </q-list>
            </template>

            <!-- Step 2 — the shared entry form. -->
            <template v-else>
                <div class="row items-center q-mb-sm">
                    <BaseButton
                        variant="icon"
                        :icon="ICONS.arrow_back"
                        aria-label="Back to item picker"
                        @click="clearSelection"
                    />
                    <div class="text-subtitle1 q-ml-sm">{{ selectedItem.name }}</div>
                </div>
                <AppSpinner v-if="prefillLoading" />
                <PriceEntry
                    v-else
                    mode="shelf"
                    :prefill="prefill"
                    :stores="storesList"
                    :busy="submitting"
                    @submit="onSubmit"
                    @cancel="closeLogPrice"
                />
            </template>
        </q-card-section>
    </BaseDialog>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import AppSpinner from 'src/components/AppSpinner.vue';
    import PriceEntry from 'src/components/dora/PriceEntry.vue';
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { colourForSequence } from 'src/helpers/stockLevelLogic';
    import type { PriceEntryPrefill } from 'src/models/stockItemDetail';
    import type { StockItem } from 'src/models/stockItem';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import { useLogPrice } from 'src/composables/useLogPrice';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { useStoresStore } from 'src/stores/storesStore';
    import { useQuasar } from 'quasar';
    import { computed, ref, watch } from 'vue';

    const stockItemApi = new StockItemApiService();
    const $q = useQuasar();

    const { isOpen, presetStockItemId, closeLogPrice } = useLogPrice();

    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const storesStore = useStoresStore();
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);
    const storesList = computed(() => storesStore.stores);

    const open = computed({
        get: () => isOpen.value,
        set: (v) => {
            if (!v) closeLogPrice();
        },
    });

    const query = ref('');
    const selectedItem = ref<StockItem | null>(null);
    const prefill = ref<PriceEntryPrefill | null>(null);
    const prefillLoading = ref(false);
    const submitting = ref(false);

    function levelSequence(id: string | null): number {
        return stockLevels.value.find((l) => l.stock_level_id === id)?.sequence ?? -1;
    }
    function levelColour(id: string | null): string | null {
        const seq = stockLevels.value.find((l) => l.stock_level_id === id)?.sequence;
        return typeof seq === 'number' ? colourForSequence(seq) : null;
    }

    const results = computed(() => {
        const q = query.value?.trim().toLowerCase() ?? '';
        const items = [...stockItems.value];
        if (q) {
            return items.filter((i) => i.name.toLowerCase().includes(q)).slice(0, 30);
        }
        // No query: lead with the most-restock-relevant (low/out first) so
        // "the thing I just bought that was running low" is one tap away.
        return items
            .sort((a, b) => levelSequence(b.stock_level_id) - levelSequence(a.stock_level_id))
            .slice(0, 12);
    });

    async function selectItem(item: StockItem) {
        selectedItem.value = item;
        prefill.value = null;
        prefillLoading.value = true;
        try {
            const detail = await stockItemApi.getDetailAsync(item.stock_item_id);
            prefill.value = detail.price_entry_prefill ?? null;
        } catch {
            // Silent — the form is still usable without prefill.
        } finally {
            prefillLoading.value = false;
        }
    }

    function clearSelection() {
        selectedItem.value = null;
        prefill.value = null;
    }

    async function onSubmit(value: {
        total_price: number;
        total_measure: number;
        unit: string;
        store_id: string | null;
        pack_count: number | null;
    }) {
        if (!selectedItem.value) return;
        submitting.value = true;
        try {
            await stockItemApi.addPriceObservationAsync(selectedItem.value.stock_item_id, value);
            $q.notify({
                type: 'positive',
                message: `Logged a price for ${selectedItem.value.name}.`,
                timeout: 2500,
            });
            closeLogPrice();
        } finally {
            submitting.value = false;
        }
    }

    function onHide() {
        query.value = '';
        clearSelection();
    }

    // On open, load supporting data + apply preset. If a preset stock item
    // was passed, jump straight to step 2.
    watch(isOpen, async (nowOpen) => {
        if (!nowOpen) return;
        await Promise.all([
            stockItemStore.ensureLoadedAsync(),
            stockLevelStore.ensureLoadedAsync(),
            storesStore.ensureLoadedAsync(),
        ]);
        if (presetStockItemId.value) {
            const preset = stockItems.value.find(
                (i) => i.stock_item_id === presetStockItemId.value,
            );
            if (preset) await selectItem(preset);
        }
    });
</script>

<style scoped>
    .log-price-sheet__results {
        max-height: 320px;
        overflow-y: auto;
    }
</style>
