<template>
    <PageErrorState
        variant="not_found"
        :show-reload="false"
        :show-dashboard="true"
        :show-report="false"
    />
</template>

<script setup lang="ts">
    // In-layout 404 — used when a known-shape URL (`/stock/<unknown-id>`)
    // resolves to "no such entity" and we want to keep the chrome around
    // the message. The bare-URL catch-all still renders the fullscreen
    // ErrorNotFound page for typo'd routes.
    import PageErrorState from 'src/components/PageErrorState.vue';
</script>
