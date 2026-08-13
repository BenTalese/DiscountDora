<template>
    <!-- Shown by NotificationsSettings when a per-user channel is gated on an
         install-wide setup that hasn't happened yet (SMTP for email, VAPID for
         push). A warning card — not a muted footnote — so the "why is this
         toggle disabled?" answer actually pops (owner feedback). Admin viewers
         get a direct link to the setup page instead of "ask an admin", since
         they *are* the admin. -->
    <q-banner class="dora-bg-warning-soft text-warning channel-setup-note" rounded>
        <template #avatar>
            <q-icon :name="ICONS.warning_amber" size="22px" />
        </template>

        <div class="channel-setup-note__body">
            <div class="text-weight-medium channel-setup-note__title">
                {{ cfg.label }} isn't set up on this install yet
            </div>
            <p class="channel-setup-note__text">
                <template v-if="isAdmin">
                    {{ cfg.adminHint }}
                </template>
                <template v-else>
                    Ask an admin to {{ cfg.verb }} and this will unlock.
                </template>
            </p>
            <div v-if="isAdmin" class="channel-setup-note__actions">
                <BaseButton
                    variant="secondary"
                    :icon="ICONS.settings"
                    :label="cfg.setupLabel"
                    :to="cfg.setupPath"
                />
            </div>
        </div>
    </q-banner>
</template>

<script lang="ts" setup>
    import { computed } from 'vue';
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';

    const props = defineProps<{
        // 'email' backs both the deals + alerts email channels (both need SMTP);
        // 'push' backs the web-push channel (needs VAPID keys).
        channel: 'email' | 'push';
        isAdmin: boolean;
    }>();

    const cfg = computed(() =>
        props.channel === 'email'
            ? {
                  label: 'Email',
                  verb: 'configure SMTP',
                  adminHint: 'Configure SMTP to start sending emails from this install.',
                  setupLabel: 'Set up email',
                  setupPath: '/settings/admin/system/email',
              }
            : {
                  label: 'Push',
                  verb: 'generate VAPID keys',
                  adminHint: 'Generate VAPID keys to enable web push on this install.',
                  setupLabel: 'Set up push',
                  setupPath: '/settings/admin/system/push',
              },
    );
</script>

<style scoped lang="scss">
    .channel-setup-note {
        margin: 4px 0 6px;
    }
    .channel-setup-note__body {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .channel-setup-note__title {
        color: var(--text-primary);
    }
    .channel-setup-note__text {
        margin: 0;
        color: var(--text-primary);
        font-size: 0.875rem;
        line-height: 1.45;
        max-width: 70ch;
    }
    .channel-setup-note__actions {
        margin-top: 4px;
    }
</style>
