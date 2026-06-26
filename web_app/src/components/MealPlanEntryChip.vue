<template>
    <button
        type="button"
        class="entry-chip"
        :class="{
            'entry-chip--consumed': !!entry.consumed_at,
            'entry-chip--shortfall': shortfall && batchEnabled && !entry.consumed_at,
            'entry-chip--highlight': highlight,
        }"
        :aria-label="accessibleLabel"
        :disabled="!!entry.consumed_at"
    >
        <div class="entry-chip__body">
            <div v-if="showSlot" class="entry-chip__slot">{{ entry.slot }}</div>
            <div class="entry-chip__main">
                <span class="entry-chip__name">{{ entry.recipe_name }}</span>
                <span class="entry-chip__pill">×{{ entry.servings }}</span>
                <q-icon
                    v-if="entry.consumed_at"
                    :name="ICONS.check"
                    size="14px"
                    class="entry-chip__status text-positive"
                >
                    <q-tooltip>Cooked</q-tooltip>
                </q-icon>
                <q-icon
                    v-else-if="shortfall && batchEnabled"
                    :name="ICONS.chef_hat"
                    size="14px"
                    class="entry-chip__status text-warning"
                >
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
                            <BaseButton variant="icon" :icon="ICONS.remove" @click.stop="emit('adjust', -1)">
                                <q-tooltip>One fewer (removes the entry at 0)</q-tooltip>
                            </BaseButton>
                            <span class="text-weight-medium" style="min-width: 1.2rem; text-align: center">
                                {{ entry.servings }}
                            </span>
                            <BaseButton variant="icon" :icon="ICONS.add" @click.stop="emit('adjust', 1)">
                                <q-tooltip>One more</q-tooltip>
                            </BaseButton>
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
    </button>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import { useBatchEnabled } from 'src/composables/useBatchEnabled';
    import type { MealPlanEntry } from 'src/models/mealPlan';
    import { computed } from 'vue';

    const { batchEnabled } = useBatchEnabled();

    const props = withDefaults(
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

    // R-Phase 6 §4.6 — single accessible label that names the recipe + slot +
    // servings, so AT users hear the whole meal at once instead of three
    // separate spans. Shortfall is announced as a status, not a colour.
    const accessibleLabel = computed(() => {
        const base = `${props.entry.recipe_name}, ${props.entry.slot}, ${props.entry.servings} serving${props.entry.servings === 1 ? '' : 's'}`;
        if (props.entry.consumed_at) return `${base}, cooked`;
        if (props.shortfall && batchEnabled.value) return `${base}, needs cooking`;
        return base;
    });
</script>

<style scoped>
    /*
        §7 colour discipline — chip is a content-forward card, not a
        saturated fill. Status reads through:
            border-left accent (brand-primary normally, amber on shortfall,
            neutral on consumed)  +  icon  +  text alternative (aria-label).
        Three channels = WCAG 1.4.1 honoured without colour-only signalling.
    */
    .entry-chip {
        display: flex;
        align-items: stretch;
        width: 100%;
        text-align: left;
        padding: 6px 8px;
        margin-bottom: 4px;
        background: var(--surface-elevated);
        border: 1px solid var(--separator);
        border-left: 3px solid var(--brand-primary);
        border-radius: 8px;
        color: var(--text-primary);
        cursor: pointer;
        transition: background 0.12s ease, border-color 0.12s ease;
        min-height: 28px;
        font: inherit;
    }
    .entry-chip:hover,
    .entry-chip:focus-visible {
        background: var(--surface-sunken);
        outline: none;
    }
    .entry-chip:focus-visible {
        border-color: var(--q-primary);
    }
    .entry-chip--shortfall {
        border-left-color: var(--q-warning);
    }
    .entry-chip--consumed {
        opacity: 0.55;
        border-left-color: var(--separator);
        cursor: default;
    }
    .entry-chip--highlight {
        outline: 2px solid var(--brand-primary);
        outline-offset: 1px;
    }
    .entry-chip__body {
        width: 100%;
        min-width: 0;
    }
    .entry-chip__slot {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.02em;
        color: var(--text-muted);
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
        font-weight: 600;
    }
    .entry-chip__pill {
        flex: 0 0 auto;
        background: var(--surface-sunken);
        color: var(--text-secondary);
        border-radius: 6px;
        padding: 1px 6px;
        font-weight: 700;
        font-size: 0.8rem;
    }
    .entry-chip__status {
        flex: 0 0 auto;
    }
</style>
