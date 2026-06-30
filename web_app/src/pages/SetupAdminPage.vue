<template>
    <div class="setup-shell" role="main">
        <!-- Same animated mesh-gradient backdrop as the login page —
             keeps brand continuity while the badge + copy below
             differentiate this from a normal sign-in. -->
        <div class="setup-bg" aria-hidden="true">
            <span class="setup-blob setup-blob--1" />
            <span class="setup-blob setup-blob--2" />
            <span class="setup-blob setup-blob--3" />
        </div>

        <img
            class="setup-mascot"
            src="../assets/logo-mascot.png"
            alt=""
            aria-hidden="true"
        />

        <q-card class="setup-card" flat>
            <q-card-section class="text-center setup-card-head">
                <!-- One-time-setup badge — the strongest visual signal
                     that this is NOT a normal sign-in/register screen.
                     Tagged role="status" so a screen reader announces
                     the context on page load. -->
                <div class="setup-badge" role="status">
                    <q-icon name="auto_awesome" size="14px" /> One-time setup
                </div>
                <div class="setup-title" style="font-family: 'Cute Dino'">
                    Dashy Dora
                </div>
                <div class="setup-sub">
                    Welcome! Create the first admin account to get started.
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
                        outlined
                        v-model="form.email"
                        label="Email"
                        type="email"
                        autocomplete="email"
                        :error="!!fieldErrors.email"
                        :error-message="fieldErrors.email"
                        @update:model-value="clearField('email')"
                        :rules="[(v: string) => !!v || 'Email is required']"
                    />

                    <q-input
                        outlined
                        v-model="form.password"
                        label="Password"
                        :type="showPassword ? 'text' : 'password'"
                        autocomplete="new-password"
                        :error="!!fieldErrors.password"
                        :error-message="fieldErrors.password"
                        @update:model-value="clearField('password')"
                        :rules="[
                            (v: string) => !!v || 'Password is required',
                            (v: string) => v.length >= 10 || 'At least 10 characters',
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

                    <BaseButton
                        type="submit"
                        size="lg"
                        class="full-width setup-submit"
                        :loading="submitting"
                        label="Create admin account"
                    />
                </q-form>
            </q-card-section>

            <q-card-section class="text-center q-pt-none">
                <div class="setup-fineprint">
                    This screen only appears once. After setup completes,
                    sign-in becomes the entry point and new accounts can
                    register normally.
                </div>
                <div class="setup-fineprint q-mt-xs">
                    Passwords must be at least 10 characters and include
                    a letter and a digit.
                </div>
            </q-card-section>
        </q-card>
    </div>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import BaseButton from 'src/components/BaseButton.vue';
    import FormErrorSummary from 'src/components/FormErrorSummary.vue';
    import { useFormErrors } from 'src/composables/useFormErrors';
    import { useAuthStore } from 'src/stores/authStore';
    import { reactive, ref } from 'vue';
    import { useRouter } from 'vue-router';

    const $q = useQuasar();
    const authStore = useAuthStore();
    const router = useRouter();

    const showPassword = ref(false);
    const submitting = ref(false);
    const { fieldErrors, generalError, handleSaveError, reset: resetErrors } = useFormErrors();

    const form = reactive({
        username: '',
        password: '',
        email: '',
    });

    function clearField(field: string) {
        if (fieldErrors.value[field]) {
            const next = { ...fieldErrors.value };
            delete next[field];
            fieldErrors.value = next;
        }
    }

    async function onSubmit() {
        submitting.value = true;
        resetErrors();
        try {
            await authStore.setupAdminAsync({
                username: form.username,
                password: form.password,
                email: form.email,
            });
            $q.notify({
                type: 'positive', position: 'top',
                message: 'Admin account created. Welcome to Dashy Dora!',
                timeout: 4000,
            });
            void router.replace('/');
        } catch (err) {
            handleSaveError(
                err,
                'Setup failed. Please review the form and try again.',
            );
        } finally {
            submitting.value = false;
        }
    }
</script>

<style scoped>
    /* Mirrors LoginPage's locally-scoped colour system so the splash never
       blinks to a dark-theme token before auth is established. The setup
       page also runs pre-auth, so the same rules apply. */
    .setup-shell {
        --lp-bg-base: #1f2647;
        --lp-blob-1: #ff7ad9;
        --lp-blob-2: #f5c462;
        --lp-blob-3: #4cd5b7;
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

    .setup-bg {
        position: absolute;
        inset: 0;
        z-index: 0;
        overflow: hidden;
        pointer-events: none;
    }
    .setup-blob {
        position: absolute;
        width: 60vmax;
        height: 60vmax;
        border-radius: 50%;
        filter: blur(80px);
        opacity: 0.75;
        mix-blend-mode: screen;
        will-change: transform;
    }
    .setup-blob--1 {
        top: -20vmax;
        left: -10vmax;
        background: var(--lp-blob-1);
        animation: drift-1 22s ease-in-out infinite;
    }
    .setup-blob--2 {
        bottom: -20vmax;
        right: -10vmax;
        background: var(--lp-blob-2);
        animation: drift-2 26s ease-in-out infinite;
    }
    .setup-blob--3 {
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

    .setup-mascot {
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
        .setup-mascot {
            top: 2%;
            right: 50%;
            margin-right: -48px;
            width: 96px;
            height: 96px;
        }
    }
    @media (max-width: 360px) {
        .setup-mascot {
            margin-right: -36px;
            width: 72px;
            height: 72px;
        }
    }

    .setup-card {
        position: relative;
        z-index: 2;
        width: 100%;
        max-width: 460px;
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
    .setup-card-head { padding-top: 22px; padding-bottom: 4px; }

    /* The "One-time setup" pill — the marker that this isn't /login.
       Lives above the title so it reads first. */
    .setup-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        margin-bottom: 10px;
        border-radius: 999px;
        background: linear-gradient(135deg, var(--lp-accent-strong), var(--lp-accent));
        color: #fff;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        box-shadow: 0 6px 14px -6px rgba(0, 106, 128, 0.6);
    }
    .setup-title {
        font-size: 2.1rem;
        line-height: 1.1;
        letter-spacing: 0.01em;
        background: linear-gradient(135deg, var(--lp-accent-strong), var(--lp-accent));
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .setup-sub {
        color: var(--lp-text-muted);
        font-size: 0.95rem;
        margin-top: 6px;
    }

    .setup-card :deep(.q-field__native),
    .setup-card :deep(.q-field__input),
    .setup-card :deep(.q-field__prefix),
    .setup-card :deep(.q-field__suffix),
    .setup-card :deep(.q-field__label) {
        color: var(--lp-text);
    }
    .setup-card :deep(.q-field--outlined .q-field__control::before) {
        border-color: rgba(31, 38, 71, 0.25);
    }
    .setup-card :deep(.q-field--outlined.q-field--focused .q-field__control::after) {
        border-color: var(--lp-accent-strong);
    }

    .setup-submit {
        background: linear-gradient(135deg, var(--lp-accent-strong), var(--lp-accent));
        color: #fff;
        font-weight: 600;
        letter-spacing: 0.02em;
        border-radius: 12px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        box-shadow: 0 10px 24px -10px rgba(0, 106, 128, 0.55);
    }
    .setup-submit:hover {
        transform: translateY(-1px);
        box-shadow: 0 14px 28px -10px rgba(0, 106, 128, 0.65);
    }

    .setup-fineprint { color: var(--lp-text-muted); font-size: 0.78rem; line-height: 1.4; }
    .full-width { width: 100%; }

    @media (prefers-reduced-motion: reduce) {
        .setup-blob,
        .setup-mascot,
        .setup-card { animation: none !important; }
        .setup-blob { opacity: 0.6; }
    }
</style>
