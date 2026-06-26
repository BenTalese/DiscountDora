<template>
    <!-- Dietary tags carry a grouping label, so they keep a bespoke editor
         (the shared TaxonomyManagerPage covers the name-only types). §2.11:
         create/rename now use one DietaryTagFormDialog instead of two
         sequential prompts. -->
    <div class="settings-page">
        <SettingsPageHeader
            title="Dietary tags"
            :description="`Dietary / allergen / nutritional tags recipes can be tagged with. ${dietaryTags.length} tag${dietaryTags.length === 1 ? '' : 's'}.`"
            :icon="ICONS.label"
        >
            <template #actions>
                <BaseButton
                    :icon="ICONS.add"
                    label="New tag"
                    :loading="busy"
                    @click="onCreateDietaryTag"
                />
            </template>
        </SettingsPageHeader>

        <q-list class="settings-list" separator>
            <q-item v-for="tag in dietaryTags" :key="tag.dietary_tag_id" class="q-py-sm">
                <q-item-section avatar><q-icon :name="ICONS.label" /></q-item-section>
                <q-item-section>
                    <q-item-label>{{ tag.name }}</q-item-label>
                    <q-item-label caption>
                        {{ tag.category }} ·
                        {{ tag.recipe_count ?? 0 }} recipe{{ (tag.recipe_count ?? 0) === 1 ? '' : 's' }}
                    </q-item-label>
                </q-item-section>
                <q-item-section side>
                    <div class="row q-gutter-xs">
                        <BaseButton variant="icon" :icon="ICONS.edit" @click="onRenameDietaryTag(tag)">
                            <q-tooltip>Rename</q-tooltip>
                        </BaseButton>
                        <BaseButton variant="icon" :icon="ICONS.delete_outline" @click="onDeleteDietaryTag(tag)">
                            <q-tooltip>Delete</q-tooltip>
                        </BaseButton>
                    </div>
                </q-item-section>
            </q-item>
            <q-item v-if="!loading && dietaryTags.length === 0">
                <q-item-section class="dora-text-muted text-center">
                    No dietary tags yet.
                </q-item-section>
            </q-item>
        </q-list>

        <q-inner-loading :showing="loading && dietaryTags.length === 0">
            <q-spinner color="primary" size="48px" />
        </q-inner-loading>

        <DietaryTagFormDialog
            v-model="dialogOpen"
            :tag="editingTag"
            :busy="busy"
            @confirm="onDialogConfirm"
        />
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { useQuasar } from 'quasar';
    import DietaryTagFormDialog from 'src/components/settings/DietaryTagFormDialog.vue';
    import type { DietaryTag } from 'src/models/recipeVocab';
    import DietaryTagApiService from 'src/services/api/dietaryTagApiService';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import { onMounted, ref } from 'vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';

    const $q = useQuasar();
    const dietaryTagApi = new DietaryTagApiService();

    const dietaryTags = ref<DietaryTag[]>([]);
    const loading = ref(false);
    const busy = ref(false);

    // Dialog state — `editingTag` null means create, populated means rename.
    const dialogOpen = ref(false);
    const editingTag = ref<DietaryTag | null>(null);

    function notifyError(message: string, err: unknown) {
        $q.notify({
            type: 'negative',
            position: 'bottom-right',
            message,
            caption: describeApiError(err) || '',
        });
    }

    async function load() {
        loading.value = true;
        try {
            dietaryTags.value = await dietaryTagApi.getAllAsync();
        } catch (err) {
            notifyError('Could not load dietary tags.', err);
        } finally {
            loading.value = false;
        }
    }

    async function run(action: () => Promise<unknown>) {
        busy.value = true;
        try {
            await action();
            await load();
        } catch (err) {
            notifyError('Could not save the change.', err);
        } finally {
            busy.value = false;
        }
    }

    function onCreateDietaryTag() {
        editingTag.value = null;
        dialogOpen.value = true;
    }

    function onRenameDietaryTag(tag: DietaryTag) {
        editingTag.value = tag;
        dialogOpen.value = true;
    }

    async function onDialogConfirm(payload: { name: string; category: string }) {
        const target = editingTag.value;
        await run(() =>
            target
                ? dietaryTagApi.updateAsync(target.dietary_tag_id, payload)
                : dietaryTagApi.createAsync(payload),
        );
        dialogOpen.value = false;
    }

    async function onDeleteDietaryTag(tag: DietaryTag) {
        const count = tag.recipe_count ?? 0;
        const ok = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: `Delete "${tag.name}"?`,
                message:
                    count > 0
                        ? `${count} recipe${count === 1 ? '' : 's'} tagged with this will lose the tag.`
                        : 'Nothing currently uses this tag.',
                cancel: true,
            })
                .onOk(() => resolve(true))
                .onCancel(() => resolve(false))
                .onDismiss(() => resolve(false));
        });
        if (ok) await run(() => dietaryTagApi.deleteAsync(tag.dietary_tag_id).then(() => undefined));
    }

    onMounted(load);
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; position: relative; }
    .settings-list {
        border-top: 1px solid color-mix(in srgb, var(--text-primary) 8%, transparent);
        border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 8%, transparent);
    }
</style>
