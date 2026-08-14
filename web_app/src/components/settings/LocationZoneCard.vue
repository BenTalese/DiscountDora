<template>
    <section class="zone-card">
        <header class="zone-card__header">
            <BaseButton
                variant="icon"
                size="sm"
                :icon="expanded ? ICONS.expand_more : ICONS.chevron_right"
                :aria-label="`${expanded ? 'Collapse' : 'Expand'} ${node.name}`"
                :aria-expanded="expanded"
                @click="$emit('toggle', node.location_id)"
            />

            <button type="button" class="zone-card__identity" @click="$emit('toggle', node.location_id)">
                <q-icon :name="ICONS.place" size="18px" class="zone-card__icon" />
                <span class="zone-card__name">{{ node.name }}</span>
            </button>

            <span class="zone-card__meta">{{ filtered ? 'Matches only' : metaLabel }}</span>

            <div class="zone-card__actions">
                <BaseButton
                    variant="ghost"
                    :icon="ICONS.add"
                    label="Area"
                    size="sm"
                    @click="$emit('addChild', node)"
                />
                <BaseButton
                    variant="icon"
                    :icon="ICONS.more_vert"
                    :aria-label="`Actions for ${node.name}`"
                >
                    <q-menu auto-close anchor="bottom right" self="top right">
                        <q-list dense style="min-width: 180px">
                            <q-item
                                v-if="node.descendant_item_count > 0"
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
                </BaseButton>
            </div>
        </header>

        <div v-if="expanded" class="zone-card__body">
            <LocationAreaRow
                v-for="area in node.children"
                :key="area.location_id"
                :node="area"
                @rename="$emit('rename', $event)"
                @delete="$emit('delete', $event)"
                @add-child="$emit('addChild', $event)"
                @view-items="$emit('viewItems', $event)"
            />
            <p v-if="node.children.length === 0" class="zone-card__no-areas">
                Nothing inside {{ node.name }} yet — add an area if you want to break it up,
                or leave it flat and store items straight in the zone.
            </p>
        </div>
    </section>
</template>

<script lang="ts" setup>
    // A zone — the top level of the location tree — rendered as its own card
    // rather than as the first row of one long indented list.
    //
    // The tree is fixed at exactly three levels (zone → area → section), so
    // each level gets a visual that suits it: card, row, chip. Depth is then
    // carried by the container rather than by indent alone, which is what the
    // old uniform recursive row could never express — and it drops the grey
    // `zone`/`area`/`section` chip that used to repeat on every single row.
    import BaseButton from 'src/components/BaseButton.vue';
    import LocationAreaRow from 'src/components/settings/LocationAreaRow.vue';
    import { ICONS } from 'src/style/icons';
    import { computed } from 'vue';
    import type { LocationNode } from 'src/models/location';

    const props = defineProps<{
        node: LocationNode;
        expanded: boolean;
        // True when a search has narrowed this node's children. The item
        // counts are server-side rollups over the *whole* subtree (R-003 —
        // the client doesn't re-sum them), so alongside a filtered child list
        // they'd describe two different things. The card says so instead.
        filtered: boolean;
    }>();

    defineEmits<{
        (e: 'toggle', id: string): void;
        (e: 'rename', node: LocationNode): void;
        (e: 'delete', node: LocationNode): void;
        (e: 'addChild', parent: LocationNode): void;
        (e: 'viewItems', node: LocationNode): void;
    }>();

    const metaLabel = computed(() => {
        const areas = props.node.children.length;
        const items = props.node.descendant_item_count;
        const itemsLabel = items === 1 ? '1 item' : `${items} items`;
        // "0 areas · 9 items" reads like a defect; a flat zone is a perfectly
        // ordinary shape, so it just states what it holds.
        if (areas === 0) return itemsLabel;
        return `${areas === 1 ? '1 area' : `${areas} areas`} · ${itemsLabel}`;
    });
</script>

<style scoped lang="scss">
    .zone-card {
        background: var(--surface-component);
        border: 1px solid var(--border-default);
        border-radius: var(--radius-lg);
        box-shadow: var(--elevation-card);
        overflow: hidden;
    }
    .zone-card__header {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        padding: var(--space-3) var(--space-4);
    }
    .zone-card__identity {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        min-width: 0;
        padding: 0;
        border: 0;
        background: none;
        font: inherit;
        color: var(--text-primary);
        cursor: pointer;
        text-align: left;
    }
    .zone-card__identity:focus-visible {
        outline: 2px solid var(--focus-ring);
        outline-offset: 2px;
        border-radius: var(--radius-sm);
    }
    .zone-card__icon {
        color: var(--text-muted);
        flex: 0 0 auto;
    }
    .zone-card__name {
        font-size: 1rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .zone-card__meta {
        flex: 1 1 auto;
        min-width: 0;
        font-size: 0.8125rem;
        color: var(--text-muted);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .zone-card__actions {
        flex: 0 0 auto;
        display: flex;
        align-items: center;
        gap: var(--space-1);
    }
    .zone-card__body {
        display: flex;
        flex-direction: column;
    }
    .zone-card__no-areas {
        margin: 0;
        padding: var(--space-3) var(--space-4);
        border-top: 1px solid var(--divider);
        color: var(--text-muted);
        font-size: 0.8125rem;
        line-height: 1.5;
    }
    /* Phone: the meta line loses its inline slot so the zone name keeps the
       width, and the actions stay on the header line (D-011 — no wrapping
       toolbar, no truncated primary label). */
    @media (max-width: 599px) {
        .zone-card__header {
            flex-wrap: wrap;
        }
        .zone-card__meta {
            order: 10;
            flex-basis: 100%;
            padding-left: calc(var(--space-8) + var(--space-2));
        }
    }
</style>
