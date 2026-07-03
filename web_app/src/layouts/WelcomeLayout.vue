<template>
    <!-- Minimal first-run shell: no nav drawer, no header chrome — just a
         centred container so the user's eye lands on the wizard, not the
         app furniture. We keep the offline banner because the wizard
         needs the API to seed and complete.

         Onboarding is deliberately a plain dark canvas — no AuthShell
         blobs — so focus stays on the scene text, not the backdrop. -->
    <q-layout view="hHh Lpr lFf" class="welcome-layout">
        <q-header reveal class="bg-transparent welcome-header q-px-md">
            <q-toolbar class="welcome-toolbar">
                <q-avatar square size="36px">
                    <img src="../assets/logo-mascot.png" alt="Dashy Dora" />
                </q-avatar>
                <q-toolbar-title class="welcome-title">
                    Dashy Dora
                </q-toolbar-title>
                <BaseButton
                    variant="ghost"
                    dense
                    :icon="ICONS.logout"
                    label="Sign out"
                    @click="onSignOut"
                />
            </q-toolbar>
        </q-header>

        <q-page-container>
            <OfflineBanner />
            <router-view v-slot="{ Component }">
                <FadeTransition mode="out-in">
                    <component :is="Component" />
                </FadeTransition>
            </router-view>
        </q-page-container>
    </q-layout>
</template>

<script setup lang="ts">
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import OfflineBanner from 'src/components/OfflineBanner.vue';
    import FadeTransition from 'src/components/transitions/FadeTransition.vue';
    import { useAuthStore } from 'src/stores/authStore';
    import { useRouter } from 'vue-router';

    const authStore = useAuthStore();
    const router = useRouter();

    async function onSignOut() {
        await authStore.logoutAsync();
        void router.push('/login');
    }
</script>

<style scoped>
    .welcome-layout {
        background: #1e2a26;
        color: #ffffff;
        min-height: 100vh;
    }
    .welcome-header {
        color: #ffffff;
    }
    .welcome-toolbar {
        max-width: 960px;
        width: 100%;
        margin: 0 auto;
    }
    .welcome-title {
        font-weight: 600;
        letter-spacing: -0.01em;
    }
</style>
