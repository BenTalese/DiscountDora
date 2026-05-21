<template>
    <div class="dora-bubble-root" :class="{ 'dora-bubble-open': open }">
        <transition name="dora-bubble-pop">
            <DoraChat v-if="open" :current-user="currentUser" @close="onClose" />
        </transition>

        <transition name="dora-bubble-hint">
            <div v-if="showFirstTimeHint && !open" class="dora-bubble-hint">
                <div class="dora-bubble-hint-arrow"></div>
                <div class="dora-bubble-hint-text">
                    <strong>Hi! I'm Dora.</strong>
                    Click me whenever you're lost or want a tip.
                </div>
                <q-btn
                    flat
                    round
                    dense
                    size="sm"
                    icon="close"
                    @click.stop="dismissHint"
                />
            </div>
        </transition>

        <button
            class="dora-bubble-launcher"
            :aria-label="open ? 'Close Dora' : 'Open Dora help assistant'"
            @click="toggle"
        >
            <DoraMascot :mood="mood" :size="56" />
            <q-badge
                v-if="updateBadge"
                floating
                color="accent"
                text-color="grey-10"
                rounded
                class="dora-update-badge"
            >
                NEW
                <q-tooltip>A newer version of Discount Dora is available.</q-tooltip>
            </q-badge>
        </button>
    </div>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import DoraChat from 'src/components/dora/DoraChat.vue';
    import DoraMascot from 'src/components/dora/DoraMascot.vue';
    import type { DoraMood } from 'src/components/dora/doraTypes';
    import HelpApiService from 'src/services/api/helpApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { onMounted, ref, watch } from 'vue';

    const LOCAL_STORAGE_HINT_KEY = 'dora.helpHintDismissed';

    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);
    const helpApi = new HelpApiService();

    const open = ref(false);
    const mood = ref<DoraMood>('happy');
    const updateBadge = ref(false);
    const showFirstTimeHint = ref(false);

    function dismissHint() {
        showFirstTimeHint.value = false;
        try {
            localStorage.setItem(LOCAL_STORAGE_HINT_KEY, '1');
        } catch {
            // Storage can be disabled (private mode). Not a problem — we'll
            // just show the hint again next session, which is fine for a
            // helper that's trying to be discoverable.
        }
    }

    function toggle() {
        open.value = !open.value;
        if (open.value) dismissHint();
    }

    function onClose() {
        open.value = false;
    }

    onMounted(async () => {
        // Surface the first-time hint once per browser. Skip on the login
        // page (the bubble itself only renders behind auth via MainLayout).
        try {
            if (!localStorage.getItem(LOCAL_STORAGE_HINT_KEY)) {
                // Tiny delay so the hint doesn't fight with the initial page
                // load animation.
                setTimeout(() => {
                    if (!open.value) showFirstTimeHint.value = true;
                }, 1500);
            }
        } catch {
            showFirstTimeHint.value = true;
        }

        // Probe the version endpoint so the launcher can show a NEW badge
        // when there's an update. Failures are silent — the badge just
        // doesn't appear.
        try {
            const info = await helpApi.getVersionAsync();
            updateBadge.value = info.update_available;
            if (info.update_available) mood.value = 'excited';
        } catch {
            // Don't bug the user — the bubble still works without this.
        }
    });

    // If the user goes quiet on the chat, cycle the launcher mood to a
    // subtle "curious" so it feels alive. Just on open/close right now —
    // expressive enough without a timer.
    watch(open, (isOpen) => {
        if (!isOpen) {
            mood.value = updateBadge.value ? 'excited' : 'happy';
        } else {
            mood.value = 'curious';
        }
    });
</script>

<style scoped>
    .dora-bubble-root {
        position: fixed;
        right: 18px;
        bottom: 18px;
        z-index: 3000;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 12px;
    }
    .dora-bubble-launcher {
        appearance: none;
        background: transparent;
        border: none;
        padding: 0;
        cursor: pointer;
        position: relative;
        transition: transform 180ms ease;
    }
    .dora-bubble-launcher:hover {
        transform: translateY(-2px);
    }
    .dora-update-badge {
        font-weight: 700;
        letter-spacing: 0.05em;
        font-size: 0.65rem;
    }
    .dora-bubble-hint {
        background: white;
        color: #333;
        padding: 10px 14px;
        border-radius: 12px;
        max-width: 260px;
        box-shadow: 0 6px 22px rgba(0, 0, 0, 0.18);
        position: relative;
        font-size: 0.85em;
        display: flex;
        gap: 8px;
        align-items: flex-start;
    }
    .body--dark .dora-bubble-hint {
        background: var(--q-component);
        color: var(--q-text);
    }
    .dora-bubble-hint-text {
        flex: 1;
    }
    .dora-bubble-hint-arrow {
        position: absolute;
        right: 24px;
        bottom: -8px;
        width: 0;
        height: 0;
        border-left: 8px solid transparent;
        border-right: 8px solid transparent;
        border-top: 8px solid white;
    }
    .body--dark .dora-bubble-hint-arrow {
        border-top-color: var(--q-component);
    }
    .dora-bubble-pop-enter-active,
    .dora-bubble-pop-leave-active {
        transition: opacity 180ms ease, transform 180ms ease;
        transform-origin: bottom right;
    }
    .dora-bubble-pop-enter-from,
    .dora-bubble-pop-leave-to {
        opacity: 0;
        transform: scale(0.92) translateY(8px);
    }
    .dora-bubble-hint-enter-active,
    .dora-bubble-hint-leave-active {
        transition: opacity 240ms ease, transform 240ms ease;
    }
    .dora-bubble-hint-enter-from,
    .dora-bubble-hint-leave-to {
        opacity: 0;
        transform: translateY(6px);
    }
</style>
