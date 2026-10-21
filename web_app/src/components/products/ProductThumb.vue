<template>
    <!-- `fill` stretches to the parent box instead of sizing itself. A
         `q-avatar` sizes via font-size, so it cannot be told to fill a
         container — passing it `size="100%"` yields a tiny glyph in the
         corner, which is exactly what the product card's square media area
         got before this existed. -->
    <div v-if="fill" class="dora-bg-sunken product-thumb product-thumb--fill">
        <img v-if="src" :src="src" :alt="alt" />
        <q-icon v-else :name="ICONS.shopping_bag" :size="iconSize" />
    </div>
    <q-avatar v-else rounded :size="size" class="dora-bg-sunken product-thumb">
        <img v-if="src" :src="src" :alt="alt" />
        <q-icon v-else :name="ICONS.shopping_bag" :size="iconSize" />
    </q-avatar>
</template>

<script lang="ts" setup>
    /**
     * A product's image, fetched through the HTTP client (R-045).
     *
     * ## Why this exists
     *
     * Three surfaces rendered `<img :src="`/api/products/${id}/image`">`
     * directly — the dashboard's Best-deals and Price-drops rows and
     * `MyProductsPage`. R-045 is explicit that a bare `<img :src>` pointed at an
     * API route is **unauthenticated by construction**: it carries the session
     * cookie only if the browser volunteers it, which depends on SameSite, on
     * the SPA and API being same-site, and on the platform. Those assumptions
     * hold on a dev box and fail in real deployments — a split `app.`/`api.`
     * host makes the subresource cross-site (Lax declines), and the Capacitor
     * shell serves the SPA from an origin that is never the API's.
     *
     * These three were worse than the rule's stated signal, too: the paths were
     * **relative** (`/api/...`), with no `resolveBaseURL()`, so in the Capacitor
     * shell they never even reached the API. And the failure is silent — a
     * broken image, which reads as "this product has no photo" rather than as an
     * auth problem.
     *
     * So: fetch the bytes through `AxiosHttpClient` (which the interceptor
     * authenticates) and hand the browser an object URL, exactly as the
     * QR-label fix does. `objectUrlFor` revokes on a timer, so a list that
     * scrolls through many products doesn't leak.
     *
     * ## Why a component and not a composable
     *
     * All three call sites render the identical anatomy — a rounded `q-avatar`
     * on the sunken surface, the image if there is one, a shopping-bag glyph if
     * not. A composable would have left that markup duplicated three ways
     * (R-001: componentisation first). The fallback glyph now can't drift
     * between surfaces either.
     */
    import { onBeforeUnmount, ref, watch } from 'vue';
    import { ICONS } from 'src/style/icons';
    import AxiosHttpClient from 'src/services/api/axiosHttpClient';
    import { objectUrlFor } from 'src/services/files/printView';

    const props = withDefaults(
        defineProps<{
            productId: string;
            /** Server-provided flag. When false we never make the request —
             *  the glyph is the correct render, not a fallback from a failure. */
            hasImage?: boolean;
            alt?: string;
            /** Avatar size, any CSS length Quasar accepts. Ignored when
             *  `fill` is set. */
            size?: string;
            iconSize?: string;
            /** Stretch to the parent box rather than sizing to `size`. For
             *  full-bleed media (the product card's square image well). */
            fill?: boolean;
        }>(),
        { hasImage: false, alt: '', size: '36px', iconSize: '18px', fill: false },
    );

    const http = new AxiosHttpClient();
    const src = ref<string | null>(null);
    // Tracks the id whose fetch is in flight, so a row recycled onto a
    // different product (a `v-for` re-keying, a filter change) can't paint the
    // previous product's photo when the slower response lands.
    let inFlightFor: string | null = null;

    async function load(productId: string, hasImage: boolean) {
        src.value = null;
        if (!hasImage || !productId) {
            inFlightFor = null;
            return;
        }
        inFlightFor = productId;
        try {
            const blob = await http.getBlob(
                `/products/${encodeURIComponent(productId)}/image`,
            );
            // Discard a late response for a product we're no longer showing.
            if (inFlightFor !== productId) return;
            src.value = objectUrlFor(blob);
        } catch {
            // Leave `src` null so the glyph shows. A missing product photo is
            // not worth a toast — but it must not render as a broken image,
            // which is what the bare <img> did on every failure.
            if (inFlightFor === productId) src.value = null;
        }
    }

    watch(
        () => [props.productId, props.hasImage] as const,
        ([id, has]) => void load(id, has),
        { immediate: true },
    );

    onBeforeUnmount(() => {
        // `objectUrlFor` already revokes on a timer; this just stops a late
        // response assigning into an unmounted component.
        inFlightFor = null;
    });
</script>

<style scoped lang="scss">
    .product-thumb :deep(img),
    .product-thumb img {
        object-fit: contain;
        max-width: 100%;
        max-height: 100%;
    }
    /* Absolutely fills its parent rather than taking `height: 100%`, so the
       glyph stays centred in a box sized by `aspect-ratio` without depending
       on that box resolving a percentage height first.
       Requires the parent to be `position: relative`. */
    .product-thumb--fill {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }
</style>
