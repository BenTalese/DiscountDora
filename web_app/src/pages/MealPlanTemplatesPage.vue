<template>
    <div class="q-pa-md column q-gutter-md page">
        <div class="row items-center">
            <BaseButton variant="icon" :icon="ICONS.chevron_left" @click="goToPlanner">
                <q-tooltip>Back to the planner</q-tooltip>
            </BaseButton>
            <div class="text-h6 q-ml-sm">Meal plan templates</div>
        </div>

        <!-- ── Templates ──────────────────────────────────────────────── -->
        <q-card flat bordered>
            <q-card-section class="q-pb-xs">
                <div class="text-subtitle1">Templates</div>
                <div class="text-caption dora-text-muted">
                    Saved week shapes. Apply them to a week from the planner.
                </div>
            </q-card-section>
            <q-separator />
            <q-list separator>
                <q-item v-for="t in templates" :key="t.meal_plan_template_id">
                    <q-item-section>
                        <q-item-label>{{ t.name }}</q-item-label>
                        <q-item-label caption>
                            {{ t.entry_count }} meal{{ t.entry_count === 1 ? '' : 's' }}
                            <span v-if="t.description"> · {{ t.description }}</span>
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <div class="row items-center q-gutter-xs">
                            <BaseButton variant="icon" :icon="ICONS.edit" @click="renameTemplate(t)">
                                <q-tooltip>Rename</q-tooltip>
                            </BaseButton>
                            <BaseButton variant="ghost" dense label="Clone" @click="cloneTemplate(t)" />
                            <BaseButton variant="icon" :icon="ICONS.delete" @click="deleteTemplate(t)">
                                <q-tooltip>Delete</q-tooltip>
                            </BaseButton>
                        </div>
                    </q-item-section>
                </q-item>
                <q-item v-if="templates.length === 0">
                    <q-item-section class="dora-text-muted text-center q-py-md">
                        No templates yet — save a week from the planner first.
                    </q-item-section>
                </q-item>
            </q-list>
        </q-card>

        <!-- ── Rotating sets ──────────────────────────────────────────── -->
        <q-card flat bordered>
            <q-card-section class="row items-center q-pb-xs">
                <div>
                    <div class="text-subtitle1">Rotating sets</div>
                    <div class="text-caption dora-text-muted">
                        An ordered list of templates that rotates week-to-week.
                    </div>
                </div>
                <q-space />
                <BaseButton
                    variant="primary" :icon="ICONS.add" label="New set"
                    :disable="templates.length === 0"
                    @click="openSetEditor(null)"
                />
            </q-card-section>
            <q-separator />
            <q-list separator>
                <q-item v-for="s in sets" :key="s.meal_plan_template_set_id">
                    <q-item-section>
                        <q-item-label>{{ s.name }}</q-item-label>
                        <q-item-label caption>{{ s.template_names.join(' → ') || 'empty' }}</q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <div class="row items-center q-gutter-xs">
                            <BaseButton variant="icon" :icon="ICONS.edit" @click="openSetEditor(s.meal_plan_template_set_id)">
                                <q-tooltip>Edit</q-tooltip>
                            </BaseButton>
                            <BaseButton variant="icon" :icon="ICONS.delete" @click="deleteSet(s)">
                                <q-tooltip>Delete</q-tooltip>
                            </BaseButton>
                        </div>
                    </q-item-section>
                </q-item>
                <q-item v-if="sets.length === 0">
                    <q-item-section class="dora-text-muted text-center q-py-md">
                        No sets yet.
                    </q-item-section>
                </q-item>
            </q-list>
        </q-card>

        <!-- ── Set editor ─────────────────────────────────────────────── -->
        <BaseDialog
            v-model="setEditorOpen"
            :title="editingSetId ? 'Edit set' : 'New set'"
            closable
            card-style="min-width: 420px; max-width: 95vw"
        >
            <q-card-section class="q-pt-none q-gutter-sm">
                <q-input v-model="setName" outlined dense autofocus label="Set name" :disable="savingSet" />
                <div class="text-caption dora-text-muted">Templates rotate in this order:</div>
                <q-list bordered separator class="rounded-borders">
                    <q-item v-for="(tid, idx) in setTemplateIds" :key="`${tid}-${idx}`">
                        <q-item-section>
                            <q-item-label>{{ idx + 1 }}. {{ templateNameFor(tid) }}</q-item-label>
                        </q-item-section>
                        <q-item-section side>
                            <div class="row items-center no-wrap">
                                <BaseButton variant="icon" size="sm" :icon="ICONS.arrow_upward" :disable="idx === 0" @click="moveItem(idx, -1)" />
                                <BaseButton variant="icon" size="sm" :icon="ICONS.arrow_downward" :disable="idx === setTemplateIds.length - 1" @click="moveItem(idx, 1)" />
                                <BaseButton variant="icon" size="sm" :icon="ICONS.close" @click="removeItem(idx)" />
                            </div>
                        </q-item-section>
                    </q-item>
                    <q-item v-if="setTemplateIds.length === 0">
                        <q-item-section class="dora-text-muted">Add at least one template.</q-item-section>
                    </q-item>
                </q-list>
                <q-select
                    :model-value="null"
                    outlined dense
                    :options="templateOptions"
                    label="Add a template"
                    emit-value map-options
                    :disable="savingSet"
                    @update:model-value="onAddTemplate"
                />
            </q-card-section>
            <template #actions>
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <BaseButton
                    variant="primary" label="Save set"
                    :loading="savingSet"
                    :disable="!setName.trim() || setTemplateIds.length === 0"
                    @click="saveSet"
                />
            </template>
        </BaseDialog>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import type { MealPlanTemplateSummary } from 'src/models/mealPlanTemplate';
    import MealPlanTemplateSetApiService from 'src/services/api/mealPlanTemplateSetApiService';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { useMealPlanTemplateStore } from 'src/stores/mealPlanTemplateStore';
    import { useMealPlanTemplateSetStore } from 'src/stores/mealPlanTemplateSetStore';
    import { computed, onMounted, ref } from 'vue';
    import { useRouter } from 'vue-router';

    const $q = useQuasar();
    const router = useRouter();
    const templateStore = useMealPlanTemplateStore();
    const setStore = useMealPlanTemplateSetStore();
    const setApi = new MealPlanTemplateSetApiService();
    const { templates } = storeToRefs(templateStore);
    const { sets } = storeToRefs(setStore);

    const templateOptions = computed(() =>
        templates.value.map((t) => ({ label: t.name, value: t.meal_plan_template_id })),
    );
    function templateNameFor(id: string): string {
        return templates.value.find((t) => t.meal_plan_template_id === id)?.name ?? '(deleted template)';
    }

    function goToPlanner() {
        void router.push('/meal-plans');
    }

    // ── Templates ──────────────────────────────────────────────────────────
    function renameTemplate(t: MealPlanTemplateSummary) {
        $q.dialog({
            title: 'Rename template',
            prompt: { model: t.name, type: 'text', isValid: (v: string) => v.trim().length > 0 },
            cancel: { noCaps: true },
            ok: { label: 'Save', noCaps: true, color: 'primary' },
        }).onOk((name: string) => void run(
            () => templateStore.updateAsync(t.meal_plan_template_id, { name: name.trim() }),
            'Renamed.',
        ));
    }
    function cloneTemplate(t: MealPlanTemplateSummary) {
        void run(() => templateStore.cloneAsync(t.meal_plan_template_id), 'Cloned.');
    }
    function deleteTemplate(t: MealPlanTemplateSummary) {
        $q.dialog({
            title: 'Delete template',
            message: `Delete "${t.name}"? Weeks already created from it are unaffected.`,
            cancel: { noCaps: true },
            ok: { label: 'Delete', noCaps: true, color: 'negative' },
        }).onOk(() => void run(() => templateStore.deleteAsync(t.meal_plan_template_id), 'Deleted.'));
    }

    // ── Sets ─────────────────────────────────────────────────────────────────
    const setEditorOpen = ref(false);
    const editingSetId = ref<string | null>(null);
    const setName = ref('');
    const setTemplateIds = ref<string[]>([]);
    const savingSet = ref(false);

    async function openSetEditor(setId: string | null) {
        editingSetId.value = setId;
        if (setId) {
            const detail = await setApi.getDetailAsync(setId);
            setName.value = detail.name;
            setTemplateIds.value = detail.items.map((i) => i.template_id);
        } else {
            setName.value = '';
            setTemplateIds.value = [];
        }
        setEditorOpen.value = true;
    }
    function onAddTemplate(id: string | null) {
        if (id) setTemplateIds.value = [...setTemplateIds.value, id];
    }
    function moveItem(idx: number, delta: number) {
        const next = [...setTemplateIds.value];
        const target = idx + delta;
        if (target < 0 || target >= next.length) return;
        [next[idx], next[target]] = [next[target]!, next[idx]!];
        setTemplateIds.value = next;
    }
    function removeItem(idx: number) {
        setTemplateIds.value = setTemplateIds.value.filter((_, i) => i !== idx);
    }
    async function saveSet() {
        savingSet.value = true;
        try {
            if (editingSetId.value) {
                await setStore.updateAsync(editingSetId.value, {
                    name: setName.value.trim(),
                    template_ids: setTemplateIds.value,
                });
            } else {
                await setStore.createAsync({
                    name: setName.value.trim(),
                    template_ids: setTemplateIds.value,
                });
            }
            setEditorOpen.value = false;
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Set saved.' });
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save the set.',
                caption: toastCaption(err),
            });
        } finally {
            savingSet.value = false;
        }
    }
    function deleteSet(s: { meal_plan_template_set_id: string; name: string }) {
        $q.dialog({
            title: 'Delete set',
            message: `Delete the set "${s.name}"? (The templates in it are kept.)`,
            cancel: { noCaps: true },
            ok: { label: 'Delete', noCaps: true, color: 'negative' },
        }).onOk(() => void run(() => setStore.deleteAsync(s.meal_plan_template_set_id), 'Deleted.'));
    }

    async function run(action: () => Promise<unknown>, successMessage: string) {
        try {
            await action();
            if (successMessage) {
                $q.notify({ type: 'positive', position: 'bottom-right', message: successMessage });
            }
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Something went wrong.',
                caption: toastCaption(err),
            });
        }
    }

    onMounted(async () => {
        await Promise.all([templateStore.getTemplatesAsync(), setStore.getSetsAsync()]);
    });
</script>

<style scoped>
    .page {
        max-width: 900px;
        margin: 0 auto;
    }
</style>
