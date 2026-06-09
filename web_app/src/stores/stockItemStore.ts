import { acceptHMRUpdate, defineStore } from 'pinia';
import { notifyUndoable } from 'src/composables/useNotifyUndoable';
import {
    tryWithQueue,
    type QueueableMutationKind,
} from 'src/composables/useOfflineQueue';
import { register as registerUndo } from 'src/composables/useUndo';
import type { StockItem } from 'src/models/stockItem';
import { resolveBaseURL } from 'src/services/api/axiosHttpClient';
import type {
    CreateStockItemCommand,
    RestoreStockItemCommand,
    UpdateStockItemCommand
} from 'src/services/api/stockItemApiService';
import StockItemApiService from 'src/services/api/stockItemApiService';
import { clearRollbacks, registerRollback } from 'src/services/errorHandling/rollbackRegistry';
import type { Ref } from 'vue';
import { readonly, ref } from 'vue';

const stockItemApiService = new StockItemApiService();

function stockItemUrl(stockItemId: string): string {
    return `${resolveBaseURL('dora')}/stock-items/${stockItemId}`;
}

// Pick the queue kind that best describes a PATCH payload, so the queued
// label / drain notification reads naturally ("Marked restocked" vs
// "Push expiry" vs the catch-all). Falls back to generic stock_level_update.
function classifyUpdate(cmd: UpdateStockItemCommand): {
    kind: QueueableMutationKind;
    label: string;
} {
    if ('expiry_date' in cmd) {
        if (cmd.expiry_date === null) return { kind: 'clear_expiry', label: 'Clear expiry' };
        return { kind: 'push_expiry', label: 'Push expiry' };
    }
    if ('is_open' in cmd) return { kind: 'mark_open', label: 'Mark opened' };
    if ('stock_level_id' in cmd) {
        return { kind: 'stock_level_update', label: 'Update stock level' };
    }
    return { kind: 'stock_level_update', label: 'Update stock item' };
}

export const useStockItemStore = defineStore('stockItem', () => {
    const stockItems: Ref<StockItem[]> = ref([]);
    const collator = new Intl.Collator('en', { sensitivity: 'base' });

    /** C-1 Stock Overview Chunk 1 — page until exhausted so a pantry of
     *  >50 items doesn't silently get truncated to the first page
     *  (FU-035). Callers that only need a quick prefix (autocomplete-
     *  style) should hit `getAllAsync` on the service directly. */
    const getStockItemsAsync = () =>
        stockItemApiService.getAllPagesAsync().then((items) => {
            stockItems.value = [...items].sort((si1, si2) =>
                collator.compare(si1.name, si2.name)
            );
        });

    const createStockItemAsync = async (stockItemToCreate: CreateStockItemCommand) => {
        const created = await stockItemApiService.createAsync(stockItemToCreate);
        // The API returns the full DTO body when available.
        const entity =
            'stock_item_id' in created
                ? (created as unknown as StockItem)
                : await stockItemApiService.getAsync(created.id as string);
        stockItems.value.push(entity);
        stockItems.value.sort((a, b) => collator.compare(a.name, b.name));
    };

    /** Optimistic stock-level swap with rollback if the API rejects.
     *  Network failures are absorbed into the offline queue so the user
     *  can keep ticking the kitchen over without internet.
     *  Registers a quiet undo entry (no toast) so the header Undo button
     *  / Ctrl-Z can roll the level back. */
    async function updateStockLevelAsync(stockItemToUpdate: UpdateStockItemCommand) {
        const stockItemIndex = stockItems.value.findIndex(
            (si) => si.stock_item_id == stockItemToUpdate.stock_item_id
        );
        if (stockItemIndex < 0) return;

        const originalStockLevel = stockItems.value[stockItemIndex]!.stock_level_id;
        const nextStockLevel = stockItemToUpdate.stock_level_id!;
        const itemName = stockItems.value[stockItemIndex]!.name;
        stockItems.value[stockItemIndex]!.stock_level_id = nextStockLevel;

        registerRollback(() => {
            stockItems.value[stockItemIndex]!.stock_level_id = originalStockLevel;
        });

        const { stock_item_id, ...payload } = stockItemToUpdate;
        const result = await tryWithQueue(
            () => stockItemApiService.updateAsync(stockItemToUpdate),
            {
                url: stockItemUrl(stock_item_id),
                method: 'PATCH',
                body: payload,
                kind: 'stock_level_update',
                label: 'Update stock level',
            },
        );
        // Online path: refetch the canonical row so any server-derived
        // fields (timestamps, normalised values) are picked up. Offline
        // path: trust the optimistic value until the queue drains.
        if (typeof result !== 'object' || result === null || !('queued' in result)) {
            stockItems.value[stockItemIndex] = await stockItemApiService.getAsync(stock_item_id);
        }
        clearRollbacks();

        // F5: register a silent undo entry (no toast — cart-button level
        // bumps already toast and we don't want two). The Undo button /
        // Ctrl-Z surface it. Skip when the swap was a no-op.
        //
        // The inverse / redo call the underlying API service directly
        // (rather than recursing through `updateStockLevelAsync`) so
        // pressing Undo doesn't itself spawn another undo entry.
        if (originalStockLevel !== nextStockLevel) {
            const applyLevel = async (levelId: string) => {
                await stockItemApiService.updateAsync({
                    stock_item_id,
                    stock_level_id: levelId,
                });
                const idx = stockItems.value.findIndex(
                    (si) => si.stock_item_id === stock_item_id,
                );
                if (idx >= 0) {
                    stockItems.value[idx]!.stock_level_id = levelId;
                }
            };
            registerUndo({
                label: `Stock level: ${itemName}`,
                inverse: () => applyLevel(originalStockLevel),
                redo: () => applyLevel(nextStockLevel),
            });
        }
    }

    /** General-purpose update for the detail page (name/notes/location/etc).
     *  Same offline-queue treatment as the level swap above for the kinds
     *  registered (mark opened/restocked, push/clear expiry).
     *  Registers a silent undo entry covering whichever scalar fields
     *  were changed (we snapshot the pre-state of any field in `cmd`). */
    const updateStockItemAsync = async (cmd: UpdateStockItemCommand) => {
        const { stock_item_id, ...payload } = cmd;
        const { kind, label } = classifyUpdate(cmd);
        // Snapshot the fields we're about to overwrite, so undo can
        // restore them. Field-by-field (instead of cloning the whole
        // item) keeps the inverse payload narrow — no risk of
        // accidentally reverting unrelated changes that landed since.
        const before = stockItems.value.find((si) => si.stock_item_id === stock_item_id);
        const inverseFields: Record<string, unknown> = {};
        const redoFields: Record<string, unknown> = {};
        if (before) {
            for (const key of Object.keys(payload) as (keyof typeof payload)[]) {
                inverseFields[key as string] = before[key as keyof StockItem] ?? null;
                redoFields[key as string] = payload[key];
            }
        }
        const result = await tryWithQueue(
            () => stockItemApiService.updateAsync(cmd),
            {
                url: stockItemUrl(stock_item_id),
                method: 'PATCH',
                body: payload,
                kind,
                label,
            },
        );
        if (typeof result === 'object' && result !== null && 'queued' in result) {
            // Optimistic only — caller's UI already reflects intent; we
            // don't have a canonical refresh until the queue drains.
            return;
        }
        const refreshed = await stockItemApiService.getAsync(stock_item_id);
        const idx = stockItems.value.findIndex((si) => si.stock_item_id === stock_item_id);
        if (idx >= 0) {
            stockItems.value[idx] = refreshed;
            stockItems.value.sort((a, b) => collator.compare(a.name, b.name));
        }
        // F5: only register when there was something to roll back. Skip
        // when the field set was empty (defensive) or the values matched.
        if (before && Object.keys(inverseFields).length > 0) {
            const applyFields = async (fields: Record<string, unknown>) => {
                await stockItemApiService.updateAsync({
                    stock_item_id,
                    ...fields,
                } as UpdateStockItemCommand);
                const refreshed = await stockItemApiService.getAsync(stock_item_id);
                const idx = stockItems.value.findIndex(
                    (si) => si.stock_item_id === stock_item_id,
                );
                if (idx >= 0) stockItems.value[idx] = refreshed;
            };
            registerUndo({
                label: `${label}: ${before.name}`,
                inverse: () => applyFields(inverseFields),
                redo: () => applyFields(redoFields),
            });
        }
    };

    /** Delete + queue an Undo via the snapshot/restore endpoint. The toast
     *  carries an inline Undo — and even after the toast disappears the
     *  entry is still on the global stack until 20 newer actions push it
     *  off. */
    const deleteStockItemAsync = async (stockItemID: string) => {
        const before = stockItems.value.find((si) => si.stock_item_id === stockItemID);
        await stockItemApiService.deleteAsync(stockItemID);
        stockItems.value = stockItems.value.filter((si) => si.stock_item_id !== stockItemID);
        if (!before) return;
        const snapshot: RestoreStockItemCommand = {
            stock_item_id: before.stock_item_id,
            name: before.name,
            stock_level_id: before.stock_level_id,
            stock_location_id: before.stock_location_id ?? null,
            stock_group_id: before.stock_group_id ?? null,
            expiry_date: before.expiry_date ?? null,
            is_flagged: before.is_flagged ?? false,
            auto_add_when_low: before.auto_add_when_low ?? false,
            is_open: before.is_open ?? false,
        };
        notifyUndoable({
            message: `Deleted "${before.name}".`,
            undo: {
                label: `Delete: ${before.name}`,
                inverse: async () => {
                    await stockItemApiService.restoreAsync(snapshot);
                    // Pull the row back into the store so it shows up
                    // immediately in lists / pickers.
                    const restored = await stockItemApiService.getAsync(
                        snapshot.stock_item_id,
                    );
                    stockItems.value.push(restored);
                    stockItems.value.sort((a, b) => collator.compare(a.name, b.name));
                },
                redo: async () => {
                    await stockItemApiService.deleteAsync(snapshot.stock_item_id);
                    stockItems.value = stockItems.value.filter(
                        (si) => si.stock_item_id !== snapshot.stock_item_id,
                    );
                },
            },
        });
    };

    return {
        stockItems: readonly(stockItems),
        getStockItemsAsync,
        createStockItemAsync,
        updateStockLevelAsync,
        updateStockItemAsync,
        deleteStockItemAsync
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useStockItemStore, import.meta.hot));
}
