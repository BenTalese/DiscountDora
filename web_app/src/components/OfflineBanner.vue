<template>
    <transition name="offline-banner">
        <div
            v-if="!isFullyOnline"
            class="offline-banner"
            role="status"
            aria-live="polite"
        >
            <q-icon
                :name="online ? 'sync_problem' : 'wifi_off'"
                size="18px"
                class="q-mr-sm"
            />
            <span class="offline-banner-text">{{ message }}</span>
            <q-space />
            <BaseButton
                variant="ghost"
                size="sm"
                class="dora-text-on-primary"
                :icon="reconnecting ? 'sync' : 'refresh'"
                :label="reconnecting ? 'Checking…' : 'Retry'"
                :loading="reconnecting"
                @click="retryNow"
            />
        </div>
    </transition>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { useNetworkStatus } from 'src/composables/useNetworkStatus';
    import { computed } from 'vue';

    const { online, apiReachable, isFullyOnline, reconnecting, retryNow } =
        useNetworkStatus();

    // Offline is READ-ONLY (owner decision 2026-08-23). The write queue that
    // used to back this banner is gone, so the copy makes no promise about
    // syncing — it says what's true (you can look, you can't change) and
    // nothing more. Two variants because the distinction is actionable: your
    // own connection is your problem to fix, an unreachable server is Dora's.
    const message = computed(() => {
        if (!online.value) return "You're offline — you can look around, but not make changes.";
        if (!apiReachable.value) return "Can't reach Dora — you can look around, but not make changes.";
        return '';
    });
</script>

<style scoped>
    .offline-banner {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 6px 16px;
        background: var(--q-negative);
        color: var(--text-on-primary);
        font-size: 0.85rem;
        font-weight: 500;
        line-height: 1.3;
        position: sticky;
        top: 0;
        z-index: 2500;
        box-shadow: var(--elevation-1);
    }
    .offline-banner-text {
        flex: 1;
        min-width: 0;
    }
    .offline-banner-enter-active,
    .offline-banner-leave-active {
        transition: opacity var(--motion-normal) var(--motion-ease),
            transform var(--motion-normal) var(--motion-ease);
    }
    .offline-banner-enter-from,
    .offline-banner-leave-to {
        opacity: 0;
        transform: translateY(-100%);
    }
</style>
