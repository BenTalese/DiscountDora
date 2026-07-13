<template>
    <!-- Splash sits in front of the router-view until the auth bootstrap probe
         resolves. If the probe fails (backend unreachable) the splash also
         renders a retry button — without this, a failed probe leaves the
         router guard awaiting forever and the user staring at a blank page.
         The Transition fades the splash out once the app is ready so the
         handoff feels intentional rather than abrupt. -->
    <Transition name="splash-fade">
        <SplashScreen
            v-if="!authStore.isBootstrapped"
            :error="authStore.bootstrapError"
            @retry="authStore.retryBootstrap"
        />
    </Transition>
    <ErrorBoundary v-if="authStore.isBootstrapped">
        <router-view />
    </ErrorBoundary>
    <!-- FU-392 — self-gates on the pre-auth demo_mode capability, so it's a
         no-op on normal installs and safe to mount unconditionally here. -->
    <DemoBanner />
</template>

<script setup lang="ts">
    import DemoBanner from 'src/components/DemoBanner.vue';
    import ErrorBoundary from 'src/components/ErrorBoundary.vue';
    import SplashScreen from 'src/components/SplashScreen.vue';
    import { useAuthStore } from 'src/stores/authStore';
    import { onMounted } from 'vue';

    const authStore = useAuthStore();
    // Kick off the boot probe immediately so the splash shows even before the
    // router has resolved its first navigation — the guard awaits the same
    // promise, so this just front-loads it.
    void authStore.bootstrapAsync();

    // The inline splash in index.html paints before Vue mounts so the user
    // never sees a black flash on cold load. Once Vue takes over, remove it
    // so it doesn't sit underneath our reactive splash forever.
    onMounted(() => {
        document.getElementById('pre-mount-splash')?.remove();
    });
</script>

<style>
    .splash-fade-leave-active {
        transition: opacity var(--motion-slow) var(--motion-ease);
    }
    .splash-fade-leave-to {
        opacity: 0;
    }
</style>
