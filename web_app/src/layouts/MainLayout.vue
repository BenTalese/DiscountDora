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

                <AlertsBell v-if="currentUser" class="q-mr-sm" />

                <BaseButton
                    v-if="currentUser"
                    variant="icon"
                    aria-label="Account menu"
                >
                    <!-- Settings rebuild Phase 4: profile picture when set,
                         else the original account-circle icon (preserved per
                         the feedback). -->
                    <UserAvatar
                        :user-id="currentUser.user_id"
                        :has-image="currentUser.has_image"
                        size="30px"
                        fallback="icon"
                        :fallback-icon="ICONS.account_circle"
                        :username="currentUser.username"
                    />
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
                </BaseButton>
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
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AlertsBell from 'src/components/AlertsBell.vue';
    import UserAvatar from 'src/components/UserAvatar.vue';
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
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import { useProductSearchUrl } from 'src/composables/useProductSearchUrl';
    import { useShortcut, useShortcutRegistry } from 'src/composables/useShortcut';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, ref } from 'vue';
    import { useRoute, useRouter } from 'vue-router';

    const $q = useQuasar();
    const route = useRoute();
    const router = useRouter();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

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

    // Phase D / FU-186 — the "Product Search" entry:
    //   - hidden when products is off (no product data ⇒ no search surface)
    //   - visible-but-disabled with a "Set up in Settings" hint when products
    //     is on but no `product_search_url` is configured (R-014)
    //   - external link (new tab) when both flags are good. The destination
    //     (a sibling companion / a static page / whatever the operator runs)
    //     is **never named** here — it's just "Product Search".
    const features = useFeatureFlags();
    const productSearch = useProductSearchUrl();

    const productSearchEntry = computed<MenuButtonProps | null>(() => {
        if (!features.products.value) return null;
        const url = productSearch.url.value.trim();
        if (!url) {
            return {
                label: 'Product Search',
                icon: ICONS.search,
                link: '',
                disabled: true,
                disabledTooltip: 'Set the Product search URL in admin System settings.'
            };
        }
        return {
            label: 'Product Search',
            icon: ICONS.search,
            link: '',
            href: url
        };
    });

    const linksList = computed<MenuButtonProps[]>(() => {
        const base: MenuButtonProps[] = [
            { label: 'Stock', icon: 'inventory_2', link: '/stock' }
        ];
        if (productSearchEntry.value) {
            base.push(productSearchEntry.value);
        }
        base.push(
            { label: 'My Products', icon: ICONS.shopping_bag, link: '/my-products' },
            { label: 'Cookbook', icon: ICONS.menu_book, link: '/cookbook' },
            { label: 'Meal Plans', icon: ICONS.calendar_month, link: '/meal-plans' },
            { label: 'Shopping Lists', icon: ICONS.shopping_cart, link: '/shopping-lists' },
            { label: 'Data', icon: ICONS.storage, link: '/data' },
            { label: 'Reports', icon: ICONS.insights, link: '/reports' },
            // C-waste W6 — Waste nav slot removed; near-expiry items
            // surface via Needs-your-attention on the dashboard and
            // through Dora's `expiry_rescue` tool. No replacement slot
            // (PROPOSAL_WASTE_MINIMISATION §2 D11).
            // B9.3: Settings used to live here too; it's already in the user
            // dropdown (header avatar). Duplicating it in the main menu was
            // confusing — removed.
        );
        return base;
    });

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
