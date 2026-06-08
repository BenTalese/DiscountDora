<template>
    <!-- P6-01 Chunk 5 — router-landing page. The proposal merges the
         standalone overview into the detail (one canonical surface);
         /shopping-lists now picks a target list by status priority and
         redirects to its detail. When there are no lists yet, this page
         renders a one-button empty state. -->
    <q-page padding>
        <!-- Load error banner is surfaced first so failures aren't silent
             (was a blank-screen root cause). -->
        <q-banner
            v-if="loadError"
            class="dora-bg-negative-soft text-negative q-mb-md"
            dense
            rounded
        >
            <strong>Couldn't load your shopping lists.</strong>
            {{ loadError }}
            <template #action>
                <q-btn flat no-caps label="Retry" @click="retryLoad" />
            </template>
        </q-banner>

        <div v-if="loading && summariesEmpty" class="text-center q-py-xl">
            <AppSpinner size="48px" />
        </div>
        <div v-else-if="summariesEmpty" class="text-center dora-text-muted q-py-xl">
            <q-icon :name="ICONS.shopping_cart" size="60px" class="q-mb-sm" />
            <div class="text-h6">No shopping lists yet.</div>
            <div class="q-mt-md">
                Get started by creating your first list — empty, from a
                template, or auto-filled from your stock.
            </div>
            <div class="q-mt-md">
                <q-btn
                    color="primary"
                    no-caps
                    :icon="ICONS.add"
                    label="New list"
                    @click="newListOpen = true"
                />
            </div>
        </div>
        <div v-else class="text-center q-py-xl dora-text-muted">
            <AppSpinner size="32px" />
            <div class="q-mt-sm">Opening your list…</div>
        </div>

        <NewListDialog
            v-model="newListOpen"
            @created="onListCreated"
        />
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import AppSpinner from 'src/components/AppSpinner.vue';
    import NewListDialog from 'src/components/dialogs/NewListDialog.vue';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { computed, nextTick, onMounted, ref, watch } from 'vue';
    import { useRouter } from 'vue-router';

    const router = useRouter();
    const store = useShoppingListStore();

    const loading = computed(() => store.loading);
    const loadError = computed(() => store.loadError);
    const summariesEmpty = computed(() => store.summaries.length === 0);
    const newListOpen = ref(false);

    async function retryLoad() {
        await store.refreshAsync();
        redirectIfPossible();
    }

    // Priority for landing: an in-flight shop wins (resume), then a DRAFT
    // whose `planned_shop_date` is today (Chunk 7 "keyed to today's
    // date"), then any DRAFT (freshest first), then a DONE (freshest
    // first). Pure-frontend pick — the server stays neutral.
    function pickTargetList(): string | null {
        const summaries = store.summaries;
        if (summaries.length === 0) return null;
        const shopping = summaries.find((s) => s.status === 'shopping');
        if (shopping) return shopping.shopping_list_id;
        const today = new Date().toISOString().slice(0, 10);
        const drafts = summaries
            .filter((s) => s.status === 'draft')
            .slice()
            .sort((a, b) => (b.created_at ?? '').localeCompare(a.created_at ?? ''));
        const todayDraft = drafts.find((s) => s.planned_shop_date === today);
        if (todayDraft) return todayDraft.shopping_list_id;
        if (drafts[0]) return drafts[0].shopping_list_id;
        const done = summaries
            .filter((s) => s.status === 'done')
            .slice()
            .sort((a, b) => (b.completed_at ?? '').localeCompare(a.completed_at ?? ''));
        return done[0]?.shopping_list_id ?? null;
    }

    // **Important**: redirects MUST be deferred via `nextTick` (or longer).
    // `MainLayout.vue` wraps the router-view in a `<FadeTransition
    // mode="out-in">`; calling `router.replace` synchronously inside
    // `onMounted` here unmounts this component while it's still mid-
    // enter-transition, which can leave the global transition state
    // stuck and every subsequent page renders blank. The nextTick lets
    // the entering transition settle before we trigger the next route
    // change. Same fix is applied to Detail's status watcher.
    async function redirectIfPossible() {
        const id = pickTargetList();
        if (!id) return;
        await nextTick();
        await router.replace(`/shopping-lists/${id}`);
    }

    async function onListCreated({ listId }: { listId: string }) {
        await nextTick();
        await router.replace(`/shopping-lists/${listId}`);
    }

    onMounted(async () => {
        if (store.summaries.length === 0 && !store.loading) {
            await store.refreshAsync();
        }
        await redirectIfPossible();
    });

    // If summaries arrive after mount (in-flight refresh), redirect as
    // soon as one appears.
    watch(
        () => store.summaries.length,
        (count, prev) => {
            if (count > 0 && prev === 0) void redirectIfPossible();
        },
    );
</script>
