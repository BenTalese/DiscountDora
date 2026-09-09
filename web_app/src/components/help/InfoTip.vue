<template>
    <!--
        Owner feedback 2026-08-29 — *"The info chip for mode feels a bit small.
        Are the other info chips this size? Consistency!"* They weren't: the
        same (?)-with-a-tooltip shape had been hand-rolled at 14px on the
        Assistant page, the meal-plan week status and the Dora score card, and
        at 16px on the stock-row legend. One component, one size, one tooltip
        width — so the next one can't drift either.

        Distinct from `HelpHint`, which *navigates* to a Help guide. This one
        just says the thing inline; reach for HelpHint when the explanation is
        long enough to want its own page.
    -->
    <span class="info-tip" :aria-label="`More information: ${label}`" tabindex="0">
        <q-icon :name="ICONS.help_outline" size="18px" />
        <BaseTooltip max-width="340px" :offset="[0, 6]" class="info-tip__tooltip">
            <slot />
        </BaseTooltip>
    </span>
</template>

<script setup lang="ts">
    import BaseTooltip from 'src/components/BaseTooltip.vue';
    import { ICONS } from 'src/style/icons';

    defineProps<{
        /** What the tip is about — screen-reader label, never rendered. */
        label: string;
    }>();
</script>

<style scoped lang="scss">
    .info-tip {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        /* D-004 — the icon is 18px, but a bare 18px target is unhittable on a
           phone (where the tooltip opens on long-press). Padding takes the box
           to 26px without changing how big the glyph looks. */
        padding: 4px;
        margin: -4px 0 -4px 2px;
        vertical-align: middle;
        color: var(--text-muted);
        cursor: help;
    }
    .info-tip:hover,
    .info-tip:focus-visible {
        color: var(--text-secondary);
    }
    .info-tip:focus-visible {
        outline: 2px solid var(--ring-focus);
        outline-offset: 1px;
        border-radius: 50%;
    }
    .info-tip__tooltip {
        font-size: 0.8125rem;
        line-height: 1.45;
    }
</style>
