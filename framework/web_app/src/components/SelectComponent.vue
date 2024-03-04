<template>
    <q-select
        bg-color="white"
        class="q-ma-sm"
        :clearable="clearable"
        clear-icon="cancel"
        dense
        color="black"
        dropdown-icon="expand_more"
        :label="label"
        label-color="black"
        :multiple="multiple"
        :options="options"
        :option-label="optionLabel"
        standout="bg-teal text-yellow"
        style="min-width: 90px;"
        v-model="internalModelValue"
        @update:model-value="onUpdateModelValue"
        transition-show="jump-up"
        transition-hide="jump-up"
    >
        <template v-slot:no-option>
            <q-item>
                <q-item-section class="text-italic text-grey">
                    No options
                </q-item-section>
            </q-item>
        </template>
    </q-select>
</template>

<script setup lang="ts">

    const emit = defineEmits<{
        (e: 'update:model-value', value: unknown) : void
    }>();

    const props = defineProps<{
        clearable?: boolean
        label: string
        multiple?: boolean
        options: Array<unknown>
        optionLabel: ((option: string | unknown) => string) | string | undefined
        modelValue: Array<unknown> | unknown
    }>()

    // const internalOptions = props.optionsSelector ?? ;
    const internalModelValue = props.modelValue;

    const onUpdateModelValue = (value: string | null): void =>
        emit('update:model-value', value);
</script>
