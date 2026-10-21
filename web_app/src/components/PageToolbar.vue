<template>
    <div class="row items-center q-mb-md page-toolbar">
        <BaseButton
            v-if="backTo"
            variant="icon"
            class="q-mr-sm dora-text-secondary"
            :icon="ICONS.arrow_back"
            :to="backTo"
            aria-label="Back"
        />
        <div class="col">
            <div class="text-h5">{{ title }}</div>
            <div v-if="subtitle" class="text-caption dora-text-muted">
                {{ subtitle }}
            </div>
        </div>
        <div class="row items-center q-gutter-sm page-toolbar-actions">
            <slot name="actions" />
        </div>
    </div>
</template>

<script setup lang="ts">
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';

    defineProps<{
        title: string;
        subtitle?: string;
        backTo?: string | object;
    }>();
</script>

<style scoped>
    .page-toolbar {
        min-height: 44px;
        /* Vertical breathing room for when the actions wrap onto their own
           line below the title on narrow screens (DR-9 / D-011). */
        row-gap: var(--space-2, 8px);
    }
    /* Let the title cell shrink so a wide action cluster can't shove it
       off-screen or squeeze it into a mid-word wrap that collides with the
       actions (FU-578 #40). When the actions wrap below, the title takes the
       full line. */
    .page-toolbar > .col {
        min-width: 0;
    }
    .page-toolbar-actions {
        /* Was `flex-shrink: 0`, which forced the whole action cluster (up to
           ~930px on the shopping-list toolbar) to keep its width — overflowing
           the viewport on mobile (FU-578 #4, ~255px of horizontal scroll) and
           colliding with the title at desktop widths (#40). Allowing it to
           shrink + wrap drops the buttons onto their own line(s) instead, so
           the toolbar never causes horizontal page scroll (D-011). It is
           already a `.row` (flex-wrap: wrap); the buttons re-flow within it. */
        flex-wrap: wrap;
        justify-content: flex-end;
    }
</style>
