<template>
    <div class="auth-shell">
        <q-card class="auth-card" flat bordered>
            <q-card-section class="text-center">
                <q-icon
                    :name="status === 'ok' ? 'mark_email_read' : status === 'error' ? 'error' : 'mail_lock'"
                    :color="status === 'ok' ? 'positive' : status === 'error' ? 'negative' : undefined"
                    :class="{ 'dora-text-secondary': status !== 'ok' && status !== 'error' }"
                    size="64px"
                />
                <div class="text-h6 q-mt-md">
                    {{ headline }}
                </div>
                <div class="text-caption dora-text-muted q-mt-xs">
                    {{ subline }}
                </div>
            </q-card-section>
            <q-card-actions align="center">
                <BaseButton
                    v-if="status === 'ok'"
                    variant="primary"
                    label="Continue to sign in"
                    to="/login?verified=1"
                />
                <BaseButton
                    v-else-if="status === 'error'"
                    variant="ghost"
                    class="text-primary"
                    label="Resend verification"
                    @click="resendOpen = true"
                />
                <BaseButton
                    v-else
                    variant="ghost"
                    class="text-primary"
                    label="Cancel"
                    to="/login"
                />
            </q-card-actions>
        </q-card>

        <BaseDialog v-model="resendOpen" card-style="min-width: 320px">
                <q-card-section>
                    <div class="text-h6">Resend verification</div>
                </q-card-section>
                <q-card-section>
                    <q-input
                        v-model="resendEmail"
                        type="email"
                        outlined
                        dense
                        label="Email address"
                        autofocus
                    />
                </q-card-section>
                <q-card-actions align="right">
                    <BaseButton variant="ghost" label="Cancel" v-close-popup />
                    <BaseButton
                        variant="primary"
                        label="Send"
                        :loading="resending"
                        :disable="!resendEmail.trim() || resending"
                        @click="onResend"
                    />
                </q-card-actions>
        </BaseDialog>
    </div>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { computed, onMounted, ref } from 'vue';
    import { useRoute } from 'vue-router';
    import AuthApiService from 'src/services/api/authApiService';

    const $q = useQuasar();
    const route = useRoute();
    const api = new AuthApiService();

    const status = ref<'pending' | 'ok' | 'error'>('pending');
    const resendOpen = ref(false);
    const resendEmail = ref('');
    const resending = ref(false);

    const headline = computed(() => {
        if (status.value === 'ok') return 'Email verified';
        if (status.value === 'error') return 'Verification link invalid';
        return 'Verifying your email…';
    });
    const subline = computed(() => {
        if (status.value === 'ok') return 'You can now sign in to Dashy Dora.';
        if (status.value === 'error') return 'The link may have expired. Request a fresh one below.';
        return 'Just a moment.';
    });

    onMounted(async () => {
        const token = String(route.query.token ?? '').trim();
        if (!token) {
            status.value = 'error';
            return;
        }
        try {
            await api.verifyEmailAsync(token);
            status.value = 'ok';
        } catch {
            status.value = 'error';
        }
    });

    async function onResend() {
        resending.value = true;
        try {
            await api.resendVerificationAsync(resendEmail.value.trim());
            $q.notify({
                type: 'positive',
                position: 'top',
                message: 'If that address is registered, a verification email is on its way.',
            });
            resendOpen.value = false;
            resendEmail.value = '';
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'top',
                message: err instanceof Error ? err.message : 'Could not send.',
            });
        } finally {
            resending.value = false;
        }
    }
</script>

<style scoped>
    .auth-shell {
        min-height: 100vh; display: flex; align-items: center; justify-content: center;
        padding: 24px; background: var(--surface-page);
    }
    .auth-card { max-width: 420px; width: 100%; padding: 16px; }
</style>
