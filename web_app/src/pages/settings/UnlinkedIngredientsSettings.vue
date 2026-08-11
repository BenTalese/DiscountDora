<template>
    <!-- IMPL_PLAN_RECIPE_IMPORTER §Chunk 6 — bulk-linker for unlinked
         recipe ingredients. Chunk 5's paste importer produces
         `stock_item_id=null` rows when RapidFuzz can't match; this page
         is where the user resolves them in one sitting instead of
         page-by-page editing. Grouped by normalised raw_text
         (server-owned) with count + affected-recipe list; picking a
         StockItem links every row in the group with one request. -->
    <div class="settings-page q-gutter-md">
        <SettingsPageHeader
            title="Unlinked ingredients"
            description="Recipe ingredients that couldn't be matched to a tracked stock item when you imported them. Link each one to a stock item — Dora updates every recipe that uses that text in one go. Recipes flip back to a real cookable / not-cookable state as soon as their last unlinked row is resolved."
            :icon="ICONS.link"
        />

        <div v-if="loading" class="row items-center q-gutter-sm">
            <q-spinner-dots size="24px" color="primary" />
            <span class="text-caption dora-text-muted">Loading…</span>
        </div>

        <div
            v-else-if="groups.length === 0"
            class="dora-text-muted text-caption q-pa-md"
        >
            No unlinked ingredients right now. Every recipe ingredient is
            linked to a stock item.
        </div>

        <q-card v-else flat bordered>
            <q-list separator>
                <q-item
                    v-for="group in groups"
                    :key="group.raw_text"
                    class="q-py-md"
                >
                    <q-item-section>
                        <q-item-label>{{ group.raw_text }}</q-item-label>
                        <q-item-label caption>
                            Used in {{ group.count }}
                            recipe<template v-if="group.count !== 1">s</template>
                        </q-item-label>
                    </q-item-section>
                    <q-item-section style="min-width: 260px; max-width: 360px">
                        <q-select
                            v-model="picks[group.raw_text]"
                            :options="stockItemOptions(group.raw_text)"
                            emit-value
                            map-options
                            outlined
                            dense
                            use-input
                            fill-input
                            hide-selected
                            input-debounce="80"
                            label="Link to stock item"
                            @filter="(value, update) => onFilter(group.raw_text, value, update)"
                        >
                            <template #no-option>
                                <q-item>
                                    <q-item-section class="text-caption dora-text-muted">
                                        No matches. Use "Create new" →
                                    </q-item-section>
                                </q-item>
                            </template>
                        </q-select>
                    </q-item-section>
                    <q-item-section side>
                        <div class="row q-gutter-xs">
                            <BaseButton
                                variant="primary"
                                :label="linkingKey === group.raw_text ? 'Linking…' : 'Link'"
                                :loading="linkingKey === group.raw_text"
                                :disable="!picks[group.raw_text]"
                                @click="onLink(group)"
                            />
                            <BaseButton
                                variant="ghost"
                                label="Create new"
                                @click="onCreateAndLink(group)"
                            />
                        </div>
                    </q-item-section>
                </q-item>
            </q-list>
        </q-card>
    </div>
</template>

<script setup lang="ts">
    /**
     * IMPL_PLAN_RECIPE_IMPORTER §Chunk 6 — the whole page is a
     * one-request-per-group workflow:
     *
     *   1. GET /api/recipes/unlinked-ingredients → grouped rows (the
     *      server owns the normalisation, so what the SPA calls "one
     *      group" is exactly what the linker updates).
     *   2. User picks a StockItem from the autocomplete (or creates
     *      one seeded from the raw_text).
     *   3. POST /api/recipes/unlinked-ingredients/bulk-link with the
     *      raw_text + stock_item_id → server atomically flips the FK
     *      on every matching row. Cookability re-derives on the next
     *      recipe read (R-003 — server-owned).
     *   4. Refresh the list so the linked group disappears.
     *
     * Charter P1 Effortless: no per-recipe walkthrough. Charter P12
     * No-invent: only shows the actual unlinked set — nothing is
     * fabricated for the user to link.
     */
    import { computed, onMounted, reactive, ref, watch } from 'vue';
    import { useQuasar } from 'quasar';
    import BaseButton from 'src/components/BaseButton.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import { ICONS } from 'src/style/icons';
    import RecipeApiService, {
        type UnlinkedIngredientGroup,
    } from 'src/services/api/recipeApiService';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { storeToRefs } from 'pinia';

    const $q = useQuasar();
    const recipeApi = new RecipeApiService();

    const stockItemStore = useStockItemStore();
    const { stockItems } = storeToRefs(stockItemStore);
    const stockLevelStore = useStockLevelStore();
    const { stockLevels } = storeToRefs(stockLevelStore);

    const groups = ref<UnlinkedIngredientGroup[]>([]);
    const loading = ref(false);
    const linkingKey = ref<string | null>(null);

    // Keyed by group.raw_text — the picker's selected stock_item_id.
    const picks = reactive<Record<string, string | null>>({});
    // Per-group q-select filter text (autocomplete input). We keep
    // an independent filter buffer per group so typing in one row
    // doesn't reset another row's options.
    const filters = reactive<Record<string, string>>({});

    const stockItemsSorted = computed(() =>
        [...stockItems.value].sort((a, b) => a.name.localeCompare(b.name)),
    );

    function stockItemOptions(rawText: string) {
        const q = (filters[rawText] ?? '').trim().toLowerCase();
        const src = stockItemsSorted.value;
        const filtered = q
            ? src.filter((si) => si.name.toLowerCase().includes(q))
            : src;
        return filtered.slice(0, 50).map((si) => ({
            label: si.name,
            value: si.stock_item_id,
        }));
    }

    function onFilter(
        rawText: string,
        value: string,
        update: (cb: () => void) => void,
    ) {
        // Quasar's use-input picker hands us (value, update) — value is
        // the current text, update is a commit callback so the filtered
        // options render in the same tick as the input keys. We store
        // the value keyed by group and let stockItemOptions() re-derive.
        update(() => {
            filters[rawText] = value;
        });
    }

    // The store's stockItems can start empty on first mount; hydrate.
    onMounted(async () => {
        await Promise.all([
            stockItemStore.ensureLoadedAsync(),
            stockLevelStore.ensureLoadedAsync(),
            refresh(),
        ]);
    });

    // If the stock-item list refreshes mid-page (rare — e.g. after
    // "Create new" adds one), re-derive the picker options.
    watch(stockItems, () => { /* computed picks it up */ });

    async function refresh() {
        loading.value = true;
        try {
            const dto = await recipeApi.getUnlinkedIngredientsAsync();
            groups.value = dto.unlinked;
        } catch (err) {
            console.warn('Failed to load unlinked ingredients', err);
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not load unlinked ingredients.',
            });
        } finally {
            loading.value = false;
        }
    }

    async function onLink(group: UnlinkedIngredientGroup) {
        const stockItemId = picks[group.raw_text];
        if (!stockItemId) return;
        linkingKey.value = group.raw_text;
        try {
            const result = await recipeApi.bulkLinkUnlinkedIngredientsAsync(
                group.raw_text,
                stockItemId,
            );
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message:
                    result.linked_count === 1
                        ? `Linked "${group.raw_text}" in 1 recipe.`
                        : `Linked "${group.raw_text}" in ${result.linked_count} recipes.`,
            });
            delete picks[group.raw_text];
            delete filters[group.raw_text];
            await refresh();
        } catch (err) {
            console.warn('Bulk-link failed', err);
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not link. Try again in a moment.',
            });
        } finally {
            linkingKey.value = null;
        }
    }

    async function onCreateAndLink(group: UnlinkedIngredientGroup) {
        // Default the new item to the most-stocked level so it doesn't
        // immediately count as "missing" — the user hasn't told us
        // otherwise, and pulling it out of an imported recipe implies
        // they do have some of it. Mirrors RecipeDetailPage's "create
        // new inline" flow (search this file: `wellStocked` in
        // RecipeDetailPage.vue).
        const wellStocked = stockLevels.value[0];
        if (!wellStocked) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'No stock levels configured — cannot create.',
            });
            return;
        }
        const name = group.raw_text.trim();
        if (!name) return;
        linkingKey.value = group.raw_text;
        try {
            const created = await stockItemStore.createStockItemAsync({
                name,
                stock_level_id: wellStocked.stock_level_id,
                stock_location_id: null,
            });
            const result = await recipeApi.bulkLinkUnlinkedIngredientsAsync(
                group.raw_text,
                created.stock_item_id,
            );
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message:
                    result.linked_count === 1
                        ? `Created "${name}" and linked in 1 recipe.`
                        : `Created "${name}" and linked in ${result.linked_count} recipes.`,
            });
            delete picks[group.raw_text];
            delete filters[group.raw_text];
            await refresh();
        } catch (err) {
            console.warn('Create + bulk-link failed', err);
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not create + link. Try again in a moment.',
            });
        } finally {
            linkingKey.value = null;
        }
    }
</script>
