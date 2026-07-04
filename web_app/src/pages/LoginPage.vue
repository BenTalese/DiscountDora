<template>
    <AuthShell backdrop="blobs" mascot="top-right">
        <template #card-head>
            <div class="login-title" style="font-family: 'Cute Dino'">
                Dashy Dora
            </div>
            <div class="login-sub">
                {{ mode === 'login' ? 'Sign in to your pantry' : 'Create your account' }}
            </div>
        </template>

        <q-form ref="formRef" @submit.prevent="onSubmit" class="q-gutter-y-md">
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
                        mode === 'login' || v.length >= 8 || 'At least 8 characters'
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

            <AuthButton
                colour="primary"
                type="submit"
                :loading="submitting"
                :label="mode === 'login' ? 'Sign In' : 'Create Account'"
            />
        </q-form>

        <template #card-foot>
            <div class="login-foot">
                <AuthButton
                    colour="secondary"
                    :label="mode === 'login' ? 'Need an account? Register' : 'Have an account? Sign in'"
                    @click="toggleMode"
                />
                <AuthButton
                    v-if="mode === 'login'"
                    colour="ghost"
                    label="Forgot password?"
                    @click="router.push('/forgot-password')"
                />
                <div v-if="mode === 'register'" class="login-fineprint">
                    Passwords must be at least 8 characters. A short
                    passphrase of a few words works well.
                </div>
            </div>
        </template>
    </AuthShell>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import AuthShell from 'src/components/AuthShell.vue';
    import AuthButton from 'src/components/AuthButton.vue';
    import FormErrorSummary from 'src/components/FormErrorSummary.vue';
    import { NormalisedApiError } from 'src/services/api/axiosHttpClient';
    import { useFormErrors } from 'src/composables/useFormErrors';
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
    // FU-099 — R-001 form-error plumbing.
    const { fieldErrors, generalError, handleSaveError, reset: resetErrors } = useFormErrors();

    const form = reactive({
        username: '',
        password: '',
        email: ''
    });

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
                handleSaveError(
                    err,
                    mode.value === 'login'
                        ? 'Sign-in failed. Please try again.'
                        : 'Registration failed. Please review the form and try again.',
                );
            }
        } finally {
            submitting.value = false;
        }
    }
</script>

<style scoped>
    /* Only page-specific typography lives here now. All chrome + tokens
       moved to AuthShell.vue; button treatment moved to AuthButton.vue. */
    .login-title {
        font-size: 2.1rem;
        line-height: 1.1;
        letter-spacing: 0.01em;
        background: linear-gradient(135deg, var(--auth-shell-accent-strong), var(--auth-shell-accent));
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .login-sub {
        color: var(--auth-shell-text-muted);
        font-size: 0.92rem;
        margin-top: 4px;
    }
    .login-foot {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .login-fineprint {
        color: var(--auth-shell-text-muted);
        font-size: 0.78rem;
        text-align: center;
        margin-top: 4px;
    }
</style>
