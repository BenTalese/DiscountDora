<template>
    <div class="area-row">
        <div class="area-row__main">
            <div class="area-row__heading">
                <span class="area-row__name">{{ node.name }}</span>
                <button
                    v-if="node.descendant_item_count > 0"
                    type="button"
                    class="area-row__count"
                    :aria-label="`View the ${node.descendant_item_count} items in ${node.name}`"
                    @click="$emit('viewItems', node)"
                >
                    {{ countLabel }}
                </button>
                <span v-else class="area-row__count area-row__count--empty">{{ countLabel }}</span>
            </div>

            <div class="area-row__sections">
                <LocationSectionChip
                    v-for="section in node.children"
                    :key="section.location_id"
                    :node="section"
                    @rename="$emit('rename', $event)"
                    @delete="$emit('delete', $event)"
                    @view-items="$emit('viewItems', $event)"
                />
                <button
                    type="button"
                    class="area-row__add-section"
                    @click="$emit('addChild', node)"
                >
                    <q-icon :name="ICONS.add" size="14px" />
                    <span>Section</span>
                </button>
            </div>
        </div>

        <BaseButton
            variant="icon"
            :icon="ICONS.more_vert"
            :aria-label="`Actions for ${node.name}`"
        >
            <q-menu auto-close anchor="bottom right" self="top right">
                <q-list dense style="min-width: 180px">
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
        </BaseButton>
    </div>
</template>

<script lang="ts" setup>
    // An area — the middle level of the location tree — rendered as a row
    // inside its zone's card, with its sections as inline chips.
    //
    // Areas are the only level that can be either a container or a leaf, so
    // this is the only level that renders a "+ Section" affordance inline:
    // an area with no sections still shows it, which is how you learn areas
    // can hold sections at all. (The old recursive row hid the add-child
    // control behind a hover tooltip and keyed its disclosure off
    // `children.length > 0`, so an empty container looked like a leaf.)
    import BaseButton from 'src/components/BaseButton.vue';
    import LocationSectionChip from 'src/components/settings/LocationSectionChip.vue';
    import { ICONS } from 'src/style/icons';
    import { computed } from 'vue';
    import type { LocationNode } from 'src/models/location';

    const props = defineProps<{ node: LocationNode }>();

    defineEmits<{
        (e: 'rename', node: LocationNode): void;
        (e: 'delete', node: LocationNode): void;
        (e: 'addChild', parent: LocationNode): void;
        (e: 'viewItems', node: LocationNode): void;
    }>();

    const countLabel = computed(() => {
        const direct = props.node.direct_item_count;
        const total = props.node.descendant_item_count;
        if (total === 0) return 'Empty';
        if (direct === total) return total === 1 ? '1 item' : `${total} items`;
        return `${direct} here · ${total} in total`;
    });
</script>

<style scoped lang="scss">
    .area-row {
        display: flex;
        align-items: flex-start;
        gap: var(--space-3);
        padding: var(--space-3) var(--space-4);
        border-top: 1px solid var(--divider);
    }
    .area-row__main {
        flex: 1 1 auto;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
    }
    .area-row__heading {
        display: flex;
        align-items: baseline;
        flex-wrap: wrap;
        gap: var(--space-2);
        min-width: 0;
    }
    .area-row__name {
        color: var(--text-primary);
        font-size: 0.9375rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .area-row__count {
        padding: 0;
        border: 0;
        background: none;
        font: inherit;
        font-size: 0.8125rem;
        color: var(--text-muted);
        cursor: pointer;
        text-decoration: underline;
        text-decoration-color: transparent;
        text-underline-offset: 3px;
        transition: text-decoration-color var(--motion-fast, 120ms) ease;
    }
    .area-row__count:hover {
        text-decoration-color: currentcolor;
    }
    .area-row__count:focus-visible {
        outline: 2px solid var(--focus-ring);
        outline-offset: 2px;
        border-radius: var(--radius-sm);
    }
    .area-row__count--empty {
        cursor: default;
        text-decoration: none;
    }
    .area-row__sections {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: var(--space-2);
    }
    .area-row__add-section {
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        padding: var(--space-1) var(--space-3);
        border: 1px dashed var(--border-default);
        border-radius: var(--radius-sm);
        background: none;
        font: inherit;
        font-size: 0.8125rem;
        line-height: 1.4;
        color: var(--text-muted);
        cursor: pointer;
        transition: color var(--motion-fast, 120ms) ease,
            border-color var(--motion-fast, 120ms) ease;
    }
    .area-row__add-section:hover {
        color: var(--text-secondary);
        border-color: var(--border-strong);
    }
    .area-row__add-section:focus-visible {
        outline: 2px solid var(--focus-ring);
        outline-offset: 2px;
    }
    @media (pointer: coarse) {
        .area-row__add-section {
            min-height: 44px;
            padding-inline: var(--space-4);
        }
    }
</style>
