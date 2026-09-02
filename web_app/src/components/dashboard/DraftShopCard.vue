<template>
    <!-- FU-351 — "Draft my shop" one-click entry point. Legacy P6-10
         wanted a prominent CTA that pre-selects sensible defaults and
         lands the user in a DRAFT list ready to edit. Sits in the
         `act` zone next to Attention / Suggestions — the home screen
         *does*, not just shows (Charter P1 Effortless).

         Defaults (`sensibleDefaultsSubline` mirrors this list):
           • meal plan for the next 7 days (skips already-consumed
             entries — the server filters them out)
           • low + out of stock (any item that needs restocking)
           • flagged / always-include essentials

         The reason chip is not new UI — every produced line renders
         the existing `added_via` chip on ShoppingListDetail
         ("auto: meal plan", "auto: low stock", "auto: essential" /
         "auto: flagged"), same as the /auto-generate engine's
         other callers. Rebuilding it here would be duplication.
    -->
    <DashboardCard :icon="ICONS.playlist_add_check" title="Draft this week's shop">
        <div class="dora-draft-shop">
            <p class="dora-draft-shop__blurb">
                One-click starter list — meal plan for the next 7 days,
                plus anything low, out, or flagged as an essential.
                Nothing shopped yet; you edit before heading out.
            </p>
            <BaseButton
                :icon="ICONS.auto_awesome"
                label="Draft my shop"
                :loading="busy"
                :disable="busy"
                @click="onDraft"
            />
        </div>
    </DashboardCard>
</template>

<script setup lang="ts">
    /**
     * FU-351 — one-click "Draft my shop" dashboard card.
     *
     * On click: POST /shopping-lists/auto-generate with the sensible-
     * default source mix, then navigate to the newly-created draft. The
     * server engine (`features/shopping_lists/auto_generate.py`) owns
     * dedup + provenance ranking; this component only picks the source
     * mix + handles the empty / navigate branches. When nothing matches
     * the sources (fresh install, no meal plan, no low stock, no
     * essentials), the server returns `nothing_to_add: true` with
     * `shopping_list_id: null` — no empty list is materialised, and we
     * show an honest "nothing to draft yet" info toast.
     */
    import { ref } from 'vue';
    import { useQuasar } from 'quasar';
    import { useRouter } from 'vue-router';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import { formatDate as formatLocaleDate } from 'src/composables/useDateFormat';
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { localTodayIso } from 'src/helpers/weekDates';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const router = useRouter();
    const api = new ShoppingListApiService();
    const listStore = useShoppingListStore();

    const busy = ref(false);

    async function onDraft() {
        if (busy.value) return;
        busy.value = true;
        const startIso = localTodayIso();
        // Human-readable list name — the server's default is "Auto N ·
        // <date>" which reads generic. This one names the intent.
        const nameDate = formatLocaleDate(startIso, {
            weekday: 'short', day: 'numeric', month: 'short',
        });
        try {
            const result = await api.autoGenerateAsync({
                name: `Weekly shop · ${nameDate}`,
                sources: {
                    low_stock: true,
                    out_of_stock: true,
                    flagged: true,
                    // Rolling 7-day forward window from today — collector
                    // pulls `[start, start+6d]` and skips already-consumed
                    // entries, so a click on Sat pulls Sat→Fri regardless
                    // of the household's week-start convention.
                    meal_plan_week: startIso,
                    // Frequently-added is noisy on a *weekly* draft — it
                    // surfaces items the user has bought recently, which
                    // are usually already covered by low/out or essentials.
                    // Left off by default; the multi-checkbox NewListDialog
                    // is the venue for the wider mix.
                    frequently_added: false,
                    essentials_only_for_low: false,
                },
            });
            if (result.nothing_to_add || !result.shopping_list_id) {
                $q.notify({
                    type: 'info',
                    position: 'bottom-right',
                    message: 'Nothing to draft yet.',
                    caption: 'Plan some meals, or mark items as essential — then try again.',
                });
                return;
            }
            // Refresh the store so the sidebar list-selector picks up the
            // new list before the router push lands on its detail page.
            await listStore.refreshAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Drafted ${result.added_count} item${result.added_count === 1 ? '' : 's'}.`,
                caption: 'Review the list, then start shopping when ready.',
            });
            await router.push(`/shopping-lists/${result.shopping_list_id}`);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not draft the shop.',
                caption: toastCaption(err),
            });
        } finally {
            busy.value = false;
        }
    }
</script>

<style scoped lang="scss">
    .dora-draft-shop {
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
    }
    .dora-draft-shop__blurb {
        margin: 0;
        color: var(--text-secondary);
        font-size: calc(var(--font-size-sm) * 1rem);
        line-height: 1.35;
    }
</style>
