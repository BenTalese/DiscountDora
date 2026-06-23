<template>
    <div class="settings-page">
        <header class="about-header">
            <q-avatar size="56px" square>
                <img src="../../assets/logo-mascot.png" alt="Dashy Dora" />
            </q-avatar>
            <div>
                <h1 class="about-header__title">
                    <DoraBrand inline />
                </h1>
                <p class="about-header__tagline dora-text-muted">
                    Your pantry at your fingertips.
                </p>
            </div>
        </header>

        <hr class="settings-divider" />

        <SettingsSection>
            <template #title>About this install</template>

            <q-list class="about-list">
                <q-item>
                    <q-item-section>
                        <q-item-label>Build</q-item-label>
                        <q-item-label caption>
                            Local development. Versioning isn't tagged in this fork yet.
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <q-chip dense class="dora-bg-sunken dora-text-secondary">{{ buildLabel }}</q-chip>
                    </q-item-section>
                </q-item>

                <q-item>
                    <q-item-section>
                        <q-item-label>Install as an app</q-item-label>
                        <q-item-label caption>
                            Adds a Dora icon to your home screen / launcher
                            and runs in its own window. iOS Safari uses
                            "Add to Home Screen" instead.
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <PwaInstallPrompt />
                    </q-item-section>
                </q-item>

                <q-item>
                    <q-item-section>
                        <q-item-label>Web client</q-item-label>
                        <q-item-label caption>
                            Quasar 2 / Vue 3, talks to the Flask API over CORS.
                        </q-item-label>
                    </q-item-section>
                </q-item>

                <q-item>
                    <q-item-section>
                        <q-item-label>Dora API endpoint</q-item-label>
                        <q-item-label caption class="text-mono">{{ doraApiUrl }}</q-item-label>
                    </q-item-section>
                </q-item>
            </q-list>
        </SettingsSection>

        <hr class="settings-divider" />

        <!-- F1 — onboarding restart lives here as a help / re-tour action. -->
        <SettingsSection>
            <template #title>First-run wizard</template>
            <template #description>
                Want to revisit the welcome tour? This sends you back to
                /welcome — nothing in your data is touched, you'll just
                step through the prompts again.
            </template>

            <SettingsRow stacked>
                <div>
                    <q-btn
                        outline
                        no-caps
                        :icon="ICONS.restart_alt"
                        label="Restart onboarding"
                        :loading="restartingOnboarding"
                        @click="onRestartOnboarding"
                    />
                </div>
            </SettingsRow>
        </SettingsSection>

        <hr class="settings-divider" />

        <p class="about-footer dora-text-muted">
            Dora is a hobby project. The mascot is doing its best.
        </p>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { useQuasar } from 'quasar';
    import PwaInstallPrompt from 'src/components/PwaInstallPrompt.vue';
    import DoraBrand from 'src/components/DoraBrand.vue';
    import OnboardingApiService from 'src/services/api/onboardingApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, ref } from 'vue';
    import { useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';

    const $q = useQuasar();
    const router = useRouter();
    const authStore = useAuthStore();
    const onboardingApi = new OnboardingApiService();

    const restartingOnboarding = ref(false);

    async function onRestartOnboarding() {
        const ok = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: 'Restart onboarding?',
                message:
                    "We'll send you back to /welcome. Your stock items, " +
                    "groups, locations and shopping lists are untouched.",
                ok: { label: 'Restart', color: 'primary', noCaps: true },
                cancel: { noCaps: true },
            })
                .onOk(() => resolve(true))
                .onCancel(() => resolve(false))
                .onDismiss(() => resolve(false));
        });
        if (!ok) return;
        restartingOnboarding.value = true;
        try {
            await onboardingApi.restartAsync();
            await authStore.refreshAsync();
            try {
                localStorage.removeItem('dora.onboarding.skipped_at');
            } catch {
                // Ignore.
            }
            void router.push('/welcome');
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not restart onboarding.',
                caption: describeApiError(err) || '',
            });
        } finally {
            restartingOnboarding.value = false;
        }
    }

    const doraApiUrl = computed(() => {
        const env = import.meta.env.VITE_API_BASE_URL;
        if (env) return env;
        if (typeof window !== 'undefined') {
            const { protocol, hostname } = window.location;
            return `${protocol}//${hostname}:5170/api`;
        }
        return 'http://localhost:5170/api';
    });

    const buildLabel = computed(() => (import.meta.env.PROD ? 'production' : 'dev'));
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
    .about-header {
        display: flex;
        align-items: center;
        gap: 16px;
        padding-bottom: 12px;
    }
    .about-header__title {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.1;
    }
    .about-header__tagline {
        margin: 4px 0 0;
        font-size: 0.9375rem;
    }
    .about-list {
        border-top: 1px solid color-mix(in srgb, var(--text-primary) 8%, transparent);
    }
    .about-list :deep(.q-item) {
        border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 6%, transparent);
        padding: 12px 4px;
    }
    .about-footer {
        margin: 4px 0 0;
        font-size: 0.8125rem;
    }
    .settings-divider {
        border: 0;
        height: 1px;
        background: color-mix(in srgb, var(--text-primary) 8%, transparent);
        margin: 8px 0;
    }
    .text-mono {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
</style>
