<template>
    <BaseDialog
        :model-value="modelValue"
        card-style="width: 480px; max-width: 95vw"
        @update:model-value="onDialogUpdate"
    >
            <q-card-section>
                <div class="text-h6">Move {{ count }} item{{ count === 1 ? '' : 's' }}</div>
            </q-card-section>
            <q-card-section>
                <q-select
                    v-model="targetLocationId"
                    :options="locationOptions"
                    emit-value
                    map-options
                    clearable
                    outlined
                    label="Destination location"
                />
            </q-card-section>
            <q-card-actions align="right">
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <BaseButton
                    variant="primary"
                    label="Move"
                    :loading="busy"
                    @click="emit('confirm', targetLocationId)"
                />
            </q-card-actions>
    </BaseDialog>
</template>

<script setup lang="ts">
    import { ref, watch } from 'vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';

    type LocationOption = { label: string; value: string };

    const props = defineProps<{
        modelValue: boolean;
        count: number;
        locationOptions: readonly LocationOption[];
        busy?: boolean;
    }>();

    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
        (e: 'confirm', locationId: string | null): void;
    }>();

    const targetLocationId = ref<string | null>(null);

    // Reset selection each time the dialog opens so a previous pick doesn't
    // sneak into the next move.
    watch(
        () => props.modelValue,
        (open) => {
            if (open) targetLocationId.value = null;
        },
    );

    function onDialogUpdate(value: boolean) {
        emit('update:modelValue', value);
    }
</script>
