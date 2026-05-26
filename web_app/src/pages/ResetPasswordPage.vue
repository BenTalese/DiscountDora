<template>
    <div class="auth-shell">
        <q-card class="auth-card" flat bordered>
            <q-card-section class="text-center">
                <q-icon name="password" size="56px" class="text-primary" />
                <div class="text-h6 q-mt-md">Choose a new password</div>
                <div class="text-caption text-grey q-mt-xs">
                    Must be at least 10 characters and include a letter and a digit.
                </div>
            </q-card-section>
            <q-card-section v-if="!token">
                <q-banner class="bg-red-1 text-red-9" rounded>
                    This reset link is missing a token. Request a fresh one
                    from Forgot password.
                </q-banner>
            </q-card-section>
            <q-card-section v-else-if="!done">
                <q-form @submit.prevent="onSubmit" class="q-gutter-md">
                    <q-input
                        v-model="password"
                        outlined
                        autofocus
                        type="password"
                        label="New password"
                        autocomplete="new-password"
                        :error="!!fieldError"
                        :error-message="fieldError"
                        @update:model-value="fieldError = ''"
                    />
                    <q-input
                        v-model="confirm"
                        outlined
                        type="password"
                        label="Confirm new password"
                        autocomplete="new-password"
                    />
                    <q-btn
                        type="submit"
                        color="primary"
                        size="lg"
                        class="full-width"
                        :loading="submitting"
                        :disable="!password || password !== confirm"
                        label="Reset password"
                    />
                    <div v-if="password && password !== confirm" class="text-caption text-negative">
                        Passwords don't match.
                    </div>
                </q-form>
            </q-card-section>
            <q-card-section v-else>
                <q-banner class="bg-green-1 text-green-9" rounded>
                    <template #avatar><q-icon name="check_circle" /></template>
                    Password reset. Sign in with your new password.
                </q-banner>
            </q-card-section>
            <q-card-actions align="center">
                <q-btn
                    v-if="done"
                    color="primary"
                    no-caps
                    label="Continue to sign in"
                    to="/login"
                />
                <q-btn v-else flat no-caps color="primary" label="Cancel" to="/login" />
            </q-card-actions>
        </q-card>
    </div>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import { computed, ref } from 'vue';
    import { useRoute } from 'vue-router';
    import AuthApiService, { } from 'src/services/api/authApiService';
    import { NormalisedApiError } from 'src/services/api/axiosHttpClient';

    const $q = useQuasar();
    const route = useRoute();
    const api = new AuthApiService();

    const token = computed(() => String(route.query.token ?? '').trim());
    const password = ref('');
    const confirm = ref('');
    const submitting = ref(false);
    const done = ref(false);
    const fieldError = ref('');

    async function onSubmit() {
        submitting.value = true;
        fieldError.value = '';
        try {
            await api.resetPasswordAsync(token.value, password.value);
            done.value = true;
        } catch (err) {
            if (err instanceof NormalisedApiError) {
                const fieldMsg =
                    (err.details?.errors as Record<string, string[]> | undefined)?.['new_password']?.[0];
                if (fieldMsg) {
                    fieldError.value = fieldMsg;
                } else {
                    $q.notify({
                        type: 'negative',
                        position: 'top',
                        message: err.message || 'Reset failed.',
                    });
                }
            } else {
                $q.notify({ type: 'negative', position: 'top', message: String(err) });
            }
        } finally {
            submitting.value = false;
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
