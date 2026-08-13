<template>
    <!-- Splash sits in front of the router-view until the auth bootstrap probe
         resolves. If the probe fails (backend unreachable) the splash also
         renders a retry button — without this, a failed probe leaves the
         router guard awaiting forever and the user staring at a blank page.

         DR-8 (FU-578 #23): the fade-out is deliberately NOT a Vue <Transition>.
         Vue toggles the `-leave-to` class inside a requestAnimationFrame, and a
         backgrounded / occluded / throttled tab never composites a frame — so
         rAF never fires, the leave wedges at full opacity (z-9000,
         pointer-events auto) and the splash covers the app AND eats clicks.
         Instead we drive the fade with a CSS transition on a plain flag and
         guarantee unmount via a setTimeout (paint-independent), while
         `--leaving` drops pointer-events immediately so it can never block the
         app even if the fade itself is throttled. -->
    <div
        v-if="splashVisible"
        class="splash-host"
        :class="{ 'splash-host--leaving': authStore.isBootstrapped }"
    >
        <SplashScreen
            :error="authStore.bootstrapError"
            @retry="authStore.retryBootstrap"
        />
    </div>
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
    import { onBeforeUnmount, onMounted, ref, watch } from 'vue';

    const authStore = useAuthStore();
    // Kick off the boot probe immediately so the splash shows even before the
    // router has resolved its first navigation — the guard awaits the same
    // promise, so this just front-loads it.
    void authStore.bootstrapAsync();

    // ── Splash lifecycle (DR-8 / FU-578 #23) ──────────────────────────────
    // `splashVisible` owns the mount, independent of the fade. It starts shown
    // (unless bootstrap somehow already resolved) and is only torn down by a
    // paint-independent timer once the app is ready — see the template comment
    // for why a Vue <Transition> can't be trusted here. Matches --motion-slow
    // (320ms) + a small buffer so the CSS fade finishes first when the tab IS
    // painting; when it isn't, the element is already invisible + inert and
    // this just reclaims the node.
    const SPLASH_REMOVAL_MS = 360;
    const splashVisible = ref(!authStore.isBootstrapped);
    let splashRemovalTimer: ReturnType<typeof setTimeout> | null = null;
    watch(
        () => authStore.isBootstrapped,
        (ready) => {
            if (!ready || splashRemovalTimer !== null) return;
            splashRemovalTimer = setTimeout(() => {
                splashVisible.value = false;
            }, SPLASH_REMOVAL_MS);
        },
    );
    onBeforeUnmount(() => {
        if (splashRemovalTimer !== null) clearTimeout(splashRemovalTimer);
    });

    // The inline splash in index.html paints before Vue mounts so the user
    // never sees a black flash on cold load. Once Vue takes over, remove it
    // so it doesn't sit underneath our reactive splash forever.
    onMounted(() => {
        document.getElementById('pre-mount-splash')?.remove();
    });
</script>

<style>
    /* Fade container for the splash. Positioning + z-index live on the
       SplashScreen's own `.splash-overlay`; this host only owns the fade so
       the transition is always in place before `--leaving` flips opacity. */
    .splash-host {
        transition: opacity var(--motion-slow) var(--motion-ease);
    }
    .splash-host--leaving {
        opacity: 0;
        /* Drop interactivity the instant the app is ready — even if the fade
           is throttled and the node lingers, it can never cover clicks. */
        pointer-events: none;
    }
</style>
