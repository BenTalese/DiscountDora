<template>
    <div class="row items-center q-mb-md page-toolbar">
        <q-btn
            v-if="backTo"
            flat
            round
            dense
            class="q-mr-sm dora-text-secondary"
            :icon="ICONS.arrow_back"
            :to="backTo"
            aria-label="Back"
        />
        <div class="col">
            <div class="text-h5">{{ title }}</div>
            <div v-if="subtitle" class="text-caption dora-text-muted">
                {{ subtitle }}
            </div>
        </div>
        <div class="row items-center q-gutter-sm page-toolbar-actions">
            <slot name="actions" />
        </div>
    </div>
</template>

<script setup lang="ts">
    import { ICONS } from 'src/style/icons';

    defineProps<{
        title: string;
        subtitle?: string;
        backTo?: string | object;
    }>();
</script>

<style scoped>
    .page-toolbar {
        min-height: 44px;
    }
    .page-toolbar-actions {
        flex-shrink: 0;
    }
</style>
