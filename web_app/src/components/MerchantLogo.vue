<template>
    <!-- Renders the right brand logo for a merchant. Unknown merchants fall
         back to a neutral pill so the layout doesn't reflow. -->
    <component
        v-if="logoComponent"
        :is="logoComponent"
        :height="height"
        :width="width"
    />
    <div
        v-else
        class="dora-logo-placeholder dora-logo-fallback"
        :style="{ height: `${height}px`, minWidth: `${width}px` }"
        role="img"
        :aria-label="name"
    >
        {{ name }}
    </div>
</template>

<script lang="ts" setup>
    import AldiLogo from 'src/components/AldiLogo.vue';
    import ColesLogo from 'src/components/ColesLogo.vue';
    import IgaLogo from 'src/components/IgaLogo.vue';
    import WoolworthsLogo from 'src/components/WoolworthsLogo.vue';
    import type { Component } from 'vue';
    import { computed } from 'vue';

    const props = withDefaults(
        defineProps<{
            /** Merchant display name as it appears on `Product.merchant_name`. */
            name: string;
            height?: number;
            width?: number;
        }>(),
        { height: 32, width: 48 }
    );

    // Lookup by case-insensitive merchant name so callers don't have to
    // worry about whether the backend returns "ALDI" or "Aldi".
    const registry: Record<string, Component> = {
        aldi: AldiLogo,
        coles: ColesLogo,
        iga: IgaLogo,
        woolworths: WoolworthsLogo
    };

    const logoComponent = computed<Component | null>(() => {
        return registry[props.name.toLowerCase()] ?? null;
    });
</script>

<style scoped>
    .dora-logo-placeholder {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 2px 6px;
        font-weight: 700;
        font-size: 0.75rem;
        letter-spacing: 0.02em;
        border-radius: 4px;
        user-select: none;
    }
    .dora-logo-fallback {
        background: #ece1c9;
        color: #2e2820;
    }
</style>
