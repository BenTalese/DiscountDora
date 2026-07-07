<template>
    <!--
        A7 — reusable sticky page-counts footer. Sticks to the bottom of the
        page's scroll area, visually separated (top border + soft elevation),
        and wraps responsively. Each count is a labelled stat with an optional
        semantic tone. Counts are the caller's concern — pass whatever the page
        wants to surface (typically the *filtered* view).

        Feedback 2026-06-18 (round 2): counts may carry a `group` so the
        footer renders three clusters — [Shown] · [stock levels] · [other
        counts] — centered with a fixed inter-cluster gap.

        Feedback 2026-06-18 (round 6): on mobile the stack-style layout
        (number on top, label below) ate too much vertical space. Counts
        flagged `hideOnMobile` collapse out, and the surviving stats
        render as number-then-label on the same line at the narrow
        breakpoint.
    -->
    <div v-if="counts.length" class="page-counts-footer">
        <div class="page-counts-footer__inner row items-center justify-center">
            <div
                v-for="(group, idx) in groupedCounts"
                :key="idx"
                class="page-counts-footer__group row items-center q-gutter-md"
            >
                <div
                    v-for="c in group"
                    :key="c.label"
                    class="page-counts-footer__stat"
                >
                    <div class="page-counts-footer__value text-h6" :class="toneClass(c.tone)">{{ c.value }}</div>
                    <div class="page-counts-footer__label text-caption dora-text-muted">{{ c.label }}</div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
    import { computed } from 'vue';
    import { useQuasar } from 'quasar';

    export interface PageCount {
        label: string;
        value: number | string;
        /** Optional semantic colour for the value. */
        tone?: 'positive' | 'negative' | 'warning' | 'info' | 'primary' | 'secondary' | 'muted';
        /** Optional cluster id — counts sharing a `group` render together
         *  with smaller inter-stat spacing; clusters are centered across
         *  the bar. Default order: `shown` → `levels` → `other`. */
        group?: 'shown' | 'levels' | 'other';
        /** Hide this count at narrow viewports. Stock Overview marks
         *  everything but Shown + Needs attention with this so the mobile
         *  footer stays compact. */
        hideOnMobile?: boolean;
    }

    const props = defineProps<{ counts: PageCount[] }>();
    const $q = useQuasar();

    const GROUP_ORDER: Array<NonNullable<PageCount['group']>> = ['shown', 'levels', 'other'];

    // Bucket counts into ordered clusters. Counts with no `group` collapse
    // into a single cluster so callers that haven't opted into the
    // 3-cluster layout keep the original behaviour. Counts flagged
    // `hideOnMobile` drop out at narrow viewports — when an entire group
    // disappears the cluster is omitted so the inter-cluster gap doesn't
    // leave a visible hole.
    const groupedCounts = computed<PageCount[][]>(() => {
        const isMobile = $q.screen.lt.sm;
        const visible = isMobile
            ? props.counts.filter((c) => !c.hideOnMobile)
            : props.counts;
        const anyGrouped = visible.some((c) => !!c.group);
        if (!anyGrouped) return visible.length ? [visible] : [];
        const buckets = new Map<string, PageCount[]>();
        for (const c of visible) {
            const key = c.group ?? 'other';
            if (!buckets.has(key)) buckets.set(key, []);
            buckets.get(key)!.push(c);
        }
        return GROUP_ORDER
            .map((k) => buckets.get(k))
            .filter((g): g is PageCount[] => !!g && g.length > 0);
    });

    function toneClass(tone?: PageCount['tone']): string {
        switch (tone) {
            case 'positive': return 'text-positive';
            case 'negative': return 'text-negative';
            case 'warning': return 'text-warning';
            case 'info': return 'text-info';
            case 'primary': return 'text-primary';
            case 'secondary': return 'text-secondary';
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
        /* `.row` wraps by default → responsive on narrow screens. The
           horizontal `gap` here is the inter-cluster gap (between
           Shown · stock levels · other counts) — fixed at ~64px so the
           clusters read as distinct without blowing apart on wide
           viewports. */
        padding: var(--space-3, 12px) var(--space-4, 16px);
        gap: var(--space-3, 12px) 64px;
    }
    .page-counts-footer__group {
        flex: 0 1 auto;
    }
    /* Desktop default: number on top, label underneath (the original A7
       layout). The column flex centers them so the cluster reads cleanly. */
    .page-counts-footer__stat {
        min-width: 64px;
        flex: 0 0 auto;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    /* Mobile: number to the LEFT of the label on the same line so the
       footer collapses to a single short row instead of a two-line
       stack. Smaller type so the bar stays compact, and the
       inter-cluster gap shrinks since there's less to space out. */
    @media (max-width: 599px) {
        .page-counts-footer__inner {
            gap: 6px 20px;
            padding: 6px 12px;
        }
        .page-counts-footer__stat {
            flex-direction: row;
            align-items: baseline;
            gap: 6px;
            min-width: 0;
        }
        .page-counts-footer__value {
            font-size: 1rem;
            line-height: 1.2;
        }
        .page-counts-footer__label {
            line-height: 1.2;
        }
    }
</style>
