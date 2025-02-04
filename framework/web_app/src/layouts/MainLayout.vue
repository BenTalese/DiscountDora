<template>
    <q-layout view="hHh LpR lFf">
        <q-header bordered class="bg-primary text-white"> <!-- may or may not want "reveal" option for header, it's for hide on scroll (i think) -->
            <q-toolbar>
                <q-btn flat dense round icon="menu" aria-label="Menu" @click="toggleLeftDrawer" />

                <q-toolbar-title>
                    <q-avatar square>
                        <img src="../../src/assets/dora-logo.png">
                    </q-avatar>
                    Discount Dora
                </q-toolbar-title>
            </q-toolbar>
        </q-header>

        <q-drawer v-model="leftDrawerOpen" show-if-above bordered side="left">
            <q-list>
                <EssentialLink v-for="link in essentialLinks" :key="link.title" v-bind="link" />
            </q-list>
        </q-drawer>

        <q-page-container>
            <router-view />
        </q-page-container>
    </q-layout>
</template>

<script setup lang="ts">
import EssentialLink, { EssentialLinkProps } from 'components/EssentialLink.vue';
import { ref } from 'vue';

const essentialLinks: EssentialLinkProps[] = [
    {
        title: 'Product Search',
        icon: 'search',
        link: 'http://localhost:5174/#/product-search'
    },
    {
        title: 'Stock',
        icon: 'stock',
        link: 'http://localhost:5174/#'
    }
];

const leftDrawerOpen = ref(false)

function toggleLeftDrawer() {
    leftDrawerOpen.value = !leftDrawerOpen.value
}
</script>
