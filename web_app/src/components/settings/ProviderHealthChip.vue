<template>
    <q-chip
        dense
        outline
        :color="color"
        :text-color="color"
        size="sm"
        :icon="icon"
    >
        {{ label }}
        <q-tooltip>{{ tooltip }}</q-tooltip>
    </q-chip>
</template>

<script lang="ts" setup>
    import type { DataProviderHealth } from 'src/services/api/merchantManagementApiService';
    import { computed } from 'vue';

    const props = defineProps<{ health: DataProviderHealth }>();

    const color = computed(() => {
        if (props.health.skipped) return 'grey-7';
        return props.health.is_healthy ? 'positive' : 'negative';
    });

    const icon = computed(() => {
        if (props.health.skipped) return 'help_outline';
        return props.health.is_healthy ? 'check_circle' : 'cancel';
    });

    const label = computed(() => {
        if (props.health.skipped) return 'Not probed';
        return props.health.is_healthy ? 'Healthy' : 'Unhealthy';
    });

    const tooltip = computed(() => {
        const host = (() => {
            try {
                return new URL(props.health.base_url).host;
            } catch {
                return props.health.base_url;
            }
        })();
        if (props.health.skipped) {
            return `${host} — skipped (no enabled merchant matches this provider)`;
        }
        return props.health.is_healthy
            ? `${host} responded to the last health check`
            : `${host} failed the last health check`;
    });
</script>
