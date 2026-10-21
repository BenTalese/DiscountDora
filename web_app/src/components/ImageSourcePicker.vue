<template>
    <!--
        FU-334 / R-0NN — single chokepoint for "where does this image come
        from?" UX. Two source affordances:

          • Take photo     → `<input capture="environment">` (mobile only)
          • Pick image     → plain `<input>` (gallery / files / desktop disk)

        Mobile shows both; desktop shows only Pick (no camera, no value to
        offering "Take photo"). Every consumer routes through this so that
        camera-vs-gallery bias stays one decision instead of N — the same
        spirit as `processImageFile` for the resize/encode chokepoint.

        Multi-file selection is supported via `multiple` — useful for
        bulk-upload sites like RecipeStepImagesEditor. Each picked file is
        processed individually and emitted in order; the consumer decides
        whether to batch or apply one-by-one.
    -->
    <div class="row q-gutter-sm items-center image-source-picker">
        <BaseButton
            v-if="cameraVisible"
            :variant="props.variant"
            :icon="ICONS.photo_camera"
            :label="takePhotoLabel"
            :loading="busy"
            :disable="props.disabled"
            dense
            @click="triggerCamera"
        />
        <BaseButton
            :variant="props.variant"
            :icon="ICONS.image"
            :label="pickLabel"
            :loading="busy"
            :disable="props.disabled"
            dense
            @click="triggerPicker"
        />
        <input
            ref="cameraInput"
            type="file"
            :accept="accept"
            capture="environment"
            :multiple="multiple"
            class="image-source-picker__hidden"
            @change="onFiles"
        />
        <input
            ref="pickerInput"
            type="file"
            :accept="accept"
            :multiple="multiple"
            class="image-source-picker__hidden"
            @change="onFiles"
        />
        <div v-if="errorMessage" class="text-caption text-negative full-width">
            {{ errorMessage }}
        </div>
    </div>
</template>

<script setup lang="ts">
    import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import {
        processImageFile,
        type ProcessedImage,
    } from 'src/services/files/imageService';

    const props = withDefaults(defineProps<{
        /** Single shared label override when both buttons would say the
         *  same thing (e.g. an "Add image" / "Change image" surface that
         *  doesn't want to differentiate source). When set, both buttons
         *  use the same label and only the icon distinguishes them.
         *  Empty string = use the per-button defaults. */
        label?: string;
        /** Per-button label overrides. Take precedence over `label`.
         *  Empty string = use defaults. */
        takePhotoLabel?: string;
        pickLabel?: string;
        /** Allow more than one file per click. Each emits its own `pick`. */
        multiple?: boolean;
        /** `accept` for the file inputs. Defaults to `image/*`. */
        accept?: string;
        /** BaseButton variant. */
        variant?: 'primary' | 'secondary' | 'ghost' | 'positive';
        /** External busy state — shows spinners and disables the buttons.
         *  Independent of internal `processing` so the parent can keep the
         *  picker disabled across its own upload round-trip. */
        loading?: boolean;
        disabled?: boolean;
        /** Force the camera button on/off regardless of device detection.
         *  `'auto'` (default) shows it on touch-primary devices only. */
        forceCamera?: 'auto' | 'on' | 'off';
    }>(), {
        label: '',
        takePhotoLabel: '',
        pickLabel: '',
        multiple: false,
        accept: 'image/*',
        variant: 'secondary',
        loading: false,
        disabled: false,
        forceCamera: 'auto',
    });

    const emit = defineEmits<{
        /** Fires once per accepted file, in pick order. */
        (e: 'pick', image: ProcessedImage): void;
        /** Fires once if `processImageFile` rejects a file — message is
         *  safe to show the user verbatim. */
        (e: 'error', message: string): void;
    }>();

    const cameraInput = ref<HTMLInputElement | null>(null);
    const pickerInput = ref<HTMLInputElement | null>(null);
    const processing = ref(false);
    const errorMessage = ref<string | null>(null);

    // Touch-device heuristic for whether to show the camera button.
    // `pointer: coarse` is the standard CSS media query for touch-primary
    // input — covers phones / tablets, excludes most desktops + laptops.
    // Reactive so a tablet attached to a desktop dock flips correctly.
    const isTouchPrimary = ref(false);
    let mediaQuery: MediaQueryList | null = null;
    function updateTouchPrimary(e: MediaQueryList | MediaQueryListEvent) {
        isTouchPrimary.value = e.matches;
    }
    onMounted(() => {
        if (typeof window === 'undefined' || !window.matchMedia) return;
        mediaQuery = window.matchMedia('(pointer: coarse)');
        isTouchPrimary.value = mediaQuery.matches;
        mediaQuery.addEventListener('change', updateTouchPrimary);
    });
    onBeforeUnmount(() => {
        mediaQuery?.removeEventListener('change', updateTouchPrimary);
    });

    const cameraVisible = computed(() => {
        if (props.forceCamera === 'on') return true;
        if (props.forceCamera === 'off') return false;
        return isTouchPrimary.value;
    });

    const busy = computed(() => props.loading || processing.value);

    const takePhotoLabel = computed(
        () => props.takePhotoLabel || props.label || 'Take photo',
    );
    const pickLabel = computed(
        () => props.pickLabel || props.label || 'Choose image',
    );

    function triggerCamera() {
        errorMessage.value = null;
        cameraInput.value?.click();
    }
    function triggerPicker() {
        errorMessage.value = null;
        pickerInput.value?.click();
    }

    async function onFiles(ev: Event) {
        const input = ev.target as HTMLInputElement;
        const files = Array.from(input.files ?? []);
        // Clear immediately so picking the same file twice still re-fires.
        input.value = '';
        if (!files.length) return;

        processing.value = true;
        try {
            for (const file of files) {
                try {
                    const processed = await processImageFile(file);
                    emit('pick', processed);
                }
                catch (err) {
                    const message = err instanceof Error
                        ? err.message
                        : 'Could not read that image.';
                    errorMessage.value = message;
                    emit('error', message);
                    // Stop on first failure when multi-picking so the user
                    // sees the error rather than partial success.
                    break;
                }
            }
        }
        finally {
            processing.value = false;
        }
    }
</script>

<style scoped>
    .image-source-picker__hidden {
        display: none;
    }
</style>
