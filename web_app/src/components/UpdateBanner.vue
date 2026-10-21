<template>
    <!-- Pinned under the header when a newer frontend build has been cached by
         the service worker and needs a reload to take effect. Shown to every
         user (their own browser holds the new assets; an admin can't reload it
         for them). Dismissible — reappears next session if still stale.
         Sits below OfflineBanner in MainLayout; distinct accent styling so it
         reads as informational, not an error. -->
    <transition name="update-banner">
        <div
            v-if="showUpdate"
            class="update-banner"
            role="status"
            aria-live="polite"
        >
            <q-icon :name="ICONS.refresh" size="18px" class="q-mr-sm" />
            <span class="update-banner__text">
                A new version of Dora is ready. Reload to pick it up.
            </span>
            <q-space />
            <BaseButton
                variant="ghost"
                size="sm"
                class="dora-text-on-primary"
                :icon="ICONS.refresh"
                label="Reload"
                @click="onReload"
            />
            <BaseButton
                variant="icon"
                size="sm"
                class="dora-text-on-primary"
                :icon="ICONS.close"
                aria-label="Dismiss"
                @click="onDismiss"
            />
        </div>
    </transition>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import {
        applyUpdateReload,
        dismissUpdate,
        updateAvailablePrompt,
    } from 'src/composables/usePwaLifecycle';

    const showUpdate = updateAvailablePrompt();

    function onReload() {
        applyUpdateReload();
    }
    function onDismiss() {
        dismissUpdate();
    }
</script>

<style scoped>
    .update-banner {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 6px 16px;
        background: var(--q-accent);
        color: var(--text-on-primary);
        font-size: 0.85rem;
        font-weight: 500;
        line-height: 1.3;
        position: sticky;
        top: 0;
        z-index: 2500;
        box-shadow: var(--elevation-1);
    }
    .update-banner__text {
        flex: 1;
        min-width: 0;
    }
    .update-banner-enter-active,
    .update-banner-leave-active {
        transition: opacity var(--motion-normal) var(--motion-ease),
            transform var(--motion-normal) var(--motion-ease);
    }
    .update-banner-enter-from,
    .update-banner-leave-to {
        opacity: 0;
        transform: translateY(-100%);
    }
</style>
