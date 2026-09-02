<template>
    <!-- The card is deliberately not one big link: the low and out legend rows
         and donut segments deep-link to the *filtered* stock view
         (`?level_id=…`), while the header's "View →" keeps the unfiltered pantry
         link for the show-me-everything case (FU-299). -->
    <DashboardCard icon="inventory_2" title="Pantry">
        <template #action>
            <router-link class="dora-card-action dora-card-link" to="/stock">
                View →
            </router-link>
        </template>
        <div class="dora-stock-body">
            <svg
                viewBox="0 0 36 36"
                class="dora-donut"
                :aria-label="`${total} stock items: ${inStock} in stock, ${low} low, ${out} out`"
            >
                <circle class="dora-donut-track" cx="18" cy="18" r="15.915" />
                <circle
                    v-for="(seg, i) in segments"
                    :key="seg.label"
                    cx="18"
                    cy="18"
                    r="15.915"
                    fill="none"
                    stroke-width="4"
                    :stroke="seg.colour"
                    :stroke-dasharray="`${seg.percent} ${100 - seg.percent}`"
                    :stroke-dashoffset="seg.offset"
                    :style="{ transitionDelay: `${i * 60}ms`, cursor: seg.link ? 'pointer' : undefined }"
                    :role="seg.link ? 'link' : undefined"
                    :tabindex="seg.link ? 0 : undefined"
                    :aria-label="seg.link ? `View ${seg.label} items` : undefined"
                    class="dora-donut-seg"
                    :class="{ 'dora-donut-seg--link': seg.link }"
                    @click="seg.link && emit('open', seg.link)"
                    @keydown.enter="seg.link && emit('open', seg.link)"
                    @keydown.space.prevent="seg.link && emit('open', seg.link)"
                />
                <text x="18" y="17" text-anchor="middle" class="dora-donut-big">
                    {{ total }}
                </text>
                <text x="18" y="22.5" text-anchor="middle" class="dora-donut-sub">items</text>
            </svg>
            <ul class="dora-legend">
                <li>
                    <span class="dora-dot dora-dot-ok"></span>
                    <span class="dora-legend-num">{{ inStock }}</span>
                    <span class="dora-legend-label">in stock</span>
                </li>
                <li>
                    <router-link class="dora-legend-link" :to="lowLink">
                        <span class="dora-dot dora-dot-warn"></span>
                        <span class="dora-legend-num">{{ low }}</span>
                        <span class="dora-legend-label">running low</span>
                    </router-link>
                </li>
                <li>
                    <router-link class="dora-legend-link" :to="outLink">
                        <span class="dora-dot dora-dot-bad"></span>
                        <span class="dora-legend-num">{{ out }}</span>
                        <span class="dora-legend-label">out</span>
                    </router-link>
                </li>
            </ul>
        </div>
    </DashboardCard>
</template>

<script lang="ts" setup>
    /**
     * The pantry donut: how the stock is split between in-stock, low and out.
     *
     * The segment colours are resolved by the page through
     * `useThemePalette.paletteToken`, not here — an SVG `stroke` can't take a
     * CSS custom property through an attribute, so the value has to be read off
     * the document. That read used to be a one-shot `getComputedStyle` with a
     * comment claiming the donut recoloured on a theme switch; it didn't
     * (FU-824). It does now, because `paletteToken` carries a dependency on the
     * theme version.
     *
     * Extracted from `DashboardPage.vue` (FU-829).
     */
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';

    export type DonutSegment = {
        label: string;
        percent: number;
        offset: number;
        colour: string;
        /** Filtered-stock route, or null for the residual "in stock" slice —
         *  which has no `?level_id` to filter by, so it isn't clickable. */
        link: string | null;
    };

    defineProps<{
        total: number;
        inStock: number;
        low: number;
        out: number;
        segments: DonutSegment[];
        lowLink: string;
        outLink: string;
    }>();

    const emit = defineEmits<{ (e: 'open', path: string): void }>();
</script>

<style scoped lang="scss">
    /* Moved with the card (R-027); off the page-local `--c-*` aliases, which
       resolve to nothing from a component (R-060). */
    .dora-stock-body {
        display: flex;
        align-items: center;
        gap: 18px;
    }
    .dora-donut {
        width: 132px;
        height: 132px;
        flex-shrink: 0;
        transform: rotate(-90deg);
    }
    .dora-donut-track {
        fill: none;
        stroke: var(--surface-sunken);
        stroke-width: 4;
    }
    .dora-donut-seg {
        transition: stroke-dasharray 0.6s ease, stroke-dashoffset 0.6s ease, opacity 0.15s ease;
    }
    /* FU-299 — clickable low/out segments.
       ⚠️ This rule sets `outline: none` on `:focus` with only an opacity change
       as the replacement, which A6 forbids ("never `outline: none` without a
       replacement") and D-016 compounds (hover and focus are byte-identical, so
       they aren't distinguishable). Carried across the extraction verbatim
       rather than fixed here — it belongs to the chunk-6 focus pass, where the
       whole page's missing `:focus-visible` is dealt with in one go. */
    .dora-donut-seg--link:hover,
    .dora-donut-seg--link:focus {
        opacity: 0.8;
        outline: none;
    }
    /* Legend rows deep-link to the filtered pantry view; low/out are the "act"
       segments — underline on hover, keep the row layout stable. */
    .dora-legend-link {
        display: contents;
        color: inherit;
        text-decoration: none;
    }
    .dora-legend-link:hover .dora-legend-label,
    .dora-legend-link:focus .dora-legend-label {
        text-decoration: underline;
    }
    /* SVG text inherits the parent's -90deg rotation; rotate the text nodes back
       so the centre label reads normally. */
    .dora-donut-big,
    .dora-donut-sub {
        transform: rotate(90deg);
        transform-origin: 18px 18px;
    }
    .dora-donut-big {
        font-size: 7.5px;
        font-weight: 700;
        fill: var(--text-primary);
    }
    /* 3 user units in a 36-unit viewBox rendered at 132px ≈ 11px effective —
       under the D-003 12px floor. Noted for the chunk-6 type pass; the fix is a
       larger unit size, not a token (SVG font-size is in viewBox units). */
    .dora-donut-sub {
        font-size: 3px;
        fill: var(--text-secondary);
        text-transform: lowercase;
        letter-spacing: 0.05em;
    }
    .dora-legend {
        list-style: none;
        margin: 0;
        padding: 0;
        font-size: 0.85rem;
    }
    .dora-legend li {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 4px 0;
    }
    .dora-dot {
        width: 9px;
        height: 9px;
        border-radius: var(--radius-pill);
        flex-shrink: 0;
    }
    .dora-dot-ok { background: var(--semantic-positive); }
    .dora-dot-warn { background: var(--semantic-warning); }
    .dora-dot-bad { background: var(--semantic-negative); }
    .dora-legend-num {
        font-weight: 600;
        min-width: 1.4em;
        text-align: right;
    }
    .dora-legend-label {
        color: var(--text-secondary);
    }

    @media (prefers-reduced-motion: reduce) {
        .dora-donut-seg {
            transition: none !important;
        }
    }
</style>
