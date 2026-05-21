<template>
    <div class="login-shell">
        <q-card class="login-card" flat bordered>
            <q-card-section class="text-center">
                <q-avatar size="120px" class="q-mb-md">
                    <img src="../assets/logo-mascot.png" alt="Discount Dora logo" />
                </q-avatar>
                <div class="dora-fontFamily-cuteDino text-h4 text-primary">Discount Dora</div>
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
                        :rules="[(v: string) => !!v || 'Username is required']"
                    />

                    <q-input
                        v-if="mode === 'register'"
                        outlined
                        v-model="form.email"
                        label="Email (optional)"
                        type="email"
                        autocomplete="email"
                    />

                    <q-input
                        outlined
                        v-model="form.password"
                        label="Password"
                        :type="showPassword ? 'text' : 'password'"
                        :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
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

                    <q-banner v-if="errorMessage" class="bg-red-1 text-red-9" dense rounded>
                        {{ errorMessage }}
                    </q-banner>

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
            </q-card-section>
        </q-card>
    </div>
</template>

<script lang="ts" setup>
    import { useAuthStore } from 'src/stores/authStore';
    import { reactive, ref } from 'vue';
    import { useRoute, useRouter } from 'vue-router';

    const authStore = useAuthStore();
    const router = useRouter();
    const route = useRoute();

    const mode = ref<'login' | 'register'>('login');
    const showPassword = ref(false);
    const submitting = ref(false);
    const errorMessage = ref<string | null>(null);

    const form = reactive({
        username: '',
        password: '',
        email: ''
    });

    function toggleMode() {
        mode.value = mode.value === 'login' ? 'register' : 'login';
        errorMessage.value = null;
    }

    async function onSubmit() {
        submitting.value = true;
        errorMessage.value = null;
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
            errorMessage.value =
                mode.value === 'login'
                    ? 'Sign-in failed. Check your username and password.'
                    : 'Registration failed. That username may already be taken.';
            // Surface the underlying error in the console for dev visibility.
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
