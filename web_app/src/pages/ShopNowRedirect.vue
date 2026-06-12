<template>
    <div class="text-center q-pa-xl">
        <AppSpinner size="60px" />
        <div class="text-body2 dora-text-muted q-mt-md">
            {{ message }}
        </div>
    </div>
</template>

<script lang="ts" setup>
    /**
     * P2-11 — PWA shortcut landing page.
     *
     * The "Shop now" home-screen shortcut points here. We can't bake a list id
     * into the manifest at build time (it's per-user), so this resolves it on
     * mount and `replace()`s the URL to the right place.
     *
     * Chunk 2 rule (no stored "primary" anymore), UX-v2 single-page shape
     * (shop mode is merged into the detail page — no /shop route):
     *   - exactly one SHOPPING list → open it (the page is mid-shop already)
     *   - else exactly one DRAFT     → open the draft so the user can Start
     *   - else                       → overview (let them pick)
     */
    import AppSpinner from 'src/components/AppSpinner.vue';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { onMounted, ref } from 'vue';
    import { useRouter } from 'vue-router';

    const router = useRouter();
    const shoppingListStore = useShoppingListStore();
    const message = ref('Finding your shopping list…');

    onMounted(async () => {
        try {
            await shoppingListStore.refreshAsync();
            const summaries = shoppingListStore.summaries;
            const shoppingLists = summaries.filter((s) => s.status === 'shopping');
            if (shoppingLists.length === 1) {
                await router.replace(`/shopping-lists/${shoppingLists[0]!.shopping_list_id}`);
                return;
            }
            const drafts = summaries.filter((s) => s.status === 'draft');
            if (shoppingLists.length === 0 && drafts.length === 1) {
                // Send to the detail so the user can hit "Start shopping". The
                // detail page owns the transition, not us.
                await router.replace(`/shopping-lists/${drafts[0]!.shopping_list_id}`);
                return;
            }
            message.value = 'Multiple lists — pick one.';
            await router.replace('/shopping-lists');
        } catch {
            // Even on a fetch failure, the lists page is a sane fallback —
            // better than leaving a spinner spinning.
            await router.replace('/shopping-lists');
        }
    });
</script>
