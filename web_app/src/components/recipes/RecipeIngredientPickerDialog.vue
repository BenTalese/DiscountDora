<template>
    <!-- Owner feedback 2026-08-19, four changes:
           - the recipe-name caption and the "N of M selected" counter are gone
             (you opened this from that recipe; the checkboxes are the count);
           - the per-row "Out / untracked" / "Low" caption is replaced by the
             shared stock-level dot, so this list codes level the same way every
             other stock surface does (R-001/R-003);
           - Select all / Select missing use the new `subtle` BaseButton variant
             so they read as buttons, and
           - they moved into the actions row, left-aligned opposite Cancel/Add.
         The card was also `min-width: 420px`, which overflowed a small phone. -->
    <BaseDialog
        v-model="open"
        title="Add ingredients to a list"
        closable
        card-style="min-width: 0; width: min(560px, 92vw)"
    >
        <q-card-section>
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

        <q-card-section class="q-pt-sm ingredient-picker__list">
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
                        <!-- Level dot sits between the checkbox and the name.
                             Tooltip'd because a bare dot isn't a decodable
                             signal on its own (D-013). -->
                        <q-item-section side class="ingredient-picker__dot">
                            <StockLevelDot :sequence="row.levelSequence" size="12px">
                                <q-tooltip>{{ row.levelLabel }}</q-tooltip>
                            </StockLevelDot>
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>{{ row.stock_item_name }}</q-item-label>
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
                        <!-- Level dot sits between the checkbox and the name.
                             Tooltip'd because a bare dot isn't a decodable
                             signal on its own (D-013). -->
                        <q-item-section side class="ingredient-picker__dot">
                            <StockLevelDot :sequence="row.levelSequence" size="12px">
                                <q-tooltip>{{ row.levelLabel }}</q-tooltip>
                            </StockLevelDot>
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>{{ row.stock_item_name }}</q-item-label>
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
            <BaseButton variant="subtle" label="Select all" @click="selectAll" />
            <BaseButton variant="subtle" label="Select missing" @click="selectMissing" />
            <q-space />
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
    import StockLevelDot from 'src/components/stock/StockLevelDot.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
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
        /** Canonical stock-level sequence for the dot. `null` = untracked or
         *  not found, which `colourForSequence` renders as the neutral fill. */
        levelSequence: number | null;
        /** The dot's tooltip text (D-013). Prefers the item's real level name
         *  over a word we'd invent here, so the picker says the same thing the
         *  stock pages do. */
        levelLabel: string;
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
                levelSequence: si?.stock_level_sequence ?? null,
                levelLabel: si?.stock_level_name
                    ?? (ing.is_missing ? 'Out of stock or untracked' : 'In stock'),
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

    // `pickableCount` removed with the "N of M selected" line it fed.
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
    /* Just wide enough for the dot — `side` sections otherwise reserve a
       56px avatar track and push the name away from the checkbox. */
    .ingredient-picker__dot {
        min-width: 0;
        padding-right: 8px;
    }
</style>
