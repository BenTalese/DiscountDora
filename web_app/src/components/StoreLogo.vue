<template>
    <!-- FU-189 — store logo. Resolution order:
         1. The store's uploaded image (when has_image is true).
         2. A deterministic hash-swatch + initial pill, so unknown stores
            still render predictably without licensing risk. Dora ships
            zero logos; everything else falls through to the swatch.

         The pill matches the size used by the previous MerchantLogo so
         existing layouts don't reflow. -->
    <img
        v-if="hasImage"
        :src="imageUrl"
        :alt="name"
        class="dora-logo-image"
        :style="{ height: `${height}px`, width: `auto`, minWidth: `${width}px` }"
    />
    <div
        v-else
        class="dora-logo-placeholder"
        :style="placeholderStyle"
        role="img"
        :aria-label="name"
    >
        {{ initial }}
    </div>
</template>

<script lang="ts" setup>
    import { resolveBaseURL } from 'src/services/api/axiosHttpClient';
    import { computed } from 'vue';

    const props = withDefaults(
        defineProps<{
            /** Store name to render as the swatch initial / alt text. */
            name: string;
            /** Store id; required when `hasImage` is true so the route
             *  can be built. */
            storeId?: string | null | undefined;
            /** Server's `has_image` flag (StoreDto / LinkedStore). */
            hasImage?: boolean;
            height?: number;
            width?: number;
        }>(),
        { height: 32, width: 48, hasImage: false, storeId: null },
    );

    /** Stable, deterministic colour from the store name. We pick from a
     *  small palette of theme-compatible neutrals so the swatches don't
     *  clash with the Pesto palette in either theme. */
    const SWATCH_PALETTE = [
        ['#ece1c9', '#2e2820'], // sand
        ['#d8e3d0', '#1f2a1c'], // pesto-tint
        ['#e6dbe6', '#2c1f2c'], // mauve
        ['#dde6e9', '#1c2629'], // mist
        ['#ecd9d0', '#3a1f17'], // terracotta
        ['#dfe1e8', '#1d1f28'], // slate
    ] as const;

    function hashIndex(text: string): number {
        // 32-bit FNV-1a over the lowercased name. Plenty for picking
        // one of N palette entries with even-ish distribution.
        let h = 0x811c9dc5;
        const s = text.toLowerCase();
        for (let i = 0; i < s.length; i++) {
            h ^= s.charCodeAt(i);
            h = Math.imul(h, 0x01000193);
        }
        return (h >>> 0) % SWATCH_PALETTE.length;
    }

    const swatch = computed(() => SWATCH_PALETTE[hashIndex(props.name || '?')]!);

    const placeholderStyle = computed(() => ({
        height: `${props.height}px`,
        minWidth: `${props.width}px`,
        // R-002 carve-out: hash-swatch palette is a deterministic
        // brand-stable fallback (per ENGINEERING_STANDARDS §R-002
        // carve-outs — "deterministic hash swatches"). The two hex
        // values come from a sealed 6-entry palette above.
        background: swatch.value[0],
        color: swatch.value[1],
    }));

    const initial = computed(() => {
        const trimmed = (props.name || '').trim();
        if (!trimmed) return '?';
        // First letter of the first word, uppercased. Keeps the pill tight
        // on long names like "Foodstuffs North Island".
        return trimmed[0]!.toUpperCase();
    });

    const imageUrl = computed(() => {
        if (!props.storeId) return '';
        // Cache-bust query param: not strictly necessary (the route already
        // sends Cache-Control: no-cache) but it matches the stock-item
        // image pattern (FU-125) for consistency.
        return `${resolveBaseURL()}/stores/${props.storeId}/image`;
    });
</script>

<style scoped>
    .dora-logo-placeholder {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 2px 6px;
        font-weight: 700;
        font-size: 0.95rem;
        letter-spacing: 0.02em;
        border-radius: 4px;
        user-select: none;
    }
    .dora-logo-image {
        display: inline-block;
        border-radius: 4px;
        object-fit: contain;
    }
</style>
