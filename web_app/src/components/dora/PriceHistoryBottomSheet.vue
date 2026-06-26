<template>
    <!--
        FU-227 chunk 6 (C5b) — "Full history" bottom-sheet. Opens from the
        YourPrices widget; embeds the shared PriceHistoryChart scoped to one
        stock item's unioned series (observations ∪ linked-product offers,
        both normalised per-unit server-side). Offers render as subordinate
        "context" (offersAsContext) under the user's own observation line, with
        the baseline reference line drawn in (D2 + F-3).

        R-001 — reuses BaseDialog (position="bottom") as the bottom-sheet
        primitive, the same one QuickAddSheet uses; no hand-rolled q-dialog.
    -->
    <BaseDialog
        :model-value="modelValue"
        :title="`Price history — ${itemName}`"
        closable
        position="bottom"
        card-style="width: 760px; max-width: 96vw"
        @update:model-value="(v) => emit('update:modelValue', v)"
        @cancel="emit('update:modelValue', false)"
    >
        <q-card-section ref="bodyRef">
            <div v-if="loading" class="row justify-center q-pa-lg">
                <AppSpinner size="28px" />
            </div>

            <template v-else-if="hasPoints">
                <!-- Legend (D2 names the two series + the baseline). -->
                <div class="row items-center q-gutter-md q-mb-sm text-caption dora-text-secondary">
                    <span class="row items-center no-wrap">
                        <span class="legend-dot" :style="{ background: yourColour }" />
                        Your prices
                    </span>
                    <span v-if="hasOffers" class="row items-center no-wrap">
                        <span class="legend-dash" :style="{ color: yourColour }" />
                        Store offers
                    </span>
                    <span v-if="history?.baseline != null" class="row items-center no-wrap">
                        <span class="legend-dash legend-dash--baseline" />
                        Usually ${{ history.baseline.toFixed(2)
                        }}{{ history.baseline_unit ? `/${history.baseline_unit}` : '' }}
                    </span>
                    <q-space />
                    <q-chip
                        v-if="history?.above_baseline"
                        dense
                        color="warning"
                        text-color="white"
                        :icon="ICONS.trending_up"
                    >
                        above usual
                    </q-chip>
                </div>

                <PriceHistoryChart
                    :series="series"
                    :width="chartWidth"
                    :height="300"
                    offers-as-context
                />
            </template>

            <div v-else class="dora-text-muted text-body2 q-pa-md text-center">
                No price history yet — log a price to start building it.
            </div>
        </q-card-section>
    </BaseDialog>
</template>

<script lang="ts" setup>
    import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue';
    import AppSpinner from 'src/components/AppSpinner.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import PriceHistoryChart from 'src/components/PriceHistoryChart.vue';
    import { seriesColour } from 'src/composables/usePriceHistoryPalette';
    import { ICONS } from 'src/style/icons';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import type {
        PriceHistorySeries, StockItemPriceHistory,
    } from 'src/services/api/priceHistoryApiService';

    const props = withDefaults(
        defineProps<{
            modelValue: boolean;
            stockItemId: string;
            itemName?: string;
        }>(),
        { itemName: '' },
    );

    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
    }>();

    const stockItemApi = new StockItemApiService();
    const history = ref<StockItemPriceHistory | null>(null);
    const loading = ref(false);

    // "Your data" series colour — index 0 of the shared palette, same hue the
    // chart paints the observation line/dots with.
    const yourColour = computed(() => seriesColour(0));

    const hasPoints = computed(() => (history.value?.points.length ?? 0) > 0);
    const hasOffers = computed(
        () => history.value?.points.some((p) => p.source === 'offer') ?? false,
    );

    // Split the server's tagged points into the chart's offer + observation
    // series shapes. Everything is already per-unit and date-sorted server-side.
    const series = computed<PriceHistorySeries[]>(() => {
        const h = history.value;
        if (!h) return [];
        return [{
            product_id: h.stock_item_id,
            name: h.name,
            store: '',
            points: h.points
                .filter((p) => p.source === 'offer')
                .map((p) => ({
                    date: p.observed_at, unit_price: p.unit_price,
                    list_price: null, on_deal: false,
                })),
            observation_points: h.points
                .filter((p) => p.source === 'observation')
                .map((p) => ({
                    date: p.observed_at, unit_price: p.unit_price, store_name: p.store_name,
                })),
            your_prices: {
                baseline: h.baseline,
                baseline_unit: h.baseline_unit,
                current: h.current,
                above_baseline: h.above_baseline,
                sample_count: h.sample_count,
            },
            current: null,
            all_time_low: null,
        }];
    });

    // ── Responsive chart width (mirrors PriceHistoryPage) ───────────────────
    const bodyRef = ref<{ $el?: HTMLElement } | null>(null);
    const chartWidth = ref(720);
    let resizeObserver: ResizeObserver | null = null;

    function measure(): void {
        const el = bodyRef.value?.$el;
        if (!el) return;
        const next = Math.max(280, Math.floor(el.clientWidth) - 32);
        if (next !== chartWidth.value) chartWidth.value = next;
    }

    async function load(): Promise<void> {
        loading.value = true;
        try {
            history.value = await stockItemApi.getPriceHistoryAsync(props.stockItemId);
        } catch {
            history.value = null;
        } finally {
            loading.value = false;
        }
        await nextTick();
        measure();
        const el = bodyRef.value?.$el;
        if (el && typeof ResizeObserver !== 'undefined' && !resizeObserver) {
            resizeObserver = new ResizeObserver(() => measure());
            resizeObserver.observe(el);
        }
    }

    // Lazy-fetch each time the sheet opens (prices may have changed since the
    // last open; the detail page reloads its own data after a log too).
    watch(
        () => props.modelValue,
        (open) => {
            if (open && props.stockItemId) void load();
            if (!open) {
                resizeObserver?.disconnect();
                resizeObserver = null;
            }
        },
    );

    onBeforeUnmount(() => {
        resizeObserver?.disconnect();
        resizeObserver = null;
    });
</script>

<style scoped>
    .legend-dot {
        width: 10px; height: 10px; border-radius: 50%;
        display: inline-block; margin-right: 6px;
    }
    .legend-dash {
        width: 16px; height: 0; display: inline-block; margin-right: 6px;
        border-top: 2px dashed currentColor;
        opacity: 0.6;
    }
    .legend-dash--baseline {
        border-top-color: var(--text-muted);
        opacity: 0.8;
    }
</style>
