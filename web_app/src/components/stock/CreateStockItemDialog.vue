<template>
    <BaseDialog
        :model-value="modelValue"
        title="Add a stock item"
        closable
        card-style="width: 600px; max-width: 95vw"
        @update:model-value="onDialogUpdate"
        @cancel="resetForm"
    >
            <q-card-section>
                <q-form @submit.prevent="onSubmit" class="q-gutter-md">
                    <FormErrorSummary :message="generalError" />

                    <q-input
                        v-model="form.name"
                        outlined
                        autofocus
                        label="Name"
                        :error="!!fieldErrors.name"
                        :error-message="fieldErrors.name"
                        @update:model-value="clearField('name')"
                        :rules="[(v: string) => (!!v && v.length > 0) || 'Name is required']"
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
                        <template #option="scope">
                            <q-item v-bind="scope.itemProps">
                                <q-item-section avatar>
                                    <q-avatar
                                        :color="colourForSequence(scope.opt.sequence) ?? undefined"
                                        :class="{ 'dora-bg-sunken': !colourForSequence(scope.opt.sequence) }"
                                        size="16px"
                                    />
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
    import { colourForSequence } from 'src/helpers/stockLevelLogic';
    import type { LocationNode } from 'src/models/location';
    import type { StockLevel } from 'src/models/stockLevel';
    import type { CreateStockItemCommand } from 'src/services/api/stockItemApiService';
    import { useFormErrors } from 'src/composables/useFormErrors';
    import { useLocationStore } from 'src/stores/locationStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { computed, reactive, ref, watch } from 'vue';

    const props = defineProps<{ modelValue: boolean }>();
    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
        (e: 'created'): void;
    }>();

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

    const defaultForm = (): CreateStockItemCommand => ({
        name: '',
        stock_level_id: stockLevels.value[0]?.stock_level_id ?? '',
        stock_location_id: null,
    });

    const form: CreateStockItemCommand = reactive(defaultForm());
    const saving = ref(false);
    // FU-099 — R-001 form-error plumbing.
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
                if (locationStore.tree.length === 0) {
                    void locationStore.refreshAsync();
                }
            }
        },
    );

    function onDialogUpdate(value: boolean) {
        emit('update:modelValue', value);
    }

    async function onSubmit() {
        saving.value = true;
        resetFormErrors();
        try {
            await stockItemStore.createStockItemAsync({
                name: form.name,
                stock_level_id: form.stock_level_id,
                stock_location_id: form.stock_location_id,
            });
            emit('created');
            emit('update:modelValue', false);
        } catch (err) {
            handleSaveError(err, 'Could not add the item. Please review the form.');
        } finally {
            saving.value = false;
        }
    }
</script>
