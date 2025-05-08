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
                        Discount Dora
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
