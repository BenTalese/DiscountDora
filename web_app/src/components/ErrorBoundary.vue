<template>
    <PageErrorState
        v-if="caughtError"
        variant="render"
        :error="caughtError"
        :correlation-id="correlationIdFromError(caughtError)"
        :show-reload="true"
        :show-dashboard="true"
        :show-report="true"
    />
    <slot v-else />
</template>

<script lang="ts" setup>
    // Vue 3 error boundary (F3).
    //
    // `onErrorCaptured` returning `false` halts propagation so the rest of
    // the app keeps running. We render PageErrorState in place of the
    // crashed subtree — wrapping <router-view /> in App.vue means a render
    // error on one page doesn't take down the layout shell or the chat
    // bubble.
    //
    // Navigation events reset the boundary so moving away from the bad
    // page recovers automatically (no "click X to dismiss" friction).

    import PageErrorState from 'src/components/PageErrorState.vue';
    import { NormalisedApiError } from 'src/services/api/axiosHttpClient';
    import { onErrorCaptured, ref, watch } from 'vue';
    import { useRoute } from 'vue-router';

    const route = useRoute();
    const caughtError = ref<Error | null>(null);

    onErrorCaptured((err, _instance, info) => {
         
        console.error('[ErrorBoundary] caught', info, err);
        caughtError.value = err instanceof Error ? err : new Error(String(err));
        // Returning false stops the error from propagating further; the
        // global handler still fires for logging but the app stays alive.
        return false;
    });

    // Reset whenever the route changes so leaving the page clears the
    // boundary. This means navigating away from a crashed screen by
    // clicking "Go to dashboard" or hitting a menu item Just Works.
    watch(
        () => route.fullPath,
        () => {
            caughtError.value = null;
        },
    );

    function correlationIdFromError(err: Error | null): string | null {
        if (!err) return null;
        if (err instanceof NormalisedApiError && err.correlationId) {
            return err.correlationId;
        }
        return null;
    }
</script>
