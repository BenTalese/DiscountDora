<template>
    <div class="text-center q-pa-xl">
        <q-spinner color="primary" size="60px" />
        <div class="text-body2 text-grey q-mt-md">
            {{ message }}
        </div>
    </div>
</template>

<script lang="ts" setup>
    /**
     * P2-11 — PWA shortcut landing page.
     *
     * The "Shop now" home-screen shortcut points here. We can't bake the
     * primary list id into the manifest at build time (it's per-user),
     * so this lightweight page resolves it on mount and `replace()`s the
     * URL to the actual shop-mode route. Doing the redirect here (rather
     * than as a router guard) keeps the routing config flat and gives
     * us a visible spinner while the store warms up after a cold launch.
     */
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { onMounted, ref } from 'vue';
    import { useRouter } from 'vue-router';

    const router = useRouter();
    const shoppingListStore = useShoppingListStore();
    const message = ref('Finding your primary list…');

    onMounted(async () => {
        try {
            await shoppingListStore.refreshAsync();
            const id = shoppingListStore.primaryListId;
            if (id) {
                await router.replace(`/shopping-lists/${id}/shop`);
                return;
            }
            // No primary set — drop the user at the overview so they
            // can pick or set one. Replace() so the back button
            // doesn't bring them back to this stub.
            message.value = 'No primary list set. Sending you to your lists…';
            await router.replace('/shopping-lists');
        } catch {
            // Even on a fetch failure, the lists page is a sane
            // fallback — better than leaving a spinner spinning.
            await router.replace('/shopping-lists');
        }
    });
</script>
