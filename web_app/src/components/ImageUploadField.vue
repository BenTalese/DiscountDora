<template>
    <!--
        Generic image upload field. Owns the preview/placeholder render and
        reads a picked file into a data URL. The parent owns the value
        (preview URL + whether it changed) and the commit semantics — this
        component only emits `pick` (data URL ready) and `clear`. Originally
        built for recipes (RecipeImageField), generalised when the stock-item
        detail surface adopted it (FU-126 / R-001 second-consumer threshold).
    -->
    <div class="image-upload-field">
        <div class="image-upload-field__preview" :style="previewUrl ? '' : placeholderStyle">
            <img v-if="previewUrl" :src="previewUrl" :alt="altText" />
            <span v-else class="image-upload-field__placeholder">{{ initial }}</span>
        </div>
        <div class="row q-gutter-sm q-mt-sm">
            <BaseButton
                variant="secondary"
                :icon="ICONS.image"
                :label="addLabel"
                @click="trigger"
            />
            <BaseButton
                v-if="canClear"
                variant="ghost"
                :icon="ICONS.delete_outline"
                label="Remove"
                @click="emit('clear')"
            />
        </div>
        <input
            ref="fileInput"
            type="file"
            accept="image/*"
            class="hidden"
            @change="onFile"
        />
        <div v-if="error" class="text-caption text-negative q-mt-xs">{{ error }}</div>
    </div>
</template>

<script setup lang="ts">
    import { computed, ref } from 'vue';
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';

    const props = defineProps<{
        previewUrl: string | null;
        name?: string;
        alt?: string;
        // When omitted, Remove appears whenever `previewUrl` is set
        // (existing call-site behaviour). Surfaces with a fallback preview
        // (e.g. product image on a stock item) pass `false` so the button
        // reads "Add image" and Remove is hidden — the user never uploaded
        // that image, so there's nothing to remove.
        canClear?: boolean;
    }>();

    const emit = defineEmits<{
        (e: 'pick', dataUrl: string): void;
        (e: 'clear'): void;
    }>();

    const fileInput = ref<HTMLInputElement | null>(null);
    const error = ref<string | null>(null);

    // ~4MB raw cap — keeps the stored data URL under the server's 6M char cap.
    const MAX_BYTES = 4 * 1024 * 1024;

    const initial = computed(() => (props.name?.trim()[0] ?? '?').toUpperCase());
    const placeholderStyle = computed(() => {
        let hash = 0;
        for (const ch of props.name ?? '') hash = (hash * 31 + ch.charCodeAt(0)) % 360;
        return `background: hsl(${hash}, 45%, 42%)`;
    });
    const altText = computed(() => props.alt ?? props.name ?? 'Image');
    const canClear = computed(() =>
        props.canClear !== undefined ? props.canClear : !!props.previewUrl,
    );
    const addLabel = computed(() => (canClear.value ? 'Change image' : 'Add image'));

    function trigger() {
        error.value = null;
        fileInput.value?.click();
    }

    function onFile(ev: Event) {
        const input = ev.target as HTMLInputElement;
        const file = input.files?.[0];
        input.value = '';
        if (!file) return;
        if (file.size > MAX_BYTES) {
            error.value = 'Image is too large (max 4MB). Pick a smaller one.';
            return;
        }
        const reader = new FileReader();
        reader.onload = () => {
            if (typeof reader.result === 'string') emit('pick', reader.result);
        };
        reader.onerror = () => { error.value = 'Could not read that file.'; };
        reader.readAsDataURL(file);
    }
</script>

<style scoped lang="scss">
    .image-upload-field__preview {
        width: 100%;
        height: 180px;
        border-radius: 10px;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .image-upload-field__preview img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .image-upload-field__placeholder {
        font-size: 3rem;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.92);
    }
    .hidden {
        display: none;
    }
</style>
