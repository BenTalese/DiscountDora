<template>
    <BaseDialog
        :model-value="modelValue"
        :title="dialogTitle"
        closable
        card-style="width: 600px; max-width: 95vw"
        @update:model-value="onDialogUpdate"
        @cancel="resetForm"
    >
            <q-card-section>
                <!-- 2026-08-21 feedback: "location input is too wide on the
                     right (possibly same issue we faced on the stock item
                     details page?)". Same issue, same cause. This was
                     `q-gutter-md`, which spaces children by putting a -16px
                     margin on the container and +16px on each child — so the
                     container's content box is 16px WIDER than the card. Every
                     child that sizes to content is fine with that; the location
                     picker is the one that doesn't, because a `use-input`
                     QSelect carries `width: 100%` (see the `.q-select--with-input`
                     rule in app.scss), and 100% of the over-wide container
                     overhangs the card by exactly one gutter on the right.
                     A flex column with `gap` spaces the same way without
                     negative margins, so 100% means 100% of the card. -->
                <q-form @submit.prevent="onSubmit" class="create-stock-item__fields">
                    <FormErrorSummary :message="generalError" />

                    <!-- barcode-to-add suggestion banner. Shown when
                         the dialog opens from a scan flow with either an OFF
                         suggestion (source='off') or an EAN-only prefill
                         (unknown barcode, OFF miss or product_no_link). Uses
                         --surface-sunken for consistency with the FU-012
                         sub-bar treatment. -->
                    <div v-if="prefill?.barcode" class="dora-suggestion-banner">
                        <img
                            v-if="prefill.imageUrl"
                            :src="prefill.imageUrl"
                            alt=""
                            class="dora-suggestion-image"
                        />
                        <div class="col">
                            <div class="text-caption dora-text-muted">
                                <template v-if="prefill.source === 'off'">
                                    Suggested from <strong>Open Food Facts</strong> — review and confirm.
                                </template>
                                <template v-else-if="prefill.source === 'product_no_link'">
                                    This barcode matches a known product. Add a stock item to link it.
                                </template>
                                <template v-else>
                                    Adding a stock item for a scanned barcode.
                                </template>
                            </div>
                            <div class="text-caption q-mt-xs">
                                Barcode <code>{{ prefill.barcode }}</code>
                                <span v-if="prefill.brand"> · {{ prefill.brand }}</span>
                                <span v-if="prefill.quantity"> · {{ prefill.quantity }}</span>
                            </div>
                            <div v-if="prefill.categories" class="text-caption dora-text-muted q-mt-xs">
                                {{ prefill.categories }}
                            </div>
                        </div>
                    </div>

                    <q-input
                        v-model="form.name"
                        outlined
                        autofocus
                        label="Name"
                        :error="!!fieldErrors.name"
                        :error-message="fieldErrors.name"
                        @update:model-value="clearField('name')"
                        :rules="[(v: string) => (!!v && v.trim().length > 0) || 'Name is required']"
                    />
                    <q-select
                        v-model="form.stock_level_id"
                        :options="stockLevels"
                        :option-label="(o: StockLevel) => o.name"
                        :option-value="(o: StockLevel) => o.stock_level_id"
                        emit-value
                        map-options
                        outlined
                        label="Stock level"
                        :error="!!fieldErrors.stock_level_id"
                        :error-message="fieldErrors.stock_level_id"
                        @update:model-value="clearField('stock_level_id')"
                        :rules="[(v: string) => !!v || 'Pick a stock level']"
                    >
                        <!-- Feedback (stock overview): show the level
                             colour-dot on the *trigger* too, not just in
                             the dropdown list — keeps this picker
                             consistent with the detail-page picker. -->
                        <template #selected-item="scope">
                            <span class="row items-center no-wrap">
                                <StockLevelDot
                                    :sequence="selectedLevelSequence"
                                    dot-class="q-mr-sm"
                                />
                                {{ scope.opt.name }}
                            </span>
                        </template>
                        <template #option="scope">
                            <q-item v-bind="scope.itemProps">
                                <q-item-section avatar>
                                    <StockLevelDot :sequence="scope.opt.sequence" />
                                </q-item-section>
                                <q-item-section>{{ scope.opt.name }}</q-item-section>
                            </q-item>
                        </template>
                    </q-select>
                    <!-- Round-10: location picker mirrors the filter +
                         detail-page picker — path-labelled options walked
                         from the location tree, searchable on type,
                         clearable. The dialog hydrates the tree on open
                         so the picker is populated even if the parent
                         page hasn't loaded it yet. -->
                    <q-select
                        v-model="form.stock_location_id"
                        :options="locationOptions"
                        emit-value
                        map-options
                        use-input
                        fill-input
                        hide-selected
                        input-debounce="200"
                        clearable
                        outlined
                        label="Location (optional)"
                        :error="!!fieldErrors.stock_location_id"
                        :error-message="fieldErrors.stock_location_id"
                        @filter="filterLocations"
                        @update:model-value="clearField('stock_location_id')"
                    />

                    <!-- The create dialog only carries fields that are
                         permanent properties of the item. Expiry is a
                         per-batch fact that changes over the item's life,
                         so it lives on the detail page / stocktake, not
                         here. Stock group takes its place. -->
                    <q-select
                        v-model="form.stock_group_id"
                        :options="groupOptions"
                        emit-value
                        map-options
                        clearable
                        outlined
                        label="Stock group (optional)"
                        :error="!!fieldErrors.stock_group_id"
                        :error-message="fieldErrors.stock_group_id"
                        @update:model-value="clearField('stock_group_id')"
                    />

                    <div class="row items-center q-gutter-sm">
                        <q-toggle v-model="form.is_essential" label="Essential" />
                        <q-icon :name="ICONS.info_outline" size="16px" class="dora-text-secondary">
                            <!-- 2026-08-21, owner-approved copy. The old text
                                 ("shows up in 'essentials' auto-generate
                                 sources… different from auto-add…") explained
                                 the flag by naming two internal mechanisms and
                                 never mentioned the thing the user actually
                                 sees: an essential is what makes a row raise
                                 attention when it runs low (`stock_attention.py`,
                                 kind `essential_low`). D-014 — say what it does
                                 for you, not what it does in the code. Kept
                                 word-identical to the detail page's copy. -->
                            <q-tooltip max-width="320px">
                                Something you always want in the house. Dora
                                chases it up as soon as it runs low, instead of
                                waiting until it's gone.
                            </q-tooltip>
                        </q-icon>
                    </div>

                </q-form>
            </q-card-section>
            <template #actions>
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <BaseButton variant="primary" label="Add" :loading="saving" @click="onSubmit" />
            </template>
    </BaseDialog>
</template>

<script setup lang="ts">
    import { storeToRefs } from 'pinia';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import FormErrorSummary from 'src/components/FormErrorSummary.vue';
    import StockLevelDot from 'src/components/stock/StockLevelDot.vue';
    import type { LocationNode } from 'src/models/location';
    import type { StockLevel } from 'src/models/stockLevel';
    import type { CreateStockItemPrefill } from 'src/components/stock/createStockItemPrefill';
    import type { StockGroup } from 'src/models/stockGroup';
    import BarcodeApiService from 'src/services/api/barcodeApiService';
    import StockGroupApiService from 'src/services/api/stockGroupApiService';
    import type { CreateStockItemCommand } from 'src/services/api/stockItemApiService';
    import { useFormErrors } from 'src/composables/useFormErrors';
    import { useLocationStore } from 'src/stores/locationStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { useQuasar } from 'quasar';
    import { ICONS } from 'src/style/icons';
    import { computed, reactive, ref, watch } from 'vue';

    // Prefill type lives in a sibling `.ts` file so page callers
    // resolve it under ESLint's TS parser (which doesn't always trace
    // named exports across `.vue` boundaries).
    const props = defineProps<{
        modelValue: boolean;
        prefill?: CreateStockItemPrefill | null;
    }>();
    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
        (e: 'created'): void;
    }>();

    const $q = useQuasar();
    const barcodeApi = new BarcodeApiService();
    const stockGroupApi = new StockGroupApiService();

    const dialogTitle = computed(() =>
        props.prefill?.barcode ? 'Add a stock item from scan' : 'Add a stock item',
    );

    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const locationStore = useLocationStore();
    const { stockLevels } = storeToRefs(stockLevelStore);

    // Walk the location tree into path-labelled options — same shape as
    // the Stock Overview filter and the detail-page picker so the user
    // gets a single, consistent location-pick experience.
    type LocationOption = { label: string; value: string };
    const allLocationOptions = computed<LocationOption[]>(() => {
        const out: LocationOption[] = [];
        const walk = (nodes: LocationNode[], prefix: string) => {
            for (const n of nodes) {
                const path = prefix ? `${prefix} › ${n.name}` : n.name;
                out.push({ label: path, value: n.location_id });
                walk(n.children, path);
            }
        };
        walk(locationStore.tree, '');
        return out.sort((a, b) => a.label.localeCompare(b.label));
    });
    const locationOptions = ref<LocationOption[]>([]);
    watch(allLocationOptions, (v) => { locationOptions.value = v; }, { immediate: true });
    function filterLocations(val: string, update: (cb: () => void) => void) {
        update(() => {
            const needle = val.toLowerCase();
            locationOptions.value = needle
                ? allLocationOptions.value.filter((o) => o.label.toLowerCase().includes(needle))
                : allLocationOptions.value;
        });
    }

    // Stock groups — fetched straight from the API like the detail-page
    // picker does; there's no store for them and this dialog is the only
    // other consumer.
    const stockGroups = ref<StockGroup[]>([]);
    const groupOptions = computed(() =>
        stockGroups.value.map((g) => ({ label: g.name, value: g.stock_group_id })),
    );

    const defaultForm = (): CreateStockItemCommand => ({
        name: props.prefill?.name?.trim() || '',
        stock_level_id: stockLevels.value[0]?.stock_level_id ?? '',
        stock_location_id: null,
        stock_group_id: null,
        is_essential: false,
    });

    const form: CreateStockItemCommand = reactive(defaultForm());
    const saving = ref(false);
    // Sequence of the currently-picked level — drives the trigger dot.
    // q-select with `emit-value` only hands `#selected-item` the resolved
    // option object, but we still need to derive sequence here because
    // the form holds the id. Recomputed reactively so the dot updates
    // the instant the user picks a new level.
    const selectedLevelSequence = computed<number | null>(() => {
        const id = form.stock_level_id;
        if (!id) return null;
        const seq = stockLevels.value.find((l) => l.stock_level_id === id)?.sequence;
        return typeof seq === 'number' ? seq : null;
    });
    // R-001 form-error plumbing.
    const { fieldErrors, generalError, handleSaveError, reset: resetFormErrors } = useFormErrors();

    function resetForm() {
        Object.assign(form, defaultForm());
        resetFormErrors();
    }

    function clearField(field: string) {
        if (fieldErrors.value[field]) {
            const next = { ...fieldErrors.value };
            delete next[field];
            fieldErrors.value = next;
        }
    }

    // Seed the form whenever the dialog opens — picks up newly-added stock
    // levels since last close. Also ensure the location tree is loaded so
    // the picker is populated even if the parent page hasn't hydrated it
    // yet (round-10 fix: the dialog used to read from `stockLocations`
    // which a parent might never have loaded).
    watch(
        () => props.modelValue,
        (open) => {
            if (open) {
                resetForm();
                void locationStore.ensureLoadedAsync();
                void loadStockGroupsAsync();
            }
        },
    );

    async function loadStockGroupsAsync() {
        stockGroups.value = await stockGroupApi.getAllAsync();
    }

    function onDialogUpdate(value: boolean) {
        emit('update:modelValue', value);
    }

    async function onSubmit() {
        saving.value = true;
        resetFormErrors();
        try {
            const created = await stockItemStore.createStockItemAsync({
                name: form.name.trim(),
                stock_level_id: form.stock_level_id,
                stock_location_id: form.stock_location_id,
                stock_group_id: form.stock_group_id || null,
                is_essential: form.is_essential ?? false,
            });
            // if the dialog was opened from a scan flow with a
            // barcode prefill, register the EAN against the new stock
            // item so the next scan of the same code lands on this item
            // instead of re-triggering the add-flow. A conflict here (rare
            // race — another registration happened between lookup and
            // submit) is surfaced as a warning but doesn't undo the
            // create; the item exists, the user can add the barcode
            // manually if the race really matters.
            if (props.prefill?.barcode) {
                try {
                    await barcodeApi.registerAsync({
                        barcode: props.prefill.barcode,
                        stock_item_id: created.stock_item_id,
                    });
                } catch (regErr) {
                    $q.notify({
                        type: 'warning',
                        position: 'bottom-right',
                        message: 'Item added, but the barcode was already registered elsewhere.',
                        caption: regErr instanceof Error ? regErr.message : String(regErr),
                    });
                }
            }
            emit('created');
            emit('update:modelValue', false);
        } catch (err) {
            handleSaveError(err, 'Could not add the item. Please review the form.');
        } finally {
            saving.value = false;
        }
    }
</script>

<style scoped>
    /* Replaces `q-gutter-md` on the form — same 16px rhythm, but with `gap`
       instead of the gutter's negative container margin, which made the form
       16px wider than its card and pushed any `width: 100%` child (the
       location picker) off the right edge. */
    .create-stock-item__fields {
        display: flex;
        flex-direction: column;
        gap: var(--space-4, 16px);
    }

    /* P8-02 — scan-driven prefill banner. Uses the same sunken-well
       treatment as FU-012 filter sub-bars so the "this data came from
       elsewhere" affordance reads consistently across surfaces. */
    .dora-suggestion-banner {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 10px 12px;
        background: var(--surface-sunken);
        border-radius: 6px;
    }
    .dora-suggestion-image {
        width: 56px;
        height: 56px;
        object-fit: cover;
        border-radius: 4px;
        flex-shrink: 0;
        background: var(--surface-default);
    }
</style>
