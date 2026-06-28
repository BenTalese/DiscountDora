<template>
    <!-- FU-094 — drag-and-drop reorder. The whole row listens for
         dragover/drop, but `draggable` lives only on the handle so the
         textareas/selects below stay clickable + selectable. Siblings-
         only constraint: dragover only allows a drop when the dragged
         row shares this row's `parent_client_id` (a top-step can't
         become a sub-step via drag — that change-of-nesting is its own
         affordance and out of scope here). -->
    <div
        class="recipe-step-row q-mb-sm"
        :class="{
            'recipe-step-row--sub': row.depth === 1,
            'recipe-step-row--drop-over': isDropOver,
            'recipe-step-row--dragging': isBeingDragged,
        }"
        @dragover="onRowDragOver"
        @dragleave="onRowDragLeave"
        @drop="onRowDrop"
    >
        <div class="recipe-step-row__header row items-center q-gutter-xs no-wrap">
            <div
                class="recipe-step-row__handle dora-text-muted"
                draggable="true"
                aria-label="Drag to reorder"
                @dragstart="onHandleDragStart"
                @dragend="onHandleDragEnd"
            >
                <q-icon :name="ICONS.drag_indicator" />
                <q-tooltip>Drag to reorder among siblings</q-tooltip>
            </div>
            <div class="recipe-step-row__label dora-text-muted">
                {{ row.depth === 0 ? `Step ${row.sibling_index + 1}` : `↳ Sub-step ${row.sibling_index + 1}` }}
            </div>
            <q-space />
            <!-- FU-117 — section picker, only when the recipe has named
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
        // FU-117 — section choices. Optional so callers without named
        // sections leave the picker entirely off-screen.
        sectionOptions?: SectionOption[];
        canAddSubStep: boolean;
        /** FU-094 — client_id currently being dragged (parent owns this state
         *  so cross-row dragover can validate against the source). null when
         *  no drag is in progress. */
        draggingClientId?: string | null;
        /** Parent of the row currently being dragged. Sibling check on
         *  dragover compares this against `row.parent_client_id`. */
        draggingParentId?: string | null;
    }>();

    const emit = defineEmits<{
        (e: 'update', updated: EditableStep): void;
        (e: 'add-sub'): void;
        (e: 'remove'): void;
        // FU-094 — lifecycle events for drag-and-drop reorder. The parent
        // (RecipeStepsEditor) owns the steps array and the dragging state;
        // the row just emits intents.
        (e: 'drag-start', clientId: string, parentClientId: string | null): void;
        (e: 'drag-end'): void;
        (e: 'drop-on-row', targetClientId: string): void;
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

    // FU-117 — section_client_id picker on top-level rows. q-select with
    // a null option ("(Main)") emits null when picked, no coercion needed.
    const sectionModel = computed<string | null>({
        get: () => props.row.section_client_id,
        set: (v) => patch({ section_client_id: v ?? null }),
    });

    // ── FU-094: drag-and-drop reorder ────────────────────────────────────
    // The handle is the only draggable element; the row itself is the drop
    // target. The parent owns the dragging state so we can validate
    // sibling-ness (same parent_client_id) at dragover time.
    const DRAG_MIME = 'application/x-dora-recipe-step';

    const isDropOver = ref(false);
    const isBeingDragged = computed(
        () => props.draggingClientId === props.row.client_id,
    );
    const isValidDropTarget = computed(() => {
        if (props.draggingClientId == null) return false;
        if (props.draggingClientId === props.row.client_id) return false;
        // Siblings-only: same parent_client_id. A drag from another
        // nesting level can hover but won't drop.
        return props.draggingParentId === props.row.parent_client_id;
    });

    function onHandleDragStart(event: DragEvent): void {
        if (!event.dataTransfer) return;
        event.dataTransfer.setData(DRAG_MIME, props.row.client_id);
        event.dataTransfer.effectAllowed = 'move';
        // Use the whole row as the drag image so the user sees the row
        // they're moving, not the tiny handle icon.
        const rowEl = (event.target as HTMLElement | null)
            ?.closest('.recipe-step-row') as HTMLElement | null;
        if (rowEl) event.dataTransfer.setDragImage(rowEl, 0, 0);
        emit('drag-start', props.row.client_id, props.row.parent_client_id);
    }
    function onHandleDragEnd(): void {
        emit('drag-end');
    }
    function onRowDragOver(event: DragEvent): void {
        if (!event.dataTransfer?.types.includes(DRAG_MIME)) return;
        if (!isValidDropTarget.value) return;
        // preventDefault enables drop. Without it the browser rejects.
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
        isDropOver.value = true;
    }
    function onRowDragLeave(): void {
        isDropOver.value = false;
    }
    function onRowDrop(event: DragEvent): void {
        isDropOver.value = false;
        if (!isValidDropTarget.value) return;
        event.preventDefault();
        emit('drop-on-row', props.row.client_id);
    }
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
    /* FU-094 — drag affordances. The handle is the only "grab me"
       element; the row body keeps default cursor so textareas + selects
       behave normally. */
    .recipe-step-row__handle {
        cursor: grab;
        padding: 2px 4px;
        border-radius: var(--radius-sm, 4px);
        display: inline-flex;
        align-items: center;
    }
    .recipe-step-row__handle:hover {
        background: var(--surface-sunken);
    }
    .recipe-step-row__handle:active {
        cursor: grabbing;
    }
    .recipe-step-row--dragging {
        opacity: 0.5;
    }
    .recipe-step-row--drop-over {
        box-shadow: 0 0 0 2px var(--brand-primary);
    }
    /* FU-117 — keep the section picker compact in the header row so it
       doesn't crowd the move/sub-step/remove buttons. */
    .recipe-step-row__section-select {
        max-width: 160px;
    }
</style>
