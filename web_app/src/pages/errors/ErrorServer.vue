<template>
    <PageErrorState
        variant="server"
        :correlation-id="correlationId"
        :show-reload="true"
        :show-dashboard="true"
        :show-report="true"
    />
</template>

<script setup lang="ts">
    import PageErrorState from 'src/components/PageErrorState.vue';
    import { computed } from 'vue';
    import { useRoute } from 'vue-router';

    // Allow callers (e.g. router navigation guards) to push the user here
    // with a correlation id pinned in the query, so the report-this button
    // can reference it.
    const route = useRoute();
    const correlationId = computed(() => {
        const cid = route.query.ref;
        return typeof cid === 'string' ? cid : null;
    });
</script>
