<template>
    <!-- "Where you'll spend it" — the plan-face store breakdown.
         Renders nothing at all unless the server resolved at least one real
         store, so it never nags installs that don't use stores. -->
    <q-card v-if="buckets.length > 0" flat bordered class="sl-store-card">
        <q-card-section class="q-pb-none row items-center no-wrap q-gutter-x-sm">
            <q-icon :name="ICONS.storefront" size="18px" class="dora-text-secondary" />
            <span class="text-subtitle2">{{ title }}</span>
            <q-space />
            <!-- Mobile collapses this to the one-line summary below; desktop
                 has the room, so it stays open (D-011 — don't stack blocks
                 above the content on a phone). -->
            <BaseButton
                v-if="collapsible"
                variant="icon"
                :icon="expanded ? ICONS.collapse : ICONS.expand"
                :aria-label="expanded ? 'Hide store breakdown' : 'Show store breakdown'"
                @click="expanded = !expanded"
            />
        </q-card-section>

        <q-card-section v-if="!expanded" class="q-pt-sm">
            <div class="text-caption dora-text-muted ellipsis">{{ summaryLine }}</div>
        </q-card-section>

        <template v-else>
            <q-card-section class="q-pt-sm q-pb-xs">
                <!-- Proportional bar. Segments are spend share, so an
                     unpriced-only bucket contributes nothing and the bar
                     honestly reflects money rather than item counts. -->
                <div v-if="pricedTotal > 0" class="sl-store-bar" role="presentation">
                    <div
                        v-for="(b, i) in buckets"
                        :key="b.store_id ?? '__none__'"
                        class="sl-store-bar__seg"
                        :style="{
                            width: `${(b.subtotal / pricedTotal) * 100}%`,
                            background: segmentColour(i, b),
                        }"
                    />
                </div>
            </q-card-section>

            <q-card-section class="q-pt-xs">
                <div class="row q-gutter-xs">
                    <q-chip
                        v-for="(b, i) in buckets"
                        :key="b.store_id ?? '__none__'"
                        dense
                        square
                        class="sl-store-chip"
                        :class="{ 'sl-store-chip--none': b.store_id === null }"
                    >
                        <span
                            v-if="b.store_id !== null"
                            class="sl-store-dot"
                            :style="{ background: segmentColour(i, b) }"
                        />
                        <span class="text-weight-medium q-mr-xs">{{ b.store_name }}</span>
                        <span class="dora-text-muted">
                            {{ b.line_count }} item{{ b.line_count === 1 ? '' : 's' }}
                            <template v-if="moneyEnabled && b.priced_line_count > 0">
                                · {{ approx(b) }}{{ formatMoney(b.subtotal) }}
                            </template>
                        </span>
                    </q-chip>
                </div>

                <div v-if="footnote" class="text-caption dora-text-muted q-mt-sm">
                    {{ footnote }}
                </div>
            </q-card-section>
        </template>
    </q-card>
</template>

<script lang="ts" setup>
    /**
     * The store breakdown lifted out of the "Trip" direction (C) into the plan
     * face. It answers one question the rest of the page can't: *am I about to
     * spend $50 more at Coles than at Aldi?*
     *
     * The design constraint that shaped it: product offers are a power-user
     * feature most installs will never populate. The server's store ladder
     * resolves through `usual_store_id` and past purchases before it ever looks
     * at an offer, so this card is fully populated for someone who has simply
     * tagged items "I buy this at Aldi" and shopped twice.
     *
     * That makes partial data the normal case, not an edge case — hence the
     * explicit footnote when some lines have no price. A total that silently
     * omits a third of the list is worse than one that admits the gap.
     */
    import { computed, ref } from 'vue';
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import { formatMoney } from 'src/composables/useMoney';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import type { StoreSpend } from 'src/models/shoppingList';

    const props = withDefaults(defineProps<{
        buckets: StoreSpend[];
        /** Mobile passes true so the card starts as a one-line summary. */
        collapsible?: boolean;
        /** Past tense on the receipt face; the plan-face default otherwise. */
        title?: string;
    }>(), { collapsible: false, title: "Where you'll spend it" });

    const { moneyEnabled } = useMoneyEnabled();

    const expanded = ref(!props.collapsible);

    const pricedTotal = computed(() =>
        props.buckets.reduce((sum, b) => sum + b.subtotal, 0)
    );

    const unpricedCount = computed(() =>
        props.buckets.reduce((sum, b) => sum + (b.line_count - b.priced_line_count), 0)
    );

    /** A "~" marker whenever a bucket's money is an estimate rather than
     *  something the user actually typed for this trip. */
    function approx(bucket: StoreSpend): string {
        return bucket.priced_line_count < bucket.line_count ? '~' : '';
    }

    /** Categorical, not semantic — these are stores, not states, so they read
     *  from the chart ramp rather than any success/warning token (D-001). */
    function segmentColour(index: number, bucket: StoreSpend): string {
        if (bucket.store_id === null) return 'var(--surface-sunken)';
        return `var(--chart-${(index % 5) + 1})`;
    }

    const summaryLine = computed(() => {
        const parts = props.buckets.map((b) => {
            if (moneyEnabled.value && b.priced_line_count > 0) {
                return `${b.store_name} ${approx(b)}${formatMoney(b.subtotal)}`;
            }
            return `${b.store_name} ${b.line_count}`;
        });
        return parts.join(' · ');
    });

    /** Two separate honesty notes, deliberately combined into one line so the
     *  card doesn't grow a second paragraph: the headline gap between the two
     *  biggest stores, and how much of the list isn't priced at all. */
    const footnote = computed(() => {
        const notes: string[] = [];
        const real = props.buckets.filter((b) => b.store_id !== null && b.priced_line_count > 0);
        if (moneyEnabled.value && real.length >= 2) {
            const gap = real[0]!.subtotal - real[real.length - 1]!.subtotal;
            if (gap > 0) {
                notes.push(
                    `${formatMoney(gap)} more at ${real[0]!.store_name} than ${real[real.length - 1]!.store_name}`
                );
            }
        }
        if (unpricedCount.value > 0) {
            notes.push(
                `${unpricedCount.value} item${unpricedCount.value === 1 ? '' : 's'} unpriced, not counted`
            );
        }
        return notes.join(' · ');
    });
</script>

<style scoped>
    .sl-store-bar {
        display: flex;
        height: 8px;
        border-radius: 4px;
        overflow: hidden;
        background: var(--surface-sunken);
    }
    .sl-store-bar__seg {
        height: 100%;
        min-width: 2px;
    }
    .sl-store-chip {
        background: var(--surface-sunken);
    }
    .sl-store-chip--none {
        opacity: 0.75;
    }
    .sl-store-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
        flex: none;
    }
</style>
