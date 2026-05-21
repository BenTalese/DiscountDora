<template>
    <!-- Text placeholder until we have the real IGA mark. -->
    <div
        class="dora-logo-placeholder dora-logo-iga"
        :style="{ height: `${height}px`, width: `${width}px` }"
        role="img"
        aria-label="IGA"
    >
        IGA
    </div>
</template>

<script lang="ts" setup>
    interface IIgaLogoProps {
        height: number;
        width: number;
    }
    withDefaults(defineProps<IIgaLogoProps>(), {
        height: 32,
        width: 48
    });
</script>

<style scoped>
    .dora-logo-placeholder {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 0.75rem;
        letter-spacing: 0.02em;
        border-radius: 4px;
        padding: 2px 6px;
        user-select: none;
    }
    /* IGA's brand uses red. Approximated. */
    .dora-logo-iga {
        background: #d61f25;
        color: white;
    }
</style>
