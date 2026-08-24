<template>
    <!--
        One step (or sub-step) in the structured editor.

        Rebuilt 2026-08-24 from owner feedback ("the structured step editor is
        horrible"). The order is now the order you think in — what the step
        *says*, then what it uses, then what you can do to it:

          header   label · section picker · drag handle (pointer devices only)
          text     the step itself
          hint     only once you've asked for one
          uses     ingredients + tools
          actions  up · down · sub-step · hint · remove

        The drag handle is hidden below the tablet breakpoint: a grip you
        can't usefully drag with a thumb is noise, and ↑/↓ do the same job
        with no aiming. Sub-steps keep the same card, indented and toned, so
        the two levels read as the same kind of thing at different depths
        rather than as two different components.
    -->
    <div
        class="rstep"
        :class="{
            'rstep--sub': row.depth === 1,
            ...dragBindings.rowClass,
        }"
        v-bind="dragBindings.rowProps"
    >
        <div class="rstep__head">
            <span class="rstep__label">
                {{ row.depth === 0 ? `Step ${row.sibling_index + 1}` : `Sub-step ${row.sibling_index + 1}` }}
            </span>
            <q-space />
            <!-- Section picker, only when the recipe has named sections and
                 only at depth 0 (sub-steps inherit their parent's). -->
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
                class="rstep__section"
            />
            <div
                class="dora-dnd-handle dora-text-muted rstep__grip"
                aria-label="Drag to reorder"
                v-bind="dragBindings.handleProps"
            >
                <q-icon :name="ICONS.drag_indicator" />
                <q-tooltip>Drag to reorder among siblings</q-tooltip>
            </div>
        </div>

        <q-input
            v-model="textModel"
            :label="row.depth === 0 ? 'Step' : 'Sub-step'"
            type="textarea"
            autogrow
            outlined
            dense
        />

        <q-input
            v-if="showHint"
            v-model="hintModel"
            label="Hint (optional)"
            dense
            outlined
            class="rstep__hint"
            :debounce="100"
        />

        <div class="rstep__uses">
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

        <div class="rstep__actions">
            <BaseButton
                variant="icon"
                :icon="ICONS.arrow_upward"
                :disable="row.sibling_index === 0"
                :aria-label="`Move ${stepName} up`"
                @click="$emit('move', -1)"
            >
                <q-tooltip>Move up</q-tooltip>
            </BaseButton>
            <BaseButton
                variant="icon"
                :icon="ICONS.arrow_downward"
                :disable="row.sibling_index === row.sibling_total - 1"
                :aria-label="`Move ${stepName} down`"
                @click="$emit('move', 1)"
            >
                <q-tooltip>Move down</q-tooltip>
            </BaseButton>
            <BaseButton
                v-if="canAddSubStep"
                variant="icon"
                :icon="ICONS.subdirectory_arrow_right"
                :aria-label="`Add a sub-step under ${stepName}`"
                @click="$emit('add-sub')"
            >
                <q-tooltip>Add sub-step</q-tooltip>
            </BaseButton>
            <BaseButton
                variant="icon"
                :icon="ICONS.lightbulb"
                :aria-label="showHint ? `Remove the hint on ${stepName}` : `Add a hint to ${stepName}`"
                @click="onToggleHint"
            >
                <q-tooltip>{{ showHint ? 'Remove hint' : 'Add hint' }}</q-tooltip>
            </BaseButton>
            <q-space />
            <BaseButton
                variant="danger-icon"
                :icon="ICONS.delete"
                :aria-label="`Remove ${stepName}`"
                @click="$emit('remove')"
            >
                <q-tooltip>Remove</q-tooltip>
            </BaseButton>
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
        /** Reorder among siblings — the keyboard/thumb equivalent of the
         *  drag handle, and the only reorder affordance on a phone. */
        (e: 'move', delta: -1 | 1): void;
    }>();

    const stepName = computed(() =>
        (props.row.depth === 0 ? 'step ' : 'sub-step ') + (props.row.sibling_index + 1));

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
    function onToggleHint() {
        if (showHint.value) {
            showHint.value = false;
            patch({ hint: null });
            return;
        }
        showHint.value = true;
        if (props.row.hint === null) patch({ hint: '' });
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
    .rstep {
        border: 1px solid var(--border-default);
        border-radius: var(--radius-md, 6px);
        padding: var(--space-3, 12px);
        margin-bottom: var(--space-3, 12px);
        background: var(--surface-component);
        display: flex;
        flex-direction: column;
        gap: var(--space-2, 8px);
        transition:
            box-shadow var(--motion-normal, 200ms) ease,
            opacity var(--motion-normal, 200ms) ease,
            background-color var(--motion-normal, 200ms) ease;
    }
    /* Same card, one level in: the left rule and the sunken ground are the
       only difference, so depth reads without a second visual language. */
    .rstep--sub {
        margin-left: var(--space-5, 20px);
        background: var(--surface-sunken);
        border-left: 3px solid var(--brand-primary-soft);
    }

    .rstep__head {
        display: flex;
        align-items: center;
        gap: var(--space-2, 8px);
    }
    .rstep__label {
        font-weight: 700;
        font-size: 0.75rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--text-muted);
    }
    .rstep__section { max-width: 160px; }

    .rstep__uses {
        display: flex;
        gap: var(--space-2, 8px);
        flex-wrap: wrap;
    }
    .rstep__uses > * { flex: 1 1 200px; min-width: 0; }

    .rstep__actions {
        display: flex;
        align-items: center;
        gap: var(--space-1, 4px);
        padding-top: var(--space-1, 4px);
        border-top: 1px solid var(--divider);
    }

    /* A grip you can't drag with a thumb is noise — ↑/↓ are the phone's
       reorder affordance (owner feedback 2026-08-24). */
    @media (max-width: 767px) {
        .rstep__grip { display: none; }
    }
</style>
