<template>
    <q-select
        class="min-width-200 q-ma-sm rounded-borders shadow-1"
        :clearable="clearable"
        :dense="dense"
        :label="label"
        :model-value="internalModelValue"
        :multiple="multiple"
        :option-label="optionLabel"
        :options="internalOptions"
        :placeholder="localPlaceholder"
        :stack-label="stackLabel"
        :use-input="filter"
        @filter="onFilter"
        @popup-hide="onPopupVisibilityChange"
        @popup-show="onPopupVisibilityChange"
        @update:model-value="onUpdateModelValue"
        bg-color="white"
        clear-icon="cancel"
        color="black"
        dropdown-icon="expand_more"
        label-color="black"
        square
        standout="bg-teal"
    >
        <template v-slot:no-option>
            <q-item>
                <q-item-section class="text-italic text-grey">
                    No options
                </q-item-section>
            </q-item>
        </template>

        <template
            v-if="multiple"
            v-slot:option="scope"
        >
            <q-item
                @click="scope.itemProps.onClick"
                clickable
                v-ripple
            >
                <div class="items-center no-wrap row">
                    <q-icon
                        class="q-pr-sm"
                        :name="getOptionIconName(scope)"
                        size="md"
                    />
                    <q-item-label class="font-weight-400">
                        {{ getOptionLabel(scope) }}
                    </q-item-label>
                </div>
            </q-item>
        </template>
    </q-select>
</template>

<script lang="ts" setup>
    import { QSelect } from 'quasar';
    import { computed, ref } from 'vue';

    //#region Props & Emits

    interface ISelectComponentProps {
        /**
         * Appends clearable icon when a value (not undefined or null) is set; When clicked, model becomes null
         * Default value: false
         */
        clearable?: boolean | undefined;

        /**
         * Dense mode; occupies less space
         * Default value: true
         */
        dense?: boolean | undefined;

        /**
         * Determines whether the user can filter the options.
         * Default value: false
         */
        filter?: boolean | undefined;

        /**
         * A text label that will “float” up above the input field, once the field gets focus
         */
        label?: string | undefined;

        /**
         * Text to display as placeholder
         */
        placeholder?: string | undefined;

        /**
         * Model of the component;
         * Must be Array if using 'multiple' prop;
         * Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive
         */
        modelValue: unknown;

        /**
         * Allow multiple selection; Model must be Array
         */
        multiple?: boolean | undefined;

        /**
         * Available options that the user can select from. For best performance freeze the list of options.
         * Default value: []
         */
        options?: readonly unknown[] | undefined;

        /**
         * Icon prefixing the option label; Only supported when the multiple prop is set to true;
         * If using a function then for best performance, reference it from your scope and do not define it inline;
         * Icon Name must follow Quasar convention;
         * Make sure you have the icon library installed unless you are using 'img:' prefix;
         * If 'none' (String) is used as value then no icon is rendered (but screen real estate will still be used for it)
         * @param isOptionSelected The selected state of the current option being processed
         * @returns Name of the icon
         */
        optionIconName?:
            | ((isOptionSelected: boolean) => string)
            | string
            | undefined;

        /**
         * Property of option which holds the 'label';
         * If using a function then for best performance, reference it from your scope and do not define it inline;
         * Example function: (item) => item === null ? 'Null value' : item.itemName;
         * Example string: 'itemName';
         * Default value: label;
         * @param option The current option being processed
         * @returns Label of the current option
         */
        optionLabel?:
            | ((option: string | unknown) => string)
            | string
            | undefined;

        /**
         *
         * Default value: undefined
         */
        stackLabel?: boolean | undefined;
    }

    const props = withDefaults(defineProps<ISelectComponentProps>(), {
        clearable: false,
        dense: true,
        filter: false,
        multiple: false,
        // Object or array defaults must be returned from a factory function.
        // The function receives the raw props received by the component as the argument.
        options: () => [],
        useInput: false
    });

    const emit = defineEmits<{
        /**
         * Emitted when the component needs to change the model; Is also used by v-model
         * @param value New model value
         */
        (e: 'update:model-value', value: unknown): void;
    }>();

    //#endregion Props & Emits

    //#region Model Value

    const internalModelValue = ref(props.modelValue);

    //TODO: value can be string???
    const onUpdateModelValue = (value: string | null): void =>
        emit('update:model-value', value);

    //#endregion Model Value

    //#region Multiple

    interface IScope {
        /**
         * Option -- its value is taken from 'options' prop
         */
        opt: unknown;

        /**
         * Is option selected?
         */
        selected: boolean;
    }

    /**
     * Retrieves the name of the icon from the optionIconName prop.
     */
    const getOptionIconName = (scope: IScope): string =>
        props.optionIconName instanceof Function
            ? props.optionIconName(scope.selected)
            : (props.optionIconName as string);

    function getOptionLabel(scope: IScope): string {
        if (props.optionLabel instanceof String) {
            const opt = scope.opt as { [key: string]: string };
            return opt[props.optionLabel as string];
        } else if (props.optionLabel instanceof Function)
            return props.optionLabel(scope.opt);
        else return scope.opt as string;
    }

    //#endregion Multiple

    //#region Filter

    let internalOptions = ref(props.options);

    /**
     * Emitted when user wants to filter a value
     * @param inputValue What the user typed
     * @param doneFn Supply a function which makes the necessary updates
     * @param abortFn Call this function if something went wrong
     */
    const onFilter = (
        inputValue: string,
        doneFn: (
            callbackFn: () => void,
            afterFn?: (ref: QSelect) => void
        ) => void,
        abortFn: () => void
    ) => {
        //TODO: bug: input valid match, then add space (invalid), then remove space. options still show no results
        doneFn(() => {
            if (!props.filter || inputValue === '')
                internalOptions.value = props.options;

            const input = inputValue.toLowerCase();

            internalOptions.value = internalOptions.value.filter(
                (opt) =>
                    getOptionLabel({ opt } as IScope)
                        .toLowerCase()
                        .indexOf(input) > -1
            );
        });

    };

    //#endregion Filter

    //#region Placeholder

    let isPopupVisible = ref(false);

    //TODO: understand the difference between a lambda and function, e.g., under the hood
    const onPopupVisibilityChange = () =>
        (isPopupVisible.value = !isPopupVisible.value);

    /**
     * The placeholder value to be displayed when the pop-up is visible or an item has not been selected.
     */
    let localPlaceholder = computed((): string | undefined => {
        if (isPopupVisible.value || !internalModelValue.value)
            return props.placeholder;

        return undefined;
    });

    //#endregion Placeholder
</script>
