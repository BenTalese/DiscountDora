<template>
    <!-- P6-01 Chunk 4 — unified "New shopping list" surface. One composable
         form for empty / template / recipe / meal-plan starts, optional auto-
         fill from stock, and create-new-or-merge target. Reusable from the
         router landing page and the detail page (Chunk 5). -->
    <BaseDialog
        :model-value="modelValue"
        title="New shopping list"
        closable
        card-style="min-width: 360px; max-width: 520px"
        @update:model-value="$emit('update:modelValue', $event)"
    >
        <q-card-section>
            <div class="text-caption dora-text-muted">
                Build a fresh list, or top up an existing one.
                Items are deduped, so nothing gets added twice.
            </div>
        </q-card-section>
        <q-card-section class="q-pt-none q-gutter-sm">
            <div class="text-caption dora-text-muted q-mb-xs">Start from</div>
            <q-option-group
                v-model="form.startFrom"
                :options="startFromOptions"
                type="radio"
                inline
            />

            <q-select
                v-if="form.startFrom === 'template'"
                v-model="form.templateId"
                :options="templateOptions"
                :loading="loadingPickers"
                emit-value
                map-options
                outlined
                dense
                label="Template"
                :hint="templateOptions.length === 0 ? 'No saved templates — save a list as a template from any list\'s menu.' : ''"
            />
            <q-select
                v-if="form.startFrom === 'recipe'"
                v-model="form.recipeId"
                :options="recipeOptions"
                :loading="loadingPickers"
                emit-value
                map-options
                outlined
                dense
                label="Recipe"
                :hint="recipeOptions.length === 0 ? 'No saved recipes yet.' : 'Adds every ingredient with a linked stock item.'"
            />
            <q-select
                v-if="form.startFrom === 'meal_plan'"
                v-model="form.mealPlanId"
                :options="mealPlanOptions"
                :loading="loadingPickers"
                emit-value
                map-options
                outlined
                dense
                label="Meal plan"
                :hint="mealPlanOptions.length === 0 ? 'No meal plans yet.' : 'Aggregates ingredients across the plan, scaled by servings.'"
            />

            <q-separator class="q-my-md" />
            <div class="text-caption dora-text-muted q-mb-xs">Also auto-fill from your stock</div>
            <q-checkbox
                v-model="form.source_low_or_out"
                :label="`Items that are low or out of stock${lowOrOutCount > 0 ? ` (${lowOrOutCount})` : ''}`"
            />
            <q-checkbox
                v-model="form.source_essentials_only_for_low"
                :disable="!form.source_low_or_out"
                label="...but only flagged essentials among them"
                class="q-ml-md"
            />
            <q-checkbox
                v-model="form.source_flagged"
                label="Items flagged as always-include"
            />
            <q-checkbox
                v-model="form.source_frequently_added"
                label="Frequently added in past lists"
            />

            <q-separator class="q-my-md" />
            <div class="text-caption dora-text-muted q-mb-xs">Target</div>
            <q-option-group
                v-model="form.targetMode"
                :options="targetModeOptions"
                type="radio"
                inline
            />
            <q-input
                v-if="form.targetMode === 'new'"
                v-model="form.name"
                outlined
                dense
                label="Name (optional)"
                placeholder="Leave blank to use a default name"
            />
            <!-- P6-01 Chunk 7 — optional shop day. The selector sort, the
                 router landing's "today's list" pick, and the shopping-day
                 banner all key off this. -->
            <q-input
                v-if="form.targetMode === 'new'"
                v-model="form.plannedShopDate"
                outlined
                dense
                type="date"
                label="Plan this shop for (optional)"
                clearable
            />
            <q-select
                v-else
                v-model="form.mergeIntoListId"
                :options="mergeOptions"
                emit-value
                map-options
                outlined
                dense
                label="Add to existing list"
                :hint="mergeOptions.length === 0 ? 'No active lists yet — switch back to Create new.' : ''"
            />
        </q-card-section>
        <template #actions>
            <BaseButton variant="ghost" label="Cancel" v-close-popup />
            <BaseButton
                :label="form.targetMode === 'new' ? 'Create list' : 'Top up list'"
                :disable="!canSubmit"
                :loading="creating || autogenerating"
                @click="submit"
            />
        </template>
    </BaseDialog>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import MealPlanApiService from 'src/services/api/mealPlanApiService';
    import { needsRestockSequence } from 'src/helpers/stockStatus';
    import RecipeApiService from 'src/services/api/recipeApiService';
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import ShoppingListTemplateApiService from 'src/services/api/shoppingListTemplateApiService';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { computed, reactive, ref, watch } from 'vue';

    type StartFrom = 'empty' | 'template' | 'recipe' | 'meal_plan';
    type TargetMode = 'new' | 'merge';

    const props = withDefaults(defineProps<{
        modelValue: boolean;
        presetLowOrOut?: boolean;
        presetMergeIntoListId?: string | null;
    }>(), {
        presetLowOrOut: false,
        presetMergeIntoListId: null,
    });

    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
        (e: 'created', payload: { listId: string }): void;
    }>();

    const $q = useQuasar();
    const api = new ShoppingListApiService();
    const templateApi = new ShoppingListTemplateApiService();
    const recipeApi = new RecipeApiService();
    const mealPlanApi = new MealPlanApiService();
    const store = useShoppingListStore();
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);

    const creating = ref(false);
    const autogenerating = ref(false);
    const loadingPickers = ref(false);
    const templateOptions = ref<{ label: string; value: string }[]>([]);
    const recipeOptions = ref<{ label: string; value: string; ingredientIds: string[] }[]>([]);
    const mealPlanOptions = ref<{ label: string; value: string }[]>([]);

    const lowOrOutCount = computed(() => {
        const ids = new Set(
            stockLevels.value
                .filter((l) => needsRestockSequence(l.sequence))
                .map((l) => l.stock_level_id),
        );
        if (ids.size === 0) return 0;
        return stockItems.value.filter((s) => ids.has(s.stock_level_id)).length;
    });

    const mergeOptions = computed(() =>
        store.summaries
            .filter((s) => s.status !== 'done')
            .map((s) => ({ label: s.display_name, value: s.shopping_list_id })),
    );

    const form = reactive({
        startFrom: 'empty' as StartFrom,
        templateId: null as string | null,
        recipeId: null as string | null,
        mealPlanId: null as string | null,
        name: '',
        plannedShopDate: '' as string,
        source_low_or_out: false,
        source_essentials_only_for_low: false,
        source_flagged: false,
        source_frequently_added: false,
        targetMode: 'new' as TargetMode,
        mergeIntoListId: null as string | null,
    });

    const startFromOptions = [
        { label: 'Empty', value: 'empty' },
        { label: 'Template', value: 'template' },
        { label: 'Recipe', value: 'recipe' },
        { label: 'Meal plan', value: 'meal_plan' },
    ];
    const targetModeOptions = computed(() => [
        { label: 'Create new list', value: 'new' },
        {
            label: 'Add to existing list',
            value: 'merge',
            disable: mergeOptions.value.length === 0,
        },
    ]);

    const canSubmit = computed(() => {
        if (form.startFrom === 'template' && !form.templateId) return false;
        if (form.startFrom === 'recipe' && !form.recipeId) return false;
        if (form.startFrom === 'meal_plan' && !form.mealPlanId) return false;
        if (form.targetMode === 'merge' && !form.mergeIntoListId) return false;
        const hasAutoFill =
            form.source_low_or_out
            || form.source_flagged
            || form.source_frequently_added;
        const hasStartContent = form.startFrom !== 'empty';
        if (form.targetMode === 'merge' && !hasAutoFill && !hasStartContent) return false;
        return true;
    });

    // Reset form + lazy-load pickers each time the dialog opens.
    watch(
        () => props.modelValue,
        async (open) => {
            if (!open) return;
            form.startFrom = 'empty';
            form.templateId = null;
            form.recipeId = null;
            form.mealPlanId = null;
            form.name = '';
            form.plannedShopDate = '';
            form.source_low_or_out = props.presetLowOrOut;
            form.source_essentials_only_for_low = false;
            form.source_flagged = false;
            form.source_frequently_added = false;
            form.targetMode = props.presetMergeIntoListId ? 'merge' : 'new';
            form.mergeIntoListId = props.presetMergeIntoListId;
            if (
                templateOptions.value.length === 0
                && recipeOptions.value.length === 0
                && mealPlanOptions.value.length === 0
            ) {
                loadingPickers.value = true;
                try {
                    const [templates, recipesResp, plansResp] = await Promise.all([
                        templateApi.getAllAsync().catch(() => []),
                        recipeApi.getAllAsync().catch(() => ({ items: [] })),
                        mealPlanApi.getAllAsync().catch(() => ({ items: [] })),
                    ]);
                    templateOptions.value = templates.map((t) => ({
                        label: `${t.name} (${t.line_count} item${t.line_count === 1 ? '' : 's'})`,
                        value: t.template_id,
                    }));
                    recipeOptions.value = (recipesResp.items ?? []).map((r) => {
                        const ingredientIds = (r.ingredients ?? [])
                            .map((i) => i.stock_item_id)
                            .filter((id): id is string => Boolean(id));
                        return {
                            label: `${r.name}${ingredientIds.length ? ` (${ingredientIds.length} ingredients)` : ''}`,
                            value: r.recipe_id,
                            ingredientIds,
                        };
                    });
                    mealPlanOptions.value = (plansResp.items ?? []).map((p) => ({
                        label: `${p.name} (${p.entries?.length ?? 0} meals)`,
                        value: p.meal_plan_id,
                    }));
                } finally {
                    loadingPickers.value = false;
                }
            }
        },
    );

    async function bulkAddToList(
        listId: string,
        stockItemIds: string[],
    ): Promise<{ added: number; skipped: number }> {
        let added = 0;
        let skipped = 0;
        for (const id of stockItemIds) {
            try {
                const result = await api.addLineAsync(listId, { stock_item_id: id });
                if (result.already_on_list) skipped++;
                else added++;
            } catch {
                skipped++;
            }
        }
        return { added, skipped };
    }

    async function submit() {
        const f = form;
        const wantsAutoFill =
            f.source_low_or_out
            || f.source_flagged
            || f.source_frequently_added;

        let targetListId: string | null = null;
        let createdNew = false;
        try {
            if (f.targetMode === 'merge') {
                targetListId = f.mergeIntoListId;
            } else {
                creating.value = true;
                const payload: { name?: string; planned_shop_date?: string | null } = {};
                if (f.name.trim()) payload.name = f.name.trim();
                if (f.plannedShopDate) payload.planned_shop_date = f.plannedShopDate;
                const { shopping_list_id } = await api.createAsync(payload);
                targetListId = shopping_list_id;
                createdNew = true;
            }
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not create list.',
                caption: toastCaption(err),
            });
            creating.value = false;
            return;
        } finally {
            creating.value = false;
        }
        if (!targetListId) return;

        let preSeededAdded = 0;
        let preSeededSkipped = 0;
        try {
            if (f.startFrom === 'template' && f.templateId) {
                if (createdNew) {
                    // Templates' instantiate path creates its own list; we
                    // already created an empty shell so delete it and let
                    // instantiate own the result.
                    await api.deleteAsync(targetListId);
                    const result = await templateApi.instantiateAsync(f.templateId, {});
                    targetListId = result.shopping_list_id ?? null;
                    preSeededAdded = result.line_count;
                } else if (targetListId) {
                    // Merge mode — no "merge template" API. Spin up a temp
                    // list, copy its lines, then delete the temp.
                    const tmp = await templateApi.instantiateAsync(f.templateId, {});
                    if (tmp.shopping_list_id) {
                        const detail = await api.getDetailAsync(tmp.shopping_list_id);
                        const ids = detail.lines
                            .map((l) => l.stock_item_id)
                            .filter((id): id is string => !!id);
                        const counts = await bulkAddToList(targetListId, ids);
                        preSeededAdded += counts.added;
                        preSeededSkipped += counts.skipped;
                        await api.deleteAsync(tmp.shopping_list_id);
                    }
                }
            } else if (f.startFrom === 'recipe' && f.recipeId) {
                const opt = recipeOptions.value.find((r) => r.value === f.recipeId);
                if (opt && targetListId) {
                    const counts = await bulkAddToList(targetListId, opt.ingredientIds);
                    preSeededAdded += counts.added;
                    preSeededSkipped += counts.skipped;
                }
            } else if (f.startFrom === 'meal_plan' && f.mealPlanId) {
                const ingredients = await mealPlanApi.getIngredientsAsync(f.mealPlanId);
                if (targetListId) {
                    const counts = await bulkAddToList(
                        targetListId,
                        ingredients
                            .map((i) => i.stock_item_id)
                            .filter((id): id is string => Boolean(id)),
                    );
                    preSeededAdded += counts.added;
                    preSeededSkipped += counts.skipped;
                }
            }
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not pre-fill from the chosen source.',
                caption: toastCaption(err),
            });
        }

        let autoAdded = 0;
        let autoSkipped = 0;
        let autoNothingToAdd = false;
        if (wantsAutoFill && targetListId) {
            autogenerating.value = true;
            try {
                const result = await api.autoGenerateAsync({
                    merge_into_list_id: targetListId,
                    sources: {
                        low_stock: f.source_low_or_out,
                        out_of_stock: f.source_low_or_out,
                        essentials_only_for_low:
                            f.source_low_or_out && f.source_essentials_only_for_low,
                        flagged: f.source_flagged,
                        frequently_added: f.source_frequently_added,
                    },
                });
                if (result.nothing_to_add) {
                    autoNothingToAdd = true;
                } else {
                    autoAdded = result.added_count;
                    autoSkipped = result.skipped_already_on_list ?? 0;
                }
            } catch (err) {
                $q.notify({
                    type: 'negative',
                    position: 'bottom-right',
                    message: 'Could not auto-fill from stock.',
                    caption: toastCaption(err),
                });
            } finally {
                autogenerating.value = false;
            }
        }

        emit('update:modelValue', false);
        await store.refreshAsync();

        const totalAdded = preSeededAdded + autoAdded;
        const totalSkipped = preSeededSkipped + autoSkipped;
        if (totalAdded === 0 && !autoNothingToAdd && f.startFrom === 'empty' && !wantsAutoFill) {
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: createdNew ? 'Empty list created.' : 'No changes — nothing to add.',
            });
        } else if (autoNothingToAdd && totalAdded === 0) {
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: 'Nothing matched the picked sources.',
            });
        } else {
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message:
                    `${createdNew ? 'Created list.' : 'Topped up list.'} `
                    + `${totalAdded} item${totalAdded === 1 ? '' : 's'} added`
                    + (totalSkipped > 0 ? `, ${totalSkipped} already on list` : '')
                    + '.',
            });
        }

        if (targetListId) emit('created', { listId: targetListId });
    }
</script>
