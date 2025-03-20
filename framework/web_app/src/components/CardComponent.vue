<template>
    <q-card
        class="column full-height no-wrap rounded-borders row text-black"
        bordered
        flat
    >
        <q-img
            class="bg-white"
            :src="img"
            img-class="q-pa-lg"
            loading="lazy"
            spinner-color="info"
            spinner-size="2rem"
        >
            <div
                class="absolute-top text-center"
                v-if="imgCaption"
            >
                <span class="dora-letterSpacing-3 text-subtitle2 text-weight-regular">
                    {{ imgCaption }}
                </span>
            </div>

            <template v-slot:error>
                <div class="absolute-full flex flex-center">Error encountered</div>
            </template>
        </q-img>

        <div class="dora-component column dora-flex-1 row">
            <q-card-section>
                <q-btn
                    class="absolute dorascoped-top-right-offset"
                    :class="iconClass"
                    :icon="icon"
                    @click="emit('icon-click')"
                    color="white"
                    fab
                />
            </q-card-section>

            <slot name="body">
                <q-card-section class="dora-flex-1">
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
    }

    withDefaults(defineProps<ICardComponentProps>(), {
        chipColour: 'grey',
        img: '../../src/assets/dora-logo.png'
    });

    const emit = defineEmits<{
        /**
         * Emitted when the click event is triggered on the card component's icon;
         */
        (e: 'icon-click'): void;
    }>();

    //#endregion Props & Emits
</script>

<style scoped>
    .dorascoped-top-right-offset {
        right: 12px;
        top: 0;
        transform: translateY(-50%);
    }
</style>
