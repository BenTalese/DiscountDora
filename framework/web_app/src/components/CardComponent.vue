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

      <div class="bg-blue-grey column row" style="flex: 1;">
        <q-card-section>
          <q-btn
            :icon="icon ?? 'favorite'"
            fab
            @click="emit('icon-click')"
            :class="iconClass"
            color="white"
            class="absolute"
            style="top: 0; right: 12px; transform: translateY(-50%);"
          />
        </q-card-section>

        <q-card-section class="bg-blue-grey q-pt-none" style="flex: 1;">
          <div class="col text-h7"> {{ bodyMainText }} </div>
          <div class="text-subtitle1"> {{ bodySubtitleText }} </div>
        </q-card-section>

        <q-card-actions align="right" class="bg-blue-grey">
          <q-chip :color="chipColour" :label="chipLabel" text-color="white" />
        </q-card-actions>
      </div>
    </q-card>
</template>

<script setup lang="ts">

  //#region Props & Emits

  interface ICardComponentProps {
    bodyMainText?: string
    bodySubtitleText?: string
    chipLabel?: string
    chipColour?: string
    icon: string
    iconClass: string
    img?: string
  }

  withDefaults(defineProps<ICardComponentProps>(), {
    chipColour: 'grey',
    img: '../../src/assets/dora-logo.png'
  })

  const emit = defineEmits<{
    (e: 'icon-click'): void
  }>()

  //#endregion Props & Emits

</script>
