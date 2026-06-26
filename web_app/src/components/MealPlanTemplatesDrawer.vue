<template>
    <q-dialog
        :model-value="modelValue"
        :position="$q.screen.lt.md ? 'bottom' : 'right'"
        :transition-show="$q.screen.lt.md ? 'slide-up' : 'slide-left'"
        :transition-hide="$q.screen.lt.md ? 'slide-down' : 'slide-right'"
        @update:model-value="(v: boolean) => emit('update:modelValue', v)"
    >
        <q-card class="templates-drawer column">
            <q-card-section class="row items-center q-pb-sm">
                <div class="text-subtitle1">Templates</div>
                <q-space />
                <BaseButton variant="icon" :icon="ICONS.close" @click="emit('update:modelValue', false)">
                    <q-tooltip>Close</q-tooltip>
                </BaseButton>
            </q-card-section>
            <q-separator />

            <q-card-section class="col q-pa-none templates-drawer__body">
                <!-- Save current week ───────────────────────────────────── -->
                <div class="q-pa-md">
                    <BaseButton
                        variant="secondary"
                        :disable="!canSaveCurrentWeek"
                        :icon="ICONS.add"
                        label="Save this week as a template"
                        class="full-width"
                        @click="emit('saveCurrentWeek')"
                    >
                        <q-tooltip v-if="!canSaveCurrentWeek">
                            Add some meals to this week first.
                        </q-tooltip>
                    </BaseButton>
                    <BaseButton
                        variant="secondary"
                        :icon="ICONS.event_repeat"
                        label="Apply recurring…"
                        class="full-width q-mt-sm"
                        @click="emit('applyRecurring')"
                    />
                </div>

                <q-separator />

                <!-- Browse templates ────────────────────────────────────── -->
                <div class="q-pa-md q-pb-xs">
                    <div class="text-subtitle2">Your templates</div>
                    <div class="text-caption dora-text-muted">
                        Tap Apply to fork a template onto the focused week.
                        Rename or delete inline — no page hop.
                    </div>
                </div>

                <div v-if="templates.length === 0" class="dora-text-muted text-center q-pa-lg">
                    No templates yet. Save a planned week to start a library.
                </div>

                <q-list v-else separator>
                    <q-item
                        v-for="t in templates"
                        :key="t.meal_plan_template_id"
                        class="template-row"
                    >
                        <q-item-section>
                            <q-item-label v-if="renamingId !== t.meal_plan_template_id">
                                <span class="text-weight-medium">{{ t.name }}</span>
                            </q-item-label>
                            <q-item-label v-else>
                                <q-input
                                    v-model="renameDraft"
                                    dense outlined autofocus
                                    :disable="saving"
                                    @keyup.enter="confirmRename(t.meal_plan_template_id)"
                                    @keyup.esc="cancelRename"
                                />
                            </q-item-label>
                            <q-item-label caption>
                                {{ t.entry_count }} meal{{ t.entry_count === 1 ? '' : 's' }}
                                <span v-if="t.description"> · {{ t.description }}</span>
                            </q-item-label>
                        </q-item-section>
                        <q-item-section side>
                            <div class="row items-center no-wrap q-gutter-xs">
                                <template v-if="renamingId === t.meal_plan_template_id">
                                    <BaseButton
                                        variant="ghost"
                                        dense
                                        label="Save"
                                        :loading="saving"
                                        :disable="!renameDraft.trim()"
                                        @click="confirmRename(t.meal_plan_template_id)"
                                    />
                                    <BaseButton variant="ghost" dense label="Cancel" @click="cancelRename" />
                                </template>
                                <template v-else>
                                    <BaseButton
                                        variant="secondary" dense label="Apply"
                                        @click="onApply(t)"
                                    />
                                    <BaseButton variant="icon" :icon="ICONS.edit" @click="startRename(t)">
                                        <q-tooltip>Rename</q-tooltip>
                                    </BaseButton>
                                    <BaseButton variant="danger-ghost" :icon="ICONS.delete_outline" round dense @click="confirmDelete(t)">
                                        <q-tooltip>Delete</q-tooltip>
                                    </BaseButton>
                                </template>
                            </div>
                        </q-item-section>
                    </q-item>
                </q-list>
            </q-card-section>
        </q-card>
    </q-dialog>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import type { MealPlanTemplateSummary } from 'src/models/mealPlanTemplate';
    import { useMealPlanTemplateStore } from 'src/stores/mealPlanTemplateStore';
    import { useQuasar } from 'quasar';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import { ref } from 'vue';

    defineProps<{
        modelValue: boolean;
        templates: MealPlanTemplateSummary[];
        canSaveCurrentWeek: boolean;
    }>();

    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
        (e: 'saveCurrentWeek'): void;
        (e: 'applyRecurring'): void;
        (e: 'applyTemplate', templateId: string): void;
    }>();

    const $q = useQuasar();
    const templateStore = useMealPlanTemplateStore();

    const renamingId = ref<string | null>(null);
    const renameDraft = ref('');
    const saving = ref(false);

    function startRename(t: MealPlanTemplateSummary) {
        renamingId.value = t.meal_plan_template_id;
        renameDraft.value = t.name;
    }
    function cancelRename() {
        renamingId.value = null;
        renameDraft.value = '';
    }
    async function confirmRename(id: string) {
        const next = renameDraft.value.trim();
        if (!next) return;
        saving.value = true;
        try {
            await templateStore.updateAsync(id, { name: next });
            cancelRename();
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Renamed.' });
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not rename the template.',
                caption: describeApiError(err) || '',
            });
        } finally {
            saving.value = false;
        }
    }

    function confirmDelete(t: MealPlanTemplateSummary) {
        $q.dialog({
            title: 'Delete template',
            message: `Delete "${t.name}"? Future plans built from it stay where they are.`,
            cancel: { noCaps: true },
            ok: { label: 'Delete', noCaps: true, color: 'negative' },
            persistent: true,
        }).onOk(() => {
            void doDelete(t);
        });
    }
    async function doDelete(t: MealPlanTemplateSummary) {
        try {
            await templateStore.deleteAsync(t.meal_plan_template_id);
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Template deleted.' });
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not delete the template.',
                caption: describeApiError(err) || '',
            });
        }
    }

    function onApply(t: MealPlanTemplateSummary) {
        emit('applyTemplate', t.meal_plan_template_id);
    }
</script>

<style scoped>
    .templates-drawer {
        width: min(440px, 100vw);
        height: 100vh;
    }
    @media (max-width: 1023px) {
        .templates-drawer {
            width: 100vw;
            max-width: 100vw;
            height: 85vh;
            border-top-left-radius: 16px;
            border-top-right-radius: 16px;
        }
    }
    .templates-drawer__body {
        overflow-y: auto;
    }
    .template-row {
        align-items: center;
    }
</style>
