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
                <q-select
                    v-model="draft.stock_item_id"
                    dense
                    outlined
                    clearable
                    use-input
                    input-debounce="150"
                    autofocus
                    :options="itemOptions"
                    option-value="value"
                    option-label="label"
                    emit-value
                    map-options
                    :label="isFreeText ? 'Free-text ingredient' : 'Pantry item'"
                    :error="!!anchorError"
                    :error-message="anchorError ?? undefined"
                    @filter="onItemFilter"
                >
                    <template #no-option>
                        <q-item>
                            <q-item-section class="dora-text-muted">
                                Type to search your pantry.
                            </q-item-section>
                        </q-item>
                    </template>
                    <template v-if="typed.length > 0" #after-options>
                        <q-item clickable :disable="creating" @click="onCreateItem">
                            <q-item-section avatar>
                                <q-icon :name="ICONS.add" color="primary" />
                            </q-item-section>
                            <q-item-section class="text-primary">
                                Create "{{ typed }}" in my pantry
                            </q-item-section>
                        </q-item>
                        <!-- FU-506 — free text keeps the ingredient readable
                             without pretending it's tracked. Cookability stays
                             unknown while any required row is unlinked, and the
                             row can be linked later from this same picker. -->
                        <q-item clickable @click="onUseFreeText">
                            <q-item-section avatar>
                                <q-icon :name="ICONS.edit" color="secondary" />
                            </q-item-section>
                            <q-item-section class="dora-text-secondary">
                                Use "{{ typed }}" as free text — not tracked in stock
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
                <q-input
                    v-model="draft.unit"
                    dense
                    outlined
                    clearable
                    label="Unit"
                    placeholder="g, ml, tbsp…"
                    style="max-width: 140px"
                    hide-bottom-space
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
            <q-toggle
                v-model="draft.is_optional"
                :label="draft.is_optional ? 'Optional — skip it and still cook' : 'Required'"
            />

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
            <BaseButton variant="ghost" label="Cancel" @click="open = false" />
            <BaseButton
                variant="primary"
                label="Done"
                :disable="!!anchorError"
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
    import { useQuasar } from 'quasar';
    import { storeToRefs } from 'pinia';

    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import BaseSelect from 'src/components/BaseSelect.vue';
    import { ICONS } from 'src/style/icons';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
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

    // Re-seed the draft whenever the dialog opens on a row, so a second visit
    // never shows the previous row's values for a frame.
    watch(
        () => [props.modelValue, props.row] as const,
        ([isOpen, row]) => {
            if (!isOpen || !row) return;
            typed.value = '';
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
        return stockItems.value
            .filter((s) => !q || s.name.toLowerCase().includes(q))
            .slice(0, 60)
            .map((s) => ({ label: s.name, value: s.stock_item_id }));
    });

    const sectionOptions = computed(() =>
        props.sections.map((s) => ({ label: s.name || 'Untitled section', value: s.client_id })));

    function onItemFilter(value: string, update: (cb: () => void) => void) {
        update(() => { typed.value = value; });
    }

    function onUseFreeText() {
        const text = typed.value.trim();
        if (!text || !draft.value) return;
        draft.value.stock_item_id = null;
        draft.value.raw_text = text;
        typed.value = '';
    }

    async function onCreateItem() {
        const name = typed.value.trim();
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

    function onDone() {
        const d = draft.value;
        if (!d || anchorError.value) return;
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
