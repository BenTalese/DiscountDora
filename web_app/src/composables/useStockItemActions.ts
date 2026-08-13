import { storeToRefs } from 'pinia';
import { useQuasar } from 'quasar';
import MarkOpenExpiryDialog from 'src/components/stock/MarkOpenExpiryDialog.vue';
import {
    buildOpenTogglePatch,
    type OpenExpiryDecision,
    type OpenToggleTarget,
    type OpenTogglePatch,
} from 'src/composables/openToggle';
import { invalidateBuyVerdict } from 'src/composables/useBuyVerdict';
import ShoppingListApiService from 'src/services/api/shoppingListApiService';
import { useShoppingListStore } from 'src/stores/shoppingListStore';
import { useStockItemStore } from 'src/stores/stockItemStore';
import { useStockLevelStore } from 'src/stores/stockLevelStore';
import { useRouter } from 'vue-router';

const shoppingListApi = new ShoppingListApiService();

/**
 * Cross-feature actions for a single stock item. Every screen that touches a
 * stock item routes through here so add-to-list / restock / expiry behave the
 * same everywhere (chips, bulk bars, detail toolbar, Dora quick-actions).
 *
 * Call from a component `setup` — it relies on the active router and Quasar
 * plugin for navigation and notifications.
 */
export function useStockItemActions() {
    const $q = useQuasar();
    const router = useRouter();
    const stockItemStore = useStockItemStore();
    const shoppingListStore = useShoppingListStore();
    const stockLevelStore = useStockLevelStore();
    const { stockLevels } = storeToRefs(stockLevelStore);

    // resolve a shopping list's display name from the store's
    // hydrated summaries. Falls back to a generic label so we never
    // render an obviously-broken toast if the store isn't loaded yet.
    function listNameFor(listId: string): string {
        const summary = shoppingListStore.summaries.find(
            (s) => s.shopping_list_id === listId,
        );
        return summary?.display_name ?? 'your list';
    }

    const notifyOk = (message: string) =>
        $q.notify({ type: 'positive', position: 'bottom-right', message });
    const notifyErr = (message: string, caption?: string) =>
        $q.notify({
            type: 'negative',
            position: 'bottom-right',
            message,
            ...(caption ? { caption } : {}),
        });

    /** Add to a specific list, or resolve the quick-add target. When more than
     *  one draft list exists Dora always asks which one — the pick is never
     *  remembered across separate adds (owner call 2026-08-13: multiple lists
     *  are deliberate, so silently reusing the last pick was more annoying than
     *  helpful). `no_draft` opens the lists overview to create one.
     *
     *  Returns the shopping-list id the item landed on, or `null` when nothing
     *  was added (no draft, or the user cancelled the picker). A bulk caller
     *  uses the return value to batch the remaining items into the same list. */
    async function addToList(
        stockItemId: string,
        listId?: string | null,
        options?: { silent?: boolean },
    ): Promise<string | null> {
        // callers running this in a bulk loop pass silent:true and
        // emit one summary toast themselves instead of N per-item ones.
        const silent = options?.silent ?? false;
        const ok = (msg: string) => { if (!silent) notifyOk(msg); };
        const err = (msg: string, caption?: string) => { if (!silent) notifyErr(msg, caption); };
        try {
            if (listId) {
                const result = await shoppingListApi.addLineAsync(listId, {
                    stock_item_id: stockItemId,
                });
                await shoppingListStore.refreshAsync();
                // FU-572: list membership flips the verdict's one-tap action.
                invalidateBuyVerdict(stockItemId);
                ok(
                    result.already_on_list
                        ? `Already on ${listNameFor(listId)}.`
                        : `Added to ${listNameFor(listId)}.`,
                );
                return listId;
            }
            // No explicit list — resolve the quick-add target. We never send a
            // remembered hint, so with 2+ drafts the server replies `ambiguous`
            // and we always ask which list.
            let outcome = await shoppingListApi.quickAddToPrimaryAsync(stockItemId);
            if (outcome.result === 'no_draft') {
                $q.dialog({
                    title: 'No draft list',
                    message:
                        'You have no draft shopping list. Create one to use the cart shortcut.',
                    ok: { label: 'Open lists', noCaps: true, color: 'primary' },
                    cancel: { noCaps: true },
                }).onOk(() => void router.push('/shopping-lists'));
                return null;
            }
            if (outcome.result === 'ambiguous') {
                const choice = await new Promise<string | null>((resolve) => {
                    $q.dialog({
                        title: 'Which list?',
                        message: 'You have multiple draft lists — pick one.',
                        options: {
                            type: 'radio',
                            model: outcome.result === 'ambiguous'
                                ? outcome.candidates[0]?.shopping_list_id ?? ''
                                : '',
                            items: outcome.result === 'ambiguous'
                                ? outcome.candidates.map((c) => ({
                                      label: c.name,
                                      value: c.shopping_list_id,
                                  }))
                                : [],
                        },
                        cancel: { noCaps: true },
                        persistent: false,
                    })
                        .onOk((val: string) => resolve(val))
                        .onCancel(() => resolve(null))
                        .onDismiss(() => resolve(null));
                });
                if (!choice) return null;
                outcome = await shoppingListApi.quickAddToPrimaryAsync(stockItemId, choice);
                if (outcome.result !== 'added') {
                    err('Could not add to the chosen list.');
                    return null;
                }
            }
            await shoppingListStore.refreshAsync();
            if (outcome.result === 'added') {
                // FU-572: list membership flips the verdict's one-tap action.
                invalidateBuyVerdict(stockItemId);
                const listName = listNameFor(outcome.shopping_list_id);
                ok(
                    outcome.already_on_list
                        ? `Already on ${listName}.`
                        : `Added to ${listName}.`,
                );
                return outcome.shopping_list_id;
            }
            return null;
        } catch (e) {
            err('Could not add to list.', String(e));
            return null;
        }
    }

    /** Bump the level back to the most-stocked level (lowest sequence). */
    async function markRestocked(stockItemId: string, options?: { silent?: boolean }) {
        const silent = options?.silent ?? false;
        const top = stockLevels.value[0];
        if (!top) {
            if (!silent) notifyErr('No stock levels configured.');
            return;
        }
        try {
            await stockItemStore.updateStockLevelAsync({
                stock_item_id: stockItemId,
                stock_level_id: top.stock_level_id,
            });
            // FU-572: the level feeds the verdict's need axis.
            invalidateBuyVerdict(stockItemId);
            if (!silent) notifyOk('Marked restocked.');
        } catch (err) {
            if (!silent) notifyErr('Could not restock.', String(err));
        }
    }

    /** Push the expiry date forward by `days`. FU-123: pushes from
     *  `max(today, current expiry)` so the natural read of "+1 day" on
     *  an existing expiry actually shifts that expiry by a day, while
     *  long-stale items don't end up with a "+1 = yesterday" result.
     *  When no expiry is set yet, falls back to today + days. */
    async function pushExpiry(stockItemId: string, days = 7) {
        const current = stockItemStore.stockItems.find(
            (si) => si.stock_item_id === stockItemId,
        )?.expiry_date ?? null;
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const base = (() => {
            if (!current) return today;
            const parsed = new Date(`${current}T00:00:00`);
            if (Number.isNaN(parsed.getTime())) return today;
            return parsed.getTime() > today.getTime() ? parsed : today;
        })();
        base.setDate(base.getDate() + days);
        const iso = `${base.getFullYear()}-${String(base.getMonth() + 1).padStart(2, '0')}-${String(base.getDate()).padStart(2, '0')}`;
        try {
            await stockItemStore.updateStockItemAsync({
                stock_item_id: stockItemId,
                expiry_date: iso,
            });
            notifyOk(`Expiry pushed to ${iso}.`);
        } catch (err) {
            notifyErr('Could not update expiry.', String(err));
        }
    }

    /**
     * DR-5 (FU-578 #2) — plan an open/seal toggle. Sealing returns its patch
     * immediately; opening first prompts for the effective expiry via
     * {@link MarkOpenExpiryDialog}. Returns the PATCH body to send, or `null`
     * when the user dismissed/cancelled the prompt — in which case the caller
     * performs NO mutation (server state stays untouched). Callers own the
     * actual write + any toast, since the row and detail page mutate
     * differently (direct vs. busy-reload).
     */
    async function planOpenToggle(target: OpenToggleTarget): Promise<OpenTogglePatch | null> {
        const opening = !target.is_open;
        if (!opening) return buildOpenTogglePatch(target, null); // seal, no prompt
        const decision = await new Promise<OpenExpiryDecision>((resolve) => {
            $q.dialog({
                component: MarkOpenExpiryDialog,
                componentProps: {
                    itemName: target.name,
                    currentExpiry: target.expiry_date ?? '',
                },
            })
                // Skip / Update → confirmed open (with/without expiry).
                .onOk((payload: { expiry: string | null | undefined }) =>
                    resolve({ open: true, expiry: payload.expiry }),
                )
                // Cancel button, and Escape/backdrop (onDismiss) → abort. Both
                // resolve false; Promise.resolve is idempotent so whichever
                // fires first for a given close wins.
                .onCancel(() => resolve({ open: false }))
                .onDismiss(() => resolve({ open: false }));
        });
        return buildOpenTogglePatch(target, decision);
    }

    function openDetail(stockItemId: string) {
        void router.push(`/stock/${stockItemId}`);
    }

    /** A stock item's substitutes live on its detail page (built in P2). */
    function findSubstitutes(stockItemId: string) {
        void router.push({ path: `/stock/${stockItemId}`, query: { section: 'substitutes' } });
    }

    /** Recipes that use this item — opens the recipes screen pre-filtered. */
    function seeRecipesUsing(stockItemId: string) {
        void router.push({ path: '/cookbook', query: { usesStockItem: stockItemId } });
    }

    return {
        addToList,
        markRestocked,
        pushExpiry,
        planOpenToggle,
        openDetail,
        findSubstitutes,
        seeRecipesUsing,
    };
}
