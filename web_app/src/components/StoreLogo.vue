<template>
    <!-- store logo. Resolution order:
         1. The store's uploaded image (when has_image is true).
         2. A deterministic hash-swatch + initial pill, so unknown stores
            still render predictably without licensing risk. Dora ships
            zero logos; everything else falls through to the swatch.

         The pill matches the size used by the previous MerchantLogo so
         existing layouts don't reflow. -->
    <img
        v-if="previewSrc || hasImage"
        :src="previewSrc || imageUrl"
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
    import { hashSwatch } from 'src/style/storeSwatch';
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
            /** Local (data-URL) image to show instead of the server's, for
             *  previewing a just-picked logo before it has been saved — at
             *  that point there is no `storeId` to build a URL from. */
            previewSrc?: string | null | undefined;
            height?: number;
            width?: number;
        }>(),
        { height: 32, width: 48, hasImage: false, storeId: null, previewSrc: null },
    );

    // The palette + hash moved to `src/style/storeSwatch.ts` so the shopping
    // list's store breakdown draws each store in the same colour this
    // placeholder does (2026-08-26 feedback). R-002 carve-out and the
    // reasoning for determinism live with it there.
    const swatch = computed(() => hashSwatch(props.name));

    const placeholderStyle = computed(() => ({
        height: `${props.height}px`,
        minWidth: `${props.width}px`,
        background: swatch.value.background,
        color: swatch.value.ink,
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
