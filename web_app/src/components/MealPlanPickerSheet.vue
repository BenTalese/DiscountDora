<template>
    <q-dialog
        :model-value="modelValue"
        position="bottom"
        transition-show="slide-up"
        transition-hide="slide-down"
        @update:model-value="(v: boolean) => emit('update:modelValue', v)"
    >
        <q-card class="picker-sheet column">
            <q-card-section class="row items-center q-py-sm">
                <div class="text-subtitle1">Pick a recipe</div>
                <q-space />
                <BaseButton variant="icon" :icon="ICONS.close" @click="emit('update:modelValue', false)">
                    <q-tooltip>Close</q-tooltip>
                </BaseButton>
            </q-card-section>
            <q-separator />
            <q-card-section class="col q-pa-sm picker-sheet__body">
                <MealPlanRecipePicker
                    :recipe-search="recipeSearch"
                    :trays="trays"
                    :recipes="recipes"
                    :focused-target="focusedTarget"
                    :drag-allowed="false"
                    :format-date="formatDate"
                    :log-cook="logCook"
                    @update:recipe-search="(v: string) => emit('update:recipeSearch', v)"
                    @cancel-target="emit('cancelTarget')"
                    @recipe-pick="onRecipePicked"
                    @palette-meal-adjust="(id: string, d: number) => emit('paletteMealAdjust', id, d)"
                />
            </q-card-section>
        </q-card>
    </q-dialog>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import MealPlanRecipePicker from 'src/components/MealPlanRecipePicker.vue';
    import { ICONS } from 'src/style/icons';
    import type { Recipe } from 'src/models/recipe';
    import type { RecipeTray } from 'src/composables/useMealPlanner';

    defineProps<{
        modelValue: boolean;
        recipeSearch: string;
        trays: RecipeTray[];
        recipes: Recipe[];
        focusedTarget: { dayIso: string; slot: string } | null;
        formatDate: (iso: string) => string;
        logCook: (recipeId: string, count: number) => Promise<number>;
    }>();

    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
        (e: 'update:recipeSearch', value: string): void;
        (e: 'cancelTarget'): void;
        (e: 'recipePick', recipeId: string): void;
        (e: 'paletteMealAdjust', recipeId: string, delta: number): void;
    }>();

    function onRecipePicked(recipeId: string) {
        emit('recipePick', recipeId);
        // Auto-close after a pick on mobile — Tesler. The pinned-drawer
        // pattern is desktop-only.
        emit('update:modelValue', false);
    }
</script>

<style scoped>
    .picker-sheet {
        width: 100vw;
        max-width: 100vw;
        height: 80vh;
        border-top-left-radius: 16px;
        border-top-right-radius: 16px;
        margin: 0 !important;
    }
    .picker-sheet__body {
        overflow-y: auto;
    }
</style>
