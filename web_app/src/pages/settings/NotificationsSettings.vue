<template>
    <div v-if="!currentUser">
        <q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>
    </div>

    <div v-else class="settings-page">
        <SettingsPageHeader title="Notifications" :icon="ICONS.notifications" />

        <!--
            Owner restructure 2026-08-29 — the page was a flat run of four
            peer sections (deals email, push, evening brief) where the *channel*
            and the *thing sent over it* sat at the same level, so "Evening
            brief" gave no clue it was push-only and the deals email gave no
            clue it was the only thing that arrives by mail. Two sections now,
            one per channel, each opening with its own blocker banner and then
            listing what it can deliver as child rows.
        -->

        <!-- Push. VAPID-gated install-wide; also needs the browser to support
             web push and the user to have subscribed *this* device. -->
        <SettingsSection>
            <template #title>Push notifications</template>

            <!-- Blockers first (owner): the answer to "why is this toggle
                 dead?" belongs above the dead toggle, not under it. -->
            <ChannelSetupNote
                v-if="!pushVapidConfigured"
                channel="push"
                :is-admin="isAdmin"
            />
            <SettingsNotice v-else-if="!pushSupported" title="Not available in this browser">
                This browser doesn't support web push, so nothing in this
                section can be delivered here. Chrome, Edge, Firefox and Safari
                all support it on desktop; on iPhone the app must be installed
                to the home screen first.
            </SettingsNotice>
            <SettingsNotice v-else-if="pushState === 'denied'" title="Notifications are blocked">
                You've blocked notifications for this site. Re-enable them in
                your browser's site settings, then refresh this page.
            </SettingsNotice>
            <SettingsNotice v-else-if="pushError" title="Push subscription failed">
                {{ pushError }}
            </SettingsNotice>

            <SettingsRow>
                <template #label>
                    Push notifications on this device
                    <InfoTip label="Push notifications on this device">
                        Subscribes this browser on this device. Every device you
                        sign in on keeps its own subscription, so turning it off
                        here doesn't affect your phone.
                    </InfoTip>
                </template>
                <q-toggle
                    :model-value="pushSubscribed"
                    :disable="!pushVapidConfigured || !pushSupported || pushLoading"
                    aria-label="Send me push notifications on this device"
                    @update:model-value="onPushToggle"
                />
            </SettingsRow>

            <!-- The evening brief rides the push channel, so it lives inside
                 it rather than beside it — that relationship was invisible
                 while the two were peer sections. -->
            <SettingsRow>
                <template #label>
                    Evening brief
                    <InfoTip label="Evening brief">
                        A notification at 7pm with tomorrow's agenda.
                    </InfoTip>
                </template>
                <q-toggle
                    :model-value="currentUser.daily_brief_enabled"
                    :disable="!pushVapidConfigured || !pushSupported"
                    aria-label="Send me an evening brief"
                    @update:model-value="onDailyBriefToggle"
                />
            </SettingsRow>
            <div
                v-if="currentUser.daily_brief_enabled && !pushSubscribed && pushVapidConfigured && pushSupported"
                class="settings-page__note dora-text-muted"
            >
                Turn on push notifications above to receive it on this device.
            </div>
        </SettingsSection>

        <!-- Email. Gated on `products` (data-presence): the weekly deals email
             is currently the only thing Dora mails on a schedule, and with no
             product data ingested there's no deal source — so with products
             absent the whole channel is hidden, here and as the admin
             users-page column (owner feedback). Also SMTP-gated.
             (No alerts email digest — cut at Step-0 Q4,
             `IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md`.) -->
        <template v-if="productsEnabled">
            <hr class="settings-divider" />

            <SettingsSection>
                <template #title>Email notifications</template>

                <ChannelSetupNote
                    v-if="!emailSmtpConfigured"
                    channel="email"
                    :is-admin="isAdmin"
                />
                <!-- FU-789: the deals job skips an unverified address on
                     purpose — it's the only mail Dora sends repeatedly and
                     unprompted, and an unverified address is one nobody has
                     proved they own. Said here rather than only in a server
                     log, so the toggle can't sit on while nothing arrives with
                     no way to find out why. -->
                <SettingsNotice
                    v-else-if="!currentUser.email_verified"
                    title="Your email address isn't verified"
                >
                    Scheduled emails only go to verified addresses, so nothing
                    below will arrive until you confirm yours. Check your inbox
                    for the verification link, or send yourself a fresh one.
                    <template #actions>
                        <BaseButton
                            variant="secondary"
                            :icon="ICONS.mark_email_read"
                            label="Send verification email"
                            :disable="resendingVerification"
                            @click="onResendVerification"
                        />
                    </template>
                </SettingsNotice>

                <SettingsRow>
                    <template #label>
                        Weekly deals
                        <InfoTip label="Weekly deals">
                            Automated deals email making use of regular product
                            data pushed into Dora.
                        </InfoTip>
                    </template>
                    <q-toggle
                        :model-value="currentUser.deals_email_enabled"
                        :disable="!emailSmtpConfigured"
                        aria-label="Subscribe me to the weekly deals email"
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
                            @update:model-value="onSendDealsOnDayChange"
                        />
                    </SettingsRow>

                    <SettingsRow>
                        <template #label>
                            Compact format
                            <!-- This used to promise "images and store logos".
                                 It never could: product images are served from
                                 an authenticated endpoint an email client has
                                 no session for, so every one would render as a
                                 broken box. Corrected when the email was
                                 actually built (FU-789) rather than left as
                                 copy describing a mail nobody had written. -->
                            <InfoTip label="Compact format">
                                One line per deal — name, price, discount,
                                store. Off sends a card per deal with the brand,
                                size and what you save spelled out in dollars.
                            </InfoTip>
                        </template>
                        <q-toggle
                            :model-value="currentUser.deals_email_compact"
                            @update:model-value="onDealsCompactChange"
                        />
                    </SettingsRow>
                </template>
            </SettingsSection>
        </template>
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
    import { ICONS } from 'src/style/icons';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import ChannelSetupNote from 'src/components/settings/ChannelSetupNote.vue';
    import SettingsNotice from 'src/components/settings/SettingsNotice.vue';
    import InfoTip from 'src/components/help/InfoTip.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import AuthApiService from 'src/services/api/authApiService';

    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    // `products` is a data-presence gate (true iff product data has been
    // ingested) — the deals-email feature's whole information source. No data
    // ⇒ the deals section is hidden here and the column is dropped on the
    // admin users page (owner feedback).
    const { emailSmtpConfigured, pushVapidConfigured, products: productsEnabled } = useFeatureFlags();
    const isAdmin = computed(() => currentUser.value?.is_admin === true);
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

    // R-003 / FU-601 — shared save-toast helper (see useSettingsSave).
    const { notifySuccess, notifyError, update } = useSettingsSave();

    watch(currentUser, (u) => {
        if (!u) return;
        sendDealsOnDay.value = u.send_deals_on_day ?? 0;
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

    async function onDailyBriefToggle(value: boolean) {
        await update(
            value
                ? "You'll get an evening brief when there's something to say."
                : 'Evening brief turned off.',
            () => authStore.updateMeAsync({ daily_brief_enabled: value }),
        );
    }

    // FU-789 — resend from here rather than sending the user off to a page
    // that has no such control. The endpoint always answers 204 (it's
    // deliberately anti-enumeration and rate-limited to 1/min), so the toast
    // promises "if that address needs it" rather than claiming a send.
    const authApi = new AuthApiService();
    const resendingVerification = ref(false);
    async function onResendVerification() {
        const email = currentUser.value?.email;
        if (!email) return;
        resendingVerification.value = true;
        try {
            await authApi.resendVerificationAsync(email);
            notifySuccess(`Verification email on its way to ${email}.`);
        } catch (err) {
            notifyError("Couldn't send the verification email.", err);
        } finally {
            resendingVerification.value = false;
        }
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
