<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Image quality"
            description="How Dora encodes photos you upload — stock items, recipes, products, avatars, receipts and store logos all use these settings."
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
                <template #title>Compression</template>
                <template #description>
                    Applied when new images are uploaded — existing images are
                    unchanged. Lower quality + smaller dimensions ⇒ less disk over time.
                </template>

                <SettingsRow
                    label="JPEG/WebP quality"
                    help="30 = strong compression (visible loss); 85 (default) is visually indistinguishable from the original; 100 = no compression, large files."
                >
                    <q-slider
                        v-model="qualityInput"
                        :min="30"
                        :max="100"
                        :step="1"
                        label
                        label-always
                        color="primary"
                        style="min-width: 220px"
                    />
                </SettingsRow>
                <SettingsRow
                    label="Longest edge (px)"
                    help="Photos larger than this on their longest side are scaled down before encode. 1920 (default) is Full-HD; 1280 is a disk-conscious floor."
                >
                    <q-input
                        v-model.number="maxDimensionInput"
                        type="number"
                        outlined
                        dense
                        :min="512"
                        :max="8192"
                        style="max-width: 140px"
                    />
                </SettingsRow>
                <div class="settings-actions">
                    <BaseButton
                        variant="ghost"
                        label="Discard"
                        :disable="!dirty"
                        @click="reset"
                    />
                    <BaseButton
                        variant="primary"
                        :icon="ICONS.save"
                        label="Save"
                        :loading="saving"
                        :disable="!dirty || saving"
                        @click="onSave"
                    />
                </div>
            </SettingsSection>
        </template>
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import { refreshImagePolicy } from 'src/composables/useImagePolicy';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AppSettingsApiService from 'src/services/api/appSettingsApiService';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { useAuthStore } from 'src/stores/authStore';
    import { ICONS } from 'src/style/icons';
    import { computed, onMounted, ref } from 'vue';

    // 2026-08-23 owner feedback — the two image-encode knobs used to sit at the
    // bottom of Backup & Restore, which is about backups, not uploads. They are
    // their own install-wide surface now. Unlike the neighbouring System pages
    // this one keeps an explicit Save: a slider drag would otherwise fire a
    // PATCH per pixel.

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);
    const saving = ref(false);

    // Saved server state vs. the draft the inputs bind to, so the "dirty"
    // check stays honest after a Discard.
    const quality = ref(85);
    const maxDimension = ref(1920);
    const qualityInput = ref(85);
    const maxDimensionInput = ref(1920);

    const dirty = computed(() =>
        qualityInput.value !== quality.value
        || maxDimensionInput.value !== maxDimension.value,
    );

    function reset() {
        qualityInput.value = quality.value;
        maxDimensionInput.value = maxDimension.value;
    }

    async function onSave() {
        saving.value = true;
        try {
            const result = await api.updateAsync({
                image_quality: Number(qualityInput.value),
                image_max_dimension: Number(maxDimensionInput.value),
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
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't save image settings.",
                caption: toastCaption(err),
            });
        } finally {
            saving.value = false;
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

    .settings-actions {
        display: flex;
        justify-content: flex-end;
        gap: var(--space-2);
        margin-top: var(--space-3);
    }
</style>
