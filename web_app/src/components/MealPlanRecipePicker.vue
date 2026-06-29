<template>
    <q-card flat bordered>
        <q-card-section class="q-pb-xs">
            <q-input
                :model-value="recipeSearch"
                dense
                outlined
                clearable
                :debounce="150"
                placeholder="Search recipes"
                @update:model-value="(v) => emit('update:recipeSearch', (v ?? '') as string)"
            >
                <template #prepend><q-icon :name="ICONS.search" /></template>
            </q-input>
            <q-banner v-if="focusedTarget" dense class="dora-bg-sunken q-mt-sm rounded-borders">
                <div class="text-caption">
                    Adding to <strong>{{ focusedTarget.slot }}</strong>,
                    {{ formatDate(focusedTarget.dayIso) }} — pick a recipe.
                </div>
                <template #action>
                    <BaseButton variant="ghost" dense label="Cancel" @click="emit('cancelTarget')" />
                </template>
            </q-banner>
        </q-card-section>
        <q-separator />
        <div class="recipe-list">
            <q-expansion-item
                v-for="tray in trays"
                :key="tray.key"
                :label="tray.title"
                :default-opened="tray.defaultOpen"
                dense
                header-class="text-weight-medium"
            >
                <q-list separator>
                    <q-item
                        v-for="recipe in tray.recipes"
                        :key="tray.key + recipe.recipe_id"
                        class="recipe-row"
                        :draggable="!isMultiSelect && dragAllowed"
                        :tag="isMultiSelect ? 'label' : undefined"
                        :clickable="isMultiSelect"
                        @pointerdown="(e: PointerEvent) => !isMultiSelect && emit('recipePointerDown', e)"
                        @dragstart="!isMultiSelect && emit('recipeDragStart', recipe.recipe_id)"
                        @dragend="!isMultiSelect && emit('recipeDragEnd')"
                    >
                        <q-item-section v-if="isMultiSelect" side>
                            <q-checkbox
                                :model-value="isSelected(recipe.recipe_id)"
                                @update:model-value="toggleSelection(recipe.recipe_id)"
                            />
                        </q-item-section>
                        <q-item-section
                            :class="isMultiSelect ? '' : 'cursor-pointer'"
                            @click="!isMultiSelect && emit('recipePick', recipe.recipe_id)"
                        >
                            <q-item-label lines="2">{{ recipe.name }}</q-item-label>
                            <q-item-label v-if="batchEnabled && !isMultiSelect" caption>
                                {{ recipe.unallocated_meals }} free
                            </q-item-label>
                        </q-item-section>
                        <q-item-section v-if="batchEnabled && !isMultiSelect" side>
                            <div class="row items-center no-wrap">
                                <BaseButton
                                    variant="icon"
                                    size="sm"
                                    :icon="ICONS.remove"
                                    :disable="recipe.available_meals <= 0"
                                    @click="emit('paletteMealAdjust', recipe.recipe_id, -1)"
                                >
                                    <q-tooltip>One fewer cooked</q-tooltip>
                                </BaseButton>
                                <span class="recipe-row__pool">{{ recipe.available_meals }}</span>
                                <BaseButton
                                    variant="icon"
                                    size="sm"
                                    :icon="ICONS.add"
                                    @click="emit('paletteMealAdjust', recipe.recipe_id, 1)"
                                >
                                    <q-tooltip>One more cooked</q-tooltip>
                                </BaseButton>
                                <BaseButton
                                    variant="icon"
                                    size="sm"
                                    :icon="ICONS.restaurant"
                                    @click="openPaletteLogCook(recipe.recipe_id)"
                                >
                                    <q-tooltip>Log a cook…</q-tooltip>
                                </BaseButton>
                            </div>
                        </q-item-section>
                    </q-item>
                </q-list>
            </q-expansion-item>
            <div v-if="recipes.length === 0" class="dora-text-muted text-center q-py-md">
                No recipes yet — create some in the Cookbook.
            </div>
            <div
                v-else-if="trays.length === 1 && trays[0]?.recipes.length === 0"
                class="dora-text-muted text-center q-py-md"
            >
                No matches.
            </div>
        </div>

        <!-- Log cook from a recipe row ─────────────────────────────── -->
        <BaseDialog v-model="logCookOpen" title="Log a cook" closable card-style="min-width: 320px">
            <q-card-section class="q-pt-none">
                <q-input
                    v-model.number="logCookCount"
                    type="number"
                    min="1"
                    max="999"
                    outlined
                    dense
                    autofocus
                    label="Meals cooked"
                    hint="Adds to the recipe's pool."
                />
            </q-card-section>
            <template #actions>
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <BaseButton
                    variant="primary"
                    label="Log"
                    :loading="logging"
                    :disable="!(logCookCount > 0)"
                    @click="confirmLogCook"
                />
            </template>
        </BaseDialog>
    </q-card>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { useQuasar } from 'quasar';
    import type { Recipe } from 'src/models/recipe';
    import type { RecipeTray } from 'src/composables/useMealPlanner';
    import { useBatchEnabled } from 'src/composables/useBatchEnabled';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { computed, ref } from 'vue';

    const { batchEnabled } = useBatchEnabled();

    const props = withDefaults(
        defineProps<{
            recipeSearch: string;
            trays: RecipeTray[];
            recipes: Recipe[];
            focusedTarget: { dayIso: string; slot: string } | null;
            dragAllowed: boolean;
            formatDate: (iso: string) => string;
            logCook: (recipeId: string, count: number) => Promise<number>;
            /** When set to 'multi-select', rows show a checkbox and click
             *  toggles selection (used by the sequential builder, §9-B).
             *  Default 'click-add' is the original behaviour — click a row
             *  to add the recipe to the focused day/slot. */
            selectionMode?: 'click-add' | 'multi-select';
            /** Selected recipe ids in 'multi-select' mode. Ignored otherwise. */
            selectedIds?: string[];
        }>(),
        { selectionMode: 'click-add', selectedIds: () => [] },
    );

    const emit = defineEmits<{
        (e: 'update:recipeSearch', value: string): void;
        (e: 'update:selectedIds', ids: string[]): void;
        (e: 'cancelTarget'): void;
        (e: 'recipePick', recipeId: string): void;
        (e: 'recipePointerDown', event: PointerEvent): void;
        (e: 'recipeDragStart', recipeId: string): void;
        (e: 'recipeDragEnd'): void;
        (e: 'paletteMealAdjust', recipeId: string, delta: number): void;
    }>();

    const isMultiSelect = computed(() => props.selectionMode === 'multi-select');
    function isSelected(recipeId: string): boolean {
        return props.selectedIds.includes(recipeId);
    }
    function toggleSelection(recipeId: string) {
        const next = isSelected(recipeId)
            ? props.selectedIds.filter((id) => id !== recipeId)
            : [...props.selectedIds, recipeId];
        emit('update:selectedIds', next);
    }

    const $q = useQuasar();
    const logCookOpen = ref(false);
    const logCookCount = ref<number>(1);
    const logCookRecipeId = ref<string | null>(null);
    const logging = ref(false);

    function openPaletteLogCook(recipeId: string) {
        logCookRecipeId.value = recipeId;
        logCookCount.value = 1;
        logCookOpen.value = true;
    }
    async function confirmLogCook() {
        if (!logCookRecipeId.value) return;
        logging.value = true;
        try {
            const n = await props.logCook(logCookRecipeId.value, logCookCount.value);
            logCookOpen.value = false;
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Logged ${n} cooked meal${n === 1 ? '' : 's'}.`,
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not log cook.',
                caption: toastCaption(err),
            });
        } finally {
            logging.value = false;
        }
    }
</script>

<style scoped>
    .recipe-list {
        max-height: 65vh;
        overflow-y: auto;
    }
    .recipe-row {
        cursor: grab;
    }
    .recipe-row__pool {
        min-width: 1.4rem;
        text-align: center;
        font-weight: 600;
    }
</style>
