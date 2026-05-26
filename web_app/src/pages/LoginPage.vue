<template>
    <div class="login-shell">
        <q-card class="login-card" flat bordered>
            <q-card-section class="text-center">
                <q-avatar size="120px" class="q-mb-md">
                    <img src="../assets/logo-mascot.png" alt="Discount Dora logo" />
                </q-avatar>
                <div class="text-h4 text-primary" style="font-family: 'Cute Dino'">Discount Dora</div>
                <div class="text-caption text-grey q-mt-xs">
                    {{ mode === 'login' ? 'Sign in to your pantry' : 'Create your account' }}
                </div>
            </q-card-section>

            <q-card-section>
                <q-form ref="formRef" @submit.prevent="onSubmit" class="q-gutter-md">
                    <q-input
                        outlined
                        autofocus
                        v-model="form.username"
                        label="Username"
                        autocomplete="username"
                        :error="!!fieldErrors.username"
                        :error-message="fieldErrors.username"
                        @update:model-value="clearField('username')"
                        :rules="[(v: string) => !!v || 'Username is required']"
                    />

                    <q-input
                        v-if="mode === 'register'"
                        outlined
                        v-model="form.email"
                        label="Email (optional)"
                        type="email"
                        autocomplete="email"
                        :error="!!fieldErrors.email"
                        :error-message="fieldErrors.email"
                        @update:model-value="clearField('email')"
                    />

                    <q-input
                        outlined
                        v-model="form.password"
                        label="Password"
                        :type="showPassword ? 'text' : 'password'"
                        :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
                        :error="!!fieldErrors.password"
                        :error-message="fieldErrors.password"
                        @update:model-value="clearField('password')"
                        :rules="[
                            (v: string) => !!v || 'Password is required',
                            (v: string) =>
                                mode === 'login' || v.length >= 4 || 'At least 4 characters'
                        ]"
                    >
                        <template #append>
                            <q-icon
                                :name="showPassword ? 'visibility_off' : 'visibility'"
                                class="cursor-pointer"
                                @click="showPassword = !showPassword"
                            />
                        </template>
                    </q-input>

                    <FormErrorSummary :message="generalError" />

                    <q-btn
                        type="submit"
                        color="primary"
                        size="lg"
                        class="full-width"
                        :loading="submitting"
                        :label="mode === 'login' ? 'Sign In' : 'Create Account'"
                    />
                </q-form>
            </q-card-section>

            <q-card-section class="text-center q-pt-none">
                <q-btn
                    flat
                    dense
                    no-caps
                    size="sm"
                    color="primary"
                    :label="mode === 'login' ? 'Need an account? Register' : 'Have an account? Sign in'"
                    @click="toggleMode"
                />
                <div v-if="mode === 'login'" class="q-mt-xs">
                    <router-link
                        to="/forgot-password"
                        class="text-caption text-primary"
                        style="text-decoration: none;"
                    >
                        Forgot password?
                    </router-link>
                </div>
                <div v-else class="text-caption text-grey-7 q-mt-sm">
                    Passwords must be at least 10 characters and include
                    a letter and a digit.
                </div>
            </q-card-section>
        </q-card>
    </div>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import FormErrorSummary from 'src/components/FormErrorSummary.vue';
    import { NormalisedApiError } from 'src/services/api/axiosHttpClient';
    import { extractFieldErrors } from 'src/services/errorHandling/apiErrorHandler';
    import { useAuthStore } from 'src/stores/authStore';
    import { onMounted, reactive, ref } from 'vue';
    import { useRoute, useRouter } from 'vue-router';

    const $q = useQuasar();
    const authStore = useAuthStore();
    const router = useRouter();
    const route = useRoute();

    onMounted(() => {
        // A1: surface a toast when arriving from /verify-email so the user
        // sees confirmation of the click-through.
        if (route.query.verified === '1') {
            $q.notify({
                type: 'positive', position: 'top',
                message: 'Email verified. Sign in to continue.',
                timeout: 4000,
            });
        }
    });

    const mode = ref<'login' | 'register'>('login');
    const showPassword = ref(false);
    const submitting = ref(false);
    const generalError = ref<string | null>(null);
    const fieldErrors = ref<Record<string, string>>({});

    const form = reactive({
        username: '',
        password: '',
        email: ''
    });

    function resetErrors() {
        generalError.value = null;
        fieldErrors.value = {};
    }

    function clearField(field: string) {
        if (fieldErrors.value[field]) {
            const next = { ...fieldErrors.value };
            delete next[field];
            fieldErrors.value = next;
        }
    }

    function toggleMode() {
        mode.value = mode.value === 'login' ? 'register' : 'login';
        resetErrors();
    }

    async function onSubmit() {
        submitting.value = true;
        resetErrors();
        try {
            if (mode.value === 'login') {
                await authStore.loginAsync({
                    username: form.username,
                    password: form.password
                });
            } else {
                await authStore.registerAsync({
                    username: form.username,
                    password: form.password,
                    email: form.email.length > 0 ? form.email : null
                });
            }

            const redirect = (route.query.redirect as string | undefined) ?? '/';
            void router.replace(redirect);
        } catch (err) {
            // Login 401 is opaque by design — never tell the user *which*
            // half (username vs password) was wrong. Show a stable message
            // and skip the field-level extraction.
            if (
                mode.value === 'login' &&
                err instanceof NormalisedApiError &&
                err.status === 401
            ) {
                generalError.value = 'Sign-in failed. Check your username and password.';
            } else {
                const extracted = extractFieldErrors(err);
                fieldErrors.value = extracted.fieldErrors;
                generalError.value =
                    extracted.generalError ??
                    (mode.value === 'login'
                        ? 'Sign-in failed. Please try again.'
                        : 'Registration failed. Please review the form and try again.');
            }
            // eslint-disable-next-line no-console
            console.warn('auth submit failed', err);
        } finally {
            submitting.value = false;
        }
    }
</script>

<style scoped>
    .login-shell {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 24px;
        background: linear-gradient(135deg, #f4f1e8 0%, #d8e8f5 100%);
        /* The login page renders before the user is authenticated and
           before any saved theme preference is applied, so it always
           uses light-mode colours. Without this override, OS dark mode
           sets --q-text to a near-white value, which then matches the
           hardcoded white card background — making typed text invisible. */
        color: #222;
    }
    .login-card {
        width: 100%;
        max-width: 420px;
        padding: 16px;
        background: white;
        color: #222;
    }
    .login-card :deep(.q-field__native),
    .login-card :deep(.q-field__prefix),
    .login-card :deep(.q-field__suffix) {
        color: #222;
    }
    .full-width {
        width: 100%;
    }
</style>
