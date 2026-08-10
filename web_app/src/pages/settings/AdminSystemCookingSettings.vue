<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Cooking"
            description="Household cooking settings, shared by everyone on this install — how many people you usually cook for, and whether the meal planner shows the batch-cooking tools."
            :icon="ICONS.restaurant"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <template v-else-if="!loading">
            <SettingsSection>
                <template #title>Household headcount</template>
                <template #description>
                    How many people the household usually cooks for. Cook mode
                    scales a recipe's ingredients to this number. Leave it blank
                    to use each recipe's own serving size instead.
                </template>

                <SettingsRow label="People">
                    <q-input
                        v-model.number="headcountDraft"
                        outlined
                        dense
                        type="number"
                        :min="1"
                        :max="99"
                        style="max-width: 100px"
                        placeholder="Per recipe"
                        clearable
                        @blur="onHeadcountCommit"
                        @clear="onHeadcountCommit"
                    />
                </SettingsRow>
            </SettingsSection>

            <hr class="settings-divider" />

            <SettingsSection>
                <template #title>Cooking style</template>
                <template #description>
                    <strong>Fresh</strong> keeps the meal planner pure
                    scheduling. <strong>Batch</strong> adds the cook pool
                    (per-recipe ± / log-cook), the cook-shortfall warning, and
                    the "to cook by" sidebar line — for households that cook
                    once and eat it across several days.
                </template>

                <SettingsRow label="Cooking style">
                    <DoraSegmented
                        :model-value="batchDraft ? 'batch' : 'fresh'"
                        :options="cookingStyleOptions"
                        @update:model-value="onCookingStyleChange"
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
    import AppSettingsApiService from 'src/services/api/appSettingsApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { refreshCookingPolicy } from 'src/composables/useCookingPolicy';
    import { onMounted, ref } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import DoraSegmented, { type DoraSegmentedOption } from 'src/components/settings/DoraSegmented.vue';

    // FU-615 — the two install-wide household cooking settings (headcount +
    // cook-style), moved off the per-user record onto AppSetting. Same
    // eager-save shape as the neighbouring System settings pages; each save
    // refreshes the shared cooking policy so cook mode + the meal planner pick
    // it up without a reload.

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);

    // Headcount — nullable; null/blank means "use each recipe's servings".
    const headcountDraft = ref<number | null>(null);
    let savedHeadcount: number | null = null;

    // Cook-style toggle.
    const batchDraft = ref<boolean>(false);
    let savedBatch = false;

    type CookingStyle = 'fresh' | 'batch';
    const cookingStyleOptions: DoraSegmentedOption<CookingStyle>[] = [
        { label: 'Fresh', value: 'fresh' },
        { label: 'Batch', value: 'batch' },
    ];

    // Clamp the draft to null / 1–99 (matches the server bounds), returning
    // the normalised value the field should show.
    function normaliseHeadcount(value: number | null): number | null {
        if (value === null || value === undefined || !Number.isFinite(value) || value < 1) {
            return null;
        }
        return Math.min(99, Math.floor(value));
    }

    async function onHeadcountCommit() {
        const next = normaliseHeadcount(headcountDraft.value);
        headcountDraft.value = next;
        if (next === savedHeadcount) return;
        try {
            const result = await api.updateAsync({ household_headcount: next });
            savedHeadcount = result.household_headcount;
            headcountDraft.value = savedHeadcount;
            await refreshCookingPolicy();
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: savedHeadcount === null
                    ? 'Cook mode will use each recipe\'s serving size.'
                    : `Cook mode will scale recipes for ${savedHeadcount}.`,
            });
        } catch (err) {
            headcountDraft.value = savedHeadcount;
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save household headcount.',
                caption: toastCaption(err),
            });
        }
    }

    async function onCookingStyleChange(next: CookingStyle) {
        const wantBatch = next === 'batch';
        if (wantBatch === savedBatch) return;
        try {
            const result = await api.updateAsync({ batch_features_enabled: wantBatch });
            savedBatch = result.batch_features_enabled;
            batchDraft.value = savedBatch;
            await refreshCookingPolicy();
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: savedBatch
                    ? 'Batch tools are on in the meal planner.'
                    : 'Meal planner is back to pure scheduling.',
            });
        } catch (err) {
            batchDraft.value = savedBatch;
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not change cooking style.',
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
            const s = await api.getAsync();
            savedHeadcount = s.household_headcount ?? null;
            headcountDraft.value = savedHeadcount;
            savedBatch = !!s.batch_features_enabled;
            batchDraft.value = savedBatch;
        } catch {
            // Leave defaults; the eager-save handlers guard against a stale read.
        } finally {
            loading.value = false;
        }
    });
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
    .settings-divider {
        border: 0;
        height: 1px;
        background: color-mix(in srgb, var(--text-primary) 8%, transparent);
        margin: 8px 0;
    }
</style>
