<template>
    <q-chip
        square
        :clickable="!entry.consumed_at"
        class="q-mb-xs full-width entry-chip"
        :class="[entry.consumed_at ? 'dora-bg-sunken dora-text-muted' : '', { 'entry-chip--highlight': highlight }]"
        :color="entry.consumed_at ? undefined : (shortfall ? 'warning' : 'primary')"
        :text-color="entry.consumed_at ? undefined : 'white'"
    >
        <div class="entry-chip__body">
            <div v-if="showSlot" class="entry-chip__slot">{{ entry.slot }}</div>
            <div class="entry-chip__main">
                <span class="entry-chip__name">{{ entry.recipe_name }}</span>
                <span class="entry-chip__pill">×{{ entry.servings }}</span>
                <q-icon v-if="entry.consumed_at" :name="ICONS.check" class="entry-chip__status" />
                <q-icon v-else-if="shortfall" :name="ICONS.warning" class="entry-chip__status">
                    <q-tooltip>Needs cooking — pool is short</q-tooltip>
                </q-icon>
            </div>
        </div>

        <q-menu v-if="!entry.consumed_at" transition-show="jump-down" transition-hide="jump-up">
            <q-list dense style="min-width: 220px">
                <q-item-label header>{{ entry.recipe_name }}</q-item-label>
                <!-- Inline servings adjuster — stays open for rapid ± taps. -->
                <q-item>
                    <q-item-section>Servings</q-item-section>
                    <q-item-section side>
                        <div class="row items-center no-wrap q-gutter-xs">
                            <q-btn dense round flat :icon="ICONS.remove" @click.stop="emit('adjust', -1)">
                                <q-tooltip>One fewer (removes the entry at 0)</q-tooltip>
                            </q-btn>
                            <span class="text-weight-medium" style="min-width: 1.2rem; text-align: center">
                                {{ entry.servings }}
                            </span>
                            <q-btn dense round flat :icon="ICONS.add" @click.stop="emit('adjust', 1)">
                                <q-tooltip>One more</q-tooltip>
                            </q-btn>
                        </div>
                    </q-item-section>
                </q-item>
                <q-separator />
                <q-item clickable v-close-popup @click="emit('view')">
                    <q-item-section avatar><q-icon :name="ICONS.open_in_new" /></q-item-section>
                    <q-item-section>View recipe</q-item-section>
                </q-item>
                <q-item clickable v-close-popup @click="emit('cook')">
                    <q-item-section avatar><q-icon :name="ICONS.restaurant" /></q-item-section>
                    <q-item-section>Cook now</q-item-section>
                </q-item>
                <q-separator />
                <q-item clickable v-close-popup @click="emit('remove')">
                    <q-item-section avatar><q-icon :name="ICONS.close" color="negative" /></q-item-section>
                    <q-item-section>Remove from plan</q-item-section>
                </q-item>
            </q-list>
        </q-menu>
    </q-chip>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import type { MealPlanEntry } from 'src/models/mealPlan';

    withDefaults(
        defineProps<{
            entry: MealPlanEntry;
            shortfall?: boolean;
            showSlot?: boolean;
            highlight?: boolean;
        }>(),
        { shortfall: false, showSlot: true, highlight: false },
    );

    const emit = defineEmits<{
        (e: 'view'): void;
        (e: 'cook'): void;
        (e: 'remove'): void;
        (e: 'adjust', delta: number): void;
    }>();
</script>

<style scoped>
    .entry-chip {
        height: auto !important;
        white-space: normal;
    }
    .entry-chip__body {
        width: 100%;
    }
    .entry-chip__slot {
        font-size: 0.7rem;
        font-style: italic;
        opacity: 0.85;
    }
    .entry-chip__main {
        display: flex;
        align-items: center;
        gap: 6px;
        width: 100%;
    }
    .entry-chip__name {
        flex: 1 1 auto;
        white-space: normal;
        word-break: break-word;
        line-height: 1.2;
    }
    .entry-chip__pill {
        flex: 0 0 auto;
        background: var(--surface-elevated);
        color: var(--text-primary);
        border-radius: 6px;
        padding: 1px 6px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .entry-chip__status {
        flex: 0 0 auto;
    }
    .entry-chip--highlight {
        outline: 2px solid var(--brand-primary);
        outline-offset: 1px;
    }
</style>
