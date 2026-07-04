<template>
    <AuthShell backdrop="blobs" mascot="top-right">
        <template #card-head>
            <div class="setup-badge" role="status">
                <q-icon name="dns" size="14px" /> Choose your Dora
            </div>
            <div class="setup-title" style="font-family: 'Cute Dino'">
                Dashy Dora
            </div>
            <div class="setup-sub">
                Point this app at the Dora instance you're running &mdash;
                a home server, the shared family box, or a hosted one.
            </div>
        </template>

        <q-form ref="formRef" @submit.prevent="onSubmit" class="q-gutter-y-md">
            <q-input
                outlined
                autofocus
                v-model="form.url"
                label="Instance URL"
                autocomplete="url"
                placeholder="https://dora.example.com"
                inputmode="url"
                :error="!!errorMessage"
                :error-message="errorMessage ?? undefined"
                @update:model-value="errorMessage = null"
            />

            <AuthButton
                type="submit"
                :label="submitting ? 'Checking&hellip;' : 'Connect'"
                :loading="submitting"
                :disable="!form.url.trim()"
            />
        </q-form>

        <template #card-foot>
            <div class="setup-help">
                Enter the full URL you'd type in a browser. We'll add
                <code>/api</code> automatically if you leave it off.
                You can change this later in Settings &rarr; About.
            </div>
        </template>
    </AuthShell>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import AuthShell from 'src/components/AuthShell.vue';
    import AuthButton from 'src/components/AuthButton.vue';
    import { reactive, ref } from 'vue';
    import { useRouter } from 'vue-router';
    import axios from 'axios';
    import { setBackendBaseUrl, getBackendBaseUrl, clearBackendBaseUrl } from 'src/services/api/backendUrl';

    const $q = useQuasar();
    const router = useRouter();

    const submitting = ref(false);
    const errorMessage = ref<string | null>(null);

    const form = reactive({
        url: getBackendBaseUrl() || '',
    });

    async function onSubmit() {
        const raw = form.url.trim();
        if (!raw) return;
        submitting.value = true;
        errorMessage.value = null;
        try {
            // Provisionally set the URL so the health probe uses the
            // normalised form; roll back if the probe fails.
            const previous = getBackendBaseUrl();
            const url = await setBackendBaseUrl(raw);
            try {
                // /api/auth/me is the same anonymous-boot probe the auth
                // store uses on cold-load. It returns 200 (with or without
                // a user) or 401 — either shape means "backend answered."
                await axios.get(url + '/auth/me', {
                    withCredentials: true,
                    validateStatus: (s) => s >= 200 && s < 500,
                    timeout: 6000,
                });
            } catch (probeErr) {
                // Roll back the persisted URL so a bad answer doesn't lock
                // the app into a broken state.
                if (previous) {
                    await setBackendBaseUrl(previous);
                } else {
                    await clearBackendBaseUrl();
                }
                throw probeErr;
            }
            $q.notify({
                type: 'positive', position: 'top',
                message: 'Connected. Welcome to Dora!',
                timeout: 2500,
            });
            void router.replace('/');
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Could not reach that instance.';
            errorMessage.value = 'Could not reach that instance — check the URL and your connection.';
            console.warn('BackendSetup probe failed', message);
        } finally {
            submitting.value = false;
        }
    }
</script>

<style scoped>
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
        letter-spacing: 0.02em;
    }
    .setup-title {
        font-size: 2rem;
        line-height: 1.1;
        margin-bottom: 4px;
    }
    .setup-sub {
        font-size: 0.95rem;
        color: var(--text-secondary);
        margin-bottom: 8px;
    }
    .setup-help {
        font-size: 0.8rem;
        color: var(--text-secondary);
        text-align: center;
    }
    .setup-help code {
        background: var(--surface-sunken);
        padding: 1px 4px;
        border-radius: 3px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
</style>
