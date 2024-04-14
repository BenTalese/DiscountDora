<template>
    <q-card
      bordered
      flat
      class="column full-height no-wrap rounded-borders row text-white"
    >
      <q-img
        :src="img"
        loading="lazy"
        spinner-color="info"
        spinner-size="2rem"
        img-class="q-pa-lg"
        class="bg-white"
      >
        <template v-slot:error>
          <div class="absolute-full flex flex-center"> Error encountered </div>
        </template>
      </q-img>

      <div class="bg-blue-grey column flex-1 row">
        <q-card-section>
          <q-btn
            :icon="icon"
            fab
            @click="emit('icon-click')"
            :class="iconClass"
            color="white"
            class="absolute top-right-offset"
          />
        </q-card-section>

        <slot name="body">
          <q-card-section class="bg-blue-grey flex-1">
            {{ body }}
          </q-card-section>
        </slot>

        <q-card-actions v-if="chipLabel"  align="right" class="bg-blue-grey">
          <q-chip :color="chipColour" :label="chipLabel" text-color="white" />
        </q-card-actions>
      </div>
    </q-card>
</template>

<script setup lang="ts">

  //#region Props & Emits

  interface ICardComponentProps {

    /**
     * The text displayed in the body of the card;
     * Utilise the body slot to customise the body section as a whole;
     * Recommended component for slot: QCardSection;
     */
    body?: string

    /**
     * The label of the quasar chip component in the card footer;
     * Only rendered when a value is supplied;
     */
    chipLabel?: string | undefined

    /**
     * The colour applied to the chip in the card footer;
     * Only applied if the chipLabel prop has a value;
     * Default: grey;
     */
    chipColour?: string | undefined


    /**
     * Icon name following Quasar convention; Make sure you have the icon library installed unless you are using 'img:' prefix; If 'none' (String) is used as value then no icon is rendered (but screen real estate will still be used for it);
     */
    icon?: string | undefined

    /**
     * The CSS classes applied to card component's icon;
     */
    iconClass?: string | undefined

    /**
     * Path to image;
     * Default: '../../src/assets/dora-logo.png';
     */
    img?: string | undefined

  }

  withDefaults(defineProps<ICardComponentProps>(), {
    chipColour: 'grey',
    img: '../../src/assets/dora-logo.png'
  })

  const emit = defineEmits<{

    /**
     * Emitted when the click event is triggered on the card component's icon;
     */
    (e: 'icon-click'): void

  }>()

  //#endregion Props & Emits

</script>

<!-- TODO: Move to global styling accessible by all components -->
<style scoped>

.flex-1 {
  flex: 1;
}

.top-right-offset {
  right: 12px;
  top: 0;
  transform: translateY(-50%);
}

</style>
