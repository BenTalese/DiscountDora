<template>
    <q-card flat bordered>
        <q-card-section>
            <div class="text-h6">Account</div>
            <div class="text-caption dora-text-muted">Your sign-in identity.</div>
        </q-card-section>

        <q-separator />

        <q-card-section v-if="currentUser">
            <div class="row items-center q-gutter-md">
                <q-avatar size="60px" color="accent" text-color="dark">
                    {{ initials }}
                </q-avatar>
                <div>
                    <div class="text-h6">{{ currentUser.username }}</div>
                    <div class="text-caption dora-text-muted">
                        {{ currentUser.email ?? 'No email on file.' }}
                    </div>
                </div>
            </div>

            <q-list class="q-mt-md" separator>
                <q-item>
                    <q-item-section>
                        <q-item-label caption>User ID</q-item-label>
                        <q-item-label class="text-mono">{{ currentUser.user_id }}</q-item-label>
                    </q-item-section>
                </q-item>
            </q-list>
        </q-card-section>

        <q-card-section v-else>
            <q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>
        </q-card-section>

        <q-separator />

        <!-- ── Onboarding (F1) ─────────────────────────────────── -->
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

        <q-card-section>
            <div class="text-subtitle2 q-mb-sm">Danger zone</div>
            <div class="text-caption dora-text-muted q-mb-md">
                Sign out of this device. Your data stays where it is on the server.
            </div>
            <q-btn
                color="negative"
                no-caps
                :icon="ICONS.logout"
                label="Sign out"
                :loading="signingOut"
                @click="onSignOut"
            />
        </q-card-section>
    </q-card>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import OnboardingApiService from 'src/services/api/onboardingApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, ref } from 'vue';
    import { useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const router = useRouter();
    const authStore = useAuthStore();
    const onboardingApi = new OnboardingApiService();
    const { currentUser } = storeToRefs(authStore);

    const signingOut = ref(false);
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

    const initials = computed(() => {
        const name = currentUser.value?.username ?? '';
        return name.length > 0 ? name.charAt(0).toUpperCase() : '?';
    });

    async function onSignOut() {
        signingOut.value = true;
        try {
            await authStore.logoutAsync();
            void router.push('/login');
        } finally {
            signingOut.value = false;
        }
    }
</script>

<style scoped>
    .text-mono {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.85em;
    }
</style>
