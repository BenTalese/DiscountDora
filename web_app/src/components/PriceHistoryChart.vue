<template>
    <div ref="hostRef" class="chart-host" @mousemove="onMove" @mouseleave="onLeave">
        <svg
            :width="width"
            :height="height"
            :viewBox="`0 0 ${width} ${height}`"
            class="chart-svg"
            preserveAspectRatio="none"
        >
            <!-- Horizontal gridlines + y-axis labels -->
            <g class="gridlines">
                <line
                    v-for="(tick, i) in yTicks"
                    :key="`gl-${i}`"
                    :x1="padding.left"
                    :x2="width - padding.right"
                    :y1="tick.y"
                    :y2="tick.y"
                    class="chart-gridline"
                />
                <text
                    v-for="(tick, i) in yTicks"
                    :key="`gt-${i}`"
                    :x="padding.left - 6"
                    :y="tick.y + 3"
                    font-size="10"
                    class="chart-axis-label"
                    text-anchor="end"
                >
                    ${{ tick.value.toFixed(2) }}
                </text>
            </g>

            <!-- X axis date labels (first / mid / last) -->
            <g v-if="xLabels.length" class="x-labels">
                <text
                    v-for="(lbl, i) in xLabels"
                    :key="`xl-${i}`"
                    :x="lbl.x"
                    :y="height - 4"
                    font-size="10"
                    class="chart-axis-label"
                    text-anchor="middle"
                >
                    {{ lbl.label }}
                </text>
            </g>

            <!-- One group per series: offers (context) + observations (your
                 data) + baseline reference line (FU-227 chunk 6 / D2 + F-3). -->
            <g v-for="(s, i) in renderableSeries" :key="s.product_id">
                <!-- Offers polyline. In the union view (offersAsContext) offers
                     are subordinate: dashed + faint. On the per-product page
                     they're the primary data: solid + full strength. -->
                <polyline
                    v-if="s.path.length"
                    :points="s.path"
                    fill="none"
                    :stroke="seriesColour(i)"
                    :stroke-width="offersAsContext ? 1.4 : 1.8"
                    :stroke-dasharray="offersAsContext ? '5,3' : undefined"
                    :opacity="offersAsContext ? 0.5 : 1"
                />
                <!-- Deal markers (only when on_deal) -->
                <g v-for="(point, j) in s.dealMarkers" :key="`d-${i}-${j}`">
                    <circle
                        :cx="point.x"
                        :cy="point.y"
                        r="3"
                        :fill="seriesColour(i)"
                        :opacity="offersAsContext ? 0.5 : 0.9"
                    />
                </g>

                <!-- Observations ("your data") — solid line + dots. -->
                <polyline
                    v-if="s.observationPath.length"
                    :points="s.observationPath"
                    fill="none"
                    :stroke="seriesColour(i)"
                    stroke-width="2"
                />
                <circle
                    v-for="(point, j) in s.observationDots"
                    :key="`o-${i}-${j}`"
                    :cx="point.x"
                    :cy="point.y"
                    r="2.6"
                    :fill="seriesColour(i)"
                />

                <!-- Baseline reference line (F-3) — "usually $X". -->
                <template v-if="s.baselineY !== null">
                    <line
                        :x1="padding.left"
                        :x2="width - padding.right"
                        :y1="s.baselineY"
                        :y2="s.baselineY"
                        class="chart-baseline"
                        stroke-dasharray="4,3"
                    />
                    <text
                        :x="width - padding.right"
                        :y="s.baselineY - 4"
                        font-size="10"
                        class="chart-baseline-label"
                        text-anchor="end"
                    >
                        {{ s.baselineLabel }}
                    </text>
                </template>
            </g>

            <!-- Hover crosshair -->
            <g v-if="hover">
                <line
                    :x1="hover.x"
                    :x2="hover.x"
                    :y1="padding.top"
                    :y2="height - padding.bottom"
                    class="chart-crosshair"
                    stroke-dasharray="3,2"
                />
            </g>
        </svg>

        <!-- Hover tooltip card -->
        <div
            v-if="hover"
            class="chart-tooltip"
            :style="{ left: `${tooltipLeft}px`, top: `${tooltipTop}px` }"
        >
            <div class="chart-tooltip-date">{{ hover.dateLabel }}</div>
            <div
                v-for="(s, i) in renderableSeries"
                :key="`t-${s.product_id}`"
                class="chart-tooltip-row"
            >
                <span class="chart-tooltip-swatch" :style="{ background: seriesColour(i) }" />
                <span class="chart-tooltip-name">{{ s.name }}</span>
                <span class="chart-tooltip-price">
                    {{ hover.byProduct[s.product_id]?.price !== undefined
                        ? `$${hover.byProduct[s.product_id]!.price!.toFixed(2)}`
                        : '—' }}
                </span>
                <q-icon
                    v-if="hover.byProduct[s.product_id]?.on_deal"
                    name="local_offer"
                    size="12px"
                    color="positive"
                    class="q-ml-xs"
                />
                <q-icon
                    v-if="hover.byProduct[s.product_id]?.is_observation"
                    name="mdi-circle"
                    size="8px"
                    color="primary"
                    class="q-ml-xs"
                >
                    <q-tooltip>Your logged price</q-tooltip>
                </q-icon>
            </div>
        </div>

        <div v-if="renderableSeries.length === 0" class="chart-empty">
            Pick one or more products on the left to see their price history.
        </div>
    </div>
</template>

<script lang="ts" setup>
    import { computed, ref } from 'vue';
    import { seriesColour } from 'src/composables/usePriceHistoryPalette';
    import type { PriceHistorySeries } from 'src/services/api/priceHistoryApiService';

    const props = defineProps<{
        series: PriceHistorySeries[];
        width?: number;
        height?: number;
        /** FU-227 chunk 6 — the union view (bottom-sheet) renders offers as
         *  subordinate "context" (dashed + faint) under the user's own
         *  observation line. The per-product page leaves it false, so offers
         *  stay the primary solid series and observations only appear as the
         *  H2 fallback when a product has no offer points. */
        offersAsContext?: boolean;
    }>();

    const width = computed(() => props.width ?? 720);
    const height = computed(() => props.height ?? 320);
    const offersAsContext = computed(() => props.offersAsContext ?? false);
    const padding = { top: 12, right: 16, bottom: 22, left: 48 };

    interface RenderableSeries {
        product_id: string;
        name: string;
        path: string;
        dealMarkers: Array<{ x: number; y: number }>;
        observationPath: string;
        observationDots: Array<{ x: number; y: number }>;
        baselineY: number | null;
        baselineLabel: string | null;
    }

    // Whether a series has any plottable offer point. Drives the H2 fallback:
    // on the per-product page (offersAsContext=false) observations + baseline
    // only render when a product has no offers, so the per-unit observation
    // scale never clashes with the raw offer scale on the same series.
    function hasOffers(s: PriceHistorySeries): boolean {
        return s.points.some((p) => p.unit_price !== null && p.date !== null);
    }
    function showObservationsFor(s: PriceHistorySeries): boolean {
        if ((s.observation_points?.length ?? 0) === 0) return false;
        return offersAsContext.value || !hasOffers(s);
    }
    function showBaselineFor(s: PriceHistorySeries): boolean {
        if (s.your_prices?.baseline == null) return false;
        return offersAsContext.value || !hasOffers(s);
    }

    // Compute the chart-space bounds across all series. A series with no
    // points contributes nothing; if every series is empty we render an
    // empty-state message.
    const valueBounds = computed(() => {
        const all: number[] = [];
        for (const s of props.series) {
            for (const p of s.points) {
                if (p.unit_price !== null) all.push(p.unit_price);
            }
            // Include observation points + baseline only when they're drawn,
            // so a hidden per-unit observation series can't skew a raw-offer
            // axis (H2-fallback-only).
            if (showObservationsFor(s)) {
                for (const p of s.observation_points ?? []) {
                    if (p.unit_price !== null) all.push(p.unit_price);
                }
            }
            if (showBaselineFor(s) && s.your_prices?.baseline != null) {
                all.push(s.your_prices.baseline);
            }
        }
        if (all.length === 0) return null;
        const min = Math.min(...all);
        const max = Math.max(...all);
        const span = max - min;
        // Pad the y-axis ~5% so the top/bottom polylines don't graze the
        // chart edges; minimum span 0.5 so a perfectly-flat history still
        // looks reasonable.
        const padded = Math.max(0.5, span * 1.1);
        const centre = (min + max) / 2;
        return {
            min: Math.max(0, centre - padded / 2),
            max: centre + padded / 2,
        };
    });

    const timeBounds = computed(() => {
        const all: number[] = [];
        const pushDate = (date: string | null) => {
            if (!date) return;
            const t = new Date(date).getTime();
            if (!Number.isNaN(t)) all.push(t);
        };
        for (const s of props.series) {
            for (const p of s.points) pushDate(p.date);
            if (showObservationsFor(s)) {
                for (const p of s.observation_points ?? []) pushDate(p.date);
            }
        }
        if (all.length === 0) return null;
        return { min: Math.min(...all), max: Math.max(...all) };
    });

    function projectX(timestamp: number): number {
        const tb = timeBounds.value;
        if (!tb) return padding.left;
        const innerW = width.value - padding.left - padding.right;
        if (tb.max === tb.min) return padding.left + innerW / 2;
        return padding.left + ((timestamp - tb.min) / (tb.max - tb.min)) * innerW;
    }
    function projectY(value: number): number {
        const vb = valueBounds.value;
        if (!vb) return padding.top;
        const innerH = height.value - padding.top - padding.bottom;
        if (vb.max === vb.min) return padding.top + innerH / 2;
        return padding.top + innerH - ((value - vb.min) / (vb.max - vb.min)) * innerH;
    }

    const renderableSeries = computed<RenderableSeries[]>(() =>
        props.series.map((s) => {
            const points: Array<{ x: number; y: number; on_deal: boolean }> = [];
            for (const p of s.points) {
                if (p.date === null || p.unit_price === null) continue;
                const t = new Date(p.date).getTime();
                if (Number.isNaN(t)) continue;
                points.push({
                    x: projectX(t),
                    y: projectY(p.unit_price),
                    on_deal: p.on_deal,
                });
            }

            // Observations ("your data") — only when this series should show
            // them (offersAsContext, or the H2 no-offer fallback).
            const obsPoints: Array<{ x: number; y: number }> = [];
            if (showObservationsFor(s)) {
                for (const p of s.observation_points ?? []) {
                    if (p.date === null || p.unit_price === null) continue;
                    const t = new Date(p.date).getTime();
                    if (Number.isNaN(t)) continue;
                    obsPoints.push({ x: projectX(t), y: projectY(p.unit_price) });
                }
            }

            let baselineY: number | null = null;
            let baselineLabel: string | null = null;
            if (showBaselineFor(s) && s.your_prices?.baseline != null) {
                baselineY = projectY(s.your_prices.baseline);
                const unit = s.your_prices.baseline_unit;
                baselineLabel = `usually $${s.your_prices.baseline.toFixed(2)}${unit ? `/${unit}` : ''}`;
            }

            return {
                product_id: s.product_id,
                name: s.name,
                path: points.map((p) => `${p.x},${p.y}`).join(' '),
                dealMarkers: points.filter((p) => p.on_deal).map(
                    (p) => ({ x: p.x, y: p.y }),
                ),
                observationPath: obsPoints.map((p) => `${p.x},${p.y}`).join(' '),
                observationDots: obsPoints,
                baselineY,
                baselineLabel,
            };
        }),
    );

    // ── Y ticks: 4 evenly spaced over the visible range ─────────────────
    const yTicks = computed(() => {
        const vb = valueBounds.value;
        if (!vb) return [];
        const ticks: Array<{ y: number; value: number }> = [];
        for (let i = 0; i <= 4; i += 1) {
            const v = vb.min + (vb.max - vb.min) * (i / 4);
            ticks.push({ y: projectY(v), value: v });
        }
        return ticks;
    });

    const xLabels = computed(() => {
        const tb = timeBounds.value;
        if (!tb) return [];
        const fmt = (ms: number) => new Date(ms).toLocaleDateString(undefined, {
            month: 'short', day: 'numeric',
        });
        const mid = (tb.min + tb.max) / 2;
        return [
            { x: projectX(tb.min), label: fmt(tb.min) },
            { x: projectX(mid), label: fmt(mid) },
            { x: projectX(tb.max), label: fmt(tb.max) },
        ];
    });

    // ── Hover crosshair ────────────────────────────────────────────────
    interface HoverState {
        x: number;
        dateLabel: string;
        byProduct: Record<string, { price: number | null; on_deal: boolean; is_observation: boolean }>;
    }
    const hostRef = ref<HTMLElement | null>(null);
    const hover = ref<HoverState | null>(null);

    function onMove(event: MouseEvent) {
        if (!hostRef.value) return;
        const tb = timeBounds.value;
        if (!tb) return;
        const bounds = hostRef.value.getBoundingClientRect();
        const localX = event.clientX - bounds.left;
        const innerW = width.value - padding.left - padding.right;
        const ratio = Math.max(0, Math.min(1, (localX - padding.left) / innerW));
        const targetTime = tb.min + ratio * (tb.max - tb.min);

        const byProduct: HoverState['byProduct'] = {};
        for (const s of props.series) {
            // Nearest-point lookup per series, across offers + (when shown)
            // the user's own observations. Build the candidate list first, then
            // reduce — keeping the `best` assignment in this scope so TS narrows
            // it (a closure would widen it back to never).
            const candidates: Array<{
                dt: number; price: number | null; on_deal: boolean; is_observation: boolean;
            }> = [];
            for (const p of s.points) {
                if (!p.date) continue;
                const t = new Date(p.date).getTime();
                if (Number.isNaN(t)) continue;
                candidates.push({
                    dt: Math.abs(t - targetTime), price: p.unit_price,
                    on_deal: p.on_deal, is_observation: false,
                });
            }
            if (showObservationsFor(s)) {
                for (const p of s.observation_points ?? []) {
                    if (!p.date) continue;
                    const t = new Date(p.date).getTime();
                    if (Number.isNaN(t)) continue;
                    candidates.push({
                        dt: Math.abs(t - targetTime), price: p.unit_price,
                        on_deal: false, is_observation: true,
                    });
                }
            }
            let best: (typeof candidates)[number] | null = null;
            for (const c of candidates) {
                if (best === null || c.dt < best.dt) best = c;
            }
            byProduct[s.product_id] = best
                ? { price: best.price, on_deal: best.on_deal, is_observation: best.is_observation }
                : { price: null, on_deal: false, is_observation: false };
        }
        hover.value = {
            x: projectX(targetTime),
            dateLabel: new Date(targetTime).toLocaleDateString(),
            byProduct,
        };
    }
    function onLeave() { hover.value = null; }

    // Position the tooltip so it never falls off the chart edges.
    const tooltipLeft = computed(() => {
        if (!hover.value) return 0;
        const half = 140;   // approximate tooltip width / 2
        const x = hover.value.x;
        if (x < padding.left + half) return padding.left;
        if (x > width.value - padding.right - half) {
            return width.value - padding.right - half * 2;
        }
        return x - half;
    });
    const tooltipTop = computed(() => padding.top + 4);
</script>

<style scoped>
    .chart-host { position: relative; }
    .chart-svg { display: block; }
    .chart-gridline { stroke: var(--divider); }
    .chart-axis-label { fill: var(--text-muted); }
    .chart-crosshair { stroke: var(--border-strong); }
    /* FU-227 chunk 6 — baseline reference line ("usually $X"). Muted so it
       reads as a guide behind the data lines, not another series. */
    .chart-baseline { stroke: var(--text-muted); stroke-width: 1; opacity: 0.7; }
    .chart-baseline-label { fill: var(--text-muted); font-variant-numeric: tabular-nums; }
    .chart-tooltip {
        position: absolute;
        background: var(--surface-component);
        border: 1px solid var(--border-default);
        border-radius: 6px;
        padding: 8px 10px;
        font-size: 12px;
        pointer-events: none;
        box-shadow: 0 2px 8px var(--overlay-active);
        min-width: 200px;
    }
    .chart-tooltip-date {
        font-weight: 600;
        margin-bottom: 4px;
        color: var(--text-secondary);
    }
    .chart-tooltip-row {
        display: flex; align-items: center; gap: 6px;
        line-height: 1.4;
    }
    .chart-tooltip-swatch {
        width: 10px; height: 10px; border-radius: 2px;
        display: inline-block;
    }
    .chart-tooltip-name { flex: 1; }
    .chart-tooltip-price { font-variant-numeric: tabular-nums; }
    .chart-empty {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--text-muted);
        pointer-events: none;
    }
</style>
