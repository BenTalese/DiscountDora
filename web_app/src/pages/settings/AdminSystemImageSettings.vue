<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Image quality"
            description="How Dora encodes photos you upload. Applies to new uploads only."
            :icon="ICONS.image"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <template v-else-if="!loading">
            <!-- Applied at upload time via the shared `processImageFile`
                 helper, so every upload surface picks these up automatically.
                 Forward-only — existing images are never re-encoded. -->
            <SettingsSection>
                <SettingsRow inline>
                    <template #label>
                        JPEG/WebP quality
                        <InfoTip label="JPEG and WebP quality">
                            30 compresses hard and you can see it; 85 (the
                            default) is visually indistinguishable from the
                            original; 100 barely compresses at all.
                        </InfoTip>
                    </template>
                    <!-- `width` + `max-width`, never a `min-width` floor: an
                         inline row caps its control at 55% of a 375px screen,
                         and a floor wider than that runs the track off the
                         right edge (the same fix the settings selects took on
                         2026-09-03). -->
                    <q-slider
                        v-model="qualityInput"
                        :min="30"
                        :max="100"
                        :step="1"
                        label
                        label-always
                        color="primary"
                        style="width: 220px; max-width: 100%"
                        @change="onSave"
                    />
                </SettingsRow>
                <SettingsRow inline>
                    <template #label>
                        Longest edge
                        <InfoTip label="Longest edge">
                            Photos bigger than this on their longest side are
                            scaled down before encoding. 1920 (the default) is
                            Full-HD; 1280 is a disk-conscious floor.
                        </InfoTip>
                    </template>
                    <q-input
                        v-model.number="maxDimensionInput"
                        type="number"
                        outlined
                        dense
                        suffix="px"
                        style="max-width: 150px"
                        :min="512"
                        :max="8192"
                        @blur="onSave"
                    />
                </SettingsRow>
            </SettingsSection>
        </template>
    </div>
</template>

<script lang="ts" setup>
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import InfoTip from 'src/components/help/InfoTip.vue';
    import { refreshImagePolicy } from 'src/composables/useImagePolicy';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AppSettingsApiService from 'src/services/api/appSettingsApiService';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { useAuthStore } from 'src/stores/authStore';
    import { ICONS } from 'src/style/icons';
    import { onMounted, ref } from 'vue';

    // 2026-08-23 owner feedback — the two image-encode knobs used to sit at the
    // bottom of Backup & Restore, which is about backups, not uploads. They are
    // their own install-wide surface now.
    //
    // 2026-09-03 owner feedback — and they save on change like every other
    // settings page, rather than behind a Save/Discard pair that made two
    // inputs look like a form. The reason the pair existed was a real one (a
    // slider drag would otherwise fire a PATCH per pixel), but `@change` is the
    // seam for that: Quasar fires it on release, not on every step.

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);

    // Saved server state vs. the inputs, so a no-op blur doesn't PATCH and a
    // failed save can put the control back where it was.
    const quality = ref(85);
    const maxDimension = ref(1920);
    const qualityInput = ref(85);
    const maxDimensionInput = ref(1920);

    function reset() {
        qualityInput.value = quality.value;
        maxDimensionInput.value = maxDimension.value;
    }

    async function onSave() {
        const nextQuality = Number(qualityInput.value);
        const nextMaxDimension = Number(maxDimensionInput.value);
        if (nextQuality === quality.value && nextMaxDimension === maxDimension.value) return;
        try {
            const result = await api.updateAsync({
                image_quality: nextQuality,
                image_max_dimension: nextMaxDimension,
            });
            quality.value = result.image_quality;
            maxDimension.value = result.image_max_dimension;
            reset();
            // Kick the shared policy composable so subsequent uploads in
            // *this* session pick up the new values without a page reload.
            // Other tabs get it on their next health probe.
            void refreshImagePolicy();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Image settings saved.',
                caption: 'Applies to new uploads; existing images are unchanged.',
                timeout: 3000,
            });
        } catch (err) {
            reset();
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't save image settings.",
                caption: toastCaption(err),
            });
        }
    }

    onMounted(async () => {
        if (!isAdmin.value) {
            loading.value = false;
            return;
        }
        try {
            const settings = await api.getAsync();
            quality.value = settings.image_quality;
            maxDimension.value = settings.image_max_dimension;
            reset();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't load image settings.",
                caption: toastCaption(err),
            });
        } finally {
            loading.value = false;
        }
    });
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
</style>
