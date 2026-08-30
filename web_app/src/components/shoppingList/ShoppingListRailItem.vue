<template>
    <q-item
        clickable
        :active="active"
        active-class="dora-bg-info-soft"
        class="rounded-borders sl-rail-item"
        :class="{ 'sl-rail-item-done': summary.status === 'done' }"
        @click="emit('select')"
    >
        <q-item-section avatar>
            <q-icon
                :name="statusIcon"
                :color="statusColour ?? undefined"
                :class="{ 'dora-text-muted': !statusColour }"
            />
        </q-item-section>
        <q-item-section class="sl-rail-item__main">
            <q-item-label class="row items-center q-gutter-x-xs no-wrap">
                <span class="ellipsis sl-rail-item__name">{{ summary.display_name }}</span>
                <q-badge
                    v-if="summary.is_next_up"
                    color="primary"
                    class="sl-rail-next-badge"
                >
                    next up
                </q-badge>
            </q-item-label>
            <!-- A draft can't have ticks any more, so "0/5 ticked" there was
                 a progress reading that could only ever say zero. Drafts get a
                 plain count; a list being shopped or finished keeps the ratio,
                 where it's real. -->
            <q-item-label caption>
                {{ effectiveDateLabel }} ·
                <template v-if="summary.status === 'draft'">
                    {{ summary.line_count }} item{{ summary.line_count === 1 ? '' : 's' }}
                </template>
                <template v-else>
                    {{ summary.ticked_count }}/{{ summary.line_count }} ticked
                </template>
            </q-item-label>
        </q-item-section>
    </q-item>
</template>

<script lang="ts" setup>
    /**
     * One row of the shopping-lists rail / mobile dropdown (UX-v2 §3.1):
     * status icon, server-resolved display name, "next up" marker, and the
     * effective date the continuum is ordered by.
     *
     * The kebab is gone (2026-08-28). It carried copy-to-new and delete, and
     * both were already reachable from the list you're looking at — so it put
     * two uncommon, one of them destructive, actions on every row of a picker
     * whose only job is "take me to that list". Copy went entirely: **Save as
     * template** is the same idea with a better name, and the rest of the app
     * had no second way to copy a list you weren't looking at. Delete stayed
     * on the open list's footer, where you can see what you're deleting.
     */
    import { ICONS } from 'src/style/icons';
    import { formatDate as formatLocaleDate } from 'src/composables/useDateFormat';
    import type { ShoppingListSummary } from 'src/models/shoppingList';
    import { computed } from 'vue';

    const props = defineProps<{
        summary: ShoppingListSummary;
        active: boolean;
    }>();

    const emit = defineEmits<{ select: [] }>();

    const statusIcon = computed(() => {
        switch (props.summary.status) {
            case 'shopping':
                return ICONS.shopping_cart_checkout;
            case 'done':
                return ICONS.check_circle;
            default:
                return ICONS.list;
        }
    });
    // R-002: "done" is the neutral / finished state — null lets the
    // template apply `dora-text-muted` rather than a `grey-N` literal.
    const statusColour = computed<string | null>(() => {
        switch (props.summary.status) {
            case 'shopping':
                return 'positive';
            case 'done':
                return null;
            default:
                return 'primary';
        }
    });

    const effectiveDateLabel = computed(() => {
        try {
            return formatLocaleDate(`${props.summary.effective_date}T00:00:00`);
        } catch {
            return props.summary.effective_date;
        }
    });
</script>

<style scoped>
    /* The row truncates its own name rather than relying on whatever contains
       it. It used to sit in a width-pinned `q-virtual-scroll`; that scroller was
       removed on 2026-08-28 so the rail could size to its contents, and without
       it the names were hard-clipped by the rail's `overflow-x` instead of
       ellipsised — the flex chain defaults to `min-width: auto`, so nothing
       agreed to shrink and `.ellipsis` had no width to work against. Owning it
       here means the row behaves the same in the rail, the mobile dropdown and
       the "See older" dialog. */
    /* Every link in the chain, because one `min-width: 0` in the middle does
       nothing while the ends still refuse to shrink. Measured at 1280px inside
       the 300px rail before the fix: the `q-item` root was 433px and the name
       span 341px, both still `min-width: auto`, so the row overflowed and was
       hard-clipped by the rail's `overflow-x` rather than ellipsised. */
    .sl-rail-item {
        min-width: 0;
        max-width: 100%;
    }
    .sl-rail-item__main {
        min-width: 0;
    }
    .sl-rail-item__main :deep(.q-item__label) {
        min-width: 0;
    }
    .sl-rail-item__name {
        min-width: 0;
    }
    .sl-rail-item-done {
        opacity: 0.6;
    }
    .sl-rail-next-badge {
        font-size: 0.65rem;
    }
</style>
