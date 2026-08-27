<template>
    <BaseDialog
        v-model="open"
        :title="row ? 'Edit ingredient' : 'Ingredient'"
        closable
        card-style="min-width: 340px; max-width: 520px"
    >
        <q-card-section v-if="draft" class="column q-gutter-md">
            <!-- ── What it is ──────────────────────────────────────────────
                 One picker covers all three anchors an ingredient can have:
                 an existing pantry item, a brand-new one created here, or
                 free text with no pantry link (FU-506). The server's
                 `recipe_ingredient_anchor` CHECK wants at least one of
                 `stock_item_id` / `raw_text`, which is what `anchorError`
                 enforces before Done can commit. -->
            <div>
                <!-- `hide-selected` + `fill-input` is the standard Quasar
                     shape for a single-select typeahead, and its absence was
                     the "apple apple" bug (owner, 2026-08-27): the selected
                     label rendered *beside* the text still sitting in the
                     input, so creating "apple" from typed text read back as
                     the item twice. -->
                <q-select
                    ref="itemSelect"
                    v-model="draft.stock_item_id"
                    dense
                    outlined
                    clearable
                    use-input
                    fill-input
                    hide-selected
                    input-debounce="150"
                    autofocus
                    :options="itemOptions"
                    option-value="value"
                    option-label="label"
                    emit-value
                    map-options
                    :label="isFreeText ? 'Free-text ingredient' : 'Pantry item'"
                    :error="showAnchorError && !!anchorError"
                    :error-message="anchorError ?? undefined"
                    @filter="onItemFilter"
                >
                    <!-- Quasar renders `no-option` *instead of* the whole option
                         list — `before-options` and `after-options` included
                         (QSelect `getAllOptions`). Typing a brand-new ingredient
                         matches nothing, which is precisely when the free-text
                         action is needed, so it has to be offered from both
                         slots or it is unreachable exactly when it matters. -->
                    <template #no-option>
                        <q-item v-if="canUseTyped" clickable :disable="creating" @click="onUseTyped">
                            <q-item-section avatar>
                                <q-icon :name="ICONS.add" color="primary" />
                            </q-item-section>
                            <q-item-section class="text-primary">
                                Use "{{ typed.trim() }}"
                            </q-item-section>
                        </q-item>
                        <q-item v-else>
                            <q-item-section class="dora-text-muted">
                                Type to search your pantry.
                            </q-item-section>
                        </q-item>
                    </template>
                    <template v-if="canUseTyped" #after-options>
                        <q-item clickable :disable="creating" @click="onUseTyped">
                            <q-item-section avatar>
                                <q-icon :name="ICONS.add" color="primary" />
                            </q-item-section>
                            <q-item-section class="text-primary">
                                Use "{{ typed.trim() }}"
                            </q-item-section>
                        </q-item>
                    </template>
                </q-select>

                <div v-if="isFreeText" class="row items-center q-gutter-xs q-mt-xs">
                    <q-icon :name="ICONS.edit" size="14px" class="dora-text-muted" />
                    <span class="text-caption dora-text-secondary">
                        “{{ draft.raw_text }}” — free text, so Dora can't tell whether
                        you have it.
                    </span>
                    <BaseButton
                        variant="subtle"
                        dense
                        label="Clear"
                        @click="draft.raw_text = null"
                    />
                </div>
            </div>

            <!-- ── How much ────────────────────────────────────────────── -->
            <div class="row q-gutter-sm">
                <q-input
                    v-model.number="draft.quantity"
                    dense
                    outlined
                    type="number"
                    min="0"
                    step="any"
                    label="Quantity"
                    style="max-width: 120px"
                    hide-bottom-space
                />
                <!-- The same canonical vocabulary the substitute-ratio and
                     price widgets use, rather than this page's own free-text
                     box (R-001). Closed list, no `new-value-mode`: the owner's
                     2026-08-26 call, and the table already carries the words
                     the free-text escape existed for ("pinch", "dash",
                     "stick"). `use-input` stays — it's the typeahead over ~22
                     options and their aliases, not an escape hatch. -->
                <BaseSelect
                    v-model="draft.unit"
                    label="Unit"
                    class="col"
                    style="max-width: 160px"
                    :options="unitOptions"
                    use-input
                    fill-input
                    hide-selected
                    clearable
                    input-debounce="0"
                    @filter="onUnitFilter"
                />
            </div>

            <!-- ── Which group ─────────────────────────────────────────────
                 The only place an ingredient can be moved between sections.
                 Without it a section can be created and never filled, which
                 is what the redesign shipped with. -->
            <BaseSelect
                v-if="sections.length > 0"
                v-model="draft.section_client_id"
                label="Section"
                :options="sectionOptions"
                emit-value
                map-options
                clearable
                hint="Leave empty to keep it in the main list."
            />

            <!-- ── Qualifiers ──────────────────────────────────────────── -->
            <!-- One label, both states: a toggle whose text changes with it
                 makes you read the sentence to work out which way it's set. -->
            <q-toggle v-model="draft.is_optional" label="Optional — skip it and still cook" />

            <q-input
                v-model="draft.notes"
                dense
                outlined
                clearable
                autogrow
                type="textarea"
                maxlength="255"
                label="Note"
                placeholder="finely diced, room temperature, to taste…"
            />
        </q-card-section>

        <template #actions>
            <BaseButton variant="ghost" label="Cancel" @click="onCancel" />
            <!-- Not disabled on `anchorError`: a disabled button with a red
                 field beside it is the dialog telling you off for opening it.
                 It asks when you actually try to commit instead. -->
            <BaseButton
                variant="primary"
                label="Done"
                @click="onDone"
            />
        </template>
    </BaseDialog>
</template>

<script lang="ts" setup>
    /**
     * One ingredient row's full editor.
     *
     * The recipe page edits the *fast* things inline (quantity, and the item
     * itself) and everything an ingredient can also carry — free-text anchor,
     * section, optional flag, note — in here. Those four were all present in
     * the data model and unreachable from the redesigned page; this is where
     * they live rather than four more popovers on an already-busy row.
     *
     * Edits a **copy**. Nothing reaches the recipe form until Done, so Cancel
     * is a real cancel and the page's dirty flag isn't tripped by a dialog the
     * user backed out of.
     */
    import { computed, ref, watch } from 'vue';
    import { QSelect, useQuasar } from 'quasar';
    import { storeToRefs } from 'pinia';

    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import BaseSelect from 'src/components/BaseSelect.vue';
    import { ICONS } from 'src/style/icons';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { useUnitOptions } from 'src/composables/useUnitOptions';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import type {
        IngredientForm,
        IngredientPatch,
        SectionForm,
    } from 'src/composables/useRecipeEditor';

    const props = defineProps<{
        modelValue: boolean;
        row: IngredientForm | null;
        sections: SectionForm[];
    }>();

    const emit = defineEmits<{
        'update:modelValue': [value: boolean];
        save: [patch: IngredientPatch];
        /** Backed out of a row that never got an anchor. The page drops it —
         *  otherwise "add ingredient, change your mind" leaves a blank row
         *  behind that then blocks the save (owner: adding an ingredient
         *  "is not fluid enough", 2026-08-27). */
        cancel: [];
    }>();

    const $q = useQuasar();
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);

    const open = computed({
        get: () => props.modelValue,
        set: (v: boolean) => emit('update:modelValue', v),
    });

    const draft = ref<IngredientPatch | null>(null);
    const typed = ref('');
    const creating = ref(false);
    const itemSelect = ref<QSelect | null>(null);
    /** The anchor rule is real, but a *fresh* row hasn't broken it yet — it
     *  simply hasn't been filled in. Showing the red the instant the dialog
     *  opens is the dialog complaining about its own empty state, which is
     *  what the owner flagged. It arms on the first attempt to commit. */
    const showAnchorError = ref(false);
    // An ingredient is measured by volume, mass or count — never in kJ or cm,
    // which the unfiltered table also carries. Spelled out rather than reusing
    // the table's `PRICE_DIMENSIONS`: same three today, but that constant means
    // "what a price observation may be expressed in" and shouldn't drift by
    // proxy.
    // The second argument keeps this row's saved unit offered even when the
    // install's measurement system excludes it — an imported US recipe on a
    // metric install must not have its `lb` silently dropped from its own
    // dropdown.
    const { unitOptions, onUnitFilter } = useUnitOptions(
        ['volume', 'mass', 'count'],
        () => draft.value?.unit,
    );

    // Re-seed the draft whenever the dialog opens on a row, so a second visit
    // never shows the previous row's values for a frame.
    watch(
        () => [props.modelValue, props.row] as const,
        ([isOpen, row]) => {
            if (!isOpen || !row) return;
            typed.value = '';
            showAnchorError.value = false;
            draft.value = {
                stock_item_id: row.stock_item_id ?? null,
                raw_text: row.raw_text ?? null,
                quantity: row.quantity ?? null,
                unit: row.unit ?? null,
                notes: row.notes ?? null,
                section_client_id: row.section_client_id ?? null,
                is_optional: row.is_optional ?? false,
            };
        },
        { immediate: true },
    );

    const isFreeText = computed(() => !!draft.value?.raw_text && !draft.value.stock_item_id);

    /** Mirrors the server's `recipe_ingredient_anchor` CHECK: a row needs an
     *  item or some text. Blocking Done here is what stops a half-built row
     *  reaching the form and jamming the page's save. */
    const anchorError = computed(() => {
        const d = draft.value;
        if (!d) return null;
        if (!d.stock_item_id && !(d.raw_text ?? '').trim()) {
            return 'Pick a pantry item, or use your text as a free-text ingredient.';
        }
        return null;
    });

    const itemOptions = computed(() => {
        const q = typed.value.trim().toLowerCase();
        const matches = stockItems.value
            .filter((s) => !q || s.name.toLowerCase().includes(q))
            .slice(0, 60)
            .map((s) => ({ label: s.name, value: s.stock_item_id }));
        // `map-options` can only render a label for an option it can see, and
        // the list is capped at 60 — so a selection that filtered out (or a
        // pantry item just created here) would display as a bare UUID. Pin it
        // to the front rather than raising the cap.
        const selected = draft.value?.stock_item_id;
        if (selected && !matches.some((o) => o.value === selected)) {
            const hit = stockItems.value.find((s) => s.stock_item_id === selected);
            if (hit) matches.unshift({ label: hit.name, value: hit.stock_item_id });
        }
        return matches;
    });

    /** Offer "Use <text>" only when the text is something other than what is
     *  already selected — with `fill-input` the box carries the selected
     *  item's own name, and offering to re-create it reads as a bug. */
    const canUseTyped = computed(() => {
        const text = typed.value.trim();
        if (text.length === 0) return false;
        const selected = draft.value?.stock_item_id;
        if (!selected) return true;
        const name = stockItems.value.find((s) => s.stock_item_id === selected)?.name ?? '';
        return name.trim().toLowerCase() !== text.toLowerCase();
    });

    const sectionOptions = computed(() =>
        props.sections.map((s) => ({ label: s.name || 'Untitled section', value: s.client_id })));

    function onItemFilter(value: string, update: (cb: () => void) => void) {
        update(() => { typed.value = value; });
    }

    /** Typed something the pantry doesn't have. One action, then one question:
     *  should this be a tracked pantry item, or just words in the list? Asking
     *  is what makes the free-text path discoverable — the old two-option menu
     *  put the choice in a dropdown the user had to read to know it existed
     *  (and, worse, never rendered when nothing matched). Persistent, because
     *  a dismissed dialog would leave the typed text nowhere. */
    function onUseTyped() {
        const text = typed.value.trim();
        if (!text || !draft.value) return;
        $q.dialog({
            title: `Add "${text}" to your pantry?`,
            message: 'Tracked items let Dora tell you whether you have this and put it on a shopping list. '
                + 'Free text just reads as part of the recipe.',
            persistent: true,
            ok: { label: 'Add to pantry', color: 'primary', noCaps: true },
            cancel: { label: 'Keep as free text', flat: true, noCaps: true },
        })
            .onOk(() => { void createItem(text); })
            .onCancel(() => {
                if (!draft.value) return;
                draft.value.stock_item_id = null;
                draft.value.raw_text = text;
                typed.value = '';
            });
    }

    async function createItem(name: string) {
        if (!name || !draft.value) return;
        // Default to the most-stocked level: putting an item straight into a
        // recipe implies you have it, and the alternative is a row that reads
        // "Missing" the instant it's created.
        const wellStocked = stockLevels.value[0];
        if (!wellStocked) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'No stock levels configured — cannot create a pantry item.',
            });
            return;
        }
        creating.value = true;
        try {
            await stockItemStore.createStockItemAsync({
                name,
                stock_level_id: wellStocked.stock_level_id,
                stock_location_id: null,
            });
            const created = stockItems.value.find((s) => s.name === name);
            if (created) {
                draft.value.stock_item_id = created.stock_item_id;
                draft.value.raw_text = null;
                typed.value = '';
                showAnchorError.value = false;
                // Creating the item *is* the choice — leaving the menu open on
                // the list you just added to, waiting for a second, deliberate
                // pick, was the other half of the owner's report. Fill the box
                // with the new name and close it.
                itemSelect.value?.updateInputValue(created.name, true);
                itemSelect.value?.hidePopup();
                // The item is persisted whether or not the recipe save goes
                // through, so say so rather than letting it appear unannounced
                // on the Stock overview.
                $q.notify({
                    type: 'positive',
                    position: 'bottom-right',
                    message: `Added "${name}" to your pantry.`,
                });
            }
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not create the pantry item.',
                caption: toastCaption(err),
            });
        } finally {
            creating.value = false;
        }
    }

    /** Cancelling a row that still has no anchor removes it; cancelling an
     *  edit of a real row just closes. */
    function onCancel() {
        const row = props.row;
        open.value = false;
        if (row && !row.stock_item_id && !(row.raw_text ?? '').trim()) emit('cancel');
    }

    function onDone() {
        const d = draft.value;
        if (!d) return;
        if (anchorError.value) {
            showAnchorError.value = true;
            return;
        }
        const text = (d.raw_text ?? '').trim();
        emit('save', {
            ...d,
            // Keep `raw_text` as the readable original for a linked row (a
            // bulk-link leaves both set, which the API explicitly allows),
            // but never store an empty string.
            raw_text: text.length > 0 ? text : null,
            unit: (d.unit ?? '').trim() || null,
            notes: (d.notes ?? '').trim() || null,
        });
        open.value = false;
    }
</script>
