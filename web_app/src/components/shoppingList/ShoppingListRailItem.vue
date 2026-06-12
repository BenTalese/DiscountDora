<template>
    <q-item
        clickable
        :active="active"
        active-class="dora-bg-info-soft"
        class="rounded-borders"
        :class="{ 'sl-rail-item-done': summary.status === 'done' }"
        @click="emit('select')"
    >
        <q-item-section avatar>
            <q-icon :name="statusIcon" :color="statusColour" />
        </q-item-section>
        <q-item-section>
            <q-item-label class="row items-center q-gutter-x-xs no-wrap">
                <span class="ellipsis">{{ summary.display_name }}</span>
                <q-badge
                    v-if="summary.is_next_up"
                    color="primary"
                    class="sl-rail-next-badge"
                >
                    next up
                </q-badge>
            </q-item-label>
            <q-item-label caption>
                {{ effectiveDateLabel }} ·
                {{ summary.ticked_count }}/{{ summary.line_count }} ticked
            </q-item-label>
        </q-item-section>
        <q-item-section side @click.stop>
            <q-btn flat round dense size="sm" :icon="ICONS.more_vert" aria-label="List actions">
                <q-menu auto-close anchor="bottom right" self="top right">
                    <q-list dense style="min-width: 200px">
                        <q-item
                            v-if="summary.status === 'done'"
                            clickable
                            @click.stop="emit('copy', 'all')"
                        >
                            <q-item-section avatar><q-icon :name="ICONS.content_copy" /></q-item-section>
                            <q-item-section>Copy to new list</q-item-section>
                        </q-item>
                        <q-item
                            v-else
                            clickable
                            :disable="summary.line_count - summary.ticked_count === 0"
                            @click.stop="emit('copy', 'unticked')"
                        >
                            <q-item-section avatar><q-icon :name="ICONS.content_copy" /></q-item-section>
                            <q-item-section>Copy unticked → new</q-item-section>
                        </q-item>
                        <q-item clickable @click.stop="emit('delete')">
                            <q-item-section avatar><q-icon :name="ICONS.delete" color="negative" /></q-item-section>
                            <q-item-section class="text-negative">Delete list</q-item-section>
                        </q-item>
                    </q-list>
                </q-menu>
            </q-btn>
        </q-item-section>
    </q-item>
</template>

<script lang="ts" setup>
    /**
     * One row of the shopping-lists rail / mobile dropdown (UX-v2 §3.1):
     * status icon, server-resolved display name, "next up" marker, the
     * effective date the continuum is ordered by, and the rare per-list
     * housekeeping (copy / delete) behind a kebab. "Archive" was removed
     * deliberately — lists are finished or deleted (§12 Q2).
     */
    import { ICONS } from 'src/style/icons';
    import type { ShoppingListSummary } from 'src/models/shoppingList';
    import { computed } from 'vue';

    const props = defineProps<{
        summary: ShoppingListSummary;
        active: boolean;
    }>();

    const emit = defineEmits<{
        select: [];
        copy: [include: 'all' | 'unticked'];
        delete: [];
    }>();

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
    const statusColour = computed(() => {
        switch (props.summary.status) {
            case 'shopping':
                return 'positive';
            case 'done':
                return 'grey-6';
            default:
                return 'primary';
        }
    });

    const effectiveDateLabel = computed(() => {
        try {
            return new Date(`${props.summary.effective_date}T00:00:00`).toLocaleDateString();
        } catch {
            return props.summary.effective_date;
        }
    });
</script>

<style scoped>
    .sl-rail-item-done {
        opacity: 0.6;
    }
    .sl-rail-next-badge {
        font-size: 0.65rem;
    }
</style>
