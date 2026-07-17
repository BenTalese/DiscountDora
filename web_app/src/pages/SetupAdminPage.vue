<template>
    <AuthShell backdrop="blobs" mascot="top-right">
        <template #card-head>
            <div class="setup-badge" role="status">
                <q-icon name="auto_awesome" size="14px" /> One-time setup
            </div>
            <div class="setup-title" style="font-family: 'Cute Dino'">
                Dashy Dora
            </div>
            <div class="setup-sub">
                Welcome! Create the first admin account to get started.
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
                hint="At least 8 characters — a passphrase works well."
                :error="!!fieldErrors.password"
                :error-message="fieldErrors.password"
                @update:model-value="clearField('password')"
                :rules="[
                    (v: string) => !!v || 'Password is required',
                    (v: string) => v.length >= 8 || 'At least 8 characters',
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
                label="Create admin account"
            />
        </q-form>

        <template #card-foot>
            <div class="setup-fineprint">
                This screen only appears once. After setup completes,
                sign-in becomes the entry point and new accounts can
                register normally.
            </div>
        </template>
    </AuthShell>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import AuthShell from 'src/components/AuthShell.vue';
    import AuthButton from 'src/components/AuthButton.vue';
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
    /* Page-specific typography + the one-time-setup badge. All chrome
       + button treatment lives on AuthShell / AuthButton. Fixes FU-440
       (was verbatim copy of LoginPage's private colour ladder). */
    .setup-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        margin-bottom: 10px;
        border-radius: 999px;
        background: linear-gradient(135deg, var(--auth-shell-accent-strong), var(--auth-shell-accent));
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
        background: linear-gradient(135deg, var(--auth-shell-accent-strong), var(--auth-shell-accent));
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .setup-sub {
        color: var(--auth-shell-text-muted);
        font-size: 0.95rem;
        margin-top: 6px;
    }
    .setup-fineprint {
        color: var(--auth-shell-text-muted);
        font-size: 0.78rem;
        line-height: 1.4;
        text-align: center;
    }
</style>
