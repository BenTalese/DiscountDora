import { storeToRefs } from 'pinia';
import { useQuasar } from 'quasar';
import { useQuickAddTargetPick } from 'src/composables/useQuickAddTargetPick';
import ShoppingListApiService from 'src/services/api/shoppingListApiService';
import { useAuthStore } from 'src/stores/authStore';
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
    const authStore = useAuthStore();
    const { stockLevels } = storeToRefs(stockLevelStore);
    const { currentUser } = storeToRefs(authStore);

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

    /** Add to the inferred quick-add target (default) or a specific list.
     *  Chunk 2: handles the discriminated `QuickAddResult` — `no_draft` opens
     *  the lists overview to create one; `ambiguous` prompts the user to pick
     *  from the candidate drafts (and remembers the pick in sessionStorage). */
    async function addToList(
        stockItemId: string,
        listId?: string | null,
        options?: { silent?: boolean },
    ) {
        // callers running this in a bulk loop pass silent:true and
        // emit one summary toast themselves instead of N per-item ones.
        const silent = options?.silent ?? false;
        const ok = (msg: string) => { if (!silent) notifyOk(msg); };
        const err = (msg: string, caption?: string) => { if (!silent) notifyErr(msg, caption); };
        const pick = useQuickAddTargetPick();
        // when the user has opted into "always ask", ignore any
        // session-remembered pick so the picker fires every add.
        const alwaysAsk = currentUser.value?.always_ask_which_shopping_list ?? false;
        try {
            if (listId) {
                const result = await shoppingListApi.addLineAsync(listId, {
                    stock_item_id: stockItemId,
                });
                await shoppingListStore.refreshAsync();
                ok(
                    result.already_on_list
                        ? `Already on ${listNameFor(listId)}.`
                        : `Added to ${listNameFor(listId)}.`,
                );
                return;
            }
            const remembered = alwaysAsk ? null : pick.load();
            let outcome = await shoppingListApi.quickAddToPrimaryAsync(
                stockItemId, remembered ?? undefined,
            );
            // A stale sessionStorage pick (the list got finished/deleted) →
            // the server replies with `hint_invalid` as a 422; treat as a
            // re-prompt by retrying without the hint.
            if ((outcome as { result?: string }).result === undefined) {
                // axios threw on the 422 — fall through to catch.
                throw new Error('hint_invalid');
            }
            if (outcome.result === 'no_draft') {
                $q.dialog({
                    title: 'No draft list',
                    message:
                        'You have no draft shopping list. Create one to use the cart shortcut.',
                    ok: { label: 'Open lists', noCaps: true, color: 'primary' },
                    cancel: { noCaps: true },
                }).onOk(() => void router.push('/shopping-lists'));
                return;
            }
            if (outcome.result === 'ambiguous') {
                const choice = await new Promise<string | null>((resolve) => {
                    $q.dialog({
                        title: 'Which list?',
                        message: alwaysAsk
                            ? 'You have multiple draft lists — pick one. Dora will ask again next time (you can change this in Preferences).'
                            : 'You have multiple draft lists — pick one. We\'ll remember it for the rest of this tab.',
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
                        cancel: true,
                        persistent: false,
                    })
                        .onOk((val: string) => resolve(val))
                        .onCancel(() => resolve(null))
                        .onDismiss(() => resolve(null));
                });
                if (!choice) return;
                // always save the pick so the bulk-add caller in
                // AddToListButton can read it and batch items 2..N into
                // the same list. When "always ask" is on we clear it at
                // the end of this call so the *next* quick-add re-prompts.
                pick.save(choice);
                outcome = await shoppingListApi.quickAddToPrimaryAsync(stockItemId, choice);
                if (outcome.result !== 'added') {
                    err('Could not add to the chosen list.');
                    return;
                }
            }
            await shoppingListStore.refreshAsync();
            if (outcome.result === 'added') {
                const listName = listNameFor(outcome.shopping_list_id);
                ok(
                    outcome.already_on_list
                        ? `Already on ${listName}.`
                        : `Added to ${listName}.`,
                );
            }
        } catch (e) {
            const message = e instanceof Error ? e.message : String(e);
            if (message === 'hint_invalid') {
                // The remembered pick no longer applies — clear and retry once
                // fresh so the resolver re-evaluates from scratch.
                pick.clear();
                await addToList(stockItemId, listId, options);
                return;
            }
            err('Could not add to list.', String(e));
        } finally {
            // with "always ask" on, wipe the pick so the next
            // quick-add re-prompts. The current call already used it for
            // any bulk-follow-up read in AddToListButton.
            if (alwaysAsk) pick.clear();
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
        openDetail,
        findSubstitutes,
        seeRecipesUsing,
    };
}
