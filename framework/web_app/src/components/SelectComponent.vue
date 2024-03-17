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
                <div class="row" style="align-items: center; flex-wrap: nowrap;">
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

    const emit = defineEmits<{
        (e: 'update:model-value', value: unknown) : void
    }>();

    const props = defineProps<{
        clearable?: boolean
        // iconName only supported alongside multiple = true
        iconName?: ((selected :boolean) => string) | string
        label: string
        multiple?: boolean
        options: Array<unknown>
        optionLabel?: ((option: string | unknown) => string) | string | undefined
        modelValue: Array<unknown> | unknown
    }>()

    const internalModelValue = props.modelValue;

    const onUpdateModelValue = (value: string | null): void =>
        emit('update:model-value', value);
</script>
