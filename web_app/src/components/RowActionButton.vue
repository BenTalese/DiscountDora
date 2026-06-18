<template>
    <!--
        Round, dense, flat icon button — the standard cluster button for
        a list row (stock-row, recipe-ingredient row, shopping-list line,
        etc.). Pins the visual style so every cluster reads as a uniform
        set; the q-btn pattern (flat + dense + round + size="md") was
        being copy-pasted four times across stock-row + cart and drifted
        the first time someone forgot one of the props.

        Slots: tooltip goes in the default slot. Use `v-slot="{ menu }"`
        via the standard q-menu pattern by nesting a q-menu / q-popup-proxy
        inside the default slot if a menu is needed.
    -->
    <q-btn
        flat
        dense
        round
        size="md"
        :icon="icon"
        :color="color"
        :loading="loading"
        :disable="disable"
        :aria-label="ariaLabel"
        @click.stop="onClick"
    >
        <slot />
    </q-btn>
</template>

<script setup lang="ts">
    withDefaults(
        defineProps<{
            icon: string;
            /** Quasar semantic colour (`primary`, `warning`, `negative`…) or
             *  unset for the default text colour. */
            color?: string | undefined;
            loading?: boolean;
            disable?: boolean;
            ariaLabel?: string;
        }>(),
        { loading: false, disable: false },
    );

    const emit = defineEmits<{ (e: 'click', ev: MouseEvent): void }>();

    function onClick(ev: Event) {
        emit('click', ev as MouseEvent);
    }
</script>
