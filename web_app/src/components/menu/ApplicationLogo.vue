<template>
    <router-link
        to="/"
        class="dora-brand row items-center no-wrap"
        aria-label="Dashy Dora — home"
        @click="onBrandClick"
    >
        <q-avatar square size="44px" class="q-mr-sm dora-brand-mascot">
            <img src="../../assets/logo-mascot.png" alt="" />
        </q-avatar>
        <span
            class="dora-brand-text text-accent"
            :class="{ 'is-flashing': isFlashing }"
            @animationend="onAnimationEnd"
        >Dashy Dora</span>
    </router-link>
</template>

<script setup lang="ts">
    import { nextTick, ref } from 'vue';

    const isFlashing = ref(false);

    function onBrandClick() {
        // Re-trigger cleanly if clicked again mid-animation.
        isFlashing.value = false;
        void nextTick(() => {
            isFlashing.value = true;
        });
    }

    function onAnimationEnd(e: AnimationEvent) {
        if (e.animationName === 'brand-wave') isFlashing.value = false;
    }
</script>

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
        display: inline-block;
        transform-origin: 50% 70%;
    }

    .dora-brand-text.is-flashing {
        color: transparent;
        background: linear-gradient(
            90deg,
            var(--brand-accent) 0%,
            var(--brand-accent) 30%,
            var(--nav-slide-flash) 50%,
            var(--brand-accent) 70%,
            var(--brand-accent) 100%
        );
        background-size: 250% 100%;
        background-clip: text;
        -webkit-background-clip: text;
        animation:
            brand-bounce 0.55s cubic-bezier(0.34, 1.56, 0.64, 1),
            brand-wave 0.75s cubic-bezier(0.4, 0, 0.2, 1);
    }

    @keyframes brand-bounce {
        0%   { transform: scale(1) rotate(0); }
        30%  { transform: scale(1.18) rotate(-3deg); }
        60%  { transform: scale(0.94) rotate(2deg); }
        100% { transform: scale(1) rotate(0); }
    }

    @keyframes brand-wave {
        0%   { background-position: 120% 0; }
        100% { background-position: -20% 0; }
    }
</style>
