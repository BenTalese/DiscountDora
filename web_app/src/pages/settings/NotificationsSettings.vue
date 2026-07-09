<template>
    <div v-if="!currentUser">
        <q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>
    </div>

    <div v-else class="settings-page">
        <SettingsPageHeader
            title="Notifications"
            description="Choose how Dashy Dora reaches you about deals, alerts, and push messages on this device."
        />

        <SettingsSection>
            <template #title>Weekly deals email</template>
            <template #description>
                A digest of the latest deals once a week.
            </template>

            <SettingsRow
                label="Subscribe me to the weekly deals email"
                help="One email per week summarising deals at your stores."
            >
                <q-toggle
                    :model-value="currentUser.deals_email_enabled"
                    :disable="saving"
                    @update:model-value="onDealsEnabledChange"
                />
            </SettingsRow>

            <template v-if="currentUser.deals_email_enabled">
                <SettingsRow label="Send on">
                    <q-select
                        v-model="sendDealsOnDay"
                        :options="dayOptions"
                        option-value="value"
                        option-label="label"
                        emit-value
                        map-options
                        outlined
                        dense
                        style="min-width: 180px"
                        :disable="saving"
                        @update:model-value="onSendDealsOnDayChange"
                    />
                </SettingsRow>

                <SettingsRow
                    label="Compact format"
                    help="One line per deal (item, price, store). Off = expanded card per deal with images and store logos."
                >
                    <q-toggle
                        :model-value="currentUser.deals_email_compact"
                        :disable="saving"
                        @update:model-value="onDealsCompactChange"
                    />
                </SettingsRow>
            </template>
        </SettingsSection>

        <hr class="settings-divider" />

        <!-- Alerts email digest. SMTP-gated. R-029 carve-out: this screen
             owns the per-user opt-in, so the disabled toggle + "ask an
             admin" hint legitimately render here (and only here). -->
        <SettingsSection>
            <template #title>Alerts email digest</template>
            <template #description>
                Email me my actionable alerts on a daily or weekly cadence.
                The same alert won't email again until it clears and re-fires.
            </template>

            <SettingsRow label="Email me a digest of my alerts">
                <q-toggle
                    :model-value="currentUser.alerts_email_enabled"
                    :disable="saving || !emailSmtpConfigured"
                    @update:model-value="onAlertsEmailEnabledChange"
                />
            </SettingsRow>
            <div
                v-if="!emailSmtpConfigured"
                class="settings-page__note dora-text-muted"
            >
                Email isn't set up on this install yet — ask an admin to
                configure SMTP and this toggle will unlock.
            </div>

            <template v-if="currentUser.alerts_email_enabled">
                <SettingsRow label="Cadence">
                    <DoraSegmented
                        :model-value="alertsEmailCadenceDraft"
                        :options="alertsCadenceOptions"
                        @update:model-value="onAlertsEmailCadenceChange"
                    />
                </SettingsRow>

                <SettingsRow v-if="alertsEmailCadenceDraft === 'weekly'" label="Send on">
                    <q-select
                        v-model="alertsEmailDayDraft"
                        :options="dayOptions"
                        option-value="value"
                        option-label="label"
                        emit-value
                        map-options
                        outlined
                        dense
                        style="min-width: 180px"
                        :disable="saving"
                        @update:model-value="onAlertsEmailDayChange"
                    />
                </SettingsRow>
            </template>
        </SettingsSection>

        <hr class="settings-divider" />

        <!-- FU-450 — deal alerts. Money-features-gated (R-029 hide-don't-nag:
             the whole section is absent when money features are off, no
             disabled hint). -->
        <SettingsSection v-if="moneyEnabled">
            <template #title>Deal alerts</template>
            <template #description>
                Nudge me when something I track hits a genuinely good price.
                Dora checks your own price history so it never celebrates a
                fake "special".
            </template>

            <SettingsRow label="Alert me on">
                <DoraSegmented
                    :model-value="goodDealThresholdDraft"
                    :options="goodDealThresholdOptions"
                    @update:model-value="onGoodDealThresholdChange"
                />
            </SettingsRow>
            <div class="settings-page__note dora-text-muted">
                <template v-if="goodDealThresholdDraft === 'great'">
                    Only the very best prices — the lowest Dora has seen in months.
                </template>
                <template v-else>
                    Good and great prices both. More nudges, more savings.
                </template>
            </div>
        </SettingsSection>

        <hr v-if="moneyEnabled" class="settings-divider" />

        <!-- Push notifications. VAPID-gated. R-029 carve-out — same
             pattern as the email row above. -->
        <SettingsSection>
            <template #title>Push notifications</template>
            <template #description>
                System notifications on this device the moment a new
                actionable alert fires. Subscribe on every device you want.
            </template>

            <SettingsRow label="Send me push notifications on this device">
                <q-toggle
                    :model-value="pushSubscribed"
                    :disable="saving || !pushVapidConfigured || !pushSupported || pushLoading"
                    @update:model-value="onPushToggle"
                />
            </SettingsRow>
            <div
                v-if="!pushVapidConfigured"
                class="settings-page__note dora-text-muted"
            >
                Push isn't set up on this install yet — ask an admin to
                generate VAPID keys and this toggle will unlock.
            </div>
            <div
                v-else-if="!pushSupported"
                class="settings-page__note dora-text-muted"
            >
                This browser doesn't support web push.
            </div>
            <div
                v-else-if="pushState === 'denied'"
                class="settings-page__note dora-text-muted"
            >
                Notifications are blocked for this site. Re-enable them in
                your browser's site settings, then refresh.
            </div>
            <div
                v-else-if="pushError"
                class="settings-page__note text-negative"
            >
                {{ pushError }}
            </div>
            <div
                v-else-if="pushSubscribed"
                class="settings-page__note dora-text-muted"
            >
                This device is subscribed. Toggle off to stop receiving
                pushes here (other devices keep their own subscriptions).
            </div>
        </SettingsSection>
    </div>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import { useAuthStore } from 'src/stores/authStore';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { usePushSubscription } from 'src/composables/usePushSubscription';
    import { computed, ref, watch } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import DoraSegmented, { type DoraSegmentedOption } from 'src/components/settings/DoraSegmented.vue';

    const $q = useQuasar();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    const { emailSmtpConfigured, pushVapidConfigured } = useFeatureFlags();
    const { moneyEnabled } = useMoneyEnabled();
    type AlertsCadence = 'daily' | 'weekly';
    type GoodDealThreshold = 'good' | 'great';
    const goodDealThresholdOptions: DoraSegmentedOption<GoodDealThreshold>[] = [
        { label: 'Good & great', value: 'good' },
        { label: 'Great only', value: 'great' },
    ];
    const alertsCadenceOptions: DoraSegmentedOption<AlertsCadence>[] = [
        { label: 'Daily', value: 'daily' },
        { label: 'Weekly', value: 'weekly' },
    ];

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
    const alertsEmailCadenceDraft = ref<AlertsCadence>(
        (currentUser.value?.alerts_email_cadence === 'weekly') ? 'weekly' : 'daily'
    );
    const alertsEmailDayDraft = ref<number>(currentUser.value?.alerts_email_day ?? 0);
    const goodDealThresholdDraft = ref<GoodDealThreshold>(
        currentUser.value?.good_deal_alert_threshold === 'great' ? 'great' : 'good'
    );

    const saving = ref(false);

    watch(currentUser, (u) => {
        if (!u) return;
        sendDealsOnDay.value = u.send_deals_on_day ?? 0;
        alertsEmailCadenceDraft.value = u.alerts_email_cadence === 'weekly' ? 'weekly' : 'daily';
        alertsEmailDayDraft.value = u.alerts_email_day ?? 0;
        goodDealThresholdDraft.value = u.good_deal_alert_threshold === 'great' ? 'great' : 'good';
    });

    function notifySuccess(message: string) {
        $q.notify({ type: 'positive', position: 'bottom-right', message });
    }
    function notifyError(message: string, err?: unknown) {
        $q.notify({
            type: 'negative',
            position: 'bottom-right',
            message,
            caption: toastCaption(err)
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

    async function onAlertsEmailCadenceChange(value: AlertsCadence) {
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

    async function onGoodDealThresholdChange(value: GoodDealThreshold) {
        const previous = goodDealThresholdDraft.value;
        goodDealThresholdDraft.value = value;
        const result = await update('Deal alert threshold updated.', () =>
            authStore.updateMeAsync({ good_deal_alert_threshold: value })
        );
        if (result === null) goodDealThresholdDraft.value = previous;
    }

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

<style scoped lang="scss">
    .settings-page {
        display: flex;
        flex-direction: column;
    }
    .settings-page__note {
        font-size: 0.8125rem;
        line-height: 1.4;
        margin-top: 4px;
    }
    .settings-divider {
        border: 0;
        height: 1px;
        background: color-mix(in srgb, var(--text-primary) 8%, transparent);
        margin: 0;
    }
</style>
