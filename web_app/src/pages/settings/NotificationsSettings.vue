<template>
    <div v-if="!currentUser">
        <q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>
    </div>

    <div v-else class="settings-page">
        <SettingsPageHeader title="Notifications" />

        <!-- Weekly deals email. Gated on `products` (data-presence): with no
             product data ingested there's no deal source, so the whole feature
             is hidden — settings + the admin users-page column (owner feedback).
             Also SMTP-gated, same barrier as the alerts digest below. -->
        <template v-if="productsEnabled">
            <SettingsSection>
                <template #title>Weekly deals email</template>
                <template #description>
                    If you have a tool that regularly pushes product deal data
                    into Dora, you can turn on an automated deals email — one
                    message a week summarising deals based on that data. For
                    best results, keep the data flowing in regularly.
                </template>

                <SettingsRow label="Subscribe me to the weekly deals email">
                    <q-toggle
                        :model-value="currentUser.deals_email_enabled"
                        :disable="!emailSmtpConfigured"
                        @update:model-value="onDealsEnabledChange"
                    />
                </SettingsRow>
                <ChannelSetupNote
                    v-if="!emailSmtpConfigured"
                    channel="email"
                    :is-admin="isAdmin"
                />

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
                            @update:model-value="onSendDealsOnDayChange"
                        />
                    </SettingsRow>

                    <SettingsRow
                        label="Compact format"
                        help="One line per deal (item, price, store). Off = expanded card per deal with images and store logos."
                    >
                        <q-toggle
                            :model-value="currentUser.deals_email_compact"
                            @update:model-value="onDealsCompactChange"
                        />
                    </SettingsRow>
                </template>
            </SettingsSection>

            <hr class="settings-divider" />
        </template>

        <!-- Alerts email digest. SMTP-gated. R-029 carve-out: this screen
             owns the per-user opt-in, so the disabled toggle + setup card
             legitimately render here (and only here). Title + toggle only
             (owner: drop the descriptive blurbs). -->
        <SettingsSection>
            <template #title>Alerts email digest</template>
            <template #actions>
                <q-toggle
                    :model-value="currentUser.alerts_email_enabled"
                    :disable="!emailSmtpConfigured"
                    aria-label="Email me a digest of my alerts"
                    @update:model-value="onAlertsEmailEnabledChange"
                />
            </template>

            <ChannelSetupNote
                v-if="!emailSmtpConfigured"
                channel="email"
                :is-admin="isAdmin"
            />

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
                        @update:model-value="onAlertsEmailDayChange"
                    />
                </SettingsRow>
            </template>
        </SettingsSection>

        <hr class="settings-divider" />

        <!-- Push notifications. VAPID-gated. R-029 carve-out — same
             pattern as the email row above. Title + toggle only
             (owner: drop the descriptive blurb). -->
        <SettingsSection>
            <template #title>Push notifications</template>
            <template #actions>
                <q-toggle
                    :model-value="pushSubscribed"
                    :disable="!pushVapidConfigured || !pushSupported || pushLoading"
                    aria-label="Send me push notifications on this device"
                    @update:model-value="onPushToggle"
                />
            </template>

            <ChannelSetupNote
                v-if="!pushVapidConfigured"
                channel="push"
                :is-admin="isAdmin"
            />
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
    import { useAuthStore } from 'src/stores/authStore';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import { usePushSubscription } from 'src/composables/usePushSubscription';
    import { computed, ref, watch } from 'vue';
    import { useSettingsSave } from 'src/composables/useSettingsSave';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import ChannelSetupNote from 'src/components/settings/ChannelSetupNote.vue';
    import DoraSegmented, { type DoraSegmentedOption } from 'src/components/settings/DoraSegmented.vue';

    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    // `products` is a data-presence gate (true iff product data has been
    // ingested) — the deals-email feature's whole information source. No data
    // ⇒ the deals section is hidden here and the column is dropped on the
    // admin users page (owner feedback).
    const { emailSmtpConfigured, pushVapidConfigured, products: productsEnabled } = useFeatureFlags();
    const isAdmin = computed(() => currentUser.value?.is_admin === true);
    type AlertsCadence = 'daily' | 'weekly';
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

    // R-003 / FU-601 — shared save-toast helper (see useSettingsSave).
    const { notifySuccess, notifyError, update } = useSettingsSave();

    watch(currentUser, (u) => {
        if (!u) return;
        sendDealsOnDay.value = u.send_deals_on_day ?? 0;
        alertsEmailCadenceDraft.value = u.alerts_email_cadence === 'weekly' ? 'weekly' : 'daily';
        alertsEmailDayDraft.value = u.alerts_email_day ?? 0;
    });

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
