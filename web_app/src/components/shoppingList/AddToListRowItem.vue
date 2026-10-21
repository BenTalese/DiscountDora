<template>
    <q-item clickable v-ripple @click="emit('toggle')">
        <q-item-section avatar>
            <q-checkbox
                :model-value="checked"
                dense
                :aria-label="`Add ${row.name} to the list`"
                @update:model-value="emit('toggle')"
                @click.stop
            />
        </q-item-section>
        <!-- Level dot sits between the checkbox and the name. Tooltip'd
             because a bare dot isn't a decodable signal on its own (D-013). -->
        <q-item-section side class="add-to-list-row__dot">
            <StockLevelDot :sequence="levelSequence" size="12px">
                <BaseTooltip>{{ levelLabel }}</BaseTooltip>
            </StockLevelDot>
        </q-item-section>
        <q-item-section>
            <q-item-label>{{ row.name }}</q-item-label>
            <!-- Owner feedback 2026-08-27 — "I wonder if there'd be value in
                 showing where items have come from (what requires them)". On a
                 meal plan one item is often pulled in by several meals; on a
                 single recipe `sources` is empty, because the answer is the
                 page you're standing on. -->
            <q-item-label v-if="caption" caption>{{ caption }}</q-item-label>
        </q-item-section>
        <q-item-section v-if="onListLabel" side>
            <q-chip dense square size="sm" class="add-to-list-row__onlist">
                <q-icon :name="ICONS.shopping_cart" size="14px" class="q-mr-xs" />
                {{ onListLabel }}
            </q-chip>
        </q-item-section>
    </q-item>
</template>

<script lang="ts" setup>
    import BaseTooltip from 'src/components/BaseTooltip.vue';
    import StockLevelDot from 'src/components/stock/StockLevelDot.vue';
    import { ICONS } from 'src/style/icons';
    import { useStockStatus } from 'src/composables/useStockStatus';
    import type { AddToListRow } from 'src/components/shoppingList/addToListTypes';
    import { computed } from 'vue';

    const props = defineProps<{
        row: AddToListRow;
        checked: boolean;
        /** "On Weekly shop", or null when it isn't on one. */
        onListLabel: string | null;
    }>();

    const emit = defineEmits<{ (e: 'toggle'): void }>();

    // R-003 — level resolution is the app-wide composable's job, so this row
    // codes stock level exactly the way every other stock surface does.
    const { levelSequenceForItem, stockStatusLabel } = useStockStatus();
    const levelSequence = computed(() => levelSequenceForItem(props.row.stockItemId));
    const levelLabel = computed(() => stockStatusLabel(props.row.stockItemId));

    const caption = computed(() => {
        const parts: string[] = [];
        if (props.row.quantityLabel) parts.push(`needs ${props.row.quantityLabel}`);
        if (props.row.sources.length > 0) parts.push(`for ${props.row.sources.join(', ')}`);
        return parts.join(' · ');
    });
</script>

<style scoped>
    /* Just wide enough for the dot — `side` sections otherwise reserve a
       56px avatar track and push the name away from the checkbox. */
    .add-to-list-row__dot {
        min-width: 0;
        padding-right: 8px;
    }
    /* Says "already handled", so it must not compete with the name it
       qualifies (D-013 — a state chip, not an alert). */
    .add-to-list-row__onlist {
        background: var(--surface-sunken);
        color: var(--text-muted);
    }
</style>
