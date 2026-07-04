<template>
    <BaseDialog v-model="open" title="Add ingredients to a list" closable card-style="min-width: 420px; max-width: 560px">
        <q-card-section>
            <div class="text-caption dora-text-muted">
                {{ recipe?.name ?? 'Recipe' }}
            </div>
        </q-card-section>

        <q-card-section class="q-pt-none">
            <q-select
                v-model="targetListId"
                :options="listOptions"
                emit-value
                map-options
                outlined
                dense
                label="Add to"
            />
        </q-card-section>

        <q-separator />

        <q-card-section class="q-pt-sm q-pb-none">
            <div class="row items-center justify-between q-mb-sm">
                <div class="text-caption dora-text-muted">
                    {{ checkedCount }} of {{ pickableCount }} selected
                </div>
                <div class="row q-gutter-xs">
                    <BaseButton
                        variant="ghost"
                        dense
                        size="sm"
                        label="Select all"
                        @click="selectAll"
                    />
                    <BaseButton
                        variant="ghost"
                        dense
                        size="sm"
                        label="Select missing"
                        @click="selectMissing"
                    />
                </div>
            </div>
        </q-card-section>

        <q-card-section class="q-pt-none ingredient-picker__list">
            <q-list dense>
                <template v-for="row in requiredRows" :key="row.stock_item_id">
                    <q-item
                        clickable
                        v-ripple
                        @click="toggle(row.stock_item_id)"
                    >
                        <q-item-section avatar>
                            <q-checkbox
                                :model-value="selected[row.stock_item_id] ?? false"
                                dense
                                @update:model-value="toggle(row.stock_item_id)"
                                @click.stop
                            />
                        </q-item-section>
                        <q-item-section avatar>
                            <StockLevelDot :stock-item="row.stockItem" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>{{ row.stock_item_name }}</q-item-label>
                            <q-item-label v-if="row.statusWord" caption>
                                {{ row.statusWord }}
                            </q-item-label>
                        </q-item-section>
                    </q-item>
                </template>

                <!-- Cookbook revision §1.9 — optional ingredients section.
                     Unchecked by default regardless of stock level. -->
                <q-item v-if="optionalRows.length > 0" class="ingredient-picker__sep">
                    <q-item-section class="text-caption dora-text-muted">
                        ─── Optional ───
                    </q-item-section>
                </q-item>
                <template v-for="row in optionalRows" :key="row.stock_item_id">
                    <q-item
                        clickable
                        v-ripple
                        @click="toggle(row.stock_item_id)"
                    >
                        <q-item-section avatar>
                            <q-checkbox
                                :model-value="selected[row.stock_item_id] ?? false"
                                dense
                                @update:model-value="toggle(row.stock_item_id)"
                                @click.stop
                            />
                        </q-item-section>
                        <q-item-section avatar>
                            <StockLevelDot :stock-item="row.stockItem" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>{{ row.stock_item_name }}</q-item-label>
                            <q-item-label v-if="row.statusWord" caption>
                                {{ row.statusWord }}
                            </q-item-label>
                        </q-item-section>
                    </q-item>
                </template>

                <q-item v-if="rows.length === 0">
                    <q-item-section class="dora-text-muted text-center">
                        No ingredients to add.
                    </q-item-section>
                </q-item>
            </q-list>
        </q-card-section>

        <template #actions>
            <BaseButton variant="ghost" label="Cancel" v-close-popup />
            <BaseButton
                label="Add"
                :loading="busy"
                :disable="checkedCount === 0 || !targetListId"
                @click="onConfirm"
            />
        </template>
    </BaseDialog>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import StockLevelDot from 'src/components/StockLevelDot.vue';
    import type { Recipe } from 'src/models/recipe';
    import type { StockItem } from 'src/models/stockItem';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { storeToRefs } from 'pinia';
    import { computed, ref, watch } from 'vue';

    const props = withDefaults(
        defineProps<{
            modelValue: boolean;
            recipe: Recipe | null;
            // When provided, these ids start checked. Otherwise the default
            // policy (missing/low checked, sufficient/well unchecked) applies.
            initialCheckedIds?: string[] | undefined;
        }>(),
        { initialCheckedIds: undefined },
    );

    const emit = defineEmits<{
        (e: 'update:modelValue', v: boolean): void;
        (e: 'confirm', payload: { stockItemIds: string[]; targetListId: string }): void;
    }>();

    const busy = ref(false);
    const open = computed({
        get: () => props.modelValue,
        set: (v) => emit('update:modelValue', v),
    });

    const stockItemStore = useStockItemStore();
    const { stockItems } = storeToRefs(stockItemStore);
    const shoppingListStore = useShoppingListStore();

    const listOptions = computed(() =>
        shoppingListStore.summaries
            .filter((s) => s.status !== 'done')
            .map((s) => ({ label: s.name, value: s.shopping_list_id })),
    );
    const targetListId = ref<string | null>(null);

    type Row = {
        stock_item_id: string;
        stock_item_name: string;
        stockItem: StockItem | null;
        is_missing: boolean;
        is_low_stock: boolean;
        // Cookbook revision §1.9 — when the same stock item appears on
        // both a required and an optional ingredient row, the *required*
        // commitment wins (we'd rather over-stock than under-stock).
        is_optional: boolean;
        statusWord: string;
    };

    const rows = computed<Row[]>(() => {
        if (!props.recipe) return [];
        const byId = new Map<string, Row>();
        for (const ing of props.recipe.ingredients) {
            if (!ing.stock_item_id) continue;
            const existing = byId.get(ing.stock_item_id);
            if (existing) {
                // Any required occurrence demotes the row from optional.
                if (!ing.is_optional) existing.is_optional = false;
                continue;
            }
            const si = stockItems.value.find(
                (s) => s.stock_item_id === ing.stock_item_id,
            ) ?? null;
            byId.set(ing.stock_item_id, {
                stock_item_id: ing.stock_item_id,
                stock_item_name: ing.stock_item_name ?? ing.raw_text ?? '',
                stockItem: si,
                is_missing: ing.is_missing,
                is_low_stock: ing.is_low_stock,
                is_optional: ing.is_optional ?? false,
                statusWord: ing.is_missing
                    ? 'Out / untracked'
                    : ing.is_low_stock
                        ? 'Low'
                        : '',
            });
        }
        return Array.from(byId.values()).sort((a, b) => {
            const rank = (r: Row) => (r.is_missing ? 0 : r.is_low_stock ? 1 : 2);
            const diff = rank(a) - rank(b);
            if (diff !== 0) return diff;
            return a.stock_item_name.localeCompare(b.stock_item_name);
        });
    });

    const requiredRows = computed(() => rows.value.filter((r) => !r.is_optional));
    const optionalRows = computed(() => rows.value.filter((r) => r.is_optional));

    const selected = ref<Record<string, boolean>>({});

    function applyDefaults() {
        const next: Record<string, boolean> = {};
        const initial = props.initialCheckedIds;
        const initialSet = initial ? new Set(initial) : null;
        for (const row of rows.value) {
            if (initialSet) {
                next[row.stock_item_id] = initialSet.has(row.stock_item_id);
                continue;
            }
            // Cookbook revision §1.9 — optional rows start unchecked
            // regardless of stock level (opt-in only).
            if (row.is_optional) {
                next[row.stock_item_id] = false;
                continue;
            }
            next[row.stock_item_id] = row.is_missing || row.is_low_stock;
        }
        selected.value = next;
    }

    watch(
        () => props.modelValue,
        (isOpen) => {
            if (!isOpen) return;
            targetListId.value =
                shoppingListStore.quickAddTargetListId
                ?? listOptions.value[0]?.value
                ?? null;
            applyDefaults();
        },
        { immediate: true },
    );

    const pickableCount = computed(() => rows.value.length);
    const checkedCount = computed(
        () => rows.value.filter((r) => selected.value[r.stock_item_id]).length,
    );

    function toggle(id: string) {
        selected.value = { ...selected.value, [id]: !selected.value[id] };
    }

    function selectAll() {
        // §1.9 — "all" still excludes optional rows by default; users
        // opt in to optional rows individually via their checkbox.
        const next: Record<string, boolean> = {};
        for (const row of rows.value) next[row.stock_item_id] = !row.is_optional;
        selected.value = next;
    }

    function selectMissing() {
        const next: Record<string, boolean> = {};
        for (const row of rows.value) {
            if (row.is_optional) {
                next[row.stock_item_id] = false;
                continue;
            }
            next[row.stock_item_id] = row.is_missing || row.is_low_stock;
        }
        selected.value = next;
    }

    function onConfirm() {
        if (!targetListId.value) return;
        const ids = rows.value
            .filter((r) => selected.value[r.stock_item_id])
            .map((r) => r.stock_item_id);
        if (ids.length === 0) return;
        emit('confirm', { stockItemIds: ids, targetListId: targetListId.value });
    }

    defineExpose({ setBusy: (v: boolean) => { busy.value = v; } });
</script>

<style scoped>
    .ingredient-picker__list {
        max-height: 360px;
        overflow-y: auto;
    }
</style>
