<template>
    <!--
        DR-2 / D-013 — the row-state legend. Stock rows speak a colour/edge
        language (level squares, essential stripe, attention outlines, the
        dimmed "out" row, the stocktake pulse). D-013 requires that language
        be decodable in-UI; before this, the dimmed row in particular read as
        a rendering bug (FU-578 #33/#44). Lives in the filter panel so it's
        one tap from the list without adding permanent chrome.

        The level swatches are DERIVED, not hand-drawn: we iterate the
        household's actual level rows (so a renamed "Out of stock" → "None
        left" shows its real name) and colour each via the same
        `colourForSequence` authority + `bg-*` / `dora-bg-neutral` classes the
        row's level button uses (R-003) — the legend cannot drift from the
        rows it explains.
    -->
    <div class="stock-row-legend">
        <div class="stock-row-legend__title row items-center no-wrap">
            <q-icon :name="ICONS.help_outline" size="16px" class="q-mr-xs dora-text-muted" />
            What the row colours mean
        </div>

        <div class="stock-row-legend__grid">
            <!-- Level squares — one per real level row, escalating
                 green → amber → red (D-001), plus the "not set" dashed box. -->
            <div class="stock-row-legend__section-label">Stock level</div>
            <div
                v-for="level in sortedLevels"
                :key="level.stock_level_id"
                class="stock-row-legend__item row items-center no-wrap"
            >
                <span
                    class="stock-row-legend__swatch stock-row-legend__swatch--square"
                    :class="swatchClass(level.sequence)"
                    aria-hidden="true"
                />
                <span class="stock-row-legend__text">{{ level.name }}</span>
            </div>
            <div class="stock-row-legend__item row items-center no-wrap">
                <span
                    class="stock-row-legend__swatch stock-row-legend__swatch--square stock-row-legend__swatch--unset"
                    aria-hidden="true"
                />
                <span class="stock-row-legend__text">Level not set</span>
            </div>

            <!-- Row highlights — the whole-row / edge treatments. -->
            <div class="stock-row-legend__section-label">Row highlights</div>
            <div class="stock-row-legend__item row items-center no-wrap">
                <span class="stock-row-legend__row-swatch stock-row-legend__row-swatch--essential" aria-hidden="true" />
                <span class="stock-row-legend__text">Essential item (left edge)</span>
            </div>
            <div class="stock-row-legend__item row items-center no-wrap">
                <span class="stock-row-legend__row-swatch stock-row-legend__row-swatch--warn" aria-hidden="true" />
                <span class="stock-row-legend__text">Needs attention soon — an essential's low, or something's expiring within 7 days</span>
            </div>
            <div class="stock-row-legend__item row items-center no-wrap">
                <span class="stock-row-legend__row-swatch stock-row-legend__row-swatch--alert" aria-hidden="true" />
                <span class="stock-row-legend__text">Needs attention now — an essential's out, or something's expired</span>
            </div>
            <div class="stock-row-legend__item row items-center no-wrap">
                <span class="stock-row-legend__row-swatch stock-row-legend__row-swatch--dim" aria-hidden="true" />
                <span class="stock-row-legend__text">Dimmed — out of stock, not marked essential</span>
            </div>
            <div class="stock-row-legend__item row items-center no-wrap">
                <span class="stock-row-legend__row-swatch stock-row-legend__row-swatch--check" aria-hidden="true" />
                <span class="stock-row-legend__text">Pulsing level box — due for a stocktake check</span>
            </div>

            <!-- 2026-08-15: the two "ring" indicators. Both were previously
                 chips with their own words next to the row's buttons; now
                 they're rings ON those buttons, which means they need
                 decoding here exactly like the outlines above do (D-013).
                 Swatches mirror the real box-shadow recipes so the mapping
                 stays visual rather than verbal. -->
            <div class="stock-row-legend__section-label">Rings on the buttons</div>
            <div class="stock-row-legend__item row items-center no-wrap">
                <span class="stock-row-legend__swatch stock-row-legend__swatch--square stock-row-legend__swatch--belief" aria-hidden="true" />
                <span class="stock-row-legend__text">
                    Amber ring on the level box — Dora thinks the level is
                    something else. Open the picker for her reasoning.
                </span>
            </div>
            <div class="stock-row-legend__item row items-center no-wrap">
                <span class="stock-row-legend__swatch stock-row-legend__swatch--cart stock-row-legend__swatch--buy" aria-hidden="true" />
                <span class="stock-row-legend__text">
                    Green ring on the cart button — worth buying now
                </span>
            </div>
            <div class="stock-row-legend__item row items-center no-wrap">
                <span class="stock-row-legend__swatch stock-row-legend__swatch--cart stock-row-legend__swatch--wait" aria-hidden="true" />
                <span class="stock-row-legend__text">
                    Amber ring on the cart button — might be worth waiting
                </span>
            </div>
            <div class="stock-row-legend__item row items-center no-wrap">
                <span class="stock-row-legend__swatch stock-row-legend__swatch--cart stock-row-legend__swatch--skip" aria-hidden="true" />
                <span class="stock-row-legend__text">
                    Red ring on the cart button — probably skip. Hover any of
                    the three for the reasons behind it.
                </span>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
    import { computed } from 'vue';
    import { ICONS } from 'src/style/icons';
    import { colourForSequence } from 'src/helpers/stockLevelLogic';
    import type { StockLevel } from 'src/models/stockLevel';

    const props = defineProps<{
        /** The household's live level rows (renamed seeds included). */
        levels: readonly StockLevel[];
    }>();

    // Escalating order (Stocked → Low → Out → any custom) so the legend
    // reads top-down like the urgency ramp it documents.
    const sortedLevels = computed(() =>
        [...props.levels].sort((a, b) => a.sequence - b.sequence),
    );

    // Same mapping the row's level button uses (`levelButtonClass`): a
    // `bg-{semantic}` utility class, or the neutral token for unknown.
    function swatchClass(sequence: number): string {
        const colour = colourForSequence(sequence);
        return colour ? `bg-${colour}` : 'dora-bg-neutral';
    }
</script>

<style scoped lang="scss">
    .stock-row-legend {
        margin-top: var(--space-2);
        padding-top: var(--space-3);
        border-top: 1px solid color-mix(in srgb, var(--text-primary) 12%, transparent);
    }
    .stock-row-legend__title {
        font-size: calc(var(--font-size-sm) * 1rem);
        font-weight: 600;
        color: var(--text-secondary);
        margin-bottom: var(--space-2);
    }
    .stock-row-legend__grid {
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-1) var(--space-4);
    }
    /* Force a line break before each section label so "Stock level" and
       "Row highlights" head their own column of items. */
    .stock-row-legend__section-label {
        flex-basis: 100%;
        font-size: calc(var(--font-size-xs) * 1rem);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--text-muted);
        margin-top: var(--space-2);
    }
    .stock-row-legend__item {
        flex: 0 1 auto;
        gap: var(--space-2);
        min-height: 22px;
    }
    .stock-row-legend__text {
        font-size: calc(var(--font-size-sm) * 1rem);
        color: var(--text-secondary);
    }

    /* Level swatch — mirrors the row's 32px level button at legend scale. */
    .stock-row-legend__swatch {
        flex: 0 0 auto;
        width: 16px;
        height: 16px;
        border-radius: var(--radius-sm, 4px);
    }
    .stock-row-legend__swatch--unset {
        background: var(--surface-component);
        border: 1px dashed color-mix(in srgb, var(--text-primary) 24%, transparent);
    }

    /* Ring swatches. Same offset-ring recipe the real controls use (an inner
       ring painted in the surface colour makes the gap, the outer one is the
       line), scaled down and given margin so the ring isn't clipped by its
       neighbours. `--belief` is the square level box; `--cart` is the round
       cart button, so it carries the pill radius. */
    .stock-row-legend__swatch--belief {
        background: var(--surface-sunken);
        margin: 4px;
        box-shadow:
            0 0 0 2px var(--surface-component),
            0 0 0 3px var(--semantic-warning);
    }
    .stock-row-legend__swatch--cart {
        flex: 0 0 auto;
        width: 16px;
        height: 16px;
        margin: 4px;
        border-radius: var(--radius-full, 999px);
        background: var(--surface-sunken);
    }
    .stock-row-legend__swatch--buy {
        box-shadow:
            0 0 0 2px var(--surface-component),
            0 0 0 3px var(--semantic-positive);
    }
    .stock-row-legend__swatch--wait {
        box-shadow:
            0 0 0 2px var(--surface-component),
            0 0 0 3px var(--semantic-warning);
    }
    .stock-row-legend__swatch--skip {
        box-shadow:
            0 0 0 2px var(--surface-component),
            0 0 0 3px var(--semantic-negative);
    }

    /* Row-highlight swatches — a mini row (28×18) carrying the same
       treatment the real row does, so the mapping is visual not verbal. */
    .stock-row-legend__row-swatch {
        flex: 0 0 auto;
        width: 28px;
        height: 18px;
        border-radius: var(--radius-sm, 4px);
        background: var(--surface-component);
        border: 1px solid color-mix(in srgb, var(--text-primary) 12%, transparent);
    }
    .stock-row-legend__row-swatch--essential {
        /* left-edge secondary stripe, matching StockItemRow. */
        border-left: 6px solid var(--brand-secondary-strong);
    }
    .stock-row-legend__row-swatch--warn {
        border-color: var(--q-warning);
        box-shadow: inset 0 0 0 1px var(--q-warning);
    }
    .stock-row-legend__row-swatch--alert {
        border-color: var(--q-negative);
        box-shadow: inset 0 0 0 1px var(--q-negative);
    }
    .stock-row-legend__row-swatch--dim {
        background: color-mix(in srgb, var(--text-primary) 22%, var(--surface-component));
        opacity: 0.62;
    }
    .stock-row-legend__row-swatch--check {
        /* the level-box stocktake pulse, at legend scale. */
        animation: stock-row-legend-pulse 2s ease-in-out infinite;
    }
    @keyframes stock-row-legend-pulse {
        0%, 100% {
            box-shadow: 0 0 0 0 color-mix(in srgb, var(--brand-accent) 55%, transparent);
        }
        50% {
            box-shadow: 0 0 0 5px color-mix(in srgb, var(--brand-accent) 0%, transparent);
        }
    }
    @media (prefers-reduced-motion: reduce) {
        .stock-row-legend__row-swatch--check {
            animation: none;
            box-shadow: 0 0 0 2px color-mix(in srgb, var(--brand-accent) 45%, transparent);
        }
    }
</style>
