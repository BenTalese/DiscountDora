<template>
    <BaseDialog v-model="open" title="Quick add to list" closable position="bottom" card-style="width: 520px; max-width: 96vw" @cancel="onHide">
            <q-card-section>
                <!-- Target list -->
                <q-select
                    v-model="targetListId"
                    outlined
                    dense
                    emit-value
                    map-options
                    label="Add to"
                    :options="listOptions"
                    class="q-mb-md"
                />

                <!-- Step 1: pick a stock item -->
                <template v-if="!selectedItem">
                    <q-input
                        v-model="query"
                        outlined
                        dense
                        autofocus
                        clearable
                        debounce="150"
                        label="Search stock items"
                        prepend-:icon="ICONS.search"
                    />
                    <q-list separator class="q-mt-sm quick-add-sheet__results">
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
                            <q-item-section>
                                <div class="row items-center q-gutter-xs">
                                    <q-icon
                                        v-if="!query && isFrequent(item.stock_item_id)"
                                        name="star"
                                        size="14px"
                                        color="warning"
                                    >
                                        <q-tooltip>Frequently added</q-tooltip>
                                    </q-icon>
                                    <span>{{ item.name }}</span>
                                </div>
                            </q-item-section>
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
                    <div v-if="!query" class="text-caption dora-text-muted q-mt-xs">
                        {{
                            frequentlyAdded.length > 0
                                ? 'Showing what you usually buy, then low/out.'
                                : 'Showing low/out items first.'
                        }}
                    </div>
                </template>

                <!-- Step 2: pick quantity + store offer -->
                <template v-else>
                    <div class="row items-center q-mb-sm">
                        <BaseButton variant="icon" :icon="ICONS.arrow_back" @click="clearSelection" />
                        <div class="text-subtitle1 q-ml-sm">{{ selectedItem.name }}</div>
                    </div>

                    <q-input
                        v-model.number="quantity"
                        type="number"
                        outlined
                        dense
                        min="1"
                        label="Quantity"
                        class="q-mb-md"
                        style="max-width: 140px"
                    />

                    <div class="text-subtitle2 q-mb-xs">Store offer</div>
                    <AppSpinner v-if="offersLoading" />
                    <template v-else>
                        <q-option-group
                            v-model="selectedProductId"
                            :options="offerOptions"
                            type="radio"
                            dense
                        />
                        <div v-if="offers.length === 0" class="text-caption dora-text-muted">
                            No linked products — added without a specific offer.
                        </div>
                    </template>
                </template>
            </q-card-section>

            <template v-if="selectedItem" #actions>
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <BaseButton
                    label="Add"
                    :loading="adding"
                    :disable="!targetListId"
                    @click="confirmAdd"
                />
            </template>
    </BaseDialog>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import AppSpinner from 'src/components/AppSpinner.vue';
    import { storeToRefs } from 'pinia';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { useQuickAdd } from 'src/composables/useQuickAdd';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import { colourForSequence } from 'src/helpers/stockLevelLogic';
    import type { LinkedProduct } from 'src/models/stockItemDetail';
    import type { StockItem } from 'src/models/stockItem';
    import ShoppingListApiService, {
        type FrequentlyAddedItem,
    } from 'src/services/api/shoppingListApiService';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { computed, ref, watch } from 'vue';

    const stockItemApi = new StockItemApiService();
    const shoppingListApi = new ShoppingListApiService();

    const { isOpen, presetStockItemId, presetListId, closeQuickAdd } = useQuickAdd();
    const { addItems } = useShoppingListActions();

    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const shoppingListStore = useShoppingListStore();
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);
    const { summaries, quickAddTargetListId } = storeToRefs(shoppingListStore);

    // Bridge the module-level open flag to a local v-model so q-dialog's hide
    // event can close it cleanly.
    const open = computed({
        get: () => isOpen.value,
        set: (v) => {
            if (!v) closeQuickAdd();
        },
    });

    const query = ref('');
    const selectedItem = ref<StockItem | null>(null);
    const quantity = ref(1);
    const offers = ref<LinkedProduct[]>([]);
    const offersLoading = ref(false);
    const selectedProductId = ref<string | null>(null);
    const targetListId = ref<string | null>(null);
    const adding = ref(false);

    const listOptions = computed(() =>
        summaries.value
            .filter((s) => s.status !== 'done')
            .map((s) => ({
                label: s.display_name,
                value: s.shopping_list_id,
            })),
    );

    function levelSequence(id: string | null) {
        return stockLevels.value.find((l) => l.stock_level_id === id)?.sequence ?? -1;
    }
    function levelColour(id: string | null): string | null {
        // FU-050 — key off sequence (R-003); names can drift.
        const seq = stockLevels.value.find((l) => l.stock_level_id === id)?.sequence;
        return typeof seq === 'number' ? colourForSequence(seq) : null;
    }

    // Cached on each sheet-open: stock items the user has historically added
    // to a list most often. We surface these first when there's no query so
    // "the thing I always buy" is one tap away. Falls back gracefully if
    // the endpoint hasn't returned yet or fails.
    const frequentlyAdded = ref<FrequentlyAddedItem[]>([]);

    const results = computed(() => {
        const q = query.value?.trim().toLowerCase() ?? '';
        const items = [...stockItems.value];
        if (q) {
            return items.filter((i) => i.name.toLowerCase().includes(q)).slice(0, 30);
        }
        // No query: lead with frequently-added, then top up with low/out
        // items so first-time users (zero history) still see suggestions.
        const seen = new Set<string>();
        const ordered: StockItem[] = [];
        if (frequentlyAdded.value.length > 0) {
            const lookup = new Map(items.map((i) => [i.stock_item_id, i]));
            for (const f of frequentlyAdded.value) {
                const item = lookup.get(f.stock_item_id);
                if (item && !seen.has(item.stock_item_id)) {
                    ordered.push(item);
                    seen.add(item.stock_item_id);
                }
            }
        }
        const remaining = items
            .filter((i) => !seen.has(i.stock_item_id))
            .sort((a, b) => levelSequence(b.stock_level_id) - levelSequence(a.stock_level_id));
        return [...ordered, ...remaining].slice(0, 12);
    });

    function isFrequent(stockItemId: string): boolean {
        return frequentlyAdded.value.some((f) => f.stock_item_id === stockItemId);
    }

    const offerOptions = computed(() => [
        { label: 'No specific offer', value: null },
        ...offers.value.map((o) => ({
            label: offerLabel(o),
            value: o.product_id,
        })),
    ]);

    function offerLabel(o: LinkedProduct): string {
        const price = o.price_now != null ? `$${o.price_now.toFixed(2)}` : 'n/a';
        const store = o.store_name ? ` · ${o.store_name}` : '';
        const size = o.size ? ` · ${o.size}` : '';
        return `${o.name} — ${price}${store}${size}`;
    }

    async function selectItem(item: StockItem) {
        selectedItem.value = item;
        await loadOffers(item.stock_item_id);
    }

    async function loadOffers(stockItemId: string) {
        offersLoading.value = true;
        offers.value = [];
        selectedProductId.value = null;
        try {
            const detail = await stockItemApi.getDetailAsync(stockItemId);
            // API returns products cheapest-first; default to the cheapest.
            offers.value = detail.products ?? [];
            selectedProductId.value = offers.value[0]?.product_id ?? null;
        } catch {
            offers.value = [];
        } finally {
            offersLoading.value = false;
        }
    }

    function clearSelection() {
        selectedItem.value = null;
        offers.value = [];
        selectedProductId.value = null;
        quantity.value = 1;
    }

    async function confirmAdd() {
        if (!selectedItem.value || !targetListId.value) return;
        adding.value = true;
        try {
            await addItems(targetListId.value, [
                {
                    stock_item_id: selectedItem.value.stock_item_id,
                    quantity: quantity.value > 0 ? quantity.value : 1,
                    selected_product_id: selectedProductId.value,
                },
            ]);
            closeQuickAdd();
        } finally {
            adding.value = false;
        }
    }

    function onHide() {
        query.value = '';
        clearSelection();
    }

    // When the sheet opens, make sure the supporting data is loaded and apply
    // any presets the caller passed to openQuickAdd().
    watch(isOpen, async (nowOpen) => {
        if (!nowOpen) return;
        const loads: Promise<unknown>[] = [];
        loads.push(stockItemStore.ensureLoadedAsync());
        loads.push(stockLevelStore.ensureLoadedAsync());
        loads.push(shoppingListStore.refreshAsync());
        // Frequently-added is best-effort; failure shouldn't block the
        // sheet, so swallow errors and fall back to low/out ordering.
        loads.push(
            shoppingListApi
                .getFrequentlyAddedAsync(12)
                .then((items) => {
                    frequentlyAdded.value = items;
                })
                .catch(() => {
                    frequentlyAdded.value = [];
                }),
        );
        await Promise.all(loads);

        targetListId.value =
            presetListId.value ?? quickAddTargetListId.value ?? listOptions.value[0]?.value ?? null;

        if (presetStockItemId.value) {
            const preset = stockItems.value.find(
                (i) => i.stock_item_id === presetStockItemId.value,
            );
            if (preset) await selectItem(preset);
        }
    });
</script>

<style scoped>
    .quick-add-sheet__results {
        max-height: 320px;
        overflow-y: auto;
    }
</style>
