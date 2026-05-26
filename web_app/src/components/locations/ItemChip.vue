<template>
    <q-chip
        clickable
        square
        :color="chipColor"
        :text-color="chipTextColor"
        class="item-chip"
        :class="{ 'item-chip-dragging': dragging }"
        draggable="true"
        @click="emit('click')"
        @dragstart="onDragStart"
        @dragend="onDragEnd"
    >
        <q-avatar v-if="item.is_flagged" color="amber-10" text-color="white">
            <q-icon name="flag" size="14px" />
        </q-avatar>
        <q-icon name="drag_indicator" size="14px" class="q-mr-xs drag-handle" />
        <span>{{ item.name }}</span>
        <q-badge
            v-if="item.attention_score > 0"
            :color="attentionColor(item.attention_score)"
            class="q-ml-xs"
        >
            {{ item.attention_score }}
        </q-badge>
        <q-btn
            flat
            round
            dense
            icon="drive_file_move"
            size="sm"
            class="q-ml-xs"
            @click.stop="emit('move')"
        >
            <q-tooltip>Move</q-tooltip>
        </q-btn>
        <q-btn
            flat
            round
            dense
            icon="more_vert"
            size="sm"
            class="q-ml-xs"
            @click.stop
        >
            <q-menu auto-close>
                <q-list dense style="min-width: 200px">
                    <q-item
                        clickable
                        @click="actions.addToList(item.stock_item_id)"
                    >
                        <q-item-section avatar>
                            <q-icon name="add_shopping_cart" />
                        </q-item-section>
                        <q-item-section>Add to primary list</q-item-section>
                    </q-item>
                    <q-item
                        clickable
                        @click="actions.markRestocked(item.stock_item_id)"
                    >
                        <q-item-section avatar>
                            <q-icon name="refresh" />
                        </q-item-section>
                        <q-item-section>Mark restocked</q-item-section>
                    </q-item>
                    <q-item
                        clickable
                        @click="actions.pushExpiry(item.stock_item_id)"
                    >
                        <q-item-section avatar>
                            <q-icon name="event" />
                        </q-item-section>
                        <q-item-section>Push expiry +7 days</q-item-section>
                    </q-item>
                    <q-separator />
                    <q-item
                        clickable
                        @click="actions.findSubstitutes(item.stock_item_id)"
                    >
                        <q-item-section avatar>
                            <q-icon name="swap_horiz" />
                        </q-item-section>
                        <q-item-section>Find substitutes</q-item-section>
                    </q-item>
                    <q-item
                        clickable
                        @click="actions.seeRecipesUsing(item.stock_item_id)"
                    >
                        <q-item-section avatar>
                            <q-icon name="menu_book" />
                        </q-item-section>
                        <q-item-section>See recipes using this</q-item-section>
                    </q-item>
                    <q-separator />
                    <q-item
                        clickable
                        @click="actions.openDetail(item.stock_item_id)"
                    >
                        <q-item-section avatar>
                            <q-icon name="open_in_new" />
                        </q-item-section>
                        <q-item-section>Open detail</q-item-section>
                    </q-item>
                </q-list>
            </q-menu>
        </q-btn>
        <q-tooltip v-if="tooltip" anchor="top middle" self="bottom middle">
            {{ tooltip }}
        </q-tooltip>
    </q-chip>
</template>

<script lang="ts" setup>
    import { useStockItemActions } from 'src/composables/useStockItemActions';
    import { attentionColor, summarizeReasons, type LocationItem } from 'src/models/location';
    import { computed, ref } from 'vue';

    const actions = useStockItemActions();

    const props = defineProps<{ item: LocationItem; currentLocationId?: string | null }>();
    const emit = defineEmits<{
        (e: 'click'): void;
        (e: 'move'): void;
    }>();

    const dragging = ref(false);

    const chipColor = computed(() => {
        if (props.item.attention_score >= 41) return 'white';
        return 'grey-2';
    });
    const chipTextColor = computed(() =>
        props.item.attention_score >= 81 ? 'red-9' : 'grey-10'
    );

    const tooltip = computed(() => {
        const parts = summarizeReasons(props.item.attention_reasons);
        if (parts.length === 0 && !props.item.expiry_date) return null;
        const expiry = props.item.expiry_date ? `Expires ${props.item.expiry_date}` : null;
        return [expiry, ...parts].filter(Boolean).join(' · ');
    });

    function onDragStart(event: DragEvent) {
        if (!event.dataTransfer) return;
        // Custom mime type so we only accept our own chips on drop — pages
        // listening for the default text/plain wouldn't accidentally treat a
        // dropped chip as text.
        event.dataTransfer.setData(
            'application/x-dora-stock-item',
            JSON.stringify({
                stock_item_id: props.item.stock_item_id,
                source_location_id: props.currentLocationId ?? null,
                name: props.item.name
            })
        );
        event.dataTransfer.effectAllowed = 'move';
        dragging.value = true;
    }

    function onDragEnd() {
        dragging.value = false;
    }
</script>

<style scoped>
    .item-chip {
        border: 1px solid var(--overlay-active);
        cursor: grab;
    }
    .item-chip:active {
        cursor: grabbing;
    }
    .item-chip-dragging {
        opacity: 0.4;
    }
    .drag-handle {
        opacity: 0.45;
    }
</style>
