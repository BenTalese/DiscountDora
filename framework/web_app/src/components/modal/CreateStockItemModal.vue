<template>
    <q-dialog
        @hide="clearForm"
        v-model="isModalVisible"
    >
        <!-- TODO: Size of modal should be consistent? -->
        <!-- TODO: The default form looks a bit boring, maybe add a border? Modal background colour? -->
        <!-- TODO: Need some sort of UI feedback for success, currently it just clears the form -->
        <q-card
            class="q-pa-md"
            style="width: 700px; max-width: 80vw"
        >
            <p class="text-h4">Add a new stock item</p>
            <q-form
                class="q-gutter-md"
                @submit.prevent="handleSubmit(false)"
            >
                <q-input
                    :error-message="serverErrors.name"
                    :error="!!serverErrors.name"
                    :rules="nameInputRules"
                    autofocus
                    filled
                    for="nameInput"
                    label="Name"
                    v-model="formData.name"
                />

                <q-input
                    :error-message="serverErrors.days_until_stocktake_alert"
                    :error="!!serverErrors.days_until_stocktake_alert"
                    filled
                    hint="Alerts disabled if set to zero"
                    label="Days Until Stocktake Alert"
                    type="number"
                    v-model="formData.days_until_stocktake_alert"
                />

                <q-select
                    :error="!!serverErrors.stock_level_id"
                    :error-message="serverErrors.stock_level_id"
                    :option-label="getStockLevelName"
                    :option-value="getStockLevelID"
                    :options="stockLevelStore.stockLevels"
                    :rules="stockLevelSelectRules"
                    emit-value
                    label="Stock Level"
                    map-options
                    v-model="formData.stock_level_id"
                >
                    <template v-slot:option="scope">
                        <q-item v-bind="scope.itemProps">
                            <q-item-section avatar>
                                <q-avatar
                                    :color="getStockLevelColour(scope.opt.stock_level_id)"
                                    size="25px"
                                />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>
                                    {{ scope.opt.name }}
                                </q-item-label>
                            </q-item-section>
                        </q-item>
                    </template>
                </q-select>

                <!-- TODO: IMPLEMENT -->
                <q-select
                    :error="!!serverErrors.stock_group_id"
                    :error-message="serverErrors.stock_group_id"
                    label="Stock Group"
                    v-model="formData.stock_group_id"
                ></q-select>

                <!-- TODO: IMPLEMENT -->
                <q-select
                    :error="!!serverErrors.stock_location_id"
                    :error-message="serverErrors.stock_location_id"
                    label="Stock Location"
                    v-model="formData.stock_location_id"
                ></q-select>

                <FormErrorSummary :error-message="serverErrors.noKey" />

                <q-card-actions align="right">
                    <q-btn
                        @click="handleSubmit(false)"
                        type="submit"
                        align="right"
                        color="info"
                        label="Save & Continue"
                        size="lg"
                    />
                    <q-btn
                        @click="handleSubmit(true)"
                        type="submit"
                        align="right"
                        color="positive"
                        label="Save & Close"
                        size="lg"
                    />
                </q-card-actions>
            </q-form>
        </q-card>
    </q-dialog>
</template>

<script setup lang="ts">
    //#region Imports
    import type { AxiosError } from 'axios';
    import { storeToRefs } from 'pinia';
    import type { ValidationRule } from 'quasar';
    import { QInput } from 'quasar';
    import FormErrorSummary from 'src/components/FormErrorSummary.vue';
    import { useModalState } from 'src/composables/modalState';
    import { getStockLevelColour } from 'src/helpers/stockLevelLogic';
    import type { StockLevel } from 'src/models/stockLevel';
    import type { CreateStockItemCommand } from 'src/services/api/stockItemApiService';
    import { mapApiErrorsToForm } from 'src/services/errorHandling/apiErrorHandler';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { reactive, ref } from 'vue';
    //#endregion Imports

    //#region Store Initialization
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const { createStockItemAsync } = stockItemStore;
    const { stockLevels } = storeToRefs(stockLevelStore);
    //#endregion Store Initialization

    //#region Props and Events
    const props = defineProps<{ modelValue: boolean }>();
    const emit = defineEmits(['update:modelValue']);
    const { isModalVisible } = useModalState(props, emit);
    //#endregion Props and Events

    //#region State
    const defaultFormState = {
        days_until_stocktake_alert: 0,
        name: '',
        stock_group_id: null,
        stock_level_id: stockLevels.value[0]!.stock_level_id,
        stock_location_id: null
    };

    const formData: CreateStockItemCommand = reactive({
        ...defaultFormState
    });

    const serverErrors = ref<Record<string, string>>({
        days_until_stocktake_alert: '',
        name: '',
        noKey: '',
        stock_group_id: '',
        stock_level_id: '',
        stock_location_id: ''
    });
    //#endregion State

    //#region Methods
    function clearForm() {
        Object.assign(formData, defaultFormState);
        Object.keys(serverErrors.value).forEach((key) => (serverErrors.value[key] = ''));
        document.getElementById('nameInput')?.focus();
    }

    const getStockLevelID = (stockLevel: StockLevel) => stockLevel.stock_level_id;

    const getStockLevelName = (stockLevel: StockLevel) => stockLevel.name;

    const handleSubmit = (shouldCloseForm: boolean) => {
        createStockItemAsync(formData)
            .then(() => {
                clearForm();
                if (shouldCloseForm) {
                    isModalVisible.value = false;
                }
            })
            .catch((error: AxiosError) => {
                mapApiErrorsToForm(error, serverErrors);
            });
    };
    //#endregion Methods

    //#region Validation
    const nameInputRules: ValidationRule[] = [(val: string) => (val && val.length > 0) || 'Please type something'];
    const stockLevelSelectRules: ValidationRule[] = [(val: string) => !!val || 'Please select a stock level'];
    //#endregion Validation
</script>
