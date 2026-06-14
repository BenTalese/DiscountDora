<template>
    <!--
        A7 — reusable sticky page-counts footer. Sticks to the bottom of the
        page's scroll area, visually separated (top border + soft elevation),
        and wraps responsively. Each count is a labelled stat with an optional
        semantic tone. Counts are the caller's concern — pass whatever the page
        wants to surface (typically the *filtered* view).
    -->
    <div v-if="counts.length" class="page-counts-footer">
        <div class="page-counts-footer__inner row items-center justify-center">
            <div
                v-for="c in counts"
                :key="c.label"
                class="page-counts-footer__stat column items-center"
            >
                <div class="text-h6" :class="toneClass(c.tone)">{{ c.value }}</div>
                <div class="text-caption dora-text-muted">{{ c.label }}</div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
    export interface PageCount {
        label: string;
        value: number | string;
        /** Optional semantic colour for the value. */
        tone?: 'positive' | 'negative' | 'warning' | 'info' | 'primary' | 'muted';
    }

    defineProps<{ counts: PageCount[] }>();

    function toneClass(tone?: PageCount['tone']): string {
        switch (tone) {
            case 'positive': return 'text-positive';
            case 'negative': return 'text-negative';
            case 'warning': return 'text-warning';
            case 'info': return 'text-info';
            case 'primary': return 'text-primary';
            case 'muted': return 'dora-text-muted';
            default: return '';
        }
    }
</script>

<style scoped lang="scss">
    .page-counts-footer {
        position: sticky;
        bottom: 0;
        z-index: 5;
        // Outdent to consume the page wrapper's `q-pa-md` padding (16px on
        // all sides). Without this, when the user scrolls to the very end
        // of the page the sticky element stops sticking and reverts to its
        // in-flow position — the parent's bottom padding then shows as a
        // visible gap below it, breaking the "flush with viewport bottom"
        // feel the sticky mode gives mid-scroll. The negative side
        // margins also let the bar stretch to the page edges so the
        // border-top / shadow read as a true full-width divider.
        margin: var(--space-4, 16px) -16px -16px;
        background: var(--surface-component);
        border-top: 1px solid color-mix(in srgb, var(--text-primary) 12%, transparent);
        box-shadow: 0 -2px 10px color-mix(in srgb, var(--text-primary) 8%, transparent);
    }
    .page-counts-footer__inner {
        /* `.row` wraps by default → responsive on narrow screens. */
        padding: var(--space-3, 12px) var(--space-4, 16px);
        gap: var(--space-3, 12px) var(--space-6, 24px);
    }
    .page-counts-footer__stat {
        min-width: 64px;
        flex: 0 0 auto;
    }
</style>
