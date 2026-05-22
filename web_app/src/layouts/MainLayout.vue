<template>
    <q-layout view="hHh LpR lFf">
        <q-header
            bordered
            class="bg-primary text-white"
        >
            <q-toolbar>
                <q-btn
                    flat
                    dense
                    round
                    icon="menu"
                    aria-label="Menu"
                    @click="toggleLeftDrawer"
                />

                <q-toolbar-title class="dora-fontFamily-cuteDino dora-fontSize-30">
                    <q-avatar
                        square
                        size="50px"
                        class="q-ma-xs"
                    >
                        <img src="../../src/assets/logo-mascot.png" />
                    </q-avatar>
                    <p
                        class="dora-marginTop-5 dora-marginBottom-0 dora-marginLeft-15 dora-display-inlineBlock text-accent"
                    >
                        Discount Dora
                    </p>
                </q-toolbar-title>

                <!-- Global Undo (F5). Reflects the top of the undo stack —
                     tooltip shows the action's label, disabled when there's
                     nothing to undo. Ctrl/Cmd-Z fires the same handler. -->
                <q-btn
                    v-if="currentUser"
                    flat
                    dense
                    round
                    icon="undo"
                    :disable="!canUndo"
                    @click="onUndoClick"
                    class="q-mr-xs"
                >
                    <q-tooltip>
                        {{ canUndo ? `Undo: ${topUndoLabel}` : 'Nothing to undo' }}
                    </q-tooltip>
                </q-btn>

                <AlertsBell v-if="currentUser" class="q-mr-sm" />

                <q-btn
                    flat
                    no-caps
                    round
                    dense
                    icon="account_circle"
                    v-if="currentUser"
                >
                    <q-menu anchor="bottom right" self="top right">
                        <q-list dense style="min-width: 200px">
                            <q-item>
                                <q-item-section>
                                    <q-item-label class="text-weight-bold">
                                        {{ currentUser.username }}
                                    </q-item-label>
                                    <q-item-label caption v-if="currentUser.email">
                                        {{ currentUser.email }}
                                    </q-item-label>
                                </q-item-section>
                            </q-item>
                            <q-separator />
                            <q-item clickable v-close-popup to="/settings/account">
                                <q-item-section avatar>
                                    <q-icon name="settings" />
                                </q-item-section>
                                <q-item-section>Settings</q-item-section>
                            </q-item>
                            <q-item clickable v-close-popup to="/help">
                                <q-item-section avatar>
                                    <q-icon name="help_outline" />
                                </q-item-section>
                                <q-item-section>Help & guides</q-item-section>
                            </q-item>
                            <q-item clickable @click="onLogout">
                                <q-item-section avatar>
                                    <q-icon name="logout" />
                                </q-item-section>
                                <q-item-section>Sign out</q-item-section>
                            </q-item>
                        </q-list>
                    </q-menu>
                </q-btn>
            </q-toolbar>
        </q-header>

        <q-drawer
            v-model="leftDrawerOpen"
            show-if-above
            bordered
            side="left"
        >
            <q-list>
                <EssentialLink
                    v-for="link in linksList"
                    :key="link.title"
                    v-bind="link"
                />
            </q-list>
        </q-drawer>

        <q-page-container>
            <!-- Pinned under the header when we can't reach the API (or the
                 browser says we're offline). Sticky so it stays visible
                 while the user keeps scrolling/working. -->
            <OfflineBanner />
            <router-view />
        </q-page-container>

        <!-- Dora help assistant. Lives inside the authenticated layout so
             the login page stays clean; bubble + chat are always present
             across every authenticated route. -->
        <DoraBubble v-if="currentUser" />

        <!-- Global quick-add sheet. Mounted once; any screen pops it via
             useQuickAdd().openQuickAdd(). -->
        <QuickAddSheet v-if="currentUser" />
    </q-layout>
</template>

<script setup lang="ts">
    import EssentialLink, { type EssentialLinkProps } from 'components/EssentialLink.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AlertsBell from 'src/components/AlertsBell.vue';
    import DoraBubble from 'src/components/dora/DoraBubble.vue';
    import OfflineBanner from 'src/components/OfflineBanner.vue';
    import QuickAddSheet from 'src/components/QuickAddSheet.vue';
    import { useUndo } from 'src/composables/useUndo';
    import { useAuthStore } from 'src/stores/authStore';
    import { onMounted, onUnmounted, ref } from 'vue';
    import { useRouter } from 'vue-router';

    const $q = useQuasar();
    const router = useRouter();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    // F5: global undo wiring. The button uses canUndo / topUndoLabel
    // for visibility + tooltip, and Ctrl/Cmd-Z fires the same undo()
    // (skipped when the user is typing in an input so we don't
    // accidentally undo a stock-level swap while they're editing
    // a recipe).
    const { canUndo, canRedo, topUndoLabel, undo, redo } = useUndo();

    async function onUndoClick() {
        try {
            const did = await undo();
            if (!did) return;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't undo.",
                caption: String(err),
            });
        }
    }

    function isTypingTarget(event: KeyboardEvent): boolean {
        const t = event.target as HTMLElement | null;
        if (!t) return false;
        const tag = (t.tagName || '').toLowerCase();
        if (tag === 'input' || tag === 'textarea' || tag === 'select') return true;
        if ((t as HTMLElement).isContentEditable) return true;
        return false;
    }

    async function onKeyDown(event: KeyboardEvent) {
        if (!currentUser.value) return;
        if (isTypingTarget(event)) return;
        const isMod = event.ctrlKey || event.metaKey;
        if (!isMod) return;
        const key = event.key.toLowerCase();
        // Ctrl/Cmd-Z → undo; Ctrl/Cmd-Shift-Z or Ctrl-Y → redo.
        if (key === 'z' && !event.shiftKey) {
            if (!canUndo.value) return;
            event.preventDefault();
            void onUndoClick();
        } else if ((key === 'z' && event.shiftKey) || key === 'y') {
            if (!canRedo.value) return;
            event.preventDefault();
            try {
                await redo();
            } catch (err) {
                $q.notify({
                    type: 'negative',
                    position: 'bottom-right',
                    message: "Couldn't redo.",
                    caption: String(err),
                });
            }
        }
    }

    onMounted(() => {
        if (typeof window !== 'undefined') {
            window.addEventListener('keydown', onKeyDown);
        }
    });
    onUnmounted(() => {
        if (typeof window !== 'undefined') {
            window.removeEventListener('keydown', onKeyDown);
        }
    });

    const linksList: EssentialLinkProps[] = [
        { title: 'Dashboard', icon: 'dashboard', link: '/' },
        { title: 'Stock', icon: 'inventory_2', link: '/stock' },
        { title: 'Locations', icon: 'place', link: '/locations' },
        { title: 'Product Search', icon: 'search', link: '/product-search' },
        { title: 'My Products', icon: 'shopping_bag', link: '/my-products' },
        { title: 'Recipes', icon: 'menu_book', link: '/recipes' },
        { title: 'Meals', icon: 'restaurant', link: '/meals' },
        { title: 'Meal Plans', icon: 'calendar_month', link: '/meal-plans' },
        { title: 'Shopping Lists', icon: 'shopping_cart', link: '/shopping-lists' },
        { title: 'Settings', icon: 'settings', link: '/settings' }
    ];

    const leftDrawerOpen = ref(false);

    function toggleLeftDrawer() {
        leftDrawerOpen.value = !leftDrawerOpen.value;
    }

    async function onLogout() {
        await authStore.logoutAsync();
        void router.push('/login');
    }
</script>
