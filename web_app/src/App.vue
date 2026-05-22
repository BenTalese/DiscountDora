<template>
    <!-- ErrorBoundary catches render / lifecycle / async setup errors anywhere
         in the router-view subtree and surfaces a friendly PageErrorState
         in its place, instead of leaving a half-broken screen. Layout-level
         chrome (header bell, Dora bubble, etc.) lives outside the boundary
         in MainLayout so they keep working even when a page crashes. -->
    <ErrorBoundary>
        <router-view />
    </ErrorBoundary>
</template>

<script setup lang="ts">
    import ErrorBoundary from 'src/components/ErrorBoundary.vue';
</script>
