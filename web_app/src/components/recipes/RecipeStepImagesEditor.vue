<template>
    <!--
        PROPOSAL_RECIPE_IMAGE_STEPS — editor for the "image" steps_mode.

        The user uploads ordered photos of their recipe steps (a cookbook
        spread, a handwritten card, a printout); we resize + re-encode via
        the centralised `processImageFile` and emit data-URLs for the
        recipe save path to send.

        Intentionally the dumbest editor in the app — no captions, no
        per-image notes, no OCR. Pictures are pictures. R-007.
    -->
    <div class="recipe-step-images-editor">
        <div
            v-if="modelValue.length === 0"
            class="recipe-step-images-editor__empty dora-text-muted q-mb-sm"
        >
            No images yet. Add photos of your steps in the order you want to cook them.
            Cook mode will show them as a scrollable gallery.
        </div>

        <div v-if="modelValue.length > 0" class="recipe-step-images-editor__list">
            <div
                v-for="(row, index) in modelValue"
                :key="row.client_id"
                class="recipe-step-images-editor__row"
            >
                <div class="recipe-step-images-editor__index">{{ index + 1 }}</div>
                <img
                    :src="row.preview_url"
                    :alt="`Step image ${index + 1}`"
                    class="recipe-step-images-editor__thumb"
                />
                <div class="recipe-step-images-editor__actions">
                    <BaseButton
                        variant="icon"
                        :icon="ICONS.arrow_upward"
                        aria-label="Move up"
                        :disabled="index === 0"
                        @click="onMove(row.client_id, -1)"
                    />
                    <BaseButton
                        variant="icon"
                        :icon="ICONS.arrow_downward"
                        aria-label="Move down"
                        :disabled="index === modelValue.length - 1"
                        @click="onMove(row.client_id, +1)"
                    />
                    <BaseButton
                        variant="ghost"
                        :icon="ICONS.delete_outline"
                        label="Remove"
                        @click="onRemove(row.client_id)"
                    />
                </div>
            </div>
        </div>

        <div class="row q-gutter-sm q-mt-sm items-center">
            <ImageSourcePicker
                variant="secondary"
                :take-photo-label="`${addVerb} (camera)`"
                :pick-label="`${addVerb} (files)`"
                multiple
                accept="image/jpeg,image/png,image/webp"
                :loading="busy"
                :disabled="atCap"
                @pick="onPick"
                @error="onError"
            />
            <div v-if="atCap" class="text-caption dora-text-muted">
                Image cap reached ({{ MAX_IMAGES }}). Remove one to add another.
            </div>
        </div>
        <div v-if="error" class="text-caption text-negative q-mt-xs">{{ error }}</div>
    </div>
</template>

<script setup lang="ts">
    import { computed, ref } from 'vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import ImageSourcePicker from 'src/components/ImageSourcePicker.vue';
    import type { ProcessedImage } from 'src/services/files/imageService';
    import type { EditableStepImage } from 'src/components/recipes/recipeStepImageEditorTypes';

    const props = defineProps<{
        modelValue: EditableStepImage[];
    }>();

    const emit = defineEmits<{
        (e: 'update:modelValue', value: EditableStepImage[]): void;
    }>();

    // Soft cap mirrored from the server (recipe_step_image_access.MAX_…).
    const MAX_IMAGES = 20;

    const error = ref<string | null>(null);
    const busy = ref(false);

    const atCap = computed(() => props.modelValue.length >= MAX_IMAGES);
    const addVerb = computed(() =>
        props.modelValue.length === 0 ? 'Add images' : 'Add more',
    );

    function newClientId(): string {
        if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
            return crypto.randomUUID();
        }
        return `tmp-${Math.random().toString(36).slice(2)}-${Date.now()}`;
    }

    // ImageSourcePicker emits one `pick` per file in order, so we buffer
    // into a transient queue and flush after processing settles. The cap
    // check happens here (the primitive is cap-agnostic).
    const pickQueue = ref<EditableStepImage[]>([]);
    let flushTimer: ReturnType<typeof setTimeout> | null = null;

    function onPick(image: ProcessedImage) {
        error.value = null;
        if (props.modelValue.length + pickQueue.value.length >= MAX_IMAGES) {
            error.value = `Image cap is ${MAX_IMAGES}. Some files were skipped.`;
            return;
        }
        busy.value = true;
        pickQueue.value.push({
            client_id: newClientId(),
            existing_image_id: null,
            preview_url: image.dataUrl,
            data_url: image.dataUrl,
        });
        // Coalesce a burst of `pick` events into one update so the parent
        // sees one append, not N. Settles a tick after the last emit.
        if (flushTimer) clearTimeout(flushTimer);
        flushTimer = setTimeout(flushQueue, 0);
    }

    function flushQueue() {
        flushTimer = null;
        const queued = pickQueue.value;
        pickQueue.value = [];
        busy.value = false;
        if (queued.length === 0) return;
        emit('update:modelValue', [...props.modelValue, ...queued]);
    }

    function onError(message: string) {
        error.value = message;
        busy.value = false;
    }

    function onRemove(clientId: string) {
        emit(
            'update:modelValue',
            props.modelValue.filter(row => row.client_id !== clientId),
        );
    }

    function onMove(clientId: string, delta: -1 | 1) {
        const list = [...props.modelValue];
        const idx = list.findIndex(r => r.client_id === clientId);
        if (idx < 0) return;
        const target = idx + delta;
        if (target < 0 || target >= list.length) return;
        const moved = list.splice(idx, 1)[0];
        if (!moved) return;
        list.splice(target, 0, moved);
        emit('update:modelValue', list);
    }
</script>

<style scoped lang="scss">
    .recipe-step-images-editor__list {
        display: flex;
        flex-direction: column;
        gap: var(--space-sm);
    }
    .recipe-step-images-editor__row {
        display: flex;
        align-items: center;
        gap: var(--space-sm);
        padding: var(--space-sm);
        background: var(--c-surface-2);
        border: 1px solid var(--c-line);
        border-radius: var(--radius-md);
    }
    .recipe-step-images-editor__actions {
        display: flex;
        align-items: center;
        gap: var(--space-xs);
        margin-left: auto;
    }
    .recipe-step-images-editor__index {
        font-weight: 600;
        min-width: 1.5em;
        text-align: center;
        color: var(--c-text-muted);
    }
    .recipe-step-images-editor__thumb {
        width: 96px;
        height: 96px;
        object-fit: cover;
        border-radius: var(--radius-sm);
        flex: 0 0 auto;
    }
</style>
