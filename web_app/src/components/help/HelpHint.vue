<template>
    <!--
        Feedback 2026-08-24 — the (?) that takes a heading to its help guide.

        Surfaces like Substitutes and Barcodes each carried a paragraph of
        explainer prose on the page itself, which is a lot of permanent chrome
        to pay for a thing you read once. The prose moved to Help → Guides; this
        is the way back to it, so the surface stays lean without the explanation
        becoming unfindable.

        `topic` is matched against the guide's own title via the Help page's
        existing `?q=` filter deep-link — no second registry of anchors to keep
        in sync with the guide list.
    -->
    <BaseButton
        variant="icon"
        dense
        :icon="ICONS.help_outline"
        :aria-label="`What is this? — ${topic}`"
        :to="{ path: '/help', query: { q: topic } }"
    >
        <q-tooltip>Read the "{{ topic }}" guide</q-tooltip>
    </BaseButton>
</template>

<script setup lang="ts">
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';

    defineProps<{
        /** Guide title to filter Help → Guides down to. */
        topic: string;
    }>();
</script>
