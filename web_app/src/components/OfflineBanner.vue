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
            <span class="offline-banner-text">
                {{ message }}
                <span v-if="queuedCount > 0" class="offline-banner-queue">
                    · {{ queuedCount }} change{{ queuedCount === 1 ? '' : 's' }} queued
                </span>
            </span>
            <q-space />
            <q-btn
                flat
                dense
                no-caps
                size="sm"
                color="white"
                :icon="reconnecting ? 'sync' : 'refresh'"
                :label="reconnecting ? 'Checking…' : 'Retry'"
                :loading="reconnecting"
                @click="retryNow"
            />
        </div>
    </transition>
</template>

<script lang="ts" setup>
    import { useNetworkStatus } from 'src/composables/useNetworkStatus';
    import { useOfflineQueue } from 'src/composables/useOfflineQueue';
    import { computed } from 'vue';

    const { online, apiReachable, isFullyOnline, reconnecting, retryNow } =
        useNetworkStatus();
    const { queuedCount } = useOfflineQueue();

    const message = computed(() => {
        if (!online.value) {
            return "You're offline. Some actions are queued and will sync when you're back.";
        }
        if (!apiReachable.value) {
            return "We can't reach the server. Most actions still work and will sync when we reconnect.";
        }
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
        color: white;
        font-size: 0.85rem;
        font-weight: 500;
        line-height: 1.3;
        position: sticky;
        top: 0;
        z-index: 2500;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
    }
    .offline-banner-text {
        flex: 1;
        min-width: 0;
    }
    .offline-banner-queue {
        opacity: 0.85;
        font-weight: 400;
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
