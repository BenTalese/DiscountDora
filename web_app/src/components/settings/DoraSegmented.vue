<template>
    <div class="dora-segmented" role="radiogroup">
        <button
            v-for="opt in options"
            :key="String(opt.value)"
            type="button"
            role="radio"
            class="dora-segmented__opt"
            :class="{ 'dora-segmented__opt--active': isActive(opt.value) }"
            :aria-checked="isActive(opt.value)"
            :disabled="disabled || opt.disabled"
            @click="onPick(opt.value)"
        >
            <q-icon v-if="opt.icon" :name="opt.icon" size="16px" class="dora-segmented__icon" />
            <span class="dora-segmented__label">{{ opt.label }}</span>
        </button>
    </div>
</template>

<script setup lang="ts" generic="T extends string | number | boolean">
    // IMPL_PLAN_SETTINGS_REBUILD §2.6 + §6.1 (user pick: soft sunken fill).
    // Replacement for q-btn-toggle on settings pages. No saturated green
    // block; active uses dora-bg-sunken + bold text. Inactive uses
    // text-secondary, no border. Hover on inactive → accent text colour.
    export interface DoraSegmentedOption<V> {
        label: string;
        value: V;
        icon?: string;
        disabled?: boolean;
    }

    const props = defineProps<{
        modelValue: T;
        options: DoraSegmentedOption<T>[];
        disabled?: boolean;
    }>();
    const emit = defineEmits<{ (e: 'update:modelValue', value: T): void }>();

    function isActive(v: T): boolean {
        return props.modelValue === v;
    }

    function onPick(v: T): void {
        if (v === props.modelValue) return;
        emit('update:modelValue', v);
    }
</script>

<style scoped lang="scss">
    .dora-segmented {
        display: inline-flex;
        flex-wrap: wrap;
        align-items: stretch;
        gap: 2px;
        padding: 2px;
        border-radius: 8px;
        background: color-mix(in srgb, var(--text-primary) 4%, transparent);
        max-width: 100%;
    }
    .dora-segmented__opt {
        all: unset;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 8px 14px;
        min-height: 32px;
        border-radius: 6px;
        cursor: pointer;
        color: var(--text-secondary);
        font-size: 0.8125rem;
        font-weight: 500;
        line-height: 1;
        white-space: nowrap;
        transition: color 0.18s ease, background-color 0.18s ease, font-weight 0s;
    }
    .dora-segmented__opt:not(.dora-segmented__opt--active):hover {
        color: var(--q-accent);
    }
    .dora-segmented__opt:focus-visible {
        outline: 2px solid var(--ring-focus);
        outline-offset: 1px;
    }
    .dora-segmented__opt--active {
        background: var(--surface-sunken);
        color: var(--text-primary);
        font-weight: 700;
    }
    .dora-segmented__opt[disabled] {
        opacity: 0.5;
        cursor: not-allowed;
    }
    .dora-segmented__icon { flex: 0 0 auto; }
    .dora-segmented__label { white-space: nowrap; }

    @media (max-width: 599px) {
        .dora-segmented {
            overflow-x: auto;
            scrollbar-width: none;
            flex-wrap: nowrap;
        }
        .dora-segmented::-webkit-scrollbar { display: none; }
    }
</style>
