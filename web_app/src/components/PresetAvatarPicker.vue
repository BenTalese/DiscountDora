<template>
    <!--
        The pre-made profile pictures (owner ask 2026-10-17) as a wrapping grid
        of round buttons. Shared by onboarding's welcome step and Settings →
        Account so the two can't drift. Picking one renders it to a data URL
        (`renderPresetAvatar`) and emits it; the caller decides whether that's
        an immediate save (Account) or a draft applied on Finish (onboarding).
    -->
    <div class="preset-avatars" role="radiogroup" :aria-label="label">
        <button
            v-for="preset in PRESET_AVATARS"
            :key="preset.key"
            type="button"
            role="radio"
            class="preset-avatar"
            :class="{ 'preset-avatar--active': selectedKey === preset.key }"
            :style="{ background: preset.backdrop }"
            :aria-checked="selectedKey === preset.key"
            :aria-label="preset.label"
            :disabled="disabled || rendering !== null"
            @click="onPick(preset)"
        >
            <img :src="preset.src" alt="" class="preset-avatar__art" draggable="false" />
            <q-icon
                v-if="selectedKey === preset.key"
                :name="ICONS.check_circle"
                size="18px"
                class="preset-avatar__badge"
            />
            <BaseTooltip>{{ preset.label }}</BaseTooltip>
        </button>
    </div>
</template>

<script setup lang="ts">
    import BaseTooltip from 'src/components/BaseTooltip.vue';
    import {
        PRESET_AVATARS,
        renderPresetAvatar,
        type PresetAvatar,
    } from 'src/assets/avatars/presetAvatars';
    import { ICONS } from 'src/style/icons';
    import { ref } from 'vue';

    withDefaults(
        defineProps<{
            /** Key of the preset currently chosen, if the caller tracks one. */
            selectedKey?: string | null;
            disabled?: boolean;
            label?: string;
        }>(),
        { selectedKey: null, disabled: false, label: 'Pick a profile picture' },
    );
    const emit = defineEmits<{
        pick: [payload: { key: string; dataUrl: string }];
        error: [message: string];
    }>();

    const rendering = ref<string | null>(null);

    async function onPick(preset: PresetAvatar) {
        rendering.value = preset.key;
        try {
            const dataUrl = await renderPresetAvatar(preset);
            emit('pick', { key: preset.key, dataUrl });
        } catch (err) {
            emit('error', err instanceof Error ? err.message : 'Could not use that picture.');
        } finally {
            rendering.value = null;
        }
    }
</script>

<style scoped>
    .preset-avatars {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(48px, 1fr));
        gap: var(--space-2);
    }
    .preset-avatar {
        position: relative;
        appearance: none;
        aspect-ratio: 1;
        width: 100%;
        min-width: 44px;
        padding: 0;
        border: 2px solid transparent;
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform var(--motion-fast) var(--motion-ease),
            border-color var(--motion-fast) var(--motion-ease);
    }
    .preset-avatar:hover:not(:disabled) {
        transform: scale(1.08);
    }
    .preset-avatar:focus-visible {
        outline: 2px solid var(--accent-mark);
        outline-offset: 2px;
    }
    .preset-avatar:disabled {
        cursor: default;
        opacity: 0.6;
    }
    .preset-avatar--active {
        /* Selection ring — a graphic, so the 3:1 tier (D-rules). */
        border-color: var(--accent-mark);
    }
    .preset-avatar__art {
        width: 70%;
        height: 70%;
        object-fit: contain;
        pointer-events: none;
    }
    .preset-avatar__badge {
        position: absolute;
        right: -4px;
        bottom: -4px;
        color: var(--accent-mark);
        background: var(--surface-component);
        border-radius: 50%;
    }
</style>
