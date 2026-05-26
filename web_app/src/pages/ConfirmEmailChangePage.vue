<template>
    <div class="auth-shell">
        <q-card class="auth-card" flat bordered>
            <q-card-section class="text-center">
                <q-icon
                    :name="status === 'ok' ? 'check_circle' : status === 'error' ? 'error' : 'mail_lock'"
                    :color="status === 'ok' ? 'positive' : status === 'error' ? 'negative' : 'grey-7'"
                    size="56px"
                />
                <div class="text-h6 q-mt-md">
                    {{ status === 'ok' ? 'Email updated' : status === 'error' ? 'Link invalid' : 'Confirming…' }}
                </div>
                <div class="text-caption text-grey q-mt-xs">
                    {{ status === 'ok'
                        ? 'Your account email has been changed.'
                        : status === 'error'
                            ? 'The link may have expired or already been used.'
                            : 'Just a moment.' }}
                </div>
            </q-card-section>
            <q-card-actions align="center">
                <q-btn color="primary" no-caps label="Continue" to="/" />
            </q-card-actions>
        </q-card>
    </div>
</template>

<script lang="ts" setup>
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
    .auth-shell {
        min-height: 100vh; display: flex; align-items: center; justify-content: center;
        padding: 24px; background: #f9f6f0;
    }
    .auth-card { max-width: 420px; width: 100%; padding: 16px; }
</style>
