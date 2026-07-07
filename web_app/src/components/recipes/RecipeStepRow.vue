<template>
    <!-- drag-and-drop reorder via `useDragDropList`.
         The parent editor owns the drag state + sibling-pair predicate
         and passes per-row bindings down through `dragBindings`. The
         row spreads `rowProps` on its outer wrapper (drop target) and
         `handleProps` on the handle icon (the only draggable element),
         so textareas/selects below stay normally clickable. -->
    <div
        class="recipe-step-row q-mb-sm"
        :class="{
            'recipe-step-row--sub': row.depth === 1,
            ...dragBindings.rowClass,
        }"
        v-bind="dragBindings.rowProps"
    >
        <div class="recipe-step-row__header row items-center q-gutter-xs no-wrap">
            <div
                class="dora-dnd-handle dora-text-muted"
                aria-label="Drag to reorder"
                v-bind="dragBindings.handleProps"
            >
                <q-icon :name="ICONS.drag_indicator" />
                <q-tooltip>Drag to reorder among siblings</q-tooltip>
            </div>
            <div class="recipe-step-row__label dora-text-muted">
                {{ row.depth === 0 ? `Step ${row.sibling_index + 1}` : `↳ Sub-step ${row.sibling_index + 1}` }}
            </div>
            <q-space />
            <!-- section picker, only when the recipe has named
                 sections and only at depth 0 (sub-steps inherit visually
                 from their parent). Mirrors the ingredient row picker on
                 RecipeDetailPage. -->
            <q-select
                v-if="row.depth === 0 && (sectionOptions?.length ?? 0) > 1"
                v-model="sectionModel"
                :options="sectionOptions"
                option-value="value"
                option-label="label"
                emit-value
                map-options
                dense
                outlined
                label="Section"
                class="recipe-step-row__section-select"
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
    import type { DragDropRowBindings } from 'src/composables/useDragDropList';
    import type {
        StepRowView,
        EditableStep,
        IngredientOption,
        ToolOption,
        SectionOption,
    } from 'src/components/recipes/recipeStepEditorTypes';

    const props = defineProps<{
        row: StepRowView;
        ingredientOptions: IngredientOption[];
        toolOptions: ToolOption[];
        // section choices. Optional so callers without named
        // sections leave the picker entirely off-screen.
        sectionOptions?: SectionOption[];
        canAddSubStep: boolean;
        /** FU-094 / R-022 — per-row DnD bindings supplied by the parent's
         *  `useDragDropList`. Spread `handleProps` on the drag handle and
         *  `rowProps` + `rowClass` on the row body. */
        dragBindings: DragDropRowBindings;
    }>();
    const emit = defineEmits<{
        (e: 'update', updated: EditableStep): void;
        (e: 'add-sub'): void;
        (e: 'remove'): void;
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

    // section_client_id picker on top-level rows. q-select with
    // a null option ("(Main)") emits null when picked, no coercion needed.
    const sectionModel = computed<string | null>({
        get: () => props.row.section_client_id,
        set: (v) => patch({ section_client_id: v ?? null }),
    });

</script>

<style scoped lang="scss">
    .recipe-step-row {
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 8px 12px;
        background: var(--surface-card);
        transition:
            box-shadow var(--motion-normal, 200ms) ease,
            opacity var(--motion-normal, 200ms) ease,
            background-color var(--motion-normal, 200ms) ease;
    }
    .recipe-step-row--sub {
        margin-left: 24px;
        background: var(--surface-sunken);
    }
    .recipe-step-row__label {
        font-weight: 500;
        font-size: 0.85em;
    }
    /* FU-094 / R-022 — drag affordances live in src/css/dnd.scss
       (.dora-dnd-row / .dora-dnd-handle). The composable applies the
       classes via `rowClass`; the template uses .dora-dnd-handle on
       the handle wrapper. No per-component DnD CSS needed. */
    /* FU-117 — keep the section picker compact in the header row so it
       doesn't crowd the move/sub-step/remove buttons. */
    .recipe-step-row__section-select {
        max-width: 160px;
    }
</style>
