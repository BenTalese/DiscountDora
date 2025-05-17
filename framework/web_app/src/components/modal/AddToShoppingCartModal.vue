<template>
    <q-dialog v-model="isModalVisible">
        <q-card style="width: 700px; max-width: 80vw">
            <q-card-section class="row items-center">
                <span class="q-ml-sm">Add {{ 'stock item' }} to a shopping list.</span>
            </q-card-section>

            <q-card-actions align="right">
                <q-btn
                    color="primary"
                    flat
                    label="Cancel"
                    v-close-popup
                />
                <q-btn
                    color="primary"
                    flat
                    label="Add to list"
                    v-close-popup
                />
            </q-card-actions>
        </q-card>
    </q-dialog>
</template>

<script setup lang="ts">
    //#region Imports
    import { useModalState } from 'src/composables/modalState';
    //#endregion Imports

    //#region Store Initialization
    //#endregion Store Initialization

    //#region Props and Events
    const props = defineProps<{ modelValue: boolean }>();
    const emit = defineEmits(['update:modelValue']);
    const { isModalVisible } = useModalState(props, emit);
    //#endregion Props and Events
</script>
