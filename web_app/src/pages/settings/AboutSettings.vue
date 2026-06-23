<template>
    <q-card flat bordered>
        <q-card-section class="row items-center q-gutter-md">
            <q-avatar size="56px" square>
                <img src="../../assets/logo-mascot.png" alt="Dashy Dora" />
            </q-avatar>
            <div>
                <div class="text-h6" style="font-family: 'Cute Dino'">Dashy Dora</div>
                <div class="text-caption dora-text-muted">Your pantry at your fingertips.</div>
            </div>
        </q-card-section>

        <q-separator />

        <q-card-section>
            <q-list separator>
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
                            Quasar 2 / Vue 3, talks to two Flask APIs over CORS.
                        </q-item-label>
                    </q-item-section>
                </q-item>

                <q-item>
                    <q-item-section>
                        <q-item-label>Dora API endpoint</q-item-label>
                        <q-item-label caption class="text-mono">{{ doraApiUrl }}</q-item-label>
                    </q-item-section>
                </q-item>

                <!-- Phase D / FU-186: the standalone merchant_api backend
                     was retired from this repo; the SPA only talks to dora_api
                     now. The retailer-scraping side runs in the sibling
                     dora-companion repo + pushes via POST /api/ingest. -->

                <!-- Repo is private — public-repo + public issue
                     links removed. Bug reports go through whatever
                     channel the operator has set up. -->

            </q-list>
        </q-card-section>

        <q-separator />

        <!-- ── Onboarding (F1) ─────────────────────────────────────────
             Moved here from Account (Settings rebuild Phase 2): it's a
             help / re-tour action, not identity management. -->
        <q-card-section>
            <div class="text-subtitle2 q-mb-sm">First-run wizard</div>
            <div class="text-caption dora-text-muted q-mb-md">
                Want to revisit the welcome tour? This sends you back to
                /welcome — nothing in your data is touched, you'll just
                step through the prompts again.
            </div>
            <q-btn
                outline
                no-caps
                :icon="ICONS.restart_alt"
                label="Restart onboarding"
                :loading="restartingOnboarding"
                @click="onRestartOnboarding"
            />
        </q-card-section>

        <q-separator />

        <q-card-section class="text-caption dora-text-muted">
            Dora is a hobby project. The mascot is doing its best.
        </q-card-section>
    </q-card>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { useQuasar } from 'quasar';
    import PwaInstallPrompt from 'src/components/PwaInstallPrompt.vue';
    import OnboardingApiService from 'src/services/api/onboardingApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, ref } from 'vue';
    import { useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

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
            // Refresh the auth payload so the router guard sees the
            // newly-NULL onboarding_completed_at and bounces us to /welcome
            // on the next navigation.
            await authStore.refreshAsync();
            // Drop the "skipped" flag too so the dashboard banner is
            // suppressed once the user is back in the wizard properly.
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

    // Reflects what AxiosHttpClient will actually use — keeps this section
    // honest for debugging deployments.
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

<style scoped>
    .text-mono {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
</style>
