<template>
    <button
        type="button"
        class="section-chip"
        :aria-label="`${node.name}, ${countLabel}. Open actions.`"
    >
        <span class="section-chip__name">{{ node.name }}</span>
        <span class="section-chip__count">{{ node.direct_item_count }}</span>

        <q-menu auto-close anchor="bottom left" self="top left">
            <q-list dense style="min-width: 180px">
                <q-item-label header>{{ node.name }}</q-item-label>
                <q-item
                    v-if="node.direct_item_count > 0"
                    v-close-popup
                    clickable
                    @click="$emit('viewItems', node)"
                >
                    <q-item-section avatar>
                        <q-icon :name="ICONS.inventory_2" size="18px" />
                    </q-item-section>
                    <q-item-section>View items</q-item-section>
                </q-item>
                <q-item v-close-popup clickable @click="$emit('rename', node)">
                    <q-item-section avatar>
                        <q-icon :name="ICONS.edit" size="18px" />
                    </q-item-section>
                    <q-item-section>Rename</q-item-section>
                </q-item>
                <q-item v-close-popup clickable @click="$emit('delete', node)">
                    <q-item-section avatar>
                        <q-icon :name="ICONS.delete_outline" size="18px" color="negative" />
                    </q-item-section>
                    <q-item-section class="text-negative">Delete</q-item-section>
                </q-item>
            </q-list>
        </q-menu>
    </button>
</template>

<script lang="ts" setup>
    // A section — the third and last level of the location tree — rendered as
    // an inline chip under its area rather than as another indented row.
    //
    // Sections are always leaves (the tree is fixed at zone → area → section),
    // so they never need a disclosure, and there is nothing to show but a name
    // and a count. Chips let a whole area's sections read in one line instead
    // of N rows of mostly-empty width.
    import { ICONS } from 'src/style/icons';
    import { computed } from 'vue';
    import type { LocationNode } from 'src/models/location';

    const props = defineProps<{ node: LocationNode }>();

    defineEmits<{
        (e: 'rename', node: LocationNode): void;
        (e: 'delete', node: LocationNode): void;
        (e: 'viewItems', node: LocationNode): void;
    }>();

    const countLabel = computed(() => {
        const count = props.node.direct_item_count;
        return count === 1 ? '1 item' : `${count} items`;
    });
</script>

<style scoped lang="scss">
    .section-chip {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        padding: var(--space-1) var(--space-3);
        border: 1px solid transparent;
        border-radius: var(--radius-sm);
        background: var(--surface-sunken);
        color: var(--text-secondary);
        font: inherit;
        font-size: 0.8125rem;
        line-height: 1.4;
        cursor: pointer;
        transition: background-color var(--motion-fast, 120ms) ease,
            border-color var(--motion-fast, 120ms) ease;
    }
    .section-chip:hover {
        border-color: var(--border-strong);
    }
    .section-chip:focus-visible {
        outline: 2px solid var(--focus-ring);
        outline-offset: 2px;
    }
    .section-chip__name {
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        max-width: 22ch;
    }
    .section-chip__count {
        color: var(--text-muted);
        font-variant-numeric: tabular-nums;
    }
    /* D-004 — chips are real controls here (they open the actions menu), so
       they carry a touch target on coarse pointers rather than chip density. */
    @media (pointer: coarse) {
        .section-chip {
            min-height: 44px;
            padding-inline: var(--space-4);
        }
    }
</style>
