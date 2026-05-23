<template>
    <q-dialog :model-value="modelValue" @update:model-value="onDialogUpdate" @hide="resetForm">
        <q-card style="width: 600px; max-width: 95vw">
            <q-card-section>
                <div class="text-h6">Add a stock item</div>
            </q-card-section>
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
                                        :color="getStockLevelColour(scope.opt.name)"
                                        size="16px"
                                    />
                                </q-item-section>
                                <q-item-section>{{ scope.opt.name }}</q-item-section>
                            </q-item>
                        </template>
                    </q-select>
                    <q-select
                        v-model="form.stock_location_id"
                        :options="stockLocations"
                        option-label="name"
                        option-value="stock_location_id"
                        emit-value
                        map-options
                        clearable
                        outlined
                        label="Location (optional)"
                        :error="!!fieldErrors.stock_location_id"
                        :error-message="fieldErrors.stock_location_id"
                        @update:model-value="clearField('stock_location_id')"
                    />

                    <q-card-actions align="right">
                        <q-btn flat label="Cancel" v-close-popup />
                        <q-btn type="submit" color="primary" label="Add" :loading="saving" />
                    </q-card-actions>
                </q-form>
            </q-card-section>
        </q-card>
    </q-dialog>
</template>

<script setup lang="ts">
    import { storeToRefs } from 'pinia';
    import FormErrorSummary from 'src/components/FormErrorSummary.vue';
    import { getStockLevelColour } from 'src/helpers/stockLevelLogic';
    import type { StockLevel } from 'src/models/stockLevel';
    import type { CreateStockItemCommand } from 'src/services/api/stockItemApiService';
    import { extractFieldErrors } from 'src/services/errorHandling/apiErrorHandler';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { useStockLocationStore } from 'src/stores/stockLocationStore';
    import { reactive, ref, watch } from 'vue';

    const props = defineProps<{ modelValue: boolean }>();
    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
        (e: 'created'): void;
    }>();

    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const stockLocationStore = useStockLocationStore();
    const { stockLevels } = storeToRefs(stockLevelStore);
    const { stockLocations } = storeToRefs(stockLocationStore);

    const defaultForm = (): CreateStockItemCommand => ({
        name: '',
        stock_level_id: stockLevels.value[0]?.stock_level_id ?? '',
        stock_location_id: null,
    });

    const form: CreateStockItemCommand = reactive(defaultForm());
    const saving = ref(false);
    const generalError = ref<string | null>(null);
    const fieldErrors = ref<Record<string, string>>({});

    function resetForm() {
        Object.assign(form, defaultForm());
        generalError.value = null;
        fieldErrors.value = {};
    }

    function clearField(field: string) {
        if (fieldErrors.value[field]) {
            const next = { ...fieldErrors.value };
            delete next[field];
            fieldErrors.value = next;
        }
    }

    // Seed the form whenever the dialog opens — picks up newly-added stock
    // levels since last close.
    watch(
        () => props.modelValue,
        (open) => {
            if (open) resetForm();
        },
    );

    function onDialogUpdate(value: boolean) {
        emit('update:modelValue', value);
    }

    async function onSubmit() {
        saving.value = true;
        generalError.value = null;
        fieldErrors.value = {};
        try {
            await stockItemStore.createStockItemAsync({
                name: form.name,
                stock_level_id: form.stock_level_id,
                stock_location_id: form.stock_location_id,
            });
            emit('created');
            emit('update:modelValue', false);
        } catch (err) {
            const extracted = extractFieldErrors(err);
            fieldErrors.value = extracted.fieldErrors;
            generalError.value =
                extracted.generalError ?? 'Could not add the item. Please review the form.';
        } finally {
            saving.value = false;
        }
    }
</script>
