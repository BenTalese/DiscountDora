<template>
    <div class="login-shell" role="main">
        <!-- Animated mesh-gradient backdrop. Three colour blobs slowly
             drift; CSS keyframes only — no canvas, no JS. Reduced-motion
             freezes everything. -->
        <div class="login-bg" aria-hidden="true">
            <span class="login-blob login-blob--1" />
            <span class="login-blob login-blob--2" />
            <span class="login-blob login-blob--3" />
        </div>

        <!-- Floating mascot — bobs gently. Sits behind the card on
             desktop, hidden on small screens to avoid card overlap. -->
        <img
            class="login-mascot"
            src="../assets/logo-mascot.png"
            alt=""
            aria-hidden="true"
        />

        <q-card class="login-card" flat>
            <q-card-section class="text-center login-card-head">
                <div class="login-title" style="font-family: 'Cute Dino'">
                    Dashy Dora
                </div>
                <div class="login-sub">
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
                        size="lg"
                        class="full-width login-submit"
                        :loading="submitting"
                        :label="mode === 'login' ? 'Sign In' : 'Create Account'"
                        unelevated
                    />
                </q-form>
            </q-card-section>

            <q-card-section class="text-center q-pt-none">
                <q-btn
                    flat
                    dense
                    no-caps
                    size="sm"
                    class="login-link-btn"
                    :label="mode === 'login' ? 'Need an account? Register' : 'Have an account? Sign in'"
                    @click="toggleMode"
                />
                <div v-if="mode === 'login'" class="q-mt-xs">
                    <router-link to="/forgot-password" class="login-link">
                        Forgot password?
                    </router-link>
                </div>
                <div v-else class="login-fineprint q-mt-sm">
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
             
            console.warn('auth submit failed', err);
        } finally {
            submitting.value = false;
        }
    }
</script>

<style scoped>
    /* The login page renders pre-auth, so we deliberately *do not* read
       from --text-primary or any of the app's data-theme tokens — those
       can flip to dark values before the user has signed in. Everything
       here is locally scoped and forced light. */
    .login-shell {
        --lp-bg-base: #1f2647;          /* deep midnight under the blobs */
        --lp-blob-1: #ff7ad9;           /* magenta */
        --lp-blob-2: #f5c462;           /* dora amber */
        --lp-blob-3: #4cd5b7;           /* mint */
        --lp-card-bg: rgba(255, 255, 255, 0.94);
        --lp-card-border: rgba(255, 255, 255, 0.6);
        --lp-text: #1f2330;
        --lp-text-muted: #5b6173;
        --lp-accent: #006a80;
        --lp-accent-strong: #17b073;
        --lp-shadow: 0 30px 80px -30px rgba(20, 12, 50, 0.55);

        color-scheme: light;
        min-height: 100vh;
        position: relative;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 24px;
        background: var(--lp-bg-base);
        color: var(--lp-text);
    }

    /* ───── Animated backdrop ─────────────────────────────────────── */
    .login-bg {
        position: absolute;
        inset: 0;
        z-index: 0;
        overflow: hidden;
        pointer-events: none;
    }
    .login-blob {
        position: absolute;
        width: 60vmax;
        height: 60vmax;
        border-radius: 50%;
        filter: blur(80px);
        opacity: 0.75;
        mix-blend-mode: screen;
        will-change: transform;
    }
    .login-blob--1 {
        top: -20vmax;
        left: -10vmax;
        background: var(--lp-blob-1);
        animation: drift-1 22s ease-in-out infinite;
    }
    .login-blob--2 {
        bottom: -20vmax;
        right: -10vmax;
        background: var(--lp-blob-2);
        animation: drift-2 26s ease-in-out infinite;
    }
    .login-blob--3 {
        top: 30%;
        left: 40%;
        background: var(--lp-blob-3);
        animation: drift-3 30s ease-in-out infinite;
    }
    @keyframes drift-1 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        33%      { transform: translate(15vmax, 8vmax) scale(1.1); }
        66%      { transform: translate(-8vmax, 18vmax) scale(0.95); }
    }
    @keyframes drift-2 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        33%      { transform: translate(-12vmax, -10vmax) scale(1.05); }
        66%      { transform: translate(6vmax, -16vmax) scale(1.15); }
    }
    @keyframes drift-3 {
        0%, 100% { transform: translate(-50%, -50%) scale(1); }
        50%      { transform: translate(-30%, -70%) scale(1.2); }
    }

    /* ───── Mascot ────────────────────────────────────────────────── */
    .login-mascot {
        position: absolute;
        top: 8%;
        right: 7%;
        width: 160px;
        height: 160px;
        object-fit: contain;
        z-index: 1;
        animation: bob 6s ease-in-out infinite;
        filter: drop-shadow(0 18px 22px rgba(20, 12, 50, 0.45));
    }
    @keyframes bob {
        0%, 100% { transform: translateY(0) rotate(-2deg); }
        50%      { transform: translateY(-12px) rotate(2deg); }
    }
    @media (max-width: 760px) {
        .login-mascot { display: none; }
    }

    /* ───── Card ──────────────────────────────────────────────────── */
    .login-card {
        position: relative;
        z-index: 2;
        width: 100%;
        max-width: 420px;
        padding: 8px 4px;
        border-radius: 22px;
        background: var(--lp-card-bg);
        border: 1px solid var(--lp-card-border);
        backdrop-filter: blur(18px) saturate(140%);
        -webkit-backdrop-filter: blur(18px) saturate(140%);
        box-shadow: var(--lp-shadow);
        color: var(--lp-text);
        animation: card-enter 0.55s cubic-bezier(0.2, 0.9, 0.25, 1.1) both;
    }
    @keyframes card-enter {
        from { opacity: 0; transform: translateY(18px) scale(0.97); }
        to   { opacity: 1; transform: translateY(0) scale(1); }
    }
    .login-card-head { padding-top: 28px; padding-bottom: 4px; }
    .login-title {
        font-size: 2.1rem;
        line-height: 1.1;
        letter-spacing: 0.01em;
        background: linear-gradient(135deg, var(--lp-accent-strong), var(--lp-accent));
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .login-sub {
        color: var(--lp-text-muted);
        font-size: 0.92rem;
        margin-top: 4px;
    }

    /* Force the inputs to be readable regardless of any global theme
       state. Quasar's outlined inputs pick up the field text colour from
       the cascade — pin it here so dark-mode tokens can never bleed in. */
    .login-card :deep(.q-field__native),
    .login-card :deep(.q-field__input),
    .login-card :deep(.q-field__prefix),
    .login-card :deep(.q-field__suffix),
    .login-card :deep(.q-field__label) {
        color: var(--lp-text);
    }
    .login-card :deep(.q-field--outlined .q-field__control:before) {
        border-color: rgba(31, 38, 71, 0.25);
    }
    .login-card :deep(.q-field--outlined.q-field--focused .q-field__control:after) {
        border-color: var(--lp-accent-strong);
    }

    .login-submit {
        background: linear-gradient(135deg, var(--lp-accent-strong), var(--lp-accent));
        color: #fff;
        font-weight: 600;
        letter-spacing: 0.02em;
        border-radius: 12px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        box-shadow: 0 10px 24px -10px rgba(0, 106, 128, 0.55);
    }
    .login-submit:hover {
        transform: translateY(-1px);
        box-shadow: 0 14px 28px -10px rgba(0, 106, 128, 0.65);
    }

    .login-link-btn { color: var(--lp-accent); }
    .login-link {
        color: var(--lp-accent);
        text-decoration: none;
        font-size: 0.82rem;
    }
    .login-link:hover { text-decoration: underline; }
    .login-fineprint { color: var(--lp-text-muted); font-size: 0.78rem; }
    .full-width { width: 100%; }

    /* Respect users who don't want motion. Lock the blobs and mascot to
       their initial position; card still fades in but without scaling. */
    @media (prefers-reduced-motion: reduce) {
        .login-blob,
        .login-mascot,
        .login-card { animation: none !important; }
        .login-blob { opacity: 0.6; }
    }
</style>
