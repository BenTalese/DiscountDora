<template>
    <div class="q-gutter-md">
        <q-banner class="dora-bg-sunken dora-text-secondary text-caption" dense rounded>
            <template #avatar>
                <q-icon :name="ICONS.info" size="18px" />
            </template>
            Print a printable view of a shopping list or recipe — your browser's
            print dialog lets you "Save as PDF" too. CSV exports give you the
            raw rows for editing in a spreadsheet.
        </q-banner>

        <!-- ── Shopping lists ─────────────────────────────────────── -->
        <q-card flat bordered>
            <q-card-section class="row items-center justify-between q-gutter-sm">
                <div class="row items-center q-gutter-sm">
                    <q-icon :name="ICONS.shopping_cart" size="24px" class="text-primary" />
                    <div class="text-h6">Shopping lists</div>
                </div>
                <q-btn-toggle
                    v-model="listFilter"
                    :options="listFilterOptions"
                    dense
                    flat
                    color="grey"
                    toggle-color="primary"
                />
            </q-card-section>
            <q-separator />
            <q-card-section v-if="loadingLists" class="row items-center q-gutter-sm">
                <q-spinner size="20px" />
                <div class="text-caption dora-text-muted">Loading lists…</div>
            </q-card-section>
            <q-card-section
                v-else-if="filteredShoppingLists.length === 0"
                class="dora-text-secondary"
            >
                <div v-if="(shoppingListStore.summaries ?? []).length === 0">
                    No shopping lists yet.
                    <router-link to="/shopping-lists">Create one</router-link>
                    to get started.
                </div>
                <div v-else>
                    No lists match the current filter.
                </div>
            </q-card-section>
            <q-list v-else separator>
                <q-item
                    v-for="list in filteredShoppingLists"
                    :key="list.shopping_list_id"
                >
                    <q-item-section>
                        <q-item-label>
                            {{ list.name }}
                            <q-chip
                                v-if="list.is_primary"
                                dense
                                size="sm"
                                color="primary"
                                text-color="white"
                                class="q-ml-sm"
                            >
                                Primary
                            </q-chip>
                            <q-chip
                                v-if="list.status === 'done'"
                                dense
                                size="sm"
                                color="grey"
                                text-color="white"
                                class="q-ml-sm"
                            >
                                Archived
                            </q-chip>
                        </q-item-label>
                        <q-item-label caption>
                            {{ list.line_count }} item(s) ·
                            {{ list.ticked_count }} ticked
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <div class="row q-gutter-xs">
                            <q-btn
                                flat
                                dense
                                :icon="ICONS.file_download"
                                label="CSV"
                                no-caps
                                @click="shoppingExport.downloadCsv(list.shopping_list_id)"
                            />
                            <q-btn
                                flat
                                dense
                                :icon="ICONS.print"
                                label="Print"
                                no-caps
                                color="primary"
                                @click="shoppingExport.openPrintView(list.shopping_list_id)"
                            />
                        </div>
                    </q-item-section>
                </q-item>
            </q-list>
        </q-card>

        <!-- ── Recipes ────────────────────────────────────────────── -->
        <q-card flat bordered>
            <q-card-section class="row items-center justify-between q-gutter-sm">
                <div class="row items-center q-gutter-sm">
                    <q-icon :name="ICONS.menu_book" size="24px" class="text-primary" />
                    <div class="text-h6">Recipes</div>
                </div>
                <q-input
                    v-model="recipeFilter"
                    dense
                    outlined
                    clearable
                    placeholder="Filter by name"
                    style="width: 240px"
                >
                    <template #prepend>
                        <q-icon :name="ICONS.search" size="16px" />
                    </template>
                </q-input>
            </q-card-section>
            <q-separator />
            <q-card-section v-if="loadingRecipes" class="row items-center q-gutter-sm">
                <q-spinner size="20px" />
                <div class="text-caption dora-text-muted">Loading recipes…</div>
            </q-card-section>
            <q-card-section
                v-else-if="filteredRecipes.length === 0"
                class="dora-text-secondary"
            >
                <div v-if="(recipeStore.recipes ?? []).length === 0">
                    No recipes yet.
                    <router-link to="/recipes">Create one</router-link> to get started.
                </div>
                <div v-else>
                    No recipes match "{{ recipeFilter }}".
                </div>
            </q-card-section>
            <q-list v-else separator>
                <q-item
                    v-for="recipe in filteredRecipes"
                    :key="recipe.recipe_id"
                >
                    <q-item-section>
                        <q-item-label>
                            {{ recipe.name }}
                            <q-chip
                                v-if="recipe.is_favourite"
                                dense
                                size="sm"
                                color="warning"
                                text-color="white"
                                class="q-ml-sm"
                            >
                                ★
                            </q-chip>
                        </q-item-label>
                        <q-item-label caption>
                            <span v-if="recipe.category">{{ recipe.category }}</span>
                            <span v-if="recipe.servings">
                                · {{ recipe.servings }} serving(s)
                            </span>
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <div class="row q-gutter-xs">
                            <q-btn
                                flat
                                dense
                                :icon="ICONS.file_download"
                                label="CSV"
                                no-caps
                                @click="recipeExport.downloadCsv(recipe.recipe_id)"
                            />
                            <q-btn
                                flat
                                dense
                                :icon="ICONS.print"
                                label="Print"
                                no-caps
                                color="primary"
                                @click="recipeExport.openPrintView(recipe.recipe_id)"
                            />
                        </div>
                    </q-item-section>
                </q-item>
            </q-list>
        </q-card>

        <!-- ── Stock overview (install-wide) ─────────────────────────── -->
        <q-card flat bordered>
            <q-card-section class="row items-center justify-between q-gutter-sm">
                <div class="row items-center q-gutter-sm">
                    <q-icon name="inventory_2" size="24px" class="text-primary" />
                    <div>
                        <div class="text-h6">Stock overview</div>
                        <div class="text-caption dora-text-muted">
                            Every stock item, grouped by location — handy as a
                            stocktake printout.
                        </div>
                    </div>
                </div>
                <div class="row q-gutter-xs">
                    <q-btn
                        flat
                        dense
                        :icon="ICONS.file_download"
                        label="CSV"
                        no-caps
                        @click="overviewExport.downloadCsv()"
                    />
                    <q-btn
                        flat
                        dense
                        :icon="ICONS.print"
                        label="Print"
                        no-caps
                        color="primary"
                        @click="overviewExport.openPrintView()"
                    />
                </div>
            </q-card-section>
        </q-card>

        <!-- ── Meal plans ────────────────────────────────────────────── -->
        <q-card flat bordered>
            <q-card-section class="row items-center q-gutter-sm">
                <q-icon :name="ICONS.calendar_month" size="24px" class="text-primary" />
                <div class="text-h6">Meal plans</div>
            </q-card-section>
            <q-separator />
            <q-card-section
                v-if="(mealStore.mealPlans ?? []).length === 0"
                class="dora-text-secondary"
            >
                No meal plans yet.
                <router-link to="/meal-plans">Create one</router-link>
                to get started.
            </q-card-section>
            <q-list v-else separator>
                <q-item
                    v-for="plan in (mealStore.mealPlans ?? [])"
                    :key="plan.meal_plan_id"
                >
                    <q-item-section>
                        <q-item-label>{{ plan.name }}</q-item-label>
                        <q-item-label caption>
                            Starts {{ plan.start_date }} · {{ plan.entries.length }} entr(y/ies)
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <div class="row q-gutter-xs">
                            <q-btn
                                flat
                                dense
                                :icon="ICONS.file_download"
                                label="CSV"
                                no-caps
                                @click="mealPlanExport.downloadCsv(plan.meal_plan_id)"
                            />
                            <q-btn
                                flat
                                dense
                                :icon="ICONS.print"
                                label="Print"
                                no-caps
                                color="primary"
                                @click="mealPlanExport.openPrintView(plan.meal_plan_id)"
                            />
                        </div>
                    </q-item-section>
                </q-item>
            </q-list>
        </q-card>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { computed, onMounted, ref } from 'vue';
    import { useMealPlanStore } from 'src/stores/mealPlanStore';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useMealPlanExport } from 'src/composables/useMealPlanExport';
    import { useRecipeExport } from 'src/composables/useRecipeExport';
    import { useShoppingListExport } from 'src/composables/useShoppingListExport';
    import { useStockOverviewExport } from 'src/composables/useStockOverviewExport';

    const shoppingListStore = useShoppingListStore();
    const recipeStore = useRecipeStore();
    const mealStore = useMealPlanStore();
    const shoppingExport = useShoppingListExport();
    const recipeExport = useRecipeExport();
    const mealPlanExport = useMealPlanExport();
    const overviewExport = useStockOverviewExport();

    type ListFilter = 'active' | 'archived' | 'all';
    const listFilter = ref<ListFilter>('active');
    const listFilterOptions = [
        { label: 'Active', value: 'active' },
        { label: 'Archived', value: 'archived' },
        { label: 'All', value: 'all' },
    ];

    const recipeFilter = ref('');

    const loadingLists = ref(false);
    const loadingRecipes = ref(false);

    const filteredShoppingLists = computed(() => {
        const all = shoppingListStore.summaries ?? [];
        let filtered = all;
        if (listFilter.value === 'active') {
            filtered = all.filter((s) => s.status !== 'done');
        } else if (listFilter.value === 'archived') {
            filtered = all.filter((s) => s.status === 'done');
        }
        // Sort: primary first, then active by recency, archived last.
        return [...filtered].sort((a, b) => {
            if (a.is_primary !== b.is_primary) return a.is_primary ? -1 : 1;
            const aDone = a.status === 'done';
            const bDone = b.status === 'done';
            if (aDone !== bDone) return aDone ? 1 : -1;
            return (b.created_at ?? '').localeCompare(a.created_at ?? '');
        });
    });

    const filteredRecipes = computed(() => {
        const needle = recipeFilter.value.trim().toLowerCase();
        const all = recipeStore.recipes ?? [];
        if (!needle) return all;
        return all.filter((r) => r.name.toLowerCase().includes(needle));
    });

    onMounted(async () => {
        // Stores may already be hydrated from a prior visit; refresh in
        // the background so this page never shows stale-looking counts.
        const hadLists = (shoppingListStore.summaries ?? []).length > 0;
        const hadRecipes = (recipeStore.recipes ?? []).length > 0;
        loadingLists.value = !hadLists;
        loadingRecipes.value = !hadRecipes;
        try {
            await Promise.all([
                shoppingListStore.refreshAsync(),
                recipeStore.getRecipesAsync(),
                mealStore.getMealPlansAsync(),
            ]);
        } finally {
            loadingLists.value = false;
            loadingRecipes.value = false;
        }
    });
</script>
