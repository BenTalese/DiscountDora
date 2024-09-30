<template>
    <q-card
        class="cursor-pointer full-height no-wrap row text-black"
        :class="row ? 'row' : 'column'"
        bordered
        flat
    >
        <q-img
            class="flex-1 bg-white"
            fit="contain"
            :src="img"
            :style="imgStyle"
            img-class="q-pa-sm"
            loading="lazy"
            spinner-color="info"
            spinner-size="2rem"
        >
            <div
                class="absolute-top text-center"
                v-if="imgCaption"
            >
                <span class="ltr-sp-3 text-subtitle2 text-weight-regular">
                    {{ imgCaption }}
                </span>
            </div>

            <template v-slot:error>
                <div class="absolute-full flex flex-center">
                    Error encountered
                </div>
            </template>
        </q-img>

        <div class="bg-off-white column flex-1 row">
            <q-card-section v-if="icon" @click="emit('icon-container-click', $event)">
                <q-btn
                    class="absolute top-right-offset"
                    :class="iconClass"
                    :icon="icon"
                    @click="onIconClick"
                    color="white"
                    fab
                />
            </q-card-section>

            <slot name="body">
                <q-card-section
                    class="flex-1"
                    @click="emit('body-click')"
                >
                    {{ body }}
                </q-card-section>
            </slot>

            <slot name="footer"></slot>
        </div>
    </q-card>
</template>

<script lang="ts" setup>

    //#region Props & Emits

    interface ICardComponentProps {
        /**
         * The text displayed in the body of the card;
         * Utilise the body slot to customise the body section as a whole;
         * Recommended component for slot: QCardSection;
         */
        body?: string;

        /**
         * Determines whether the card layout is a column or a row.
         * Default: False;
         */
        row?: boolean | undefined;

        /**
         * Icon name following Quasar convention; Make sure you have the icon library installed unless you are using 'img:' prefix; If 'none' (String) is used as value then no icon is rendered (but screen real estate will still be used for it);
         */
        icon?: string | undefined;

        /**
         * The CSS classes applied to card component's icon;
         */
        iconClass?: string | undefined;

        /**
         * Path to image;
         * Default: '../../src/assets/dora-logo.png';
         */
        img?: string | undefined;

        /**
         * A caption for the img; Only renders when a value is provided.
         */
        imgCaption?: string | undefined;

        /**
         *
         */
         imgStyle?: string | undefined;
    }

    withDefaults(defineProps<ICardComponentProps>(), {
        column: true,
        chipColour: 'grey',
        img: '../../src/assets/dora-logo.png',
        row: false
    });

    const emit = defineEmits<{
        /**
         * Emitted when the click event is triggered on the card component's icon;
         */
        (e: 'icon-click', event?: Event): void;

        /**
         * Emitted when the click event is triggered on the container card component's icon;
         */
        (e: 'icon-container-click', event?: Event): void;

        /**
         * Emitted when the click event is triggered on the card component's body;
         */
        (e: 'body-click'): void;
    }>();

    //#endregion Props & Emits

    //#region Event Handlers

    const onIconClick = (event: Event) => {
        event.stopPropagation();
        emit('icon-click', event);
    };

    //#endregion Event Handlers
</script>

<style scoped>
    .ltr-sp-3 {
        letter-spacing: 3px;
    }

    .top-right-offset {
        right: 12px;
        top: 0;
        transform: translateY(-50%);
    }
</style>
