<template>
    <AuthShell backdrop="blobs" mascot="none">
        <template #card-head>
            <q-icon
                :name="status === 'ok' ? 'check_circle' : status === 'error' ? 'error' : 'mail_lock'"
                :color="status === 'ok' ? 'positive' : status === 'error' ? 'negative' : undefined"
                :style="status !== 'ok' && status !== 'error' ? 'color: var(--auth-shell-accent)' : ''"
                size="56px"
            />
            <div class="text-h6 q-mt-md">
                {{ status === 'ok' ? 'Email updated' : status === 'error' ? 'Link invalid' : 'Confirming…' }}
            </div>
            <div class="text-caption q-mt-xs auth-aux-sub">
                {{ status === 'ok'
                    ? 'Your account email has been changed.'
                    : status === 'error'
                        ? 'The link may have expired or already been used.'
                        : 'Just a moment.' }}
            </div>
        </template>

        <template #card-foot>
            <AuthButton colour="primary" label="Continue" to="/" />
        </template>
    </AuthShell>
</template>

<script lang="ts" setup>
    import AuthShell from 'src/components/AuthShell.vue';
    import AuthButton from 'src/components/AuthButton.vue';
    import { onMounted, ref } from 'vue';
    import { useRoute } from 'vue-router';
    import AuthApiService from 'src/services/api/authApiService';

    const route = useRoute();
    const api = new AuthApiService();
    const status = ref<'pending' | 'ok' | 'error'>('pending');

    onMounted(async () => {
        const token = String(route.query.token ?? '').trim();
        if (!token) { status.value = 'error'; return; }
        try {
            await api.confirmEmailChangeAsync(token);
            status.value = 'ok';
        } catch {
            status.value = 'error';
        }
    });
</script>

<style scoped>
    .auth-aux-sub {
        color: var(--auth-shell-text-muted);
    }
</style>
