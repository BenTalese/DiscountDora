<template>
    <!--
        PROPOSAL_RECIPE_IMAGE_STEPS — read-only viewer for the "image"
        steps_mode. Used on the recipe detail page steps slot when
        `steps_mode === 'image'`. Cook mode uses its own dedicated
        component (RecipeCookModeImageView) for the larger gallery.
    -->
    <div v-if="images.length === 0" class="dora-text-muted">
        No step images.
    </div>
    <div v-else class="recipe-step-images-viewer">
        <div
            v-for="(image, index) in images"
            :key="image.image_id"
            class="recipe-step-images-viewer__row"
        >
            <div class="recipe-step-images-viewer__index">{{ index + 1 }}</div>
            <img
                :src="srcFor(image)"
                :alt="`Step image ${index + 1}`"
                class="recipe-step-images-viewer__thumb"
                @click="$emit('zoom', image)"
            />
        </div>
    </div>
</template>

<script setup lang="ts">
    import type { RecipeStepImage } from 'src/models/recipe';

    const props = defineProps<{
        recipeId: string;
        images: RecipeStepImage[];
    }>();

    defineEmits<{
        (e: 'zoom', image: RecipeStepImage): void;
    }>();

    function srcFor(image: RecipeStepImage): string {
        return `/api/recipes/${props.recipeId}/step-images/${image.image_id}`;
    }
</script>

<style scoped lang="scss">
    .recipe-step-images-viewer {
        display: flex;
        flex-direction: column;
        gap: var(--space-sm);
    }
    .recipe-step-images-viewer__row {
        display: flex;
        align-items: center;
        gap: var(--space-sm);
    }
    .recipe-step-images-viewer__index {
        font-weight: 600;
        min-width: 1.5em;
        text-align: center;
        color: var(--c-text-muted);
    }
    .recipe-step-images-viewer__thumb {
        width: 100%;
        max-width: 480px;
        height: auto;
        border-radius: var(--radius-md);
        border: 1px solid var(--c-line);
        cursor: zoom-in;
        object-fit: contain;
    }
</style>
