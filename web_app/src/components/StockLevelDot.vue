<template>
    <span class="stock-level-dot row inline items-center no-wrap">
        <q-icon
            name="circle"
            :color="hasAlert ? 'negative' : (levelColour ?? undefined)"
            :class="{ 'dora-text-muted': !hasAlert && !levelColour }"
            :size="hasAlert ? '11px' : '9px'"
        />
        <span
            v-if="levelShort"
            class="text-caption q-ml-xs"
            :class="hasAlert ? 'text-negative' : 'dora-text-muted'"
        >
            {{ levelShort }}
        </span>
        <q-tooltip v-if="tooltip">{{ tooltip }}</q-tooltip>
    </span>
</template>

<script lang="ts" setup>
    /**
     * UX-v2 replacement for the retired StockItemChip: just the stock-level
     * signal — coloured dot, short level name, and an alert state
     * (low/out, expiring soon, or flagged-essential) with the detail in a
     * tooltip. Callers render the item name/link themselves; this component
     * deliberately carries no navigation and no cross-feature menu
     * (PROPOSAL_SHOPPING_LIST_UX_V2.md §6).
     */
    import { storeToRefs } from 'pinia';
    import { colourForSequence } from 'src/helpers/stockLevelLogic';
    import {
        LOW_STOCK_SEQUENCE,
        needsRestockSequence,
        OUT_OF_STOCK_SEQUENCE,
        SUFFICIENT_STOCK_SEQUENCE,
        WELL_STOCKED_SEQUENCE,
    } from 'src/helpers/stockStatus';
    import type { StockItem } from 'src/models/stockItem';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { computed } from 'vue';

    const props = defineProps<{
        stockItem: StockItem | null;
    }>();

    const stockLevelStore = useStockLevelStore();
    const { stockLevels } = storeToRefs(stockLevelStore);

    const level = computed(
        () =>
            stockLevels.value.find(
                (l) => l.stock_level_id === props.stockItem?.stock_level_id,
            ) ?? null,
    );
    const levelName = computed<string | null>(() => level.value?.name ?? null);
    const levelSequence = computed<number | null>(
        () => props.stockItem?.stock_level_sequence ?? level.value?.sequence ?? null,
    );
    const levelColour = computed(() => colourForSequence(levelSequence.value));
    const levelShort = computed(() => {
        switch (levelSequence.value) {
            case WELL_STOCKED_SEQUENCE:
                return 'OK';
            case SUFFICIENT_STOCK_SEQUENCE:
                return 'Mid';
            case LOW_STOCK_SEQUENCE:
                return 'Low';
            case OUT_OF_STOCK_SEQUENCE:
                return 'Out';
            default:
                return '';
        }
    });

    const expiringSoon = computed(() => {
        const raw = props.stockItem?.expiry_date;
        if (!raw) return false;
        const days = (new Date(raw).getTime() - Date.now()) / 86_400_000;
        return days <= 7;
    });
    const lowOrOut = computed(
        () =>
            props.stockItem?.needs_restock ??
            needsRestockSequence(levelSequence.value),
    );
    const hasAlert = computed(
        () =>
            lowOrOut.value
            || expiringSoon.value
            || props.stockItem?.is_flagged === true,
    );
    const tooltip = computed(() => {
        const reasons: string[] = [];
        if (levelName.value) reasons.push(levelName.value);
        if (expiringSoon.value) reasons.push('Expiring soon');
        if (props.stockItem?.is_flagged) reasons.push('Essential');
        return reasons.join(' · ');
    });
</script>
