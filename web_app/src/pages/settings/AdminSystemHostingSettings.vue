<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Hosting"
            description="Install-wide operational knobs that describe where Dora is hosted and how long audit records live."
            :icon="ICONS.cloud_upload"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <template v-else-if="!loading">
            <SettingsSection>
                <template #title>Public URL</template>
                <template #description>
                    Where the SPA lives on the public internet. Embedded in
                    verification and password-reset emails. Falls back to the
                    request's Origin header when unset.
                </template>

                <SettingsRow label="URL" stacked>
                    <q-input
                        v-model="draft.public_url"
                        outlined dense clearable
                        placeholder="https://dora.example.com"
                        :disable="saving"
                        :error="publicUrlHasError"
                        :error-message="publicUrlHasError ? 'Must start with http:// or https://.' : ''"
                        @blur="() => onSavePublicUrl()"
                    />
                </SettingsRow>
            </SettingsSection>

            <SettingsSection>
                <template #title>Audit retention</template>
                <template #description>
                    Audit events older than this many days are pruned nightly.
                    Bounds: 1–3650 (10 years).
                </template>

                <SettingsRow label="Days">
                    <q-input
                        v-model.number="draft.audit_retention_days"
                        type="number"
                        outlined dense
                        style="max-width: 140px"
                        :min="1"
                        :max="3650"
                        :disable="saving"
                        @blur="() => onSaveField('audit_retention_days')"
                    />
                </SettingsRow>
            </SettingsSection>
        </template>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AppSettingsApiService, { type AppSettings } from 'src/services/api/appSettingsApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, onMounted, reactive, ref } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';

    type HostingField = 'public_url' | 'audit_retention_days';

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);
    const saving = ref(false);
    const saved = reactive({
        public_url: '',
        audit_retention_days: 365,
    });
    const draft = reactive({ ...saved });

    const publicUrlHasError = computed(() => {
        const value = (draft.public_url ?? '').trim();
        if (!value) return false;
        return !value.startsWith('http://') && !value.startsWith('https://');
    });

    function resetDrafts() {
        Object.assign(draft, saved);
    }

    async function onSavePublicUrl() {
        const value = (draft.public_url ?? '').trim();
        if (value === saved.public_url) return;
        // Server also validates, but bail early on the obvious case so the
        // user sees the inline error instead of a toast.
        if (publicUrlHasError.value) return;
        await persist('public_url', value);
    }

    async function onSaveField(field: HostingField) {
        const value = draft[field];
        if (value === saved[field]) return;
        await persist(field, value);
    }

    async function persist(field: HostingField, value: unknown) {
        saving.value = true;
        try {
            const result = await api.updateAsync({ [field]: value });
            (saved as Record<HostingField, unknown>)[field] = result[field];
            resetDrafts();
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: 'Hosting settings saved.',
            });
        } catch (err) {
            resetDrafts();
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save hosting settings.',
                caption: toastCaption(err),
            });
        } finally {
            saving.value = false;
        }
    }

    function hydrate(s: AppSettings) {
        saved.public_url = s.public_url;
        saved.audit_retention_days = s.audit_retention_days;
        resetDrafts();
    }

    onMounted(async () => {
        if (!isAdmin.value) {
            loading.value = false;
            return;
        }
        try {
            hydrate(await api.getAsync());
        } catch {
            // Leave defaults; env fallback still active.
        } finally {
            loading.value = false;
        }
    });
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
</style>
