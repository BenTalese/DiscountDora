<template>
    <div class="q-pa-md row q-col-gutter-md">
        <!-- ── Left rail: picker + selected chips ─────────────────── -->
        <div class="col-12 col-md-3">
            <q-card flat bordered>
                <q-card-section>
                    <div class="text-subtitle1">Pick products</div>
                    <div class="text-caption dora-text-muted">
                        Compare up to 5 products' price history side by side.
                    </div>
                </q-card-section>
                <q-card-section class="q-pt-none">
                    <q-input
                        v-model="filter"
                        outlined
                        dense
                        clearable
                        placeholder="Search saved products"
                    >
                        <template #prepend>
                            <q-icon :name="ICONS.search" size="16px" />
                        </template>
                    </q-input>
                </q-card-section>
                <q-card-section class="q-pt-none">
                    <div class="text-caption dora-text-muted-7 q-mb-xs">Selected</div>
                    <div v-if="selectedIds.length === 0" class="text-caption dora-text-muted-5">
                        Pick from the list below.
                    </div>
                    <div v-else>
                        <q-chip
                            v-for="(p, i) in selectedProducts"
                            :key="p.product_id"
                            removable
                            dense
                            :color="seriesColour(i)"
                            text-color="white"
                            @remove="toggleSelect(p.product_id)"
                        >
                            {{ p.name }}
                        </q-chip>
                    </div>
                </q-card-section>
                <q-separator />
                <q-card-section class="q-pt-none" style="max-height: 360px; overflow: auto">
                    <q-list dense>
                        <q-item
                            v-for="p in filteredCandidates"
                            :key="p.product_id"
                            clickable
                            :active="selectedIds.includes(p.product_id)"
                            active-class="active-product-row"
                            @click="toggleSelect(p.product_id)"
                        >
                            <q-item-section avatar>
                                <q-checkbox
                                    :model-value="selectedIds.includes(p.product_id)"
                                    :disable="
                                        !selectedIds.includes(p.product_id)
                                        && selectedIds.length >= 5
                                    "
                                    @update:model-value="toggleSelect(p.product_id)"
                                    @click.stop
                                />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>{{ p.name }}</q-item-label>
                                <q-item-label caption>
                                    {{ p.store_name ?? '' }}
                                </q-item-label>
                            </q-item-section>
                        </q-item>
                        <q-item v-if="filteredCandidates.length === 0">
                            <q-item-section class="dora-text-muted text-caption">
                                No products match.
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-card-section>
            </q-card>
        </div>

        <!-- ── Chart + range + comparison strip ──────────────────── -->
        <div class="col-12 col-md-9">
            <div class="row items-center q-mb-sm">
                <div class="text-h5">Price history</div>
                <q-space />
                <BaseSegmented
                    v-model="range"
                    :options="rangeOptions"
                    dense
                    flat
                    color="grey"
                />
                <BaseButton
                    variant="ghost"
                    :icon="ICONS.notifications"
                    label="Manage alerts"
                    class="q-ml-md"
                    @click="alertsOpen = true"
                />
            </div>

            <q-card ref="chartCardRef" flat bordered>
                <q-card-section class="q-pa-sm">
                    <PriceHistoryChart :series="series" :width="chartWidth" :height="320" />
                </q-card-section>
            </q-card>

            <!-- Per-product comparison strip -->
            <div class="row q-col-gutter-sm q-mt-sm">
                <div
                    v-for="(s, i) in series"
                    :key="s.product_id"
                    class="col-12 col-sm-6 col-md-4"
                >
                    <q-card flat bordered>
                        <q-card-section>
                            <div class="row items-center q-gutter-sm">
                                <span
                                    class="series-swatch"
                                    :style="{ background: seriesColour(i) }"
                                />
                                <div class="col">
                                    <div class="text-subtitle2">{{ s.name }}</div>
                                    <div class="text-caption dora-text-muted-7">
                                        {{ s.store }}
                                    </div>
                                </div>
                            </div>
                        </q-card-section>
                        <q-card-section v-if="s.current" class="q-pt-none">
                            <div class="text-h6">
                                {{ s.current.unit_price != null ? formatMoney(s.current.unit_price) : '—' }}
                                <q-chip
                                    v-if="s.current.deal_pct"
                                    dense
                                    size="sm"
                                    color="positive"
                                    text-color="white"
                                    class="q-ml-xs"
                                >
                                    -{{ s.current.deal_pct }}%
                                </q-chip>
                            </div>
                            <div v-if="s.all_time_low" class="text-caption dora-text-muted-7">
                                All-time low:
                                <strong>{{ formatMoney(s.all_time_low.unit_price) }}</strong>
                                <span v-if="aboveLowPct(s) !== null">
                                    · currently {{ aboveLowPct(s) }}% above
                                    <q-icon :name="ICONS.help_outline" size="14px" class="q-ml-xs">
                                        <q-tooltip>
                                            You're paying more than your own usual
                                            price for this product, based on prices
                                            you've logged. Not a comparison to the
                                            all-time-low across all stores — it's
                                            personal.
                                        </q-tooltip>
                                    </q-icon>
                                </span>
                            </div>
                            <!-- the user's own usual
                                 price for this product + above-usual signal. A
                                 caption (not on the chart axis) so the per-unit
                                 baseline never clashes with the raw offer scale. -->
                            <div
                                v-if="s.your_prices?.baseline != null"
                                class="text-caption dora-text-muted-7 q-mt-xs"
                            >
                                Your usual:
                                <strong>
                                    {{ formatMoney(s.your_prices.baseline)
                                    }}{{ s.your_prices.baseline_unit ? `/${s.your_prices.baseline_unit}` : '' }}
                                </strong>
                                <q-icon :name="ICONS.help_outline" size="14px" class="q-ml-xs">
                                    <q-tooltip>
                                        "Usually" is the median of prices you've
                                        logged for this item. "Above usual" means
                                        today's shelf price is meaningfully higher
                                        than that median.
                                    </q-tooltip>
                                </q-icon>
                                <q-chip
                                    v-if="s.your_prices.above_baseline"
                                    dense
                                    size="sm"
                                    color="warning"
                                    text-color="white"
                                    class="q-ml-xs"
                                    :icon="ICONS.trending_up"
                                >
                                    above usual
                                </q-chip>
                            </div>
                        </q-card-section>
                        <q-card-section v-else class="text-caption dora-text-muted-5">
                            No data yet.
                        </q-card-section>
                        <q-separator />
                        <q-card-section class="q-pt-sm">
                            <div class="row items-end q-gutter-sm">
                                <q-input
                                    v-model.number="alertInputs[s.product_id]"
                                    outlined
                                    dense
                                    type="number"
                                    step="0.01"
                                    :label="`Notify me below (${currencySymbol})`"
                                    class="col"
                                />
                                <BaseButton
                                    variant="primary"
                                    :icon="ICONS.notifications_active"
                                    label="Set alert"
                                    :disable="!alertInputs[s.product_id] || alertInputs[s.product_id]! <= 0"
                                    @click="onSetAlert(s.product_id)"
                                />
                            </div>
                        </q-card-section>
                    </q-card>
                </div>
            </div>
        </div>

        <!-- ── Alerts modal ──────────────────────────────────────── -->
        <BaseDialog v-model="alertsOpen" title="Price alerts" closable card-style="min-width: 420px">
                <q-card-section v-if="alerts.length === 0" class="dora-text-secondary">
                    No active alerts yet.
                </q-card-section>
                <q-list v-else separator>
                    <q-item v-for="a in alerts" :key="a.price_alert_id">
                        <q-item-section>
                            <q-item-label>{{ a.product_name }}</q-item-label>
                            <q-item-label caption>
                                {{ a.store_name }} ·
                                notify below
                                <strong>{{ formatMoney(a.threshold_unit_price) }}</strong>
                            </q-item-label>
                        </q-item-section>
                        <q-item-section side>
                            <BaseButton
                                variant="danger-ghost"
                                dense
                                :icon="ICONS.delete"
                                label="Remove"
                                @click="onDeleteAlert(a.price_alert_id)"
                            />
                        </q-item-section>
                    </q-item>
                </q-list>
        </BaseDialog>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseSegmented from 'src/components/BaseSegmented.vue';
    import { useMoney, formatMoney } from 'src/composables/useMoney';
    // money renders + input labels read the install-currency
    // symbol from the shared money policy.
    const { currencySymbol } = useMoney();
    import { useQuasar } from 'quasar';
    import { computed, onBeforeUnmount, onMounted, ref, watch, reactive } from 'vue';
    import { useRoute } from 'vue-router';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import PriceHistoryChart from 'src/components/PriceHistoryChart.vue';
    import { seriesColour } from 'src/composables/usePriceHistoryPalette';
    import type { Product } from 'src/models/product';
    import PriceHistoryApiService, {
        type PriceAlert, type PriceHistorySeries, type PriceRange,
    } from 'src/services/api/priceHistoryApiService';
    import { useProductStore } from 'src/stores/productStore';
    import { storeToRefs } from 'pinia';

    const $q = useQuasar();
    const route = useRoute();
    const historyApi = new PriceHistoryApiService();
    // products come through the store (R-003), so a save on the
    // product-search surface is visible here without a hard refresh.
    const productStore = useProductStore();
    const { products: candidates } = storeToRefs(productStore);

    const selectedIds = ref<string[]>([]);
    const filter = ref('');
    const range = ref<PriceRange>('90d');
    const rangeOptions = [
        { label: '30d', value: '30d' },
        { label: '90d', value: '90d' },
        { label: '1y', value: '1y' },
        { label: 'All', value: 'all' },
    ];

    const series = ref<PriceHistorySeries[]>([]);
    const alerts = ref<PriceAlert[]>([]);
    const alertsOpen = ref(false);
    const alertInputs = reactive<Record<string, number | null>>({});

    // chart width tracks the surrounding card so the graph extends to
    // the card edge at every viewport size. Was hard-coded to 720, which
    // left a gap on wide screens and overflowed on narrow ones.
    const chartCardRef = ref<{ $el?: HTMLElement } | null>(null);
    const chartWidth = ref(720);
    let chartResizeObserver: ResizeObserver | null = null;

    function measureChart(): void {
        const el = chartCardRef.value?.$el;
        if (!el) return;
        // Account for q-card-section padding (q-pa-sm ≈ 8px each side).
        const next = Math.max(280, Math.floor(el.clientWidth) - 16);
        if (next !== chartWidth.value) chartWidth.value = next;
    }

    const filteredCandidates = computed(() => {
        const needle = filter.value.trim().toLowerCase();
        const all = candidates.value;
        if (!needle) return all.slice(0, 100);
        return all
            .filter((p) =>
                p.name.toLowerCase().includes(needle)
                || (p.store_name ?? '').toLowerCase().includes(needle),
            )
            .slice(0, 100);
    });

    const selectedProducts = computed(() =>
        selectedIds.value
            .map((id) => candidates.value.find((p) => p.product_id === id))
            .filter((p): p is Product => Boolean(p)),
    );

    function toggleSelect(productId: string) {
        const idx = selectedIds.value.indexOf(productId);
        if (idx >= 0) {
            // Reassign (not splice/push) so the `watch([selectedIds, …])`
            // below fires: it's a shallow ref watch, and an in-place mutation
            // leaves `.value` identity unchanged, so the series never
            // refetched on interactive picking (only the deep-link preselect,
            // which reassigns, worked). FU-605.
            selectedIds.value = selectedIds.value.filter((id) => id !== productId);
        } else {
            if (selectedIds.value.length >= 5) {
                $q.notify({
                    type: 'warning', position: 'bottom-right',
                    message: 'Up to 5 products at a time.',
                });
                return;
            }
            selectedIds.value = [...selectedIds.value, productId];
        }
    }

    function aboveLowPct(s: PriceHistorySeries): number | null {
        if (!s.current?.unit_price || !s.all_time_low?.unit_price) return null;
        if (s.all_time_low.unit_price === 0) return null;
        const pct = ((s.current.unit_price - s.all_time_low.unit_price) / s.all_time_low.unit_price) * 100;
        return Math.max(0, Math.round(pct));
    }

    async function refreshSeries() {
        if (selectedIds.value.length === 0) { series.value = []; return; }
        try {
            const result = await historyApi.seriesAsync(selectedIds.value, range.value);
            series.value = result.series;
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: "Couldn't load price history.",
                caption: err instanceof Error ? err.message : String(err),
            });
        }
    }

    async function refreshAlerts() {
        try {
            const result = await historyApi.listAlertsAsync();
            alerts.value = result.items;
        } catch { /* alerts list is non-critical */ }
    }

    async function onSetAlert(productId: string) {
        const value = alertInputs[productId];
        if (!value || value <= 0) return;
        try {
            await historyApi.createAlertAsync(productId, value);
            await refreshAlerts();
            alertInputs[productId] = null;
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: "We'll notify you when it drops.",
            });
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: "Couldn't set the alert.",
                caption: err instanceof Error ? err.message : String(err),
            });
        }
    }

    async function onDeleteAlert(alertId: string) {
        try {
            await historyApi.deleteAlertAsync(alertId);
            await refreshAlerts();
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: "Couldn't remove the alert.",
                caption: err instanceof Error ? err.message : String(err),
            });
        }
    }

    watch([selectedIds, range], () => { void refreshSeries(); });

    onMounted(async () => {
        // hydrate via the store so a save on the product-search
        // surface (which writes through `productStore.createProductAsync`)
        // is visible here without a hard refresh.
        await productStore.getProductsAsync();
        // Deep-link: ?product_id=<id> pre-selects.
        const preselect = (route.query.product_id as string | undefined) ?? null;
        if (preselect && candidates.value.find((p) => p.product_id === preselect)) {
            selectedIds.value = [preselect];
        }
        void refreshSeries();
        void refreshAlerts();
        // Wait one tick so the q-card has mounted before measuring.
        await Promise.resolve();
        measureChart();
        const el = chartCardRef.value?.$el;
        if (el && typeof ResizeObserver !== 'undefined') {
            chartResizeObserver = new ResizeObserver(() => measureChart());
            chartResizeObserver.observe(el);
        }
    });

    onBeforeUnmount(() => {
        chartResizeObserver?.disconnect();
        chartResizeObserver = null;
    });
</script>

<style scoped>
    .series-swatch {
        width: 12px; height: 12px; border-radius: 3px;
        display: inline-block;
    }
    .active-product-row {
        background: var(--brand-primary-soft);
    }
</style>
