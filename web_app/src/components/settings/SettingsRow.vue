<template>
    <div class="settings-row" :class="{ 'settings-row--stacked': stacked }">
        <div class="settings-row__info">
            <div v-if="label || $slots.label" class="settings-row__label">
                <slot name="label">{{ label }}</slot>
            </div>
            <div v-if="help || $slots.help" class="settings-row__help">
                <slot name="help">{{ help }}</slot>
            </div>
        </div>
        <div class="settings-row__control">
            <slot />
        </div>
    </div>
</template>

<script setup lang="ts">
    // IMPL_PLAN_SETTINGS_REBUILD §2.5 — single row inside a SettingsSection:
    // left = label + optional one-line help; right = control. Collapses to
    // label-above-control on narrow viewports (Phase 5 verifies).
    defineProps<{
        label?: string;
        help?: string;
        stacked?: boolean;
    }>();
</script>

<style scoped lang="scss">
    .settings-row {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 24px;
        padding: 6px 0;
    }
    .settings-row__info {
        flex: 1 1 auto;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .settings-row__label {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-primary);
        line-height: 1.3;
    }
    .settings-row__help {
        font-size: 0.8125rem;
        color: var(--text-secondary);
        line-height: 1.35;
    }
    .settings-row__control {
        flex: 0 0 auto;
        min-width: 0;
        max-width: 60%;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .settings-row--stacked,
    .settings-row--stacked.settings-row {
        flex-direction: column;
        align-items: stretch;
        gap: 10px;
    }
    .settings-row--stacked .settings-row__control {
        max-width: 100%;
        width: 100%;
    }

    @media (max-width: 599px) {
        .settings-row {
            flex-direction: column;
            align-items: stretch;
            gap: 10px;
        }
        .settings-row__control {
            max-width: 100%;
            width: 100%;
        }
    }
</style>
