<template>
    <div v-if="installed">
        <q-item-label caption class="text-positive">
            <q-icon :name="ICONS.check_circle" size="14px" class="q-mr-xs" />
            Dora is installed on this device.
        </q-item-label>
    </div>
    <BaseButton
        v-else-if="available"
        :icon="ICONS.install_desktop"
        label="Install Dora as an app"
        @click="onInstall"
    />
    <q-banner
        v-else-if="ios"
        class="dora-bg-sunken"
        dense
        rounded
    >
        <template #avatar>
            <q-icon :name="ICONS.phone_iphone" />
        </template>
        On iOS, tap the
        <q-icon :name="ICONS.ios_share" size="16px" class="q-mx-xs" />
        <strong>Share</strong> button in Safari, then
        <strong>Add to Home Screen</strong>.
    </q-banner>
    <q-item-label v-else caption class="dora-text-secondary">
        Install isn't available in this browser. Try Chrome on Android,
        Edge on Windows, or Safari on iOS.
    </q-item-label>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { useQuasar } from 'quasar';
    import {
        installPromptAvailable, isInstalled, isIosSafari, showInstallPrompt,
    } from 'src/composables/usePwaLifecycle';

    const $q = useQuasar();
    const available = installPromptAvailable();
    const installed = isInstalled();
    const ios = isIosSafari();

    async function onInstall() {
        const outcome = await showInstallPrompt();
        if (outcome === 'accepted') {
            $q.notify({ type: 'positive', position: 'top', message: 'Installing Dora…' });
        } else if (outcome === 'dismissed') {
            $q.notify({
                type: 'info', position: 'bottom-right',
                message: 'Install cancelled — open this page again any time to install.',
            });
        }
    }
</script>
