<template>
    <button
        type="button"
        class="rich-card"
        :class="[
            entry.consumed_at ? 'rich-card--consumed' : '',
            shortfall && batchEnabled ? 'rich-card--shortfall' : '',
            highlight ? 'rich-card--highlight' : '',
        ]"
        :disabled="!!entry.consumed_at"
        :aria-label="accessibleLabel"
    >
        <div class="rich-card__thumb" :class="{ 'rich-card__thumb--mono': !entry.has_image }">
            <img
                v-if="entry.has_image"
                :src="thumbUrl"
                :alt="entry.recipe_name"
                loading="lazy"
            />
            <span v-else class="rich-card__mono-letter">{{ monogramLetter }}</span>
        </div>
        <div class="rich-card__body">
            <div class="rich-card__name">{{ entry.recipe_name }}</div>
            <div class="rich-card__meta">
                <span class="rich-card__tag">{{ entry.slot }}</span>
                <span class="rich-card__servings">×{{ entry.servings }}</span>
                <span v-if="entry.cook_time_minutes" class="rich-card__cook-time">
                    <q-icon :name="ICONS.timer" size="12px" />
                    {{ entry.cook_time_minutes }}m
                </span>
                <q-icon
                    v-if="entry.consumed_at"
                    :name="ICONS.check"
                    size="14px"
                    class="rich-card__status text-positive"
                >
                    <q-tooltip>Cooked</q-tooltip>
                </q-icon>
                <q-icon
                    v-else-if="shortfall && batchEnabled"
                    :name="ICONS.chef_hat"
                    size="14px"
                    class="rich-card__status text-warning"
                >
                    <q-tooltip>Needs cooking — pool is short</q-tooltip>
                </q-icon>
            </div>
        </div>

        <q-menu
            v-if="!entry.consumed_at"
            transition-show="jump-down"
            transition-hide="jump-up"
        >
            <q-list dense style="min-width: 220px">
                <q-item-label header>{{ entry.recipe_name }}</q-item-label>
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
    import { recipeImageUrl } from 'src/services/api/recipeApiService';
    import { useBatchEnabled } from 'src/composables/useBatchEnabled';
    import type { MealPlanEntry } from 'src/models/mealPlan';
    import { computed } from 'vue';

    const { batchEnabled } = useBatchEnabled();

    const props = withDefaults(
        defineProps<{
            entry: MealPlanEntry;
            shortfall?: boolean;
            highlight?: boolean;
        }>(),
        { shortfall: false, highlight: false },
    );

    const emit = defineEmits<{
        (e: 'view'): void;
        (e: 'cook'): void;
        (e: 'remove'): void;
        (e: 'adjust', delta: number): void;
    }>();

    const thumbUrl = computed(() => recipeImageUrl(props.entry.recipe_id));
    const monogramLetter = computed(
        () => (props.entry.recipe_name?.trim().charAt(0) || '?').toUpperCase(),
    );

    // R-Phase 6 §4.6 — single combined accessible label so AT users hear the
    // whole meal at once (name + slot + servings + status) instead of as
    // separate text fragments. Status text alternative covers 1.4.1.
    const accessibleLabel = computed(() => {
        const base = `${props.entry.recipe_name}, ${props.entry.slot}, ${props.entry.servings} serving${props.entry.servings === 1 ? '' : 's'}`;
        if (props.entry.consumed_at) return `${base}, cooked`;
        if (props.shortfall && batchEnabled.value) return `${base}, needs cooking`;
        return base;
    });
</script>

<style scoped>
    .rich-card {
        display: flex;
        align-items: stretch;
        gap: 8px;
        padding: 6px 8px;
        background: var(--surface-elevated);
        border: 1px solid var(--separator);
        border-left: 3px solid var(--brand-primary);
        border-radius: 8px;
        cursor: pointer;
        transition: background 0.12s ease, border-color 0.12s ease, transform 0.12s ease;
        position: relative;
        color: var(--text-primary);
        text-align: left;
        font: inherit;
        width: 100%;
        min-height: 44px;
    }
    .rich-card:disabled {
        cursor: default;
    }
    .rich-card:hover,
    .rich-card:focus-visible {
        background: var(--surface-sunken);
        outline: none;
    }
    .rich-card:focus-visible {
        border-color: var(--q-primary);
    }
    .rich-card--consumed {
        opacity: 0.55;
        border-left-color: var(--separator);
    }
    .rich-card--shortfall {
        border-left-color: var(--q-warning);
    }
    .rich-card--highlight {
        outline: 2px solid var(--brand-primary);
        outline-offset: 1px;
    }
    .rich-card__thumb {
        flex: 0 0 auto;
        width: 42px;
        height: 42px;
        border-radius: 6px;
        overflow: hidden;
        background: var(--surface-sunken);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .rich-card__thumb img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }
    .rich-card__thumb--mono {
        background: var(--surface-elevated);
        border: 1px dashed var(--separator);
    }
    .rich-card__mono-letter {
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--text-secondary);
        line-height: 1;
    }
    .rich-card__body {
        flex: 1 1 auto;
        min-width: 0;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 2px;
    }
    .rich-card__name {
        font-weight: 600;
        font-size: 0.9rem;
        line-height: 1.2;
        word-break: break-word;
    }
    .rich-card__meta {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 6px 8px;
        font-size: 0.72rem;
        color: var(--text-muted);
    }
    .rich-card__tag {
        background: var(--surface-sunken);
        color: var(--text-secondary);
        padding: 1px 6px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }
    .rich-card__servings {
        font-weight: 600;
    }
    .rich-card__cook-time {
        display: inline-flex;
        align-items: center;
        gap: 2px;
    }
    .rich-card__status {
        margin-left: auto;
    }
</style>
