<template>
    <!--
        C-4 Chunk 3 — compact ±/count stepper for a recipe's cooked-meals
        pool. Presentational: the parent owns the API call + refresh and
        passes `busy`. Reused by RecipeCard and RecipeDetailPage (R-001).
    -->
    <div class="meal-stepper row items-center no-wrap q-gutter-xs">
        <BaseButton
            variant="icon"
            :icon="ICONS.remove"
            :disable="busy || available <= (min ?? 0)"
            aria-label="Remove one meal"
            @click.stop="emit('adjust', -1)"
        />
        <div class="meal-stepper__count text-weight-medium" :class="sizeClass">
            {{ available }}
        </div>
        <BaseButton
            variant="icon"
            :icon="ICONS.add"
            :disable="busy"
            aria-label="Add one meal"
            @click.stop="emit('adjust', 1)"
        />
    </div>
</template>

<script setup lang="ts">
    import { computed } from 'vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';

    const props = withDefaults(
        defineProps<{
            available: number;
            busy?: boolean;
            min?: number;
            size?: 'sm' | 'md';
        }>(),
        { busy: false, min: 0, size: 'md' },
    );

    const emit = defineEmits<{ (e: 'adjust', delta: number): void }>();

    const sizeClass = computed(() => (props.size === 'sm' ? 'text-subtitle1' : 'text-h5'));
</script>

<style scoped lang="scss">
    .meal-stepper__count {
        min-width: 1.75rem;
        text-align: center;
    }
</style>
