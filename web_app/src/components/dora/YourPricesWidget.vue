<template>
    <!--
        FU-227 chunk 3 — the "Your prices" inline widget (C5 revised).
        Renders the baseline + above-usual signal + last-seen line +
        `Based on N prices` count + the two actions [Log a price] /
        [Full history].

        LC-2 — source-blind UI: never says "8 observations · 3 offers"; the
        count line reads "Based on N prices" so the user doesn't have to
        ask what counts in vs out. The products-on offers sidecar (chunk 4
        wires it) is a separate section, never folded into baseline math
        or count chrome.

        Chunk 3 reads `your_prices == null` (placeholder) and renders the
        empty state. Chunk 4 lights up the baseline-ready shape. The
        [Full history] button is disabled until chunk 6 wires the
        bottom-sheet.
    -->
    <q-card flat bordered class="dora-your-prices q-pa-md q-mb-md">
        <div class="row items-center q-mb-sm">
            <div class="text-subtitle1 col">Your prices</div>
        </div>

        <!-- Below MIN_SAMPLES / null baseline → empty state (R-014). -->
        <template v-if="!yourPrices || yourPrices.baseline == null">
            <div class="text-body2 dora-text-secondary q-mb-xs">
                {{ emptyStateCopy }}
            </div>
            <div v-if="yourPrices?.current != null" class="text-caption dora-text-muted q-mb-xs">
                Last seen
                <strong>${{ yourPrices.current.toFixed(2) }}</strong>
                <span v-if="yourPrices.last_observed_at">
                    · {{ relativeTime(yourPrices.last_observed_at) }}
                </span>
                <span v-if="yourPrices.last_seen_store_name">
                    · {{ yourPrices.last_seen_store_name }}
                </span>
            </div>
        </template>

        <!-- Baseline-ready (chunk 4 lights this up). -->
        <template v-else>
            <div class="text-body1 q-mb-xs">
                Usually
                <strong>${{ yourPrices.baseline.toFixed(2) }}</strong>
                <span v-if="yourPrices.baseline_unit"> / {{ yourPrices.baseline_unit }}</span>
                <q-chip
                    v-if="yourPrices.above_baseline"
                    color="warning"
                    text-color="white"
                    dense
                    class="q-ml-sm"
                    icon="mdi-trending-up"
                >
                    paying more than usual
                </q-chip>
                <span v-else class="dora-text-muted q-ml-sm text-caption">
                    · about average
                </span>
            </div>
            <div v-if="yourPrices.current != null" class="text-caption dora-text-muted q-mb-xs">
                Last seen
                <strong>${{ yourPrices.current.toFixed(2) }}</strong>
                <span v-if="yourPrices.last_observed_at">
                    · {{ relativeTime(yourPrices.last_observed_at) }}
                </span>
                <span v-if="yourPrices.last_seen_store_name">
                    · {{ yourPrices.last_seen_store_name }}
                </span>
            </div>
            <div class="text-caption dora-text-muted q-mb-sm">
                Based on {{ yourPrices.sample_count }}
                {{ yourPrices.sample_count === 1 ? 'price' : 'prices' }}
            </div>
        </template>

        <!-- LC-2 offers sidecar — separate UI region, never folded into the
             baseline math. Only renders when products are on AND at least
             one linked product has a current offer in the same dimension. -->
        <div
            v-if="yourPrices && yourPrices.offers_sidecar.length > 0"
            class="dora-bg-sunken q-pa-sm rounded-borders q-mb-sm"
        >
            <div class="text-caption dora-text-secondary q-mb-xs">
                Current shelf prices
            </div>
            <div class="text-body2">
                <span
                    v-for="(o, i) in yourPrices.offers_sidecar"
                    :key="`${o.store_name}-${i}`"
                >
                    <span v-if="i > 0"> · </span>
                    <strong>${{ o.price_per_unit.toFixed(2) }}</strong>
                    <span class="dora-text-muted">/ {{ o.unit }}</span>
                    at {{ o.store_name }}
                </span>
            </div>
        </div>

        <div class="row justify-end q-gutter-sm q-mt-sm">
            <BaseButton
                variant="ghost"
                :icon="ICONS.history"
                label="Full history"
                :disable="true"
                aria-label="Full history (coming in chunk 6)"
            />
            <BaseButton
                variant="primary"
                :icon="ICONS.cash_plus"
                label="Log a price"
                @click="dialogOpen = true"
            />
        </div>

        <BaseDialog
            v-model="dialogOpen"
            title="Log a price"
            closable
            @cancel="dialogOpen = false"
        >
            <q-card-section>
                <PriceEntry
                    mode="shelf"
                    :prefill="prefill"
                    :stores="stores"
                    :busy="busy"
                    @submit="onSubmit"
                    @cancel="dialogOpen = false"
                />
            </q-card-section>
        </BaseDialog>
    </q-card>
</template>

<script setup lang="ts">
    import { computed, ref } from 'vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import PriceEntry from 'src/components/dora/PriceEntry.vue';
    import { ICONS } from 'src/style/icons';
    import { relativeTime } from 'src/helpers/relativeTime';
    import type {
        PriceEntryPrefill,
        YourPrices,
    } from 'src/models/stockItemDetail';
    import type { Store } from 'src/models/store';

    const props = withDefaults(
        defineProps<{
            yourPrices?: YourPrices | null | undefined;
            prefill?: PriceEntryPrefill | null | undefined;
            stores?: ReadonlyArray<Store> | undefined;
            busy?: boolean | undefined;
        }>(),
        { yourPrices: null, prefill: null, stores: () => [], busy: false },
    );

    const emit = defineEmits<{
        (e: 'submit', value: {
            total_price: number;
            total_measure: number;
            unit: string;
            store_id: string | null;
        }): void;
    }>();

    const dialogOpen = ref(false);

    // The widget handles the user-facing copy variants; the dialog only
    // emits up to the parent (which knows how to call the API service).
    const emptyStateCopy = computed(() => {
        const count = props.yourPrices?.sample_count ?? 0;
        if (count === 0) return 'No prices logged yet — log a few to see your usual.';
        return 'Not enough price data yet — log a few more.';
    });

    function onSubmit(value: {
        total_price: number;
        total_measure: number;
        unit: string;
        store_id: string | null;
    }) {
        emit('submit', value);
        dialogOpen.value = false;
    }
</script>
