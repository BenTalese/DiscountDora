<template>
    <!-- Text placeholder until we have the real ALDI mark.
         Matches the visual weight of ColesLogo / WoolworthsLogo (~32×48 px). -->
    <div
        class="dora-logo-placeholder dora-logo-aldi"
        :style="{ height: `${height}px`, width: `${width}px` }"
        role="img"
        aria-label="ALDI"
    >
        ALDI
    </div>
</template>

<script lang="ts" setup>
    interface IAldiLogoProps {
        height: number;
        width: number;
    }
    withDefaults(defineProps<IAldiLogoProps>(), {
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
    /* ALDI's brand uses orange/blue. Approximated, not exact. */
    .dora-logo-aldi {
        background: linear-gradient(135deg, #f7a600 0%, #f7a600 60%, #0e306f 60%, #0e306f 100%);
        color: white;
        text-shadow: 0 1px 0 rgba(0, 0, 0, 0.25);
    }
</style>
