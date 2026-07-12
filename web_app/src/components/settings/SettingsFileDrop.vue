<template>
    <div
        class="file-drop"
        :class="{
            'file-drop--dragging': dragging,
            'file-drop--busy': loading,
            'file-drop--disabled': disabled,
            'file-drop--filled': !!modelValue,
        }"
        role="button"
        :tabindex="disabled ? -1 : 0"
        :aria-label="label"
        @click="onZoneClick"
        @keydown.enter.prevent="onZoneClick"
        @keydown.space.prevent="onZoneClick"
        @dragover.prevent="onDragOver"
        @dragleave.prevent="onDragLeave"
        @drop.prevent="onDrop"
    >
        <!--
            The visible drop-zone (the wrapping div: role="button" + aria-label
            + tabindex) is the exposed control; this input is a hidden
            implementation detail triggered programmatically via inputEl.click().
            Keep it OUT of the accessibility tree (FU-542): aria-hidden removes
            the nested-interactive + unlabelled-input violations, tabindex="-1"
            keeps keyboard focus on the wrapper only.
        -->
        <input
            ref="inputEl"
            type="file"
            class="file-drop__input"
            aria-hidden="true"
            tabindex="-1"
            :accept="accept"
            :disabled="disabled"
            @change="onInputChange"
        />

        <!-- Idle / prompt state -->
        <template v-if="!modelValue && !loading">
            <q-icon :name="ICONS.cloud_upload" size="30px" class="file-drop__icon" />
            <div class="file-drop__label">{{ label }}</div>
            <div v-if="hint" class="file-drop__hint">{{ hint }}</div>
        </template>

        <!-- Selected-file state -->
        <template v-else-if="modelValue && !loading">
            <q-icon :name="ICONS.attach_file" size="22px" class="file-drop__icon" />
            <div class="file-drop__file">
                <span class="file-drop__filename">{{ modelValue.name }}</span>
                <span class="file-drop__filesize">{{ formatSize(modelValue.size) }}</span>
            </div>
            <BaseButton
                variant="icon"
                :icon="ICONS.close"
                aria-label="Remove file"
                @click.stop="onClear"
            >
                <q-tooltip>Remove file</q-tooltip>
            </BaseButton>
        </template>

        <!-- Busy state -->
        <template v-else>
            <q-spinner size="24px" class="file-drop__icon" />
            <div class="file-drop__label">
                {{ progressValue > 0 && progressValue < 1
                    ? `Uploading ${Math.round(progressValue * 100)}%`
                    : (loadingText || 'Working…') }}
            </div>
            <q-linear-progress
                v-if="progressValue > 0 && progressValue < 1"
                :value="progressValue"
                rounded
                size="6px"
                color="primary"
                class="file-drop__progress"
            />
        </template>
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { computed, ref } from 'vue';

    const props = defineProps<{
        modelValue: File | null;
        accept?: string;
        label: string;
        hint?: string;
        loading?: boolean;
        loadingText?: string;
        progress?: number;
        disabled?: boolean;
    }>();

    const progressValue = computed(() => props.progress ?? 0);

    const emit = defineEmits<{
        (e: 'update:modelValue', value: File | null): void;
        (e: 'pick', value: File): void;
        (e: 'clear'): void;
    }>();

    const inputEl = ref<HTMLInputElement | null>(null);
    const dragging = ref(false);

    function onZoneClick() {
        if (props.disabled || props.loading) return;
        inputEl.value?.click();
    }

    function take(file: File | null) {
        if (!file) return;
        emit('update:modelValue', file);
        emit('pick', file);
    }

    function onInputChange(event: Event) {
        const target = event.target as HTMLInputElement;
        take(target.files?.[0] ?? null);
        // Reset so re-picking the same file still fires change.
        target.value = '';
    }

    function onDragOver() {
        if (props.disabled || props.loading) return;
        dragging.value = true;
    }
    function onDragLeave() {
        dragging.value = false;
    }
    function onDrop(event: DragEvent) {
        dragging.value = false;
        if (props.disabled || props.loading) return;
        take(event.dataTransfer?.files?.[0] ?? null);
    }

    function onClear() {
        emit('update:modelValue', null);
        emit('clear');
    }

    function formatSize(bytes: number): string {
        if (bytes < 1024) return `${bytes} B`;
        const kb = bytes / 1024;
        if (kb < 1024) return `${kb.toFixed(1)} KB`;
        const mb = kb / 1024;
        if (mb < 1024) return `${mb.toFixed(1)} MB`;
        return `${(mb / 1024).toFixed(2)} GB`;
    }
</script>

<style scoped lang="scss">
    .file-drop {
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: var(--space-2);
        min-height: 132px;
        padding: var(--space-5) var(--space-4);
        border: 1.5px dashed var(--border-strong);
        border-radius: var(--radius-lg);
        background: var(--surface-elevated);
        color: var(--text-secondary);
        text-align: center;
        cursor: pointer;
        transition: border-color 160ms ease, background 160ms ease, color 160ms ease;
    }
    .file-drop:hover:not(.file-drop--disabled):not(.file-drop--busy),
    .file-drop:focus-visible {
        border-color: var(--brand-primary);
        background: color-mix(in srgb, var(--brand-primary) 5%, var(--surface-elevated));
        color: var(--text-primary);
        outline: none;
    }
    .file-drop--dragging {
        border-color: var(--brand-primary);
        border-style: solid;
        background: color-mix(in srgb, var(--brand-primary) 10%, var(--surface-elevated));
        color: var(--text-primary);
    }
    .file-drop--filled {
        flex-direction: row;
        min-height: 0;
        padding: var(--space-3) var(--space-4);
        border-style: solid;
        border-color: var(--border-default);
        background: var(--surface-component);
        cursor: default;
        text-align: left;
    }
    .file-drop--busy {
        cursor: default;
    }
    .file-drop--disabled {
        opacity: 0.55;
        cursor: not-allowed;
    }

    .file-drop__input {
        display: none;
    }
    .file-drop__icon {
        color: var(--brand-primary);
        flex: 0 0 auto;
    }
    .file-drop__label {
        font-size: 0.9375rem;
        font-weight: 600;
        color: inherit;
    }
    .file-drop__hint {
        font-size: 0.8125rem;
        color: var(--text-muted);
        line-height: 1.35;
    }
    .file-drop__file {
        flex: 1 1 auto;
        min-width: 0;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 2px;
    }
    .file-drop__filename {
        font-size: 0.9375rem;
        font-weight: 600;
        color: var(--text-primary);
        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .file-drop__filesize {
        font-size: 0.8125rem;
        color: var(--text-muted);
    }
    .file-drop__progress {
        width: min(280px, 100%);
        margin-top: var(--space-1);
    }
</style>
