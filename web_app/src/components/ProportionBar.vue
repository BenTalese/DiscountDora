<template>
    <div v-if="resolved.length > 0" class="proportion-bar" role="presentation">
        <div
            v-for="seg in resolved"
            :key="seg.key"
            class="proportion-bar__seg"
            :class="{ 'proportion-bar__seg--unassigned': seg.isUnassigned }"
            :style="{ width: `${seg.width}%`, background: seg.isUnassigned ? undefined : seg.colour }"
        >
            <q-tooltip v-if="seg.label">{{ seg.label }}</q-tooltip>
        </div>
    </div>
</template>

<script lang="ts" setup>
    /**
     * One horizontal bar showing how a total divides up.
     *
     * ## Why this is shared
     *
     * Three surfaces render "where the money went" and all three drew it
     * differently: the shopping list as this proportional bar, the dashboard as
     * a plain text list, Reports as an ECharts donut with hash-assigned hues
     * (`REPORTS_PAGE_REVIEW.md` §3.1). The donut is gone — §4.6's three
     * arguments against it are that it is unreadable past three slices, fragile
     * at half-width, and that the app already had a better answer *and had
     * already solved the two hard cases in it*: a bucket with items but no value
     * must not vanish, and the unassigned bucket must be distinguishable from a
     * real one. Both are here, once.
     *
     * ## What the caller owns
     *
     * `value` — deliberately. The shopping list weighs by spend when money is on
     * and by item count when it is off; Reports weighs by spend, always. That is
     * a question about the data, not about the bar, so this component takes
     * numbers that are already the right numbers and never asks what they mean.
     */
    import { computed } from 'vue';

    export type ProportionSegment = {
        key: string;
        /** Tooltip text. Optional — the caller usually renders a legend too, and
         *  the bar is `role="presentation"` precisely because it is not the only
         *  channel (D-001). */
        label?: string;
        value: number;
        /** Omitted for the unassigned bucket, which is drawn as a hatch and has
         *  no colour of its own to give. */
        colour?: string | undefined;
        /** The catch-all bucket — "No store set", "Uncategorised". Drawn as a
         *  hatch rather than a colour; see the stylesheet. */
        isUnassigned?: boolean;
    };

    const props = defineProps<{ segments: ProportionSegment[] }>();

    /** Floor width for a bucket that exists but has nothing to weigh it by.
     *  Enough to read as a segment at a phone's width, small enough that two
     *  unpriced items don't misrepresent themselves as a big share. */
    const MIN_SEGMENT_PCT = 7;

    const resolved = computed(() => {
        const present = props.segments;
        const valued = present.filter((s) => s.value > 0);
        const total = valued.reduce((sum, s) => sum + s.value, 0);

        // Nothing anywhere has a value: there is no proportion to draw, so show
        // the buckets as equal presences rather than inventing a ranking out of
        // something the bar isn't measuring.
        if (valued.length === 0 || total <= 0) {
            return present.map((s) => ({ ...s, width: 100 / Math.max(1, present.length) }));
        }

        // Every bucket that exists gets at least the floor; the ones that carry
        // value share what's left in true proportion. Segments still sum to
        // 100%, and the comparison between two valued buckets stays honest —
        // only the "this exists" floor is synthetic.
        const floors = (present.length - valued.length) * MIN_SEGMENT_PCT;
        const share = (100 - floors) / 100;
        return present.map((s) => ({
            ...s,
            width: s.value > 0 ? (s.value / total) * 100 * share : MIN_SEGMENT_PCT,
        }));
    });
</script>

<style scoped lang="scss">
    .proportion-bar {
        display: flex;
        height: 8px;
        border-radius: var(--radius-sm);
        overflow: hidden;
        background: var(--surface-sunken);
    }
    .proportion-bar__seg {
        height: 100%;
        min-width: 2px;
    }
    /* The catch-all: a themed grey, hatched.
       (Moved verbatim with the bar — the reasoning is what makes it a hatch.)

       The grey alone is `--border-strong`, the neutral every theme defines to
       be seen against a surface — which is right in light themes and measurably
       wrong in dark ones. Measured against the store fills either side of it:
       3.55:1 in Pesto light, but **1.19:1** in Pesto Dark and **1.02:1** in
       Cherry Cola Dark, i.e. the same lightness as its neighbour. That isn't
       fixable by picking a better grey, because the fills it competes with are
       partly *logo-derived brand colours* — arbitrary, and free to be grey
       themselves. No single neutral can be guaranteed to separate from them.

       So the segment is distinguished by **texture**, which no neighbouring
       colour can collide with, and which says the right thing: a hatch reads as
       unallocated rather than as one more store. Both stripe colours are theme
       tokens, so it inverts correctly — dark stripes on grey in light themes,
       light stripes on grey in dark ones. Colour is still carrying the message
       for anyone who sees it, but it is no longer carrying it alone (D-001). */
    .proportion-bar__seg--unassigned {
        background-color: var(--border-strong);
        background-image: repeating-linear-gradient(
            135deg,
            transparent 0 3px,
            var(--surface-component) 3px 5px
        );
    }
</style>
