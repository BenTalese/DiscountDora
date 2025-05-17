<template>
    <q-layout
        view="hHh LpR lFf"
        class="dora-scrollbarOverride"
    >
        <q-header
            bordered
            class="bg-primary text-white"
        >
            <q-toolbar class="dora-titlebar">
                <HamburgerButton
                    :is-visible="$q.screen.lt.md"
                    :onClick="toggleLeftDrawer"
                />

                <ApplicationLogo />

                <ApplicationTitle
                    :label="route.meta.title"
                    shouldShrink
                />

                <MainMenuButtonStrip
                    :is-visible="$q.screen.gt.sm"
                    :menu-links="linksList"
                />
            </q-toolbar>
        </q-header>

        <q-drawer
            v-if="$q.screen.lt.md"
            v-model="leftDrawerOpen"
            show-if-above
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

        <!-- TODO: User option: Show menu only on side (no big buttons) -->
        <!-- <q-drawer
            v-if="$q.screen.lt.md"
            v-model="leftDrawerOpen"
            show-if-above
            :mini="miniState"
            @mouseenter="miniState = false"
            @mouseleave="miniState = true"
            mini-to-overlay
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
        </q-drawer> -->

        <q-page-container>
            <router-view />
        </q-page-container>
    </q-layout>
</template>

<script setup lang="ts">
    //#region Imports
    import ApplicationLogo from 'src/components/menu/ApplicationLogo.vue';
    import ApplicationTitle from 'src/components/menu/ApplicationTitle.vue';
    import HamburgerButton from 'src/components/menu/HamburgerButton.vue';
    import MainMenuButtonStrip from 'src/components/menu/MainMenuButtonStrip.vue';
    import type { MenuButtonProps } from 'src/components/menu/menuButtonProps';
    import SideMenuButton from 'src/components/menu/SideMenuButton.vue';
    import { ref } from 'vue';
    import { useRoute } from 'vue-router';
    const route = useRoute();
    //#endregion Imports

    //#region State
    // TODO: See above 'TODO'
    // const miniState = ref(true);

    const linksList: MenuButtonProps[] = [
        {
            icon: 'mdi-view-dashboard',
            label: 'Dashboard',
            link: '/dashboard'
        },
        {
            // icon: 'stock',
            // icon: 'inventory',
            // icon: 'kitchen',
            // icon: 'storefront',
            // icon: 'fa-solid fa-cubes-stacked',
            icon: 'mdi-chart-box',
            label: 'Stock',
            link: '/stock'
        },
        {
            icon: 'search',
            label: 'Product Search',
            link: '/product-search'
        },
        {
            icon: 'shopping_cart',
            label: 'My Shopping',
            link: '/shopping'
        },
        {
            icon: 'circle',
            label: 'My Products',
            link: '/products'
        },
        {
            icon: 'water',
            label: 'Meal Planner',
            link: '/meals'
        },
        {
            icon: 'book',
            label: 'Recipe Book',
            link: '/recipes'
        },
        {
            icon: 'settings',
            label: 'Settings',
            link: '/settings'
        }
    ];

    const leftDrawerOpen = ref(false);
    //#endregion State

    //#region Methods
    function toggleLeftDrawer() {
        leftDrawerOpen.value = !leftDrawerOpen.value;
    }
    //#endregion Methods
</script>

<style scoped lang="scss">
    .dora-titlebar {
        height: 60px;
        overflow: hidden;
    }
    /* =================== Scrollbar =================== */
    .dora-scrollbarOverride {
        overflow: auto;
        height: 100px; // Doesn't feel necessary but without it the custom scrollbar doesn't work, seems it can be any value
        scrollbar-color: var(--q-secondary) var(--q-page); /* thumb, track */ // Works with Firefox, overwrites all other settings
    }

    // BELOW NOT COMPATIBLE WITH FIREFOX BROWSER

    // /* Full scrollbar container */
    // .dora-scrollbarOverride::-webkit-scrollbar {
    //     width: 10px; /* vertical scrollbar width */
    //     height: 10px; /* horizontal scrollbar height */
    // }

    // /* Track (background) */
    // .dora-scrollbarOverride::-webkit-scrollbar-track {
    //     background: var(--q-page);
    //     // border-radius: 15px;
    //     // box-shadow: inset 5px 5px 5px rgba(0, 0, 0, 0.2);
    // }

    // /* Thumb (draggable handle) */
    // .dora-scrollbarOverride::-webkit-scrollbar-thumb {
    //     background: var(--q-secondary); /* your secondary color */
    //     border-radius: 4px;
    //     // border: 1px solid #c42424;
    // }

    // /* Thumb on hover */
    // .dora-scrollbarOverride::-webkit-scrollbar-thumb:hover {
    //     background: #ffa8a8;
    // }

    // /* Bottom-right corner (when both scrollbars are visible) */
    // .dora-scrollbarOverride::-webkit-scrollbar-corner {
    //     background: var(--q-page);
    // }

    // /* Resize dragger (if resizable element) */
    // .dora-scrollbarOverride::-webkit-resizer {
    //     background: #85a70b;
    // }
    /* =================== Scrollbar =================== */
</style>
