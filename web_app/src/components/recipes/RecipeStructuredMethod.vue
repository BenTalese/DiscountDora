<template>
    <!--
        The structured method — one component, both faces.

        Owner feedback 2026-08-27 asked for the method to read as a method
        until you press the pencil, and then to *swap in place* rather than
        open a modal. That only works if the two faces share their geometry:
        the numbered bullet, the sub-step indent and the spacing are one
        stylesheet here, and `editing` decides whether the content column
        holds a paragraph or a field. When the read and edit views were two
        components (a viewer on the page, `RecipeStepsEditor` inside a
        dialog) the block changed character mid-edit, which is the thing the
        owner objected to on the masthead and objected to again here.

        It replaced `RecipeStepsEditor` + `RecipeStepRow` + the dialog they
        lived in; all three were single-consumer, so there is no second
        caller left holding the old shape.

        What a step *uses* is not on the step any more: those three pickers
        were what made the editor feel squished, and "Uses flour, butter" on
        every row was cook-mode detail on a page you read to decide what to
        cook. Links open one step at a time in `RecipeStepLinksDialog`, and
        the link surfaces instead as a *highlight* — select a step and its
        ingredients light up on the rail; select an ingredient and the steps
        that use it light up here.
    -->
    <div class="rsm">
        <ol v-if="topLevelSteps.length > 0" class="rsm__steps">
            <li
                v-for="(step, stepIndex) in topLevelSteps"
                :key="step.client_id"
                class="rsm__step"
                :class="{
                    'rsm__step--lit': isLit(step.client_id),
                    'rsm__step--editing': editing,
                    ...(editing ? dnd.bind(step).rowClass : {}),
                }"
                v-bind="editing ? dnd.bind(step).rowProps : {}"
            >
                <!-- The numeral is the drag handle while editing — a grip
                     column of its own would be a fourth thing competing with
                     the text for the width the owner asked us to give back. -->
                <span
                    class="rsm__num"
                    :class="{ 'rsm__num--grab': editing }"
                    v-bind="editing ? dnd.bind(step).handleProps : {}"
                >
                    {{ stepIndex + 1 }}
                    <q-tooltip v-if="editing">Drag to reorder</q-tooltip>
                </span>

                <div class="rsm__content">
                    <!-- ── Read ─────────────────────────────────────────── -->
                    <template v-if="!editing">
                        <button
                            type="button"
                            class="rsm__text rsm__pick"
                            :aria-pressed="selectedStepId === step.client_id"
                            :aria-label="`Step ${stepIndex + 1} — highlight the ingredients it uses`"
                            @click="onPick(step.client_id)"
                        >
                            {{ step.text || 'Empty step' }}
                        </button>
                        <span v-if="step.hint" class="rsm__hint">{{ step.hint }}</span>
                        <span v-if="step.timer_minutes !== null" class="rsm__timer">
                            <q-icon :name="ICONS.timer" size="14px" />{{ timerLabel(step) }}
                        </span>
                    </template>

                    <!-- ── Edit ─────────────────────────────────────────── -->
                    <template v-else>
                        <q-input
                            :model-value="step.text"
                            type="textarea"
                            autogrow
                            outlined
                            dense
                            :label="`Step ${stepIndex + 1}`"
                            @update:model-value="(v) => patch(step, { text: String(v ?? '') })"
                        />
                        <q-input
                            v-if="step.hint !== null"
                            :model-value="step.hint ?? ''"
                            outlined
                            dense
                            label="Hint (optional)"
                            class="rsm__hintfield"
                            @update:model-value="(v) => patch(step, { hint: String(v ?? '') })"
                        />
                        <q-input
                            v-if="step.timer_minutes !== null"
                            :model-value="step.timer_minutes"
                            type="number"
                            min="1"
                            max="1440"
                            outlined
                            dense
                            label="Timer (minutes)"
                            class="rsm__timerfield"
                            @update:model-value="(v) => patch(step, { timer_minutes: toMinutes(v) })"
                        />
                        <div class="rsm__acts">
                            <BaseButton
                                variant="icon" dense
                                :icon="ICONS.arrow_upward"
                                :disable="stepIndex === 0"
                                :aria-label="`Move step ${stepIndex + 1} up`"
                                @click="move(step, -1)"
                            >
                                <q-tooltip>Move up</q-tooltip>
                            </BaseButton>
                            <BaseButton
                                variant="icon" dense
                                :icon="ICONS.arrow_downward"
                                :disable="stepIndex === topLevelSteps.length - 1"
                                :aria-label="`Move step ${stepIndex + 1} down`"
                                @click="move(step, 1)"
                            >
                                <q-tooltip>Move down</q-tooltip>
                            </BaseButton>
                            <BaseButton
                                variant="icon" dense
                                :icon="ICONS.link"
                                :aria-label="`What step ${stepIndex + 1} uses`"
                                @click="openLinks(step, `step ${stepIndex + 1}`, true)"
                            >
                                <q-badge v-if="linkCount(step) > 0" floating rounded color="primary">
                                    {{ linkCount(step) }}
                                </q-badge>
                                <q-tooltip>Ingredients, tools and section</q-tooltip>
                            </BaseButton>
                            <BaseButton
                                variant="icon" dense
                                :icon="ICONS.lightbulb"
                                :aria-label="step.hint === null
                                    ? `Add a hint to step ${stepIndex + 1}`
                                    : `Remove the hint on step ${stepIndex + 1}`"
                                @click="toggleHint(step)"
                            >
                                <q-tooltip>{{ step.hint === null ? 'Add hint' : 'Remove hint' }}</q-tooltip>
                            </BaseButton>
                            <BaseButton
                                :variant="step.timer_minutes === null ? 'icon' : 'secondary'"
                                dense
                                :icon="ICONS.timer"
                                :aria-pressed="step.timer_minutes !== null"
                                :aria-label="step.timer_minutes === null
                                    ? `Put a timer on step ${stepIndex + 1}`
                                    : `Remove the timer on step ${stepIndex + 1}`"
                                @click="toggleTimer(step)"
                            >
                                <q-tooltip>{{ step.timer_minutes === null ? 'Add a timer' : 'Remove the timer' }}</q-tooltip>
                            </BaseButton>
                            <BaseButton
                                variant="icon" dense
                                :icon="ICONS.subdirectory_arrow_right"
                                :aria-label="`Add a sub-step under step ${stepIndex + 1}`"
                                @click="addSubStep(step.client_id)"
                            >
                                <q-tooltip>Add sub-step</q-tooltip>
                            </BaseButton>
                            <q-space />
                            <BaseButton
                                variant="danger-icon" dense
                                :icon="ICONS.delete"
                                :aria-label="`Remove step ${stepIndex + 1}`"
                                @click="remove(step.client_id)"
                            >
                                <q-tooltip>Remove</q-tooltip>
                            </BaseButton>
                        </div>
                    </template>

                    <!-- Sub-steps. The rule down their left is positioned so
                         it runs through the centre of the parent's numeral
                         (owner ask) — see `--rsm-num` in the stylesheet. -->
                    <ol v-if="subStepsOf(step).length > 0" class="rsm__substeps">
                        <li
                            v-for="(sub, subIndex) in subStepsOf(step)"
                            :key="sub.client_id"
                            class="rsm__sub"
                            :class="{
                                'rsm__step--lit': isLit(sub.client_id),
                                ...(editing ? dnd.bind(sub).rowClass : {}),
                            }"
                            v-bind="editing ? dnd.bind(sub).rowProps : {}"
                        >
                            <span
                                class="rsm__num rsm__num--sub"
                                :class="{ 'rsm__num--grab': editing }"
                                v-bind="editing ? dnd.bind(sub).handleProps : {}"
                            >{{ subIndex + 1 }}</span>
                            <div class="rsm__content">
                                <template v-if="!editing">
                                    <button
                                        type="button"
                                        class="rsm__text rsm__pick"
                                        :aria-pressed="selectedStepId === sub.client_id"
                                        :aria-label="`Sub-step ${subIndex + 1} of step ${stepIndex + 1} — highlight the ingredients it uses`"
                                        @click="onPick(sub.client_id)"
                                    >
                                        {{ sub.text || 'Empty sub-step' }}
                                    </button>
                                    <span v-if="sub.hint" class="rsm__hint">{{ sub.hint }}</span>
                                    <span v-if="sub.timer_minutes !== null" class="rsm__timer">
                                        <q-icon :name="ICONS.timer" size="14px" />{{ timerLabel(sub) }}
                                    </span>
                                </template>
                                <template v-else>
                                    <q-input
                                        :model-value="sub.text"
                                        type="textarea"
                                        autogrow
                                        outlined
                                        dense
                                        :label="`Sub-step ${subIndex + 1}`"
                                        @update:model-value="(v) => patch(sub, { text: String(v ?? '') })"
                                    />
                                    <q-input
                                        v-if="sub.hint !== null"
                                        :model-value="sub.hint ?? ''"
                                        outlined
                                        dense
                                        label="Hint (optional)"
                                        class="rsm__hintfield"
                                        @update:model-value="(v) => patch(sub, { hint: String(v ?? '') })"
                                    />
                                    <q-input
                                        v-if="sub.timer_minutes !== null"
                                        :model-value="sub.timer_minutes"
                                        type="number"
                                        min="1"
                                        max="1440"
                                        outlined
                                        dense
                                        label="Timer (minutes)"
                                        class="rsm__timerfield"
                                        @update:model-value="(v) => patch(sub, { timer_minutes: toMinutes(v) })"
                                    />
                                    <div class="rsm__acts">
                                        <BaseButton
                                            variant="icon" dense
                                            :icon="ICONS.arrow_upward"
                                            :disable="subIndex === 0"
                                            :aria-label="`Move sub-step ${subIndex + 1} up`"
                                            @click="move(sub, -1)"
                                        >
                                            <q-tooltip>Move up</q-tooltip>
                                        </BaseButton>
                                        <BaseButton
                                            variant="icon" dense
                                            :icon="ICONS.arrow_downward"
                                            :disable="subIndex === subStepsOf(step).length - 1"
                                            :aria-label="`Move sub-step ${subIndex + 1} down`"
                                            @click="move(sub, 1)"
                                        >
                                            <q-tooltip>Move down</q-tooltip>
                                        </BaseButton>
                                        <BaseButton
                                            variant="icon" dense
                                            :icon="ICONS.link"
                                            :aria-label="`What sub-step ${subIndex + 1} uses`"
                                            @click="openLinks(sub, `sub-step ${subIndex + 1}`, false)"
                                        >
                                            <q-badge v-if="linkCount(sub) > 0" floating rounded color="primary">
                                                {{ linkCount(sub) }}
                                            </q-badge>
                                            <q-tooltip>Ingredients and tools</q-tooltip>
                                        </BaseButton>
                                        <BaseButton
                                            variant="icon" dense
                                            :icon="ICONS.lightbulb"
                                            :aria-label="sub.hint === null
                                                ? `Add a hint to sub-step ${subIndex + 1}`
                                                : `Remove the hint on sub-step ${subIndex + 1}`"
                                            @click="toggleHint(sub)"
                                        >
                                            <q-tooltip>{{ sub.hint === null ? 'Add hint' : 'Remove hint' }}</q-tooltip>
                                        </BaseButton>
                                        <BaseButton
                                            :variant="sub.timer_minutes === null ? 'icon' : 'secondary'"
                                            dense
                                            :icon="ICONS.timer"
                                            :aria-pressed="sub.timer_minutes !== null"
                                            :aria-label="sub.timer_minutes === null
                                                ? `Put a timer on sub-step ${subIndex + 1}`
                                                : `Remove the timer on sub-step ${subIndex + 1}`"
                                            @click="toggleTimer(sub)"
                                        >
                                            <q-tooltip>{{ sub.timer_minutes === null ? 'Add a timer' : 'Remove the timer' }}</q-tooltip>
                                        </BaseButton>
                                        <q-space />
                                        <BaseButton
                                            variant="danger-icon" dense
                                            :icon="ICONS.delete"
                                            :aria-label="`Remove sub-step ${subIndex + 1}`"
                                            @click="remove(sub.client_id)"
                                        >
                                            <q-tooltip>Remove</q-tooltip>
                                        </BaseButton>
                                    </div>
                                </template>
                            </div>
                        </li>
                    </ol>

                    <!-- Owner ask: once a step has one sub-step, adding the
                         next shouldn't mean hunting for the ⤵ icon again.
                         Only after the first — before that, the icon in the
                         action row is the (single) way in. -->
                    <BaseButton
                        v-if="editing && subStepsOf(step).length > 0"
                        variant="subtle"
                        dense
                        class="rsm__addsub"
                        :icon="ICONS.add"
                        label="Add sub-step"
                        @click="addSubStep(step.client_id)"
                    />
                </div>
            </li>
        </ol>

        <p v-else-if="!editing" class="rsm__empty">
            No steps yet — tap Edit to add them.
        </p>
        <p v-else class="rsm__empty">
            No steps yet. Add one to link ingredients and tools to it and to get
            per-step cook mode — or switch the step style to free text.
        </p>

        <BaseButton
            v-if="editing"
            variant="subtle"
            class="rsm__add"
            :icon="ICONS.add"
            label="Add step"
            @click="addTopStep"
        />

        <RecipeStepLinksDialog
            v-model="linksOpen"
            :step-name="linksName"
            :links="linksDraft"
            :can-set-section="linksCanSetSection"
            :ingredient-options="ingredientOptions"
            :tool-options="toolOptions"
            :section-options="sectionOptions"
            @save="onLinksSave"
        />
    </div>
</template>

<script setup lang="ts">
    import { computed, ref } from 'vue';

    import BaseButton from 'src/components/BaseButton.vue';
    import RecipeStepLinksDialog from 'src/components/recipes/RecipeStepLinksDialog.vue';
    import { ICONS } from 'src/style/icons';
    import { useDragDropList } from 'src/composables/useDragDropList';
    import type {
        EditableStep,
        IngredientOption,
        SectionOption,
        StepLinks,
        ToolOption,
    } from 'src/components/recipes/recipeStepEditorTypes';

    const props = defineProps<{
        steps: EditableStep[];
        editing: boolean;
        ingredientOptions: IngredientOption[];
        toolOptions: ToolOption[];
        sectionOptions: SectionOption[];
        /** The step the reader tapped, if any — lights its ingredients. */
        selectedStepId: string | null;
        /** Steps that use the ingredient the reader tapped on the rail. The
         *  page owns the mapping; this component only paints it. */
        highlightedStepIds: string[];
    }>();

    const emit = defineEmits<{
        (e: 'update:steps', value: EditableStep[]): void;
        (e: 'update:selectedStepId', value: string | null): void;
    }>();

    function newClientId(): string {
        if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
            return crypto.randomUUID();
        }
        return `s${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`;
    }

    const topLevelSteps = computed(() =>
        props.steps.filter((s) => s.parent_client_id === null).sort((a, b) => a.sequence - b.sequence));

    function subStepsOf(step: EditableStep): EditableStep[] {
        return props.steps
            .filter((s) => s.parent_client_id === step.client_id)
            .sort((a, b) => a.sequence - b.sequence);
    }

    // ── Highlight ───────────────────────────────────────────────────────
    const highlighted = computed(() => new Set(props.highlightedStepIds));
    function isLit(clientId: string): boolean {
        return props.selectedStepId === clientId || highlighted.value.has(clientId);
    }
    /** Tapping the selected step again clears it — a highlight you can't turn
     *  off is a highlight you're stuck with on a phone, which is the only
     *  place the owner asked for this. */
    function onPick(clientId: string) {
        emit('update:selectedStepId', props.selectedStepId === clientId ? null : clientId);
    }

    // ── Mutations ───────────────────────────────────────────────────────
    function patch(step: EditableStep, partial: Partial<EditableStep>) {
        emit(
            'update:steps',
            props.steps.map((s) => (s.client_id === step.client_id ? { ...s, ...partial } : s)),
        );
    }

    /** `null` means "no hint"; `''` means "a hint the user is about to type",
     *  which is what renders the field. Same two-state trick the old row used,
     *  minus the extra `showHint` ref that could disagree with the data. */
    function toggleHint(step: EditableStep) {
        patch(step, { hint: step.hint === null ? '' : null });
    }

    /** Owner feedback 2026-09-01: *"for structured I feel a tickable box option
     *  should be added"* — cook mode used to guess a step's timer by running a
     *  regex over its text. A structured step is a row, so the fact gets
     *  recorded rather than inferred. Same `null` / value two-state the hint
     *  uses; the default of 5 is a starting number to edit, not a claim. */
    const DEFAULT_TIMER_MINUTES = 5;
    function toggleTimer(step: EditableStep) {
        patch(step, {
            timer_minutes: step.timer_minutes === null ? DEFAULT_TIMER_MINUTES : null,
        });
    }

    /** q-input hands back a string (or null when cleared). Clamp to the same
     *  1..1440 window the server validates so the field can't submit a value
     *  the API will reject. */
    function toMinutes(raw: string | number | null): number | null {
        const n = Math.floor(Number(raw));
        if (!Number.isFinite(n) || n < 1) return 1;
        return Math.min(n, 1440);
    }

    /** "20 min" / "3 hr" / "1 hr 30 min" — a three-hour ragù reads badly as
     *  "180 min". */
    function timerLabel(step: EditableStep): string {
        const total = step.timer_minutes ?? 0;
        const hours = Math.floor(total / 60);
        const minutes = total % 60;
        if (hours === 0) return `${minutes} min`;
        if (minutes === 0) return `${hours} hr`;
        return `${hours} hr ${minutes} min`;
    }

    function linkCount(step: EditableStep): number {
        return step.ingredient_client_ids.length + step.tool_ids.length;
    }

    function addTopStep() {
        emit('update:steps', [...props.steps, {
            client_id: newClientId(),
            parent_client_id: null,
            sequence: topLevelSteps.value.length,
            text: '',
            hint: null,
            ingredient_client_ids: [],
            tool_ids: [],
            section_client_id: null,
            timer_minutes: null,
        }]);
    }

    function addSubStep(parentId: string) {
        const siblings = props.steps.filter((s) => s.parent_client_id === parentId);
        emit('update:steps', [...props.steps, {
            client_id: newClientId(),
            parent_client_id: parentId,
            sequence: siblings.length,
            text: '',
            hint: null,
            ingredient_client_ids: [],
            tool_ids: [],
            // Sub-steps inherit their parent's section; the server flattens
            // cook mode by the top-level row's `section_id`.
            section_client_id: null,
            timer_minutes: null,
        }]);
    }

    function remove(clientId: string) {
        emit('update:steps', repackSequences(props.steps.filter(
            (s) => s.client_id !== clientId && s.parent_client_id !== clientId,
        )));
        if (props.selectedStepId === clientId) emit('update:selectedStepId', null);
    }

    function move(step: EditableStep, delta: -1 | 1) {
        const siblings = props.steps
            .filter((s) => s.parent_client_id === step.parent_client_id)
            .sort((a, b) => a.sequence - b.sequence);
        const ids = siblings.map((s) => s.client_id);
        const from = ids.indexOf(step.client_id);
        const to = from + delta;
        if (from < 0 || to < 0 || to >= ids.length) return;
        ids.splice(from, 1);
        ids.splice(to, 0, step.client_id);
        applySiblingOrder(ids);
    }

    function applySiblingOrder(orderedIds: string[]) {
        const seqById = new Map(orderedIds.map((id, i) => [id, i]));
        emit('update:steps', repackSequences(props.steps.map((s) =>
            seqById.has(s.client_id) ? { ...s, sequence: seqById.get(s.client_id)! } : s)));
    }

    /** Sibling `sequence` values stay 0..N-1 so a removal or a move can't
     *  leave a gap that mis-renders after a round-trip through the server. */
    function repackSequences(steps: EditableStep[]): EditableStep[] {
        const byParent = new Map<string | null, EditableStep[]>();
        for (const s of steps) {
            const bucket = byParent.get(s.parent_client_id) ?? [];
            bucket.push(s);
            byParent.set(s.parent_client_id, bucket);
        }
        const out: EditableStep[] = [];
        for (const [, bucket] of byParent) {
            bucket.sort((a, b) => a.sequence - b.sequence);
            bucket.forEach((s, i) => out.push({ ...s, sequence: i }));
        }
        return out;
    }

    // ── Drag reorder (R-022) — siblings only, pointer devices only ──────
    const dnd = useDragDropList<EditableStep>({
        mime: 'application/x-dora-recipe-step',
        getId: (s) => s.client_id,
        canDropOn: (source, target) => source.parent_client_id === target.parent_client_id,
        onDrop: ({ id: sourceId, item: source }, { id: targetId }) => {
            const ids = props.steps
                .filter((s) => s.parent_client_id === source.parent_client_id)
                .sort((a, b) => a.sequence - b.sequence)
                .map((s) => s.client_id);
            const from = ids.indexOf(sourceId);
            const to = ids.indexOf(targetId);
            if (from < 0 || to < 0) return;
            ids.splice(from, 1);
            ids.splice(to, 0, sourceId);
            applySiblingOrder(ids);
        },
    });

    // ── Links dialog ────────────────────────────────────────────────────
    const linksOpen = ref(false);
    const linksFor = ref<string | null>(null);
    const linksName = ref('');
    const linksCanSetSection = ref(true);
    const linksDraft = ref<StepLinks | null>(null);

    function openLinks(step: EditableStep, name: string, canSetSection: boolean) {
        linksFor.value = step.client_id;
        linksName.value = name;
        linksCanSetSection.value = canSetSection;
        linksDraft.value = {
            ingredient_client_ids: [...step.ingredient_client_ids],
            tool_ids: [...step.tool_ids],
            section_client_id: step.section_client_id,
        };
        linksOpen.value = true;
    }

    function onLinksSave(links: StepLinks) {
        const target = props.steps.find((s) => s.client_id === linksFor.value);
        if (!target) return;
        patch(target, links);
    }
</script>

<style scoped lang="scss">
    /* The numbering geometry, named once because three things depend on it:
       the bullet, the content column, and the sub-step rule that has to run
       through the bullet's centre (owner ask 2026-08-27). */
    .rsm {
        --rsm-num: 34px;
        --rsm-gap: var(--space-4, 16px);
        --rsm-sub-num: 24px;
    }

    .rsm__steps,
    .rsm__substeps {
        list-style: none;
        margin: 0;
        padding: 0;
    }
    .rsm__steps {
        display: flex;
        flex-direction: column;
        gap: var(--space-4, 16px);
    }
    .rsm__step,
    .rsm__sub {
        display: grid;
        grid-template-columns: var(--rsm-num) 1fr;
        gap: var(--rsm-gap);
        align-items: start;
        padding: var(--space-2, 8px);
        border-radius: var(--radius-md, 6px);
    }
    .rsm__sub { grid-template-columns: var(--rsm-sub-num) 1fr; gap: var(--space-3, 12px); }
    /* Editing rows carry fields, so they need breathing room the read rows
       don't — and a ground of their own, so it's obvious which block is live. */
    .rsm__step--editing {
        background: var(--surface-component);
        border: 1px solid var(--border-default);
        padding: var(--space-3, 12px);
    }

    .rsm__num {
        display: flex; align-items: center; justify-content: center;
        width: var(--rsm-num); height: var(--rsm-num);
        border-radius: var(--radius-full, 50%);
        background: var(--brand-primary-soft);
        color: var(--brand-primary);
        font-weight: 700; font-variant-numeric: tabular-nums;
        user-select: none;
    }
    /* A sub-step is the same thing one level in, so it is the same bullet
       with the fill taken away rather than a second colour (owner: "the
       colouring choice between main steps and sub steps is a bit odd").
       Outline + secondary ink reads as quieter at any theme's brightness,
       which a soft fill does not. */
    .rsm__num--sub {
        width: var(--rsm-sub-num); height: var(--rsm-sub-num);
        background: transparent;
        border: 1.5px solid var(--border-strong);
        color: var(--text-secondary);
        font-size: 0.75rem;
    }
    .rsm__num--grab { cursor: grab; }
    .rsm__num--grab:active { cursor: grabbing; }

    .rsm__content { min-width: 0; }

    /* Read face. The old cap was 62ch, which left most of the method column
       empty on a desktop (owner: "serious lack of use of the horizontal
       space"); 78ch still keeps a readable measure on a wide monitor. */
    .rsm__text {
        appearance: none; background: none; border: 0;
        font: inherit; color: inherit; text-align: left;
        display: block; width: 100%;
        max-width: 78ch;
        margin: 0; padding: var(--space-1, 4px) var(--space-2, 8px);
        margin-left: calc(-1 * var(--space-2, 8px));
        line-height: 1.6;
        border-radius: var(--radius-sm, 4px);
        cursor: pointer;
        transition: background var(--motion-fast, 100ms) ease;
    }
    .rsm__pick:hover { background: var(--overlay-hover); }
    .rsm__pick:focus-visible { outline: 2px solid var(--focus-ring); outline-offset: 1px; }

    .rsm__step--lit { background: var(--brand-primary-soft); }
    .rsm__step--lit > .rsm__num {
        background: var(--brand-primary);
        color: var(--text-on-primary);
    }
    .rsm__step--lit > .rsm__num--sub {
        border-color: var(--brand-primary);
    }

    .rsm__hint {
        display: block;
        font-size: 0.8125rem;
        color: var(--text-muted);
        margin-top: var(--space-1, 4px);
    }
    .rsm__hintfield { margin-top: var(--space-2, 8px); }

    /* A declared timer, on the reading face. A tinted pill rather than more
       muted caption text: it is a fact about the step you act on, not a note
       about it, and the same glyph carries it in cook mode. */
    .rsm__timer {
        display: inline-flex;
        align-items: center;
        gap: var(--space-1, 4px);
        margin-top: var(--space-2, 8px);
        padding: 2px var(--space-2, 8px);
        border-radius: var(--radius-pill);
        border: 1px solid color-mix(in srgb, var(--brand-primary) 35%, transparent);
        background: color-mix(in srgb, var(--brand-primary) 12%, transparent);
        color: var(--text-primary);
        font-size: 0.8125rem;
        font-variant-numeric: tabular-nums;
    }
    .rsm__timerfield {
        margin-top: var(--space-2, 8px);
        max-width: 12rem;
    }

    .rsm__acts {
        display: flex; align-items: center; gap: var(--space-1, 4px);
        margin-top: var(--space-2, 8px);
        padding-top: var(--space-1, 4px);
        border-top: 1px solid var(--divider);
    }

    /* The rule down the sub-steps runs through the *centre* of the parent's
       numeral rather than starting at the content column (owner ask). The
       content column begins at `num + gap`; the numeral's centre is at
       `num / 2`; a 2px border wants its left edge 1px before that. */
    .rsm__substeps {
        margin: var(--space-3, 12px) 0 0;
        margin-left: calc((var(--rsm-num) / 2) - var(--rsm-num) - var(--rsm-gap) - 1px);
        padding-left: calc(var(--rsm-num) - (var(--rsm-num) / 2) + var(--rsm-gap) + var(--space-3, 12px));
        border-left: 2px solid var(--border-default);
        display: flex; flex-direction: column;
        gap: var(--space-2, 8px);
    }
    .rsm__sub { padding: var(--space-1, 4px) var(--space-2, 8px); }
    .rsm__sub .rsm__text { font-size: 0.9375rem; line-height: 1.55; }
    .rsm__addsub { margin-top: var(--space-2, 8px); }
    .rsm__add { margin-top: var(--space-3, 12px); width: 100%; }
    .rsm__empty { color: var(--text-muted); font-size: 0.875rem; margin: 0; }

    /* A grip you can't aim at with a thumb is noise; ↑/↓ are the phone's
       reorder affordance, as on every other list in the app. */
    @media (max-width: 767px) {
        .rsm__num--grab { cursor: default; }
    }
</style>
