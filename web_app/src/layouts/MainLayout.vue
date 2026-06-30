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

                <!-- Help & guides — peer of the profile button.
                     Direct nav to `/help`; carries the same active-ring
                     affordance as the avatar so the header advertises
                     "you're somewhere reachable from here" when on a
                     /help/* route. -->
                <BaseButton
                    v-if="currentUser"
                    variant="icon"
                    aria-label="Help & guides"
                    to="/help"
                >
                    <span
                        class="dora-headerActiveRing"
                        :class="{ 'is-active': isHelpActive }"
                    >
                        <q-icon :name="ICONS.help_outline" size="24px" />
                    </span>
                    <q-tooltip>Help &amp; guides</q-tooltip>
                </BaseButton>

                <!-- Account / settings — direct nav, no dropdown.
                     Sign-out lives on the Account settings page; the
                     header dropdown was a duplicate path that mostly
                     hid the destination behind an extra click. -->
                <BaseButton
                    v-if="currentUser"
                    variant="icon"
                    aria-label="Account settings"
                    to="/settings/account"
                >
                    <!-- Settings rebuild Phase 4: profile picture when set,
                         else the original account-circle icon. Wrapping
                         span carries the box-shadow ring since q-avatar's
                         circular mask would clip its own shadow. -->
                    <span
                        class="dora-headerActiveRing"
                        :class="{ 'is-active': isAvatarActive }"
                    >
                        <UserAvatar
                            :user-id="currentUser.user_id"
                            :has-image="currentUser.has_image"
                            size="30px"
                            fallback="icon"
                            :fallback-icon="ICONS.account_circle"
                            :username="currentUser.username"
                        />
                    </span>
                    <q-tooltip>{{ currentUser.username }}</q-tooltip>
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
    const { currentUser, isAdmin } = storeToRefs(authStore);

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
    //   - visible-but-disabled with a "set up in Settings" hint when products
    //     is on but no `product_search_url` is configured (R-014). The hint
    //     names the exact settings path so the user knows where to go without
    //     having to dig through the admin nav.
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
                // R-014 "path to enable it" — name the exact settings route
                // so the hint is actionable, not just informative. Hover →
                // q-tooltip; side-menu also renders this as a caption under
                // the label (SideMenuButton.vue:14).
                disabledTooltip: isAdmin.value
                    ? 'Not set up yet — set the Product search URL in Settings → System → Features.'
                    : 'Not set up yet — ask an admin to set the Product search URL in System → Features.',
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
        // FU-209: My Products is gated on the same data-presence flag
        // as the rest of the products overlay — hide it entirely when
        // no products exist. Previously this entry slipped through
        // (productSearchEntry above was gated but the push below wasn't),
        // so the nav still advertised the surface on a products-empty
        // install.
        if (features.products.value) {
            base.push({ label: 'My Products', icon: ICONS.shopping_bag, link: '/my-products' });
        }
        base.push(
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

    // Two peer header buttons (Help + Account) each carry the active-ring
    // affordance that mirrors the main-menu strip's underline indicator.
    // Avatar lights up under `/settings/*`; Help lights up under `/help`
    // / `/help/*`. Same prefix-match style as `useMenuLinkActive`.
    function matchesPrefix(prefix: string): boolean {
        return route.path === prefix || route.path.startsWith(prefix + '/');
    }
    const isAvatarActive = computed(() => matchesPrefix('/settings'));
    const isHelpActive = computed(() => matchesPrefix('/help'));

    const leftDrawerOpen = ref(false);

    function toggleLeftDrawer() {
        leftDrawerOpen.value = !leftDrawerOpen.value;
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

    /* Shared active-ring for header peer buttons (Help + Account).
       Each button's inner content (avatar or icon) is wrapped in a
       `.dora-headerActiveRing` span that takes an `is-active` class
       from the route. Box-shadow puts the ring outside the circular
       click target without shifting layout — the avatar's mask would
       have clipped its own shadow, hence the wrapping span (the icon
       button gets the same wrap for visual consistency).

       Two shadows: a 3px ring in the accent colour (matches the main-
       menu strip's slide indicator height) + a soft glow (same
       `color-mix` shape as the strip's box-shadow). Activation also
       fires a one-shot pulse that starts in the strip's "moving"
       colour (`--nav-slide-flash`) and settles into the resting
       accent — the header button doesn't translate position the way
       the strip indicator does, so the colour transition IS the
       motion. */
    .dora-headerActiveRing {
        display: inline-flex;
        border-radius: 50%;
        box-shadow:
            0 0 0 3px transparent,
            0 0 10px transparent;
        transition: box-shadow var(--motion-slow) var(--motion-ease);
    }
    .dora-headerActiveRing.is-active {
        box-shadow:
            0 0 0 3px var(--q-accent),
            0 0 10px color-mix(in srgb, var(--brand-accent) 55%, transparent);
        animation: dora-headerActiveRing-pulse 0.55s cubic-bezier(0.4, 0, 0.2, 1);
    }

    @keyframes dora-headerActiveRing-pulse {
        0% {
            box-shadow:
                0 0 0 5px var(--nav-slide-flash),
                0 0 18px color-mix(in srgb, var(--nav-slide-flash) 70%, transparent);
        }
        55% {
            box-shadow:
                0 0 0 4px color-mix(in srgb, var(--nav-slide-flash) 60%, var(--q-accent)),
                0 0 14px color-mix(in srgb, var(--nav-slide-flash) 35%, transparent);
        }
        100% {
            box-shadow:
                0 0 0 3px var(--q-accent),
                0 0 10px color-mix(in srgb, var(--brand-accent) 55%, transparent);
        }
    }

    /* Reduced-motion users: the pulse IS the motion, so suppress it
       entirely and let the static accent ring appear without the
       flash-coloured beat. Resting state still applies. */
    @media (prefers-reduced-motion: reduce) {
        .dora-headerActiveRing.is-active {
            animation: none;
        }
    }
</style>
