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
                    stroke="#eee"
                />
                <text
                    v-for="(tick, i) in yTicks"
                    :key="`gt-${i}`"
                    :x="padding.left - 6"
                    :y="tick.y + 3"
                    font-size="10"
                    fill="#888"
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
                    fill="#888"
                    text-anchor="middle"
                >
                    {{ lbl.label }}
                </text>
            </g>

            <!-- One polyline per series -->
            <g v-for="(s, i) in renderableSeries" :key="s.product_id">
                <polyline
                    v-if="s.path.length"
                    :points="s.path"
                    fill="none"
                    :stroke="seriesColour(i)"
                    stroke-width="1.8"
                />
                <!-- Deal markers (only when on_deal) -->
                <g v-for="(point, j) in s.dealMarkers" :key="`d-${i}-${j}`">
                    <circle
                        :cx="point.x"
                        :cy="point.y"
                        r="3"
                        :fill="seriesColour(i)"
                        opacity="0.9"
                    />
                </g>
            </g>

            <!-- Hover crosshair -->
            <g v-if="hover">
                <line
                    :x1="hover.x"
                    :x2="hover.x"
                    :y1="padding.top"
                    :y2="height - padding.bottom"
                    stroke="#bbb"
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
    }>();

    const width = computed(() => props.width ?? 720);
    const height = computed(() => props.height ?? 320);
    const padding = { top: 12, right: 16, bottom: 22, left: 48 };

    interface RenderableSeries {
        product_id: string;
        name: string;
        path: string;
        dealMarkers: Array<{ x: number; y: number }>;
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
        for (const s of props.series) {
            for (const p of s.points) {
                if (p.date) {
                    const t = new Date(p.date).getTime();
                    if (!Number.isNaN(t)) all.push(t);
                }
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
            return {
                product_id: s.product_id,
                name: s.name,
                path: points.map((p) => `${p.x},${p.y}`).join(' '),
                dealMarkers: points.filter((p) => p.on_deal).map(
                    (p) => ({ x: p.x, y: p.y }),
                ),
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
        byProduct: Record<string, { price: number | null; on_deal: boolean }>;
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
            // Nearest-point lookup per series.
            let best: { dt: number; price: number | null; on_deal: boolean } | null = null;
            for (const p of s.points) {
                if (!p.date) continue;
                const t = new Date(p.date).getTime();
                if (Number.isNaN(t)) continue;
                const dt = Math.abs(t - targetTime);
                if (best === null || dt < best.dt) {
                    best = { dt, price: p.unit_price, on_deal: p.on_deal };
                }
            }
            byProduct[s.product_id] = best
                ? { price: best.price, on_deal: best.on_deal }
                : { price: null, on_deal: false };
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
    .chart-tooltip {
        position: absolute;
        background: rgba(255, 255, 255, 0.97);
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
