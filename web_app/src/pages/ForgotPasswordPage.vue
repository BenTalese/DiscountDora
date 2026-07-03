<template>
    <AuthShell backdrop="blobs" mascot="none">
        <template #card-head>
            <q-icon :name="ICONS.lock_reset" size="56px" :style="'color: var(--auth-shell-accent)'" />
            <div class="text-h6 q-mt-md">Forgot password</div>
            <div class="text-caption q-mt-xs auth-aux-sub">
                Enter your account email and we'll send a reset link.
            </div>
        </template>

        <q-form v-if="!submitted" @submit.prevent="onSubmit" class="q-gutter-y-md">
            <q-input
                v-model="email"
                type="email"
                outlined
                autofocus
                label="Email address"
                autocomplete="email"
                :rules="[(v: string) => !!v || 'Email is required']"
            />
            <AuthButton
                type="submit"
                colour="primary"
                :loading="submitting"
                label="Send reset link"
            />
        </q-form>
        <q-banner v-else class="dora-bg-sunken" rounded>
            <template #avatar><q-icon :name="ICONS.mark_email_read" /></template>
            If that address is registered, a reset link is on its way.
            Check your inbox (and spam folder).
        </q-banner>

        <template #card-foot>
            <AuthButton colour="ghost" label="Back to sign in" to="/login" />
        </template>
    </AuthShell>
</template>

<script lang="ts" setup>
    import AuthShell from 'src/components/AuthShell.vue';
    import AuthButton from 'src/components/AuthButton.vue';
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
    .auth-aux-sub {
        color: var(--auth-shell-text-muted);
    }
</style>
