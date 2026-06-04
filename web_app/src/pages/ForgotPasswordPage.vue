<template>
    <div class="auth-shell">
        <q-card class="auth-card" flat bordered>
            <q-card-section class="text-center">
                <q-icon :name="ICONS.lock_reset" size="56px" class="text-primary" />
                <div class="text-h6 q-mt-md">Forgot password</div>
                <div class="text-caption dora-text-muted q-mt-xs">
                    Enter your account email and we'll send a reset link.
                </div>
            </q-card-section>
            <q-card-section v-if="!submitted">
                <q-form @submit.prevent="onSubmit" class="q-gutter-md">
                    <q-input
                        v-model="email"
                        type="email"
                        outlined
                        autofocus
                        label="Email address"
                        autocomplete="email"
                        :rules="[(v: string) => !!v || 'Email is required']"
                    />
                    <q-btn
                        type="submit"
                        color="primary"
                        size="lg"
                        class="full-width"
                        :loading="submitting"
                        label="Send reset link"
                    />
                </q-form>
            </q-card-section>
            <q-card-section v-else>
                <q-banner class="dora-bg-sunken" rounded>
                    <template #avatar><q-icon :name="ICONS.mark_email_read" /></template>
                    If that address is registered, a reset link is on its way.
                    Check your inbox (and spam folder).
                </q-banner>
            </q-card-section>
            <q-card-actions align="center">
                <BaseButton variant="ghost" class="text-primary" label="Back to sign in" to="/login" />
            </q-card-actions>
        </q-card>
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { ref } from 'vue';
    import AuthApiService from 'src/services/api/authApiService';

    const api = new AuthApiService();
    const email = ref('');
    const submitting = ref(false);
    const submitted = ref(false);

    async function onSubmit() {
        submitting.value = true;
        try {
            await api.forgotPasswordAsync(email.value.trim());
        } finally {
            submitting.value = false;
            // Always pretend success — the backend is already anti-
            // enumeration; the SPA matches.
            submitted.value = true;
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
