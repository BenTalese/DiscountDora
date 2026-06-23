<template>
    <div v-if="!currentUser">
        <q-card flat bordered>
            <q-card-section>
                <q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>
            </q-card-section>
        </q-card>
    </div>

    <div v-else class="column q-gutter-md">
        <!-- Weekly deals email ─────────────────────────────────────── -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-h6">Weekly deals email</div>
                <div class="text-caption dora-text-muted">
                    Dashy Dora can email you a digest of the latest deals
                    once a week.
                </div>
            </q-card-section>
            <q-separator />

            <q-card-section>
                <q-toggle
                    :model-value="currentUser.deals_email_enabled"
                    label="Subscribe me to the weekly deals email"
                    :disable="saving"
                    @update:model-value="onDealsEnabledChange"
                />
            </q-card-section>

            <q-card-section
                v-if="currentUser.deals_email_enabled"
                class="row q-col-gutter-md items-center"
            >
                <div class="col-12 col-sm-4 text-subtitle2">Send on</div>
                <div class="col-12 col-sm-8">
                    <q-select
                        v-model="sendDealsOnDay"
                        :options="dayOptions"
                        option-value="value"
                        option-label="label"
                        emit-value
                        map-options
                        outlined
                        dense
                        style="max-width: 260px"
                        :disable="saving"
                        @update:model-value="onSendDealsOnDayChange"
                    />
                </div>
            </q-card-section>

            <q-card-section v-if="currentUser.deals_email_enabled">
                <q-toggle
                    :model-value="currentUser.deals_email_compact"
                    label="Compact format (one-line per deal)"
                    :disable="saving"
                    @update:model-value="onDealsCompactChange"
                />
            </q-card-section>
        </q-card>

        <!-- C-9.7 — Alerts email digest. SMTP-gated (R-014): the master
             toggle disables when the backend doesn't have email
             configured, so a self-hosted install without SMTP doesn't
             silently swallow opt-ins. -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-h6">Alerts email digest</div>
                <div class="text-caption dora-text-muted">
                    Get your actionable alerts emailed to you on a daily or
                    weekly cadence. The digest matches what you'd see on the
                    Alerts page; the same alert won't email again until it
                    clears and re-fires.
                </div>
            </q-card-section>
            <q-separator />

            <q-card-section>
                <q-toggle
                    :model-value="currentUser.alerts_email_enabled"
                    label="Email me a digest of my alerts"
                    :disable="saving || !emailSmtpConfigured"
                    @update:model-value="onAlertsEmailEnabledChange"
                />
                <div
                    v-if="!emailSmtpConfigured"
                    class="text-caption dora-text-muted q-mt-xs"
                >
                    Email isn't set up on this install yet — ask an admin
                    to configure SMTP and this toggle will unlock.
                </div>
            </q-card-section>

            <q-card-section
                v-if="currentUser.alerts_email_enabled"
                class="row q-col-gutter-md items-center"
            >
                <div class="col-12 col-sm-4 text-subtitle2">Cadence</div>
                <div class="col-12 col-sm-8">
                    <q-select
                        v-model="alertsEmailCadenceDraft"
                        :options="alertsCadenceOptions"
                        option-value="value"
                        option-label="label"
                        emit-value
                        map-options
                        outlined
                        dense
                        style="max-width: 260px"
                        :disable="saving"
                        @update:model-value="onAlertsEmailCadenceChange"
                    />
                </div>
            </q-card-section>

            <q-card-section
                v-if="currentUser.alerts_email_enabled && alertsEmailCadenceDraft === 'weekly'"
                class="row q-col-gutter-md items-center"
            >
                <div class="col-12 col-sm-4 text-subtitle2">Send on</div>
                <div class="col-12 col-sm-8">
                    <q-select
                        v-model="alertsEmailDayDraft"
                        :options="dayOptions"
                        option-value="value"
                        option-label="label"
                        emit-value
                        map-options
                        outlined
                        dense
                        style="max-width: 260px"
                        :disable="saving"
                        @update:model-value="onAlertsEmailDayChange"
                    />
                </div>
            </q-card-section>
        </q-card>

        <!-- C-9.8 — Push notifications. VAPID-gated (R-014): the toggle
             disables when the backend isn't configured, mirroring the
             alerts-email SMTP gate. The four-state lifecycle (loading /
             unsupported / denied / subscribed) is surfaced via the
             caption beneath the toggle. -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-h6">Push notifications</div>
                <div class="text-caption dora-text-muted">
                    Get a system notification on this device the moment a new
                    actionable alert fires. Only actionable alerts are pushed —
                    FYI items stay in the hub and the email digest. Subscribe
                    on every device you want to be notified on.
                </div>
            </q-card-section>
            <q-separator />

            <q-card-section>
                <q-toggle
                    :model-value="pushSubscribed"
                    label="Send me push notifications on this device"
                    :disable="saving || !pushVapidConfigured || !pushSupported || pushLoading"
                    @update:model-value="onPushToggle"
                />
                <div
                    v-if="!pushVapidConfigured"
                    class="text-caption dora-text-muted q-mt-xs"
                >
                    Push isn't set up on this install yet — ask an admin
                    to generate VAPID keys and this toggle will unlock.
                </div>
                <div
                    v-else-if="!pushSupported"
                    class="text-caption dora-text-muted q-mt-xs"
                >
                    This browser doesn't support web push.
                </div>
                <div
                    v-else-if="pushState === 'denied'"
                    class="text-caption dora-text-muted q-mt-xs"
                >
                    Notifications are blocked for this site. Re-enable them in
                    your browser's site settings, then refresh.
                </div>
                <div
                    v-else-if="pushError"
                    class="text-caption text-negative q-mt-xs"
                >
                    {{ pushError }}
                </div>
                <div
                    v-else-if="pushSubscribed"
                    class="text-caption dora-text-muted q-mt-xs"
                >
                    This device is subscribed. Toggle off to stop receiving
                    pushes here (other devices keep their own subscriptions).
                </div>
            </q-card-section>
        </q-card>
    </div>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import { useAuthStore } from 'src/stores/authStore';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import { usePushSubscription } from 'src/composables/usePushSubscription';
    import { computed, ref, watch } from 'vue';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    // C-9.7 — alerts email digest gating. The backend feature flag
    // mirrors `email_sender._config().dry_run` so the toggle reflects
    // whether emails would actually leave the box (R-014).
    const { emailSmtpConfigured, pushVapidConfigured } = useFeatureFlags();
    const alertsCadenceOptions = [
        { label: 'Daily', value: 'daily' as const },
        { label: 'Weekly', value: 'weekly' as const },
    ];

    // C-9.8 — push subscription lifecycle for this device. The
    // composable owns the four-state machine; the card binds against it.
    const {
        state: pushState,
        error: pushError,
        subscribed: pushSubscribed,
        supported: pushSupported,
        subscribe: pushSubscribe,
        unsubscribe: pushUnsubscribe,
    } = usePushSubscription();
    const pushLoading = computed(() => pushState.value === 'loading');

    const dayOptions = [
        { value: 0, label: 'Monday' },
        { value: 1, label: 'Tuesday' },
        { value: 2, label: 'Wednesday' },
        { value: 3, label: 'Thursday' },
        { value: 4, label: 'Friday' },
        { value: 5, label: 'Saturday' },
        { value: 6, label: 'Sunday' }
    ];

    const sendDealsOnDay = ref<number>(currentUser.value?.send_deals_on_day ?? 0);
    // C-9.7 — alerts email digest. Cadence and day are draft refs so the
    // q-select reflects the freshly saved value without flickering through
    // the watcher; the toggle reads `currentUser` directly (instant-flip).
    const alertsEmailCadenceDraft = ref<'daily' | 'weekly'>(
        (currentUser.value?.alerts_email_cadence === 'weekly') ? 'weekly' : 'daily'
    );
    const alertsEmailDayDraft = ref<number>(currentUser.value?.alerts_email_day ?? 0);

    const saving = ref(false);

    // Re-sync drafts when the auth store reloads (e.g. after refresh, login).
    watch(currentUser, (u) => {
        if (!u) return;
        sendDealsOnDay.value = u.send_deals_on_day ?? 0;
        alertsEmailCadenceDraft.value = u.alerts_email_cadence === 'weekly' ? 'weekly' : 'daily';
        alertsEmailDayDraft.value = u.alerts_email_day ?? 0;
    });

    function notifySuccess(message: string) {
        $q.notify({ type: 'positive', position: 'bottom-right', message });
    }
    function notifyError(message: string, err?: unknown) {
        $q.notify({
            type: 'negative',
            position: 'bottom-right',
            message,
            caption: describeApiError(err) || ''
        });
    }

    async function update<T>(label: string, run: () => Promise<T>): Promise<T | null> {
        saving.value = true;
        try {
            const result = await run();
            notifySuccess(label);
            return result;
        } catch (err) {
            notifyError(`Could not save ${label.toLowerCase()}.`, err);
            return null;
        } finally {
            saving.value = false;
        }
    }

    async function onSendDealsOnDayChange(value: number) {
        const previous = currentUser.value?.send_deals_on_day ?? 0;
        const result = await update('Weekly deals day updated.', () =>
            authStore.updateMeAsync({ send_deals_on_day: value })
        );
        if (result === null) sendDealsOnDay.value = previous;
    }

    async function onDealsEnabledChange(value: boolean) {
        await update(
            value
                ? 'Subscribed to the weekly deals email.'
                : 'Unsubscribed from the weekly deals email.',
            () => authStore.updateMeAsync({ deals_email_enabled: value })
        );
    }

    async function onDealsCompactChange(value: boolean) {
        await update('Deals email format updated.', () =>
            authStore.updateMeAsync({ deals_email_compact: value })
        );
    }

    // C-9.7 — alerts email digest handlers. Toggling the master switch
    // sends both `alerts_email_enabled` and the current cadence so a
    // fresh-opt-in user starts on a sensible default ('daily') without
    // a second click. Cadence/day changes are saved instantly.
    async function onAlertsEmailEnabledChange(value: boolean) {
        const cadence = value ? alertsEmailCadenceDraft.value : 'off';
        await update(
            value
                ? 'Subscribed to the alerts email digest.'
                : 'Unsubscribed from the alerts email digest.',
            () => authStore.updateMeAsync({
                alerts_email_enabled: value,
                alerts_email_cadence: cadence,
            })
        );
    }

    async function onAlertsEmailCadenceChange(value: 'daily' | 'weekly') {
        const previous = alertsEmailCadenceDraft.value;
        alertsEmailCadenceDraft.value = value;
        const result = await update('Digest cadence updated.', () =>
            authStore.updateMeAsync({ alerts_email_cadence: value })
        );
        if (result === null) alertsEmailCadenceDraft.value = previous;
    }

    async function onAlertsEmailDayChange(value: number) {
        const previous = alertsEmailDayDraft.value;
        alertsEmailDayDraft.value = value;
        const result = await update('Digest day updated.', () =>
            authStore.updateMeAsync({ alerts_email_day: value })
        );
        if (result === null) alertsEmailDayDraft.value = previous;
    }

    // C-9.8 — push toggle. The composable handles the permission
    // prompt + server round-trip; we just translate success/failure
    // into the standard $q.notify pattern.
    async function onPushToggle(value: boolean) {
        try {
            if (value) {
                await pushSubscribe();
                if (pushSubscribed.value) notifySuccess('Subscribed to push notifications on this device.');
            } else {
                await pushUnsubscribe();
                notifySuccess('Unsubscribed from push notifications on this device.');
            }
        } catch (err) {
            notifyError('Push subscription failed.', err);
        }
    }
</script>
