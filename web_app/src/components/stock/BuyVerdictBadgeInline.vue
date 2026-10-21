<template>
    <BuyVerdictBadge
        v-if="shouldShow"
        :verdict="verdict"
        @action="(kind) => emit('action', kind)"
    />
</template>

<script setup lang="ts">
    import BuyVerdictBadge from 'src/components/stock/BuyVerdictBadge.vue';
    import { useBuyVerdict } from 'src/composables/useBuyVerdict';
    import { useBuyVerdictEnabled } from 'src/composables/useBuyVerdictEnabled';
    import type { BuyVerdict } from 'src/services/api/buyVerdictApiService';
    import { computed } from 'vue';

    /** P8-05 — thin wrapper that fetches its own verdict for a given
     *  stock item and delegates rendering to BuyVerdictBadge. Every row-
     *  level consumer (Stock Overview row, Shopping List line, …) uses
     *  this so the "silent-on-low-confidence" rule + feature-flag check
     *  live in one place (R-003 for client-side logic). Callers that
     *  already have a fetched `BuyVerdict` in hand can use the base
     *  BuyVerdictBadge directly. */
    const props = defineProps<{
        stockItemId: string | null;
    }>();
    const emit = defineEmits<{
        (e: 'action', kind: BuyVerdict['one_tap_action']['kind']): void;
    }>();

    const idRef = computed<string | null>(() => props.stockItemId);
    const { verdict } = useBuyVerdict(idRef);
    const { buyVerdictEnabled } = useBuyVerdictEnabled();

    const shouldShow = computed(() =>
        buyVerdictEnabled.value
        && verdict.value !== null
        && verdict.value.confidence !== 'low',
    );
</script>
