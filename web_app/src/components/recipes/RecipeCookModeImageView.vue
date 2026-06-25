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
                :src="srcFor(image)"
                :alt="`Step ${index + 1}`"
                class="cook-mode-image-view__image"
                @click="openZoom(image)"
            />
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
                        v-if="zoomImage"
                        :src="srcFor(zoomImage)"
                        :alt="`Zoomed step image`"
                        class="cook-mode-image-view__zoom-image"
                    />
                </q-card-section>
            </q-card>
        </q-dialog>
    </div>
</template>

<script setup lang="ts">
    import { ref } from 'vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import type { RecipeStepImage } from 'src/models/recipe';

    const props = defineProps<{
        recipeId: string;
        images: RecipeStepImage[];
    }>();

    const zoomOpen = ref(false);
    const zoomImage = ref<RecipeStepImage | null>(null);

    function srcFor(image: RecipeStepImage): string {
        return `/api/recipes/${props.recipeId}/step-images/${image.image_id}`;
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
