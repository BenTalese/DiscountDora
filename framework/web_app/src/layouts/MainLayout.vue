<template>
    <q-layout view="hHh LpR lFf">
        <q-header
            bordered
            class="bg-primary text-white"
            :reveal="$q.screen.lt.md"
        >
            <q-toolbar class="dora-titlebar">
                <HamburgerButton
                    :is-visible="$q.screen.lt.md"
                    :onClick="toggleLeftDrawer"
                />

                <ApplicationLogo />

                <PageTitle
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
    import HamburgerButton from 'src/components/menu/HamburgerButton.vue';
    import MainMenuButtonStrip from 'src/components/menu/MainMenuButtonStrip.vue';
    import type { MenuButtonProps } from 'src/components/menu/menuButtonProps';
    import PageTitle from 'src/components/menu/PageTitle.vue';
    import SideMenuButton from 'src/components/menu/SideMenuButton.vue';
    import { ref } from 'vue';
    import { useRoute } from 'vue-router';
    const route = useRoute();
    //#endregion Imports

    //#region State
    // TODO: See above 'TODO'
    // const miniState = ref(true);

    const linksList: MenuButtonProps[] = [
        // {
        //     icon: 'mdi-view-dashboard',
        //     label: 'Dashboard',
        //     link: '/dashboard'
        // },
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
        }
        // {
        //     icon: 'shopping_cart',
        //     label: 'My Shopping',
        //     link: '/shopping'
        // },
        // {
        //     icon: 'circle',
        //     label: 'My Products',
        //     link: '/products'
        // },
        // {
        //     icon: 'water',
        //     label: 'Meal Planner',
        //     link: '/meals'
        // },
        // {
        //     icon: 'book',
        //     label: 'Recipe Book',
        //     link: '/recipes'
        // },
        // {
        //     icon: 'settings',
        //     label: 'Settings',
        //     link: '/settings'
        // }
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
</style>
