<template>
    <header class="settings-page-header">
        <div class="settings-page-header__heading">
            <q-icon v-if="icon" :name="icon" size="22px" class="settings-page-header__icon" />
            <div class="settings-page-header__text">
                <h1 class="settings-page-header__title">{{ title }}</h1>
                <p v-if="description || $slots.description" class="settings-page-header__description">
                    <slot name="description">{{ description }}</slot>
                </p>
            </div>
        </div>
        <div v-if="$slots.actions" class="settings-page-header__actions">
            <slot name="actions" />
        </div>
    </header>
</template>

<script setup lang="ts">
    // IMPL_PLAN_SETTINGS_REBUILD §2.5 — standardised page-header chrome:
    // title (h1 / 24px / weight 700) + description + optional eyebrow
    // icon (left of title) + optional right-aligned actions slot
    // (refresh / export / primary action).
    defineProps<{
        title: string;
        description?: string;
        icon?: string;
    }>();
</script>

<style scoped lang="scss">
    .settings-page-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 20px;
    }
    .settings-page-header__heading {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        min-width: 0;
    }
    .settings-page-header__icon {
        color: var(--accent-ink);
        margin-top: 2px;
        flex: 0 0 auto;
    }
    .settings-page-header__text {
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .settings-page-header__title {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: var(--text-primary);
        line-height: 1.2;
    }
    .settings-page-header__description {
        margin: 0;
        color: var(--text-secondary);
        font-size: 0.9375rem;
        max-width: 60ch;
        line-height: 1.4;
    }
    .settings-page-header__actions {
        flex: 0 0 auto;
        display: flex;
        align-items: center;
        gap: 8px;
    }
</style>
