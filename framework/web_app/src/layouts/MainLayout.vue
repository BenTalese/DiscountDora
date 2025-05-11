<template>
    <q-layout
        view="hHh LpR lFf"
        class="scrollable"
    >
        <q-header
            bordered
            class="bg-primary text-white"
        >
            <q-toolbar style="height: 60px">
                <q-btn
                    @click="toggleLeftDrawer"
                    aria-label="Menu"
                    dense
                    flat
                    icon="menu"
                    round
                    v-if="$q.screen.lt.md"
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
                        {{ route.meta.title }}
                    </p>
                </q-toolbar-title>
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
            <router-view />
        </q-page-container>
    </q-layout>
</template>

<script setup lang="ts">
    import EssentialLink, { type EssentialLinkProps } from 'components/EssentialLink.vue';
    import { ref } from 'vue';

    const linksList: EssentialLinkProps[] = [
        {
            title: 'Stock',
            icon: 'stock',
            link: 'http://localhost:5174/#'
        },
        {
            title: 'Product Search',
            icon: 'search',
            link: 'http://localhost:5174/#/product-search'
        }
    ];

    const leftDrawerOpen = ref(false);

    function toggleLeftDrawer() {
        leftDrawerOpen.value = !leftDrawerOpen.value;
    }
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
