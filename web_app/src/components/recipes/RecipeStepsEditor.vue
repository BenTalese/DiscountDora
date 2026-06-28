<template>
    <div class="recipe-steps-editor">
        <div v-if="steps.length === 0" class="recipe-steps-editor__empty dora-text-muted q-mb-sm">
            No structured steps yet. Add one to highlight ingredients/tools per step
            and unlock per-step cook mode, or stick to the freeform Advanced fallback below.
        </div>

        <draggable-step-row
            v-for="row in flatRows"
            :key="row.client_id"
            :row="row"
            :ingredient-options="ingredientOptions"
            :tool-options="toolOptions"
            :section-options="sectionOptions ?? []"
            :can-add-sub-step="row.parent_client_id === null"
            :dragging-client-id="draggingClientId"
            :dragging-parent-id="draggingParentId"
            @update="onRowUpdate"
            @add-sub="onAddSubStep(row.client_id)"
            @remove="onRemove(row.client_id)"
            @drag-start="onDragStart"
            @drag-end="onDragEnd"
            @drop-on-row="onDropOnRow"
        />

        <BaseButton
            variant="ghost"
            :icon="ICONS.add"
            label="Add step"
            @click="onAddTopStep"
            class="q-mt-sm"
        />
    </div>
</template>

<script setup lang="ts">
    import { computed, ref } from 'vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import DraggableStepRow from 'src/components/recipes/RecipeStepRow.vue';
    import type {
        EditableStep,
        StepRowView,
        IngredientOption,
        ToolOption,
        SectionOption,
    } from 'src/components/recipes/recipeStepEditorTypes';

    const props = defineProps<{
        steps: EditableStep[];
        ingredientOptions: IngredientOption[];
        toolOptions: ToolOption[];
        // FU-117 — section choices for the top-level step picker. Defaults
        // to `[]` so callers without named sections (or that haven't wired
        // the prop yet) get the same behaviour as before: no picker
        // rendered, steps stay unsectioned.
        sectionOptions?: SectionOption[];
    }>();

    const emit = defineEmits<{
        (e: 'update:steps', value: EditableStep[]): void;
    }>();

    function newClientId(): string {
        // crypto.randomUUID is available in every browser this app targets
        // (Quasar's supported matrix); the server only needs a unique string.
        if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
            return crypto.randomUUID();
        }
        // Fallback: timestamp + random suffix.
        return `s${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`;
    }

    /** Flatten steps for rendering: top-level row, then its sub-steps, then
     *  next top-level, etc. Sequence within siblings is the user's order. */
    const flatRows = computed<StepRowView[]>(() => {
        const tops = [...props.steps.filter((s) => s.parent_client_id === null)]
            .sort((a, b) => a.sequence - b.sequence);
        const rows: StepRowView[] = [];
        for (const top of tops) {
            const topSiblings = tops;
            rows.push({
                ...top,
                depth: 0,
                sibling_index: topSiblings.indexOf(top),
                sibling_total: topSiblings.length,
            });
            const subs = props.steps
                .filter((s) => s.parent_client_id === top.client_id)
                .sort((a, b) => a.sequence - b.sequence);
            for (const sub of subs) {
                rows.push({
                    ...sub,
                    depth: 1,
                    sibling_index: subs.indexOf(sub),
                    sibling_total: subs.length,
                });
            }
        }
        return rows;
    });

    function onRowUpdate(updated: EditableStep) {
        emit(
            'update:steps',
            props.steps.map((s) => (s.client_id === updated.client_id ? updated : s)),
        );
    }

    function onAddTopStep() {
        const siblings = props.steps.filter((s) => s.parent_client_id === null);
        const next: EditableStep = {
            client_id: newClientId(),
            parent_client_id: null,
            sequence: siblings.length,
            text: '',
            hint: null,
            ingredient_client_ids: [],
            tool_ids: [],
            section_client_id: null,
        };
        emit('update:steps', [...props.steps, next]);
    }

    function onAddSubStep(parentId: string) {
        const siblings = props.steps.filter((s) => s.parent_client_id === parentId);
        const next: EditableStep = {
            client_id: newClientId(),
            parent_client_id: parentId,
            sequence: siblings.length,
            text: '',
            hint: null,
            ingredient_client_ids: [],
            tool_ids: [],
            // FU-117 — sub-steps inherit their parent's section visually
            // on the read path (server flattens cook-mode by section_id of
            // the top-level row). Keep null here; the picker isn't shown.
            section_client_id: null,
        };
        emit('update:steps', [...props.steps, next]);
    }

    function onRemove(clientId: string) {
        // Drop the row and any sub-steps it owns.
        const remaining = props.steps.filter(
            (s) => s.client_id !== clientId && s.parent_client_id !== clientId,
        );
        // Re-pack sibling sequences so the server-side ordering stays tight.
        emit('update:steps', repackSequences(remaining));
    }

    // ── FU-094: drag-and-drop reorder (siblings only) ────────────────────
    // Drag state is owned here so every row can render its drop-target
    // affordance against the active drag. Rows emit `drag-start` /
    // `drag-end` / `drop-on-row`; this component computes the new order.
    const draggingClientId = ref<string | null>(null);
    const draggingParentId = ref<string | null>(null);

    function onDragStart(clientId: string, parentClientId: string | null) {
        draggingClientId.value = clientId;
        draggingParentId.value = parentClientId;
    }
    function onDragEnd() {
        draggingClientId.value = null;
        draggingParentId.value = null;
    }
    function onDropOnRow(targetClientId: string) {
        const sourceId = draggingClientId.value;
        draggingClientId.value = null;
        draggingParentId.value = null;
        if (!sourceId || sourceId === targetClientId) return;

        const source = props.steps.find((s) => s.client_id === sourceId);
        const target = props.steps.find((s) => s.client_id === targetClientId);
        if (!source || !target) return;
        // Siblings-only is also validated on the row's dragover — re-check
        // here as a belt-and-braces against a stale drag.
        if (source.parent_client_id !== target.parent_client_id) return;

        // Reorder within the sibling group using the same "insert at the
        // target's slot" pattern as ShoppingListDetail.onLineDrop —
        // matches the user's mental model ("the dropped row lands where I
        // dragged it onto"). Other steps (sub-steps, opposite-parent
        // children) are untouched.
        const siblings = props.steps
            .filter((s) => s.parent_client_id === source.parent_client_id)
            .sort((a, b) => a.sequence - b.sequence);
        const ids = siblings.map((s) => s.client_id);
        const fromIdx = ids.indexOf(sourceId);
        const toIdx = ids.indexOf(targetClientId);
        if (fromIdx < 0 || toIdx < 0) return;
        ids.splice(fromIdx, 1);
        ids.splice(toIdx, 0, sourceId);
        // Stamp new sibling sequences.
        const newSeqById = new Map<string, number>(ids.map((id, i) => [id, i]));
        const updated = props.steps.map((s) =>
            newSeqById.has(s.client_id)
                ? { ...s, sequence: newSeqById.get(s.client_id)! }
                : s,
        );
        emit('update:steps', repackSequences(updated));
    }

    /** Force sibling `sequence` values to be 0..N-1 so removals/moves don't
     *  leave gaps that mis-render after a round-trip through the server. */
    function repackSequences(steps: EditableStep[]): EditableStep[] {
        const out: EditableStep[] = [];
        const byParent = new Map<string | null, EditableStep[]>();
        for (const s of steps) {
            const key = s.parent_client_id;
            const bucket = byParent.get(key) ?? [];
            bucket.push(s);
            byParent.set(key, bucket);
        }
        for (const [, bucket] of byParent) {
            bucket.sort((a, b) => a.sequence - b.sequence);
            bucket.forEach((s, i) => out.push({ ...s, sequence: i }));
        }
        return out;
    }
</script>

<style scoped lang="scss">
    .recipe-steps-editor__empty {
        font-size: 0.9em;
        line-height: 1.4;
    }
</style>
