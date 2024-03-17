<template>
    <q-card
      bordered
      class="rounded-borders text-white"
      flat
      style="height: 100%; display: flex; flex-direction: column;">
      <q-img
        class="bg-white"
        img-class="q-pa-lg"
        loading="lazy"
        spinner-color="info"
        spinner-size="2rem"
        src="img"
      >
        <template v-slot:error>
          <div class="absolute-full flex flex-center">
          Error encountered
        </div>
        </template>
      </q-img>

      <div class="bg-blue-grey" style="display: flex; flex: 1; flex-direction: column;">

        <q-card-section>
          <q-btn
            fab
            color="white"
            :icon="icon ?? 'favorite'"
            class="absolute"
            :class="iconClass"
            style="top: 0; right: 12px; transform: translateY(-50%);"
            @click="emit('icon-click')"
          />

        </q-card-section>

        <q-card-section class="bg-blue-grey q-pt-none" style="flex: 1;">
          <div class="col text-h7">
            {{ bodyMainText }}
          </div>
          <div class="text-subtitle1">
            {{ bodySubtitleText }}
          </div>
        </q-card-section>

        <q-card-actions align="right" class="bg-blue-grey">
          <q-chip color="grey" :label="chipLabel" text-color="white">
          </q-chip>
        </q-card-actions>

      </div>

    </q-card>
</template>

<script setup lang="ts">
  const emit = defineEmits<{
    (e: 'icon-click'): void
  }>()

  interface cardComponentProps {
    // TODO: Figure what data is received when an image does not exist.
    // Empty img should be replaced with a default/placeholder img.
    bodyMainText?: string
    bodySubtitleText?: string
    chipLabel?: string
    icon: string
    iconClass: string
    img?: string
  }

  withDefaults(defineProps<cardComponentProps>(), {
    img: '../../src/assets/dora-logo.png'
  })

  // TODO: Ensure where appropriate the usage of props have default values being utilised, e.g., placeholder img
</script>
