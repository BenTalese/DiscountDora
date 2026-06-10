<template>
    <div
        class="recipe-step-row q-mb-sm"
        :class="{ 'recipe-step-row--sub': row.depth === 1 }"
    >
        <div class="recipe-step-row__header row items-center q-gutter-xs no-wrap">
            <div class="recipe-step-row__label dora-text-muted">
                {{ row.depth === 0 ? `Step ${row.sibling_index + 1}` : `↳ Sub-step ${row.sibling_index + 1}` }}
            </div>
            <q-space />
            <BaseButton
                variant="icon"
                :icon="ICONS.arrow_upward"
                :disable="!canMoveUp"
                aria-label="Move up"
                @click="$emit('move-up')"
            />
            <BaseButton
                variant="icon"
                :icon="ICONS.arrow_downward"
                :disable="!canMoveDown"
                aria-label="Move down"
                @click="$emit('move-down')"
            />
            <BaseButton
                v-if="canAddSubStep"
                variant="icon"
                :icon="ICONS.subdirectory_arrow_right"
                aria-label="Add sub-step"
                @click="$emit('add-sub')"
            />
            <BaseButton
                variant="icon"
                :icon="ICONS.close"
                aria-label="Remove step"
                @click="$emit('remove')"
            />
        </div>

        <q-input
            v-model="textModel"
            :label="row.depth === 0 ? 'Step' : 'Sub-step'"
            type="textarea"
            autogrow
            outlined
            dense
            class="q-mt-xs"
        />

        <div class="row q-gutter-sm q-mt-xs items-center">
            <BaseButton
                v-if="!showHint"
                variant="ghost"
                :icon="ICONS.lightbulb"
                label="Add hint"
                @click="onAddHint"
            />
            <q-input
                v-else
                v-model="hintModel"
                label="Hint (optional)"
                dense
                outlined
                class="col"
                :debounce="100"
            >
                <template #append>
                    <BaseButton
                        variant="icon"
                        :icon="ICONS.close"
                        aria-label="Remove hint"
                        @click="onClearHint"
                    />
                </template>
            </q-input>
        </div>

        <div class="row q-gutter-sm q-mt-xs">
            <q-select
                v-model="ingredientsModel"
                :options="ingredientOptions"
                option-value="value"
                option-label="label"
                emit-value
                map-options
                multiple
                use-chips
                dense
                outlined
                clearable
                label="Ingredients used"
                class="col"
            />
            <q-select
                v-model="toolsModel"
                :options="toolOptions"
                option-value="value"
                option-label="label"
                emit-value
                map-options
                multiple
                use-chips
                dense
                outlined
                clearable
                label="Tools"
                class="col"
            />
        </div>
    </div>
</template>

<script setup lang="ts">
    import { computed, ref } from 'vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import type {
        StepRowView,
        EditableStep,
        IngredientOption,
        ToolOption,
    } from 'src/components/recipes/recipeStepEditorTypes';

    const props = defineProps<{
        row: StepRowView;
        ingredientOptions: IngredientOption[];
        toolOptions: ToolOption[];
        canMoveUp: boolean;
        canMoveDown: boolean;
        canAddSubStep: boolean;
    }>();

    const emit = defineEmits<{
        (e: 'update', updated: EditableStep): void;
        (e: 'add-sub'): void;
        (e: 'remove'): void;
        (e: 'move-up'): void;
        (e: 'move-down'): void;
    }>();

    function patch(partial: Partial<EditableStep>) {
        const { depth, sibling_index, sibling_total, ...base } = props.row;
        void depth; void sibling_index; void sibling_total;
        emit('update', { ...base, ...partial });
    }

    const textModel = computed<string>({
        get: () => props.row.text,
        set: (v) => patch({ text: v }),
    });

    const showHint = ref<boolean>(props.row.hint !== null && props.row.hint !== '');
    function onAddHint() {
        showHint.value = true;
        if (props.row.hint === null) patch({ hint: '' });
    }
    function onClearHint() {
        showHint.value = false;
        patch({ hint: null });
    }
    const hintModel = computed<string>({
        get: () => props.row.hint ?? '',
        set: (v) => patch({ hint: v }),
    });

    const ingredientsModel = computed<string[]>({
        get: () => props.row.ingredient_client_ids,
        set: (v) => patch({ ingredient_client_ids: v ?? [] }),
    });

    const toolsModel = computed<string[]>({
        get: () => props.row.tool_ids,
        set: (v) => patch({ tool_ids: v ?? [] }),
    });
</script>

<style scoped lang="scss">
    .recipe-step-row {
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 8px 12px;
        background: var(--surface-card);
    }
    .recipe-step-row--sub {
        margin-left: 24px;
        background: var(--surface-sunken);
    }
    .recipe-step-row__label {
        font-weight: 500;
        font-size: 0.85em;
    }
</style>
