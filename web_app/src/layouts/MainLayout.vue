<template>
    <q-layout view="hHh LpR lFf">
        <q-header
            bordered
            class="dora-toolbar-surface"
            :reveal="$q.screen.lt.md"
        >
            <q-toolbar class="dora-titlebar">
                <HamburgerButton
                    :is-visible="$q.screen.lt.md"
                    :on-click="toggleLeftDrawer"
                />

                <ApplicationLogo />

                <PageTitle
                    v-if="$q.screen.lt.md && route.meta.title"
                    :label="String(route.meta.title)"
                />

                <MainMenuButtonStrip
                    :is-visible="$q.screen.gt.sm"
                    :menu-links="linksList"
                />

                <!-- Global Undo (F5). Reflects the top of the undo stack —
                     tooltip shows the action's label, disabled when there's
                     nothing to undo. Ctrl/Cmd-Z fires the same handler. -->
                <q-btn
                    v-if="currentUser"
                    flat
                    dense
                    round
                    :icon="ICONS.undo"
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
                    :icon="ICONS.account_circle"
                    v-if="currentUser"
                >
                    <q-menu anchor="bottom right" self="top right" transition-show="jump-down" transition-hide="jump-up">
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
                                    <q-icon :name="ICONS.settings" />
                                </q-item-section>
                                <q-item-section>Settings</q-item-section>
                            </q-item>
                            <q-item clickable v-close-popup to="/help">
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.help_outline" />
                                </q-item-section>
                                <q-item-section>Help & guides</q-item-section>
                            </q-item>
                            <q-item clickable @click="onLogout">
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.logout" />
                                </q-item-section>
                                <q-item-section>Sign out</q-item-section>
                            </q-item>
                        </q-list>
                    </q-menu>
                </q-btn>
            </q-toolbar>
        </q-header>

        <q-drawer
            v-if="$q.screen.lt.md"
            v-model="leftDrawerOpen"
            bordered
            side="left"
        >
            <q-list>
                <SideMenuButton
                    v-for="link in linksList"
                    :key="link.label"
                    v-bind="link"
                />
            </q-list>
        </q-drawer>

        <q-page-container>
            <!-- Pinned under the header when we can't reach the API (or the
                 browser says we're offline). Sticky so it stays visible
                 while the user keeps scrolling/working. -->
            <OfflineBanner />
            <router-view v-slot="{ Component }">
                <FadeTransition mode="out-in">
                    <component :is="Component" />
                </FadeTransition>
            </router-view>
        </q-page-container>

        <!-- Dora help assistant. Lives inside the authenticated layout so
             the login page stays clean; bubble + chat are always present
             across every authenticated route. -->
        <DoraBubble v-if="currentUser" />

        <!-- Global quick-add sheet. Mounted once; any screen pops it via
             useQuickAdd().openQuickAdd(). -->
        <QuickAddSheet v-if="currentUser" />

        <!-- Keyboard-shortcut cheatsheet (opened with "?"). -->
        <ShortcutsCheatsheet v-if="currentUser" />
    </q-layout>
</template>

<script setup lang="ts">
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AlertsBell from 'src/components/AlertsBell.vue';
    import DoraBubble from 'src/components/dora/DoraBubble.vue';
    import OfflineBanner from 'src/components/OfflineBanner.vue';
    import FadeTransition from 'src/components/transitions/FadeTransition.vue';
    import QuickAddSheet from 'src/components/QuickAddSheet.vue';
    import ShortcutsCheatsheet from 'src/components/ShortcutsCheatsheet.vue';
    import ApplicationLogo from 'src/components/menu/ApplicationLogo.vue';
    import HamburgerButton from 'src/components/menu/HamburgerButton.vue';
    import MainMenuButtonStrip from 'src/components/menu/MainMenuButtonStrip.vue';
    import PageTitle from 'src/components/menu/PageTitle.vue';
    import SideMenuButton from 'src/components/menu/SideMenuButton.vue';
    import type { MenuButtonProps } from 'src/components/menu/menuButtonProps';
    import { useShortcut, useShortcutRegistry } from 'src/composables/useShortcut';
    import { useUndo } from 'src/composables/useUndo';
    import { useAuthStore } from 'src/stores/authStore';
    import { onMounted, onUnmounted, ref } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const route = useRoute();
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
                caption: describeApiError(err) || '',
            });
        }
    }

    function isTypingTarget(event: KeyboardEvent): boolean {
        const t = event.target as HTMLElement | null;
        if (!t) return false;
        const tag = (t.tagName || '').toLowerCase();
        if (tag === 'input' || tag === 'textarea' || tag === 'select') return true;
        if ((t).isContentEditable) return true;
        return false;
    }

    function onKeyDown(event: KeyboardEvent) {
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
            void redo().catch((err) => {
                $q.notify({
                    type: 'negative',
                    position: 'bottom-right',
                    message: "Couldn't redo.",
                    caption: describeApiError(err) || '',
                });
            });
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

    // ── Global keyboard shortcuts (S5) ──────────────────────────────────
    const { openCheatsheet } = useShortcutRegistry();
    useShortcut([
        {
            keys: '?',
            scope: 'Global',
            description: 'Show keyboard shortcuts',
            handler: openCheatsheet,
        },
        {
            keys: '/',
            scope: 'Global',
            description: 'Focus search / go to Stock',
            handler: () => {
                // On Stock the page registers its own "/" to focus the filter;
                // it wins (newest). Elsewhere we route there (search autofocuses).
                if (router.currentRoute.value.path !== '/stock') void router.push('/stock');
            },
        },
        { keys: 'g s', scope: 'Global', description: 'Go to Stock', handler: () => void router.push('/stock') },
        { keys: 'g l', scope: 'Global', description: 'Go to Shopping Lists', handler: () => void router.push('/shopping-lists') },
        { keys: 'g r', scope: 'Global', description: 'Go to Cookbook', handler: () => void router.push('/cookbook') },
        { keys: 'g d', scope: 'Global', description: 'Go to Dashboard', handler: () => void router.push('/') },
        { keys: 'g h', scope: 'Global', description: 'Go to Help', handler: () => void router.push('/help') },
    ]);

    // Command palette retired 2026-06-12 — see worklog + FU-029.
    // `useShortcut` / `useShortcutRegistry` (keyboard shortcuts) stay;
    // they were always orthogonal to the palette.

    const linksList: MenuButtonProps[] = [
        { label: 'Stock', icon: 'inventory_2', link: '/stock' },
        { label: 'Product Search', icon: ICONS.search, link: '/product-search' },
        { label: 'My Products', icon: ICONS.shopping_bag, link: '/my-products' },
        { label: 'Cookbook', icon: ICONS.menu_book, link: '/cookbook' },
        { label: 'Meal Plans', icon: ICONS.calendar_month, link: '/meal-plans' },
        { label: 'Shopping Lists', icon: ICONS.shopping_cart, link: '/shopping-lists' },
        { label: 'Data', icon: ICONS.storage, link: '/data' },
        { label: 'Reports', icon: ICONS.insights, link: '/reports' },
        { label: 'Waste', icon: ICONS.expiry, link: '/waste' },
        // B9.3: Settings used to live here too; it's already in the user
        // dropdown (header avatar). Duplicating it in the main menu was
        // confusing — removed.
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

<style scoped lang="scss">
    /* Toolbar reads its own surface + text tokens (not brand-primary)
       so themes with a yellow primary (Lemon Tart) don't render
       yellow-on-yellow Dora text or invisible active-nav links. Each
       theme controls --surface-toolbar in themes.scss. */
    .dora-toolbar-surface {
        background: var(--surface-toolbar);
        color: var(--text-on-toolbar);
    }
    .dora-titlebar {
        height: 64px;
        gap: 8px;
        padding: 0 12px;
    }
</style>
