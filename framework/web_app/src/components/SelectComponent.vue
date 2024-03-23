<template>
    <q-select
        bg-color="white"
        class="q-ma-sm shadow-3 rounded-borders"
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
        style="min-width: 175px;"
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

        <template v-if="multiple" v-slot:option="scope">
            <q-item v-ripple clickable @click="scope.itemProps.onClick">
                <div class="items-center no-wrap row">
                    <q-icon
                        size="md"
                        class="q-pr-sm"
                        :name="typeof iconName === 'function'
                            ? iconName(scope.selected)
                            : iconName" />
                    <q-item-label style="font-weight:400">
                        {{ typeof optionLabel === 'string'
                        ? scope.opt[optionLabel]
                        : typeof optionLabel === 'function'
                            ? optionLabel(scope.opt)
                            : scope.opt }}
                    </q-item-label>
                </div>
            </q-item>
        </template>

    </q-select>
</template>

<script setup lang="ts">

    //#region Props & Emits

    interface ISelectComponentProps {
        clearable?: boolean
        /**
         * The name of the icon. Refer to the Quasar Select Component name prop for guidelines.
         * Only supported when the multiple prop is set to true.
         */
        iconName?: ((selected :boolean) => string) | string
        label: string
        modelValue: Array<unknown> | unknown
        multiple?: boolean
        options: Array<unknown>
        optionLabel?: ((option: string | unknown) => string) | string | undefined
    }

    const props = withDefaults(defineProps<ISelectComponentProps>(),{
        clearable: false,
        multiple: false
    });

    const emit = defineEmits<{
        (e: 'update:model-value', value: unknown) : void
    }>();

    //#endregion Props & Emits

    //#region Model Value

    const internalModelValue = props.modelValue;

    const onUpdateModelValue = (value: string | null): void =>
        emit('update:model-value', value);

    //#endregion Model Value

</script>
