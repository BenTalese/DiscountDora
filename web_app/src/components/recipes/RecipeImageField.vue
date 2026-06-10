<template>
    <!--
        C-4 Chunk 5 — controlled recipe image field. The parent owns the value
        (preview URL + whether it changed); this component just renders the
        preview/placeholder and reads a picked file into a data URL. Reused by
        the recipe edit dialog + detail page (R-001).
    -->
    <div class="recipe-image-field">
        <div class="recipe-image-field__preview" :style="previewUrl ? '' : placeholderStyle">
            <img v-if="previewUrl" :src="previewUrl" alt="Recipe image" />
            <span v-else class="recipe-image-field__placeholder">{{ initial }}</span>
        </div>
        <div class="row q-gutter-sm q-mt-sm">
            <BaseButton
                variant="secondary"
                :icon="ICONS.image"
                :label="previewUrl ? 'Change image' : 'Add image'"
                @click="trigger"
            />
            <BaseButton
                v-if="previewUrl"
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
    .recipe-image-field__preview {
        width: 100%;
        height: 180px;
        border-radius: 10px;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .recipe-image-field__preview img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .recipe-image-field__placeholder {
        font-size: 3rem;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.92);
    }
    .hidden {
        display: none;
    }
</style>
