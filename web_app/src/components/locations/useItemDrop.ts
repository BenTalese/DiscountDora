// Tiny composable that wires HTML5 dragenter/over/leave/drop events for a
// location node to accept dropped stock-item chips. Keeps the LocationDetail
// template lean and the move logic in one place.
import { Notify } from 'quasar';
import StockItemApiService from 'src/services/api/stockItemApiService';
import { useLocationStore } from 'src/stores/locationStore';
import { ref } from 'vue';

export type DroppedItemPayload = {
    stock_item_id: string;
    source_location_id: string | null;
    name: string;
};

const MIME = 'application/x-dora-stock-item';

export function useItemDrop() {
    const locationStore = useLocationStore();
    const stockItemApi = new StockItemApiService();

    // Tracks which location id is currently being dragged over so the UI can
    // apply a highlight ring without leaking it across siblings.
    const hoveringLocationId = ref<string | null>(null);

    function onDragEnter(event: DragEvent, locationId: string) {
        if (!event.dataTransfer?.types.includes(MIME)) return;
        event.preventDefault();
        hoveringLocationId.value = locationId;
    }

    function onDragOver(event: DragEvent, locationId: string) {
        if (!event.dataTransfer?.types.includes(MIME)) return;
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
        hoveringLocationId.value = locationId;
    }

    function onDragLeave(_event: DragEvent, locationId: string) {
        if (hoveringLocationId.value === locationId) {
            hoveringLocationId.value = null;
        }
    }

    async function onDrop(event: DragEvent, locationId: string) {
        hoveringLocationId.value = null;
        const raw = event.dataTransfer?.getData(MIME);
        if (!raw) return;
        event.preventDefault();
        let payload: DroppedItemPayload;
        try {
            payload = JSON.parse(raw) as DroppedItemPayload;
        } catch {
            return;
        }

        // No-op when dropped on the source location.
        if (payload.source_location_id === locationId) return;

        try {
            await stockItemApi.moveAsync(payload.stock_item_id, locationId);
            Notify.create({
                type: 'positive',
                position: 'bottom-right',
                message: `Moved "${payload.name}".`
            });
            await locationStore.refreshAsync();
        } catch (err) {
            Notify.create({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not move the item.',
                caption: String(err)
            });
        }
    }

    return {
        hoveringLocationId,
        onDragEnter,
        onDragOver,
        onDragLeave,
        onDrop
    };
}
