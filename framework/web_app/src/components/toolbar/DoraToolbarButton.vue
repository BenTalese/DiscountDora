<template>
    <q-btn
        class="q-ma-sm"
        @click="handleClick"
        :color="props.backColour"
        :label="props.text"
    >
        <q-icon
            v-if="props.icon"
            :name="props.icon"
            :color="props.iconColour"
            size="30px"
        />
        <q-tooltip v-if="props.toolTip">
            {{ props.toolTip }}
        </q-tooltip>
    </q-btn>
</template>

<script lang="ts" setup>
    //#region Props and Events
    const props = defineProps({
        backColour: { type: String, required: true },
        icon: {
            type: String,
            required: false,
            validator(value: string, props: { iconColour: string }) {
                return !!value === !!props.iconColour;
            }
        },
        iconColour: {
            type: String,
            required: false,
            validator(value: string, props: { icon: string }) {
                return !!value === !!props.icon;
            }
        },
        onClick: { type: Function, required: true },
        text: { type: String, required: false },
        toolTip: { type: String, required: false }
    });
    //#endregion Props and Events

    //#region Methods
    const handleClick = () => props.onClick();
    //#endregion Methods
</script>
