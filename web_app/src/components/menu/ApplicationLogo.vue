<template>
    <router-link to="/" class="dora-brand row items-center no-wrap" aria-label="Discount Dora — home">
        <q-avatar square size="44px" class="q-mr-sm dora-brand-mascot">
            <img src="../../assets/logo-mascot.png" alt="" />
        </q-avatar>
        <span class="dora-brand-text text-accent">Discount Dora</span>
    </router-link>
</template>

<script setup lang="ts"></script>

<style scoped lang="scss">
    .dora-brand {
        text-decoration: none;
        color: inherit;
        flex: 0 0 auto;
    }

    .dora-brand-mascot {
        transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    .dora-brand:hover .dora-brand-mascot {
        transform: rotate(-18deg) scale(1.12);
    }

    .dora-brand-text {
        font-family: 'Cute Dino', sans-serif;
        font-size: clamp(22px, 2.4vw, 30px);
        line-height: 1;
        white-space: nowrap;
    }
</style>
