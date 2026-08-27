<template>
    <!--
        PROPOSAL_RECIPE_IMAGE_STEPS — cook-mode renderer for `steps_mode
        === 'image'`. Vertical scroll of every step image full-width; tap
        to zoom. No per-step navigation, no per-step ingredient highlight,
        no auto-timer detection — cooking from images is the dumbest mode
        on purpose. Ingredients panel + finish flow stay shared with the
        other modes (rendered by the host page, not here).
    -->
    <div class="cook-mode-image-view">
        <div
            v-if="images.length === 0"
            class="cook-mode-image-view__empty dora-text-muted text-center q-pa-xl"
        >
            This recipe is in image mode but has no images yet.
            Add some from the recipe's edit page.
        </div>
        <div
            v-for="(image, index) in images"
            :key="image.image_id"
            class="cook-mode-image-view__row"
        >
            <div class="cook-mode-image-view__index dora-text-muted text-caption">
                Step {{ index + 1 }} of {{ images.length }}
            </div>
            <img
                v-if="!failed.has(image.image_id)"
                :src="srcFor(image)"
                :alt="`Step ${index + 1}`"
                class="cook-mode-image-view__image"
                @click="openZoom(image)"
                @error="failed.add(image.image_id)"
            />
            <!-- A broken <img> renders its alt text, which here reads as a
                 plain "Step 1" line and is indistinguishable from a recipe
                 that simply has no photo. Say what actually happened. -->
            <div v-else class="cook-mode-image-view__broken dora-text-muted text-center q-pa-md">
                <q-icon :name="ICONS.image_not_supported" size="32px" />
                <div class="text-caption q-mt-xs">This step's photo couldn't be loaded.</div>
            </div>
        </div>

        <q-dialog v-model="zoomOpen" maximized>
            <q-card class="cook-mode-image-view__zoom">
                <q-card-section class="row items-center q-pa-sm">
                    <q-space />
                    <BaseButton
                        variant="icon"
                        :icon="ICONS.close"
                        aria-label="Close zoom"
                        @click="zoomOpen = false"
                    />
                </q-card-section>
                <q-card-section class="cook-mode-image-view__zoom-body">
                    <img
                        v-if="zoomImage && !failed.has(zoomImage.image_id)"
                        :src="srcFor(zoomImage)"
                        alt="Zoomed step image"
                        class="cook-mode-image-view__zoom-image"
                        @error="zoomImage && failed.add(zoomImage.image_id)"
                    />
                    <div v-else class="dora-text-muted text-center q-pa-xl">
                        <q-icon :name="ICONS.image_not_supported" size="48px" />
                        <div class="q-mt-sm">This step's photo couldn't be loaded.</div>
                    </div>
                </q-card-section>
            </q-card>
        </q-dialog>
    </div>
</template>

<script setup lang="ts">
    import { reactive, ref } from 'vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import { recipeStepImageUrl } from 'src/services/api/recipeApiService';
    import { ICONS } from 'src/style/icons';
    import type { RecipeStepImage } from 'src/models/recipe';

    const props = defineProps<{
        recipeId: string;
        images: RecipeStepImage[];
    }>();

    const zoomOpen = ref(false);
    const zoomImage = ref<RecipeStepImage | null>(null);
    /** Image ids whose fetch failed, so the row can say so rather than
     *  degrading to bare alt text. `reactive` (not `ref`) because a Set
     *  mutated in place needs deep reactivity to re-render. */
    const failed = reactive(new Set<string>());

    /** R-003 — the step-image URL has one builder, `recipeStepImageUrl`, which
     *  prefixes `resolveBaseURL()`. This component hand-rolled the path as a
     *  literal `/api/...`, which only resolves when the SPA is served from the
     *  same origin as the API. Anywhere else — the dev server, the desktop
     *  bundle, a reverse-proxied self-host on a sub-path — every step image
     *  404'd and the browser fell back to the `alt` text, which is exactly the
     *  reported *"photo steps don't appear, it's just text like 'step 1', and
     *  tapping it shows a broken modal"* (owner feedback 2026-08-27). */
    function srcFor(image: RecipeStepImage): string {
        return recipeStepImageUrl(props.recipeId, image.image_id);
    }

    function openZoom(image: RecipeStepImage) {
        zoomImage.value = image;
        zoomOpen.value = true;
    }
</script>

<style scoped lang="scss">
    .cook-mode-image-view {
        display: flex;
        flex-direction: column;
        gap: var(--space-md);
        margin-bottom: var(--space-lg);
    }
    .cook-mode-image-view__row {
        display: flex;
        flex-direction: column;
        gap: var(--space-xs);
    }
    .cook-mode-image-view__image {
        width: 100%;
        height: auto;
        max-height: 80vh;
        object-fit: contain;
        border-radius: var(--radius-md);
        border: 1px solid var(--c-line);
        background: var(--c-surface-2);
        cursor: zoom-in;
    }
    .cook-mode-image-view__broken {
        border: 1px dashed var(--c-line);
        border-radius: var(--radius-md);
        background: var(--c-surface-2);
    }
    .cook-mode-image-view__zoom {
        background: var(--c-surface-1);
    }
    .cook-mode-image-view__zoom-body {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
    }
    .cook-mode-image-view__zoom-image {
        max-width: 100%;
        max-height: calc(100vh - 80px);
        object-fit: contain;
    }
</style>
