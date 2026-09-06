<template>
    <BaseButton
        variant="icon"
        :icon="linked ? ICONS.link : ICONS.link_off"
        :color="linked ? 'positive' : undefined"
        :class="{ 'product-link-btn--unlinked': !linked }"
        :aria-label="label"
        @click.stop="onClick"
    >
        <q-tooltip>{{ label }}</q-tooltip>
    </BaseButton>
</template>

<script setup lang="ts">
    /** Link state as a single control (feedback MP-5).
     *
     *  The owner asked for the placement the companion's "save product" button
     *  uses: "grey broken link for unlinked, green connected link for linked.
     *  Clicking it shows modal to link if unlinked. Clicking it unlinks if
     *  linked." One control that both *shows* the state and *changes* it.
     *
     *  Replaces a bare `<a href="#">Link…</a>` in the card body — which read as
     *  body copy rather than a control and was far under the 44px tap floor
     *  (D-004). Which stock item is linked is still shown separately, as a
     *  chip, per the same feedback bullet.
     */
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { computed } from 'vue';

    const props = defineProps<{
        linked: boolean;
        stockItemName?: string | null;
    }>();

    const emit = defineEmits<{
        (e: 'link'): void;
        (e: 'unlink'): void;
    }>();

    // Split rather than `emit(linked ? … : …)`: the overloaded emit signature
    // can't narrow a union argument.
    function onClick(): void {
        if (props.linked) emit('unlink');
        else emit('link');
    }

    // D-005: an icon-only control needs a name that says what it does, not
    // what it is — and naming the stock item makes the unlink case specific
    // enough to be safe.
    const label = computed(() =>
        props.linked
            ? `Unlink from ${props.stockItemName ?? 'stock item'}`
            : 'Link to a stock item',
    );
</script>

<style scoped>
    /* Grey is the "no link" state. `--text-muted` rather than the icon
       variant's default ink so the two states read as different at a glance
       (D-001 reserves grey for absent/unknown, which is exactly what an
       unlinked product is). */
    .product-link-btn--unlinked {
        color: var(--text-muted);
    }
</style>
