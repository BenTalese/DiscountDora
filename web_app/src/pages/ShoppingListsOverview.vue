<template>
    <q-page padding>
        <div class="row items-center q-mb-md">
            <div class="text-caption dora-text-muted">
                {{ activeCount }} active, {{ archivedCount }} archived.
                <span v-if="!primarySummary && activeCount > 0">
                    · No primary list set — pick one for quick-add.
                </span>
            </div>
            <q-space />
            <q-btn-dropdown
                color="primary"
                no-caps
                :icon="ICONS.add"
                label="New list"
                :loading="creating || autogenerating"
                split
                @click="onCreate"
            >
                <q-list style="min-width: 320px">
                    <q-item-label header class="q-pb-none">From your stock</q-item-label>
                    <q-item clickable v-close-popup @click="onAutogenerateNew('flagged')">
                        <q-item-section avatar>
                            <q-icon :name="ICONS.auto_awesome" color="primary" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>From flagged items</q-item-label>
                            <q-item-label caption>
                                Every essential that's low or out of stock.
                            </q-item-label>
                        </q-item-section>
                    </q-item>
                    <q-item clickable v-close-popup @click="openAdvancedAutogen">
                        <q-item-section avatar>
                            <q-icon :name="ICONS.tune" color="primary" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>Advanced auto-generate…</q-item-label>
                            <q-item-label caption>
                                Pick exactly which sources to draw from.
                            </q-item-label>
                        </q-item-section>
                    </q-item>
                    <q-item clickable v-close-popup @click="onAutogenerateNew('low_or_out')">
                        <q-item-section avatar>
                            <q-icon :name="ICONS.warning" color="warning" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>
                                From all low/out stock
                                <q-badge
                                    v-if="lowOrOutCount > 0"
                                    color="warning"
                                    text-color="dark"
                                    class="q-ml-xs"
                                >
                                    {{ lowOrOutCount }}
                                </q-badge>
                            </q-item-label>
                            <q-item-label caption>
                                Every item below Sufficient stock — flagged or not.
                            </q-item-label>
                        </q-item-section>
                    </q-item>
                    <q-item
                        v-if="primarySummary"
                        clickable
                        v-close-popup
                        @click="onAutogenerateOntoPrimary"
                    >
                        <q-item-section avatar>
                            <q-icon :name="ICONS.playlist_add" color="primary" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>Top up the primary list</q-item-label>
                            <q-item-label caption>
                                Adds flagged-and-low items missing from
                                "{{ primarySummary.name }}".
                            </q-item-label>
                        </q-item-section>
                    </q-item>
                    <q-separator />
                    <q-item-label header class="q-pb-none">From your cooking</q-item-label>
                    <q-item clickable v-close-popup @click="onPickRecipe">
                        <q-item-section avatar>
                            <q-icon :name="ICONS.menu_book" color="primary" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>From a recipe…</q-item-label>
                            <q-item-label caption>
                                Pick a recipe and add its ingredients to a new list.
                            </q-item-label>
                        </q-item-section>
                    </q-item>
                    <q-item clickable v-close-popup @click="onPickMealPlan">
                        <q-item-section avatar>
                            <q-icon :name="ICONS.event_note" color="primary" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>From a meal plan…</q-item-label>
                            <q-item-label caption>
                                Aggregate ingredients across every meal in a plan.
                            </q-item-label>
                        </q-item-section>
                    </q-item>
                    <q-separator />
                    <q-item-label header class="q-pb-none">Other</q-item-label>
                    <q-item clickable v-close-popup @click="onPickTemplate">
                        <q-item-section avatar>
                            <q-icon :name="ICONS.bookmarks" color="primary" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>From a template…</q-item-label>
                            <q-item-label caption>
                                Pick a saved template to spin up a new list.
                            </q-item-label>
                        </q-item-section>
                    </q-item>
                    <q-item clickable v-close-popup to="/shopping-lists/templates">
                        <q-item-section avatar>
                            <q-icon :name="ICONS.settings" />
                        </q-item-section>
                        <q-item-section>Manage templates…</q-item-section>
                    </q-item>
                </q-list>
            </q-btn-dropdown>
        </div>

        <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-mb-md" dense rounded>
            {{ loadError }}
        </q-banner>

        <q-tabs
            v-model="tab"
            dense
            class="text-primary q-mb-sm"
            active-color="primary"
            indicator-color="primary"
            align="left"
        >
            <q-tab name="active" no-caps>
                Active
                <q-badge v-if="activeCount > 0" floating color="primary">{{ activeCount }}</q-badge>
            </q-tab>
            <q-tab name="archived" no-caps>
                Archived
                <q-badge v-if="archivedCount > 0" floating color="grey">{{ archivedCount }}</q-badge>
            </q-tab>
        </q-tabs>
        <q-separator />

        <FadeTransition mode="out-in">
        <div v-if="loading && summaries.length === 0" key="sl-loading" class="text-center q-py-xl">
            <q-spinner color="primary" size="48px" />
        </div>

        <div v-else-if="visibleLists.length === 0" key="sl-empty" class="text-center dora-text-muted q-py-xl">
            <q-icon :name="ICONS.shopping_cart" size="60px" class="q-mb-sm" />
            <template v-if="tab === 'active'">
                <div class="text-h6">No active shopping lists yet.</div>
                <div
                    v-if="lowOrOutCount > 0"
                    class="q-mt-md"
                >
                    {{ lowOrOutCount }} item{{ lowOrOutCount === 1 ? ' is' : 's are' }}
                    low or out of stock — kickstart a list:
                    <div class="row justify-center q-gutter-sm q-mt-sm">
                        <q-btn
                            color="primary"
                            no-caps
                            :icon="ICONS.auto_awesome"
                            :label="`Auto-generate from low/out (${lowOrOutCount})`"
                            :loading="autogenerating"
                            @click="onAutogenerateNew('low_or_out')"
                        />
                        <q-btn
                            outline
                            no-caps
                            :icon="ICONS.add"
                            label="Empty list"
                            :loading="creating"
                            @click="onCreate"
                        />
                    </div>
                </div>
                <div v-else class="q-mt-md">
                    Stock is full — when items go low, "New list" can
                    auto-generate from low/out items.
                </div>
            </template>
            <div v-else>No archived lists yet — finished lists show up here.</div>
        </div>

        <div v-else key="sl-content" class="row q-col-gutter-md q-mt-sm">
            <div
                v-for="list in visibleLists"
                :key="list.shopping_list_id"
                class="col-12 col-sm-6 col-md-4"
            >
                <q-card
                    flat
                    bordered
                    class="cursor-pointer shopping-list-card"
                    :class="{
                        'shopping-list-primary': list.is_primary,
                        'shopping-list-archived': list.is_archived,
                    }"
                    @click="openList(list.shopping_list_id)"
                >
                    <q-card-section class="row items-start">
                        <div class="col">
                            <div class="text-h6">
                                {{ list.name }}
                                <q-badge
                                    v-if="list.is_primary"
                                    color="primary"
                                    text-color="white"
                                    class="q-ml-sm"
                                >
                                    Primary
                                </q-badge>
                            </div>
                            <div class="text-caption dora-text-muted">
                                Created {{ formatDate(list.created_at) }}
                                <span v-if="list.completed_at">
                                    · Finished {{ formatDate(list.completed_at) }}
                                </span>
                            </div>
                        </div>

                        <q-btn flat round dense :icon="ICONS.more_vert" @click.stop>
                            <q-menu transition-show="jump-down" transition-hide="jump-up">
                                <q-list dense style="min-width: 220px">
                                    <q-item clickable v-close-popup @click.stop="openList(list.shopping_list_id)">
                                        <q-item-section avatar><q-icon :name="ICONS.open_in_new" /></q-item-section>
                                        <q-item-section>Open</q-item-section>
                                    </q-item>
                                    <q-item
                                        v-if="!list.is_archived && !list.is_primary"
                                        clickable
                                        v-close-popup
                                        @click.stop="setPrimary(list.shopping_list_id)"
                                    >
                                        <q-item-section avatar><q-icon :name="ICONS.star" /></q-item-section>
                                        <q-item-section>Set as primary</q-item-section>
                                    </q-item>
                                    <q-item
                                        v-if="!list.is_archived"
                                        clickable
                                        v-close-popup
                                        :disable="
                                            list.line_count - list.ticked_count === 0
                                        "
                                        @click.stop="copyList(list.shopping_list_id, 'unticked')"
                                    >
                                        <q-item-section avatar>
                                            <q-icon :name="ICONS.content_copy" />
                                        </q-item-section>
                                        <q-item-section>
                                            <q-item-label>Copy unticked → new list</q-item-label>
                                            <q-item-label
                                                v-if="list.line_count - list.ticked_count === 0"
                                                caption
                                            >
                                                Nothing unticked to copy
                                            </q-item-label>
                                        </q-item-section>
                                    </q-item>
                                    <q-item
                                        v-if="list.is_archived"
                                        clickable
                                        v-close-popup
                                        @click.stop="copyList(list.shopping_list_id, 'all')"
                                    >
                                        <q-item-section avatar><q-icon :name="ICONS.content_copy" /></q-item-section>
                                        <q-item-section>Copy archived → new list</q-item-section>
                                    </q-item>
                                    <q-separator />
                                    <q-item
                                        v-if="!list.is_archived"
                                        clickable
                                        v-close-popup
                                        @click.stop="archiveList(list)"
                                    >
                                        <q-item-section avatar><q-icon :name="ICONS.archive" /></q-item-section>
                                        <q-item-section>Archive list</q-item-section>
                                    </q-item>
                                    <q-item
                                        clickable
                                        v-close-popup
                                        @click.stop="onDelete(list)"
                                    >
                                        <q-item-section avatar>
                                            <q-icon :name="ICONS.delete" color="negative" />
                                        </q-item-section>
                                        <q-item-section class="text-negative">
                                            Delete list
                                        </q-item-section>
                                    </q-item>
                                </q-list>
                            </q-menu>
                        </q-btn>
                    </q-card-section>

                    <q-separator />

                    <q-card-section class="row items-center">
                        <q-circular-progress
                            :value="progressValue(list)"
                            size="40px"
                            :thickness="0.2"
                            color="primary"
                            
                        >
                            {{ list.ticked_count }}/{{ list.line_count }}
                        </q-circular-progress>
                        <div class="q-ml-md col">
                            <div class="text-body2">
                                {{ remainingCount(list) }} item{{
                                    remainingCount(list) === 1 ? '' : 's'
                                }} remaining
                            </div>
                            <div class="text-caption dora-text-muted">
                                {{ list.line_count }} total ·
                                {{ list.ticked_count }} ticked
                            </div>
                        </div>
                    </q-card-section>

                    <!-- Primary card gets a richer stats strip with the
                         live dollar totals. We only fetch detail for the
                         primary list so the overview stays cheap. -->
                    <q-separator v-if="list.is_primary" />
                    <q-card-section
                        v-if="list.is_primary"
                        class="row q-gutter-md q-pt-sm q-pb-sm primary-stats"
                    >
                        <template v-if="primaryStats">
                            <div class="col">
                                <div class="text-caption dora-text-muted">Remaining</div>
                                <div class="text-subtitle1">
                                    ${{ primaryStats.remaining.toFixed(2) }}
                                </div>
                            </div>
                            <div class="col">
                                <div class="text-caption dora-text-muted">Full total</div>
                                <div class="text-subtitle1">
                                    ${{ primaryStats.full.toFixed(2) }}
                                </div>
                            </div>
                            <div v-if="primaryStats.savings > 0" class="col">
                                <div class="text-caption dora-text-muted">Saves vs RRP</div>
                                <div class="text-subtitle1 text-positive">
                                    ${{ primaryStats.savings.toFixed(2) }}
                                </div>
                            </div>
                        </template>
                        <template v-else>
                            <div class="col text-caption dora-text-muted">
                                <q-spinner size="14px" /> Loading totals…
                            </div>
                        </template>
                    </q-card-section>
                </q-card>
            </div>
        </div>
        </FadeTransition>

        <BaseDialog v-model="advancedOpen" card-style="min-width: 360px; max-width: 480px">
                <q-card-section>
                    <div class="text-h6">Auto-generate shopping list</div>
                    <div class="text-caption dora-text-muted">
                        Pick which sources to draw from. Items are deduped so
                        nothing gets added twice.
                    </div>
                </q-card-section>
                <q-card-section class="q-pt-none">
                    <q-checkbox
                        v-model="advanced.low_stock"
                        label="Low-stock items"
                    />
                    <q-checkbox
                        v-model="advanced.out_of_stock"
                        label="Out-of-stock items"
                    />
                    <q-checkbox
                        v-model="advanced.essentials_only_for_low"
                        label="Essentials only for the low/out picks"
                    />
                    <q-checkbox
                        v-model="advanced.flagged"
                        label="Items flagged as always-include"
                    />
                    <q-checkbox
                        v-model="advanced.frequently_added"
                        label="Frequently added in past lists"
                    />
                    <q-separator class="q-my-md" />
                    <div class="text-caption dora-text-muted q-mb-xs">Target</div>
                    <q-select
                        v-model="advanced.merge_into_list_id"
                        :options="mergeOptions"
                        emit-value
                        map-options
                        outlined
                        dense
                        label="Merge into list"
                        hint="Leave blank to create a fresh list."
                    />
                </q-card-section>
                <q-card-actions align="right">
                    <q-btn flat label="Cancel" no-caps v-close-popup />
                    <q-btn
                        flat
                        no-caps
                        label="Create new list"
                        color="primary"
                        :loading="autogenerating"
                        @click="runAdvancedAutogen(true)"
                    />
                    <q-btn
                        no-caps
                        unelevated
                        label="Merge into selected"
                        color="primary"
                        :disable="!advanced.merge_into_list_id"
                        :loading="autogenerating"
                        @click="runAdvancedAutogen(false)"
                    />
                </q-card-actions>
        </BaseDialog>
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import FadeTransition from 'src/components/transitions/FadeTransition.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import {
        priceOfLine,
        savingsOfLine,
        type ShoppingListSummary,
    } from 'src/models/shoppingList';
    import MealPlanApiService from 'src/services/api/mealPlanApiService';
    import RecipeApiService from 'src/services/api/recipeApiService';
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import ShoppingListTemplateApiService from 'src/services/api/shoppingListTemplateApiService';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { computed, onMounted, reactive, ref, watch } from 'vue';
    import { useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const router = useRouter();
    const api = new ShoppingListApiService();
    const templateApi = new ShoppingListTemplateApiService();
    const recipeApi = new RecipeApiService();
    const mealPlanApi = new MealPlanApiService();
    const store = useShoppingListStore();
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);

    const tab = ref<'active' | 'archived'>('active');
    const creating = ref(false);
    const autogenerating = ref(false);

    const summaries = computed(() => store.summaries);
    const loading = computed(() => store.loading);
    const loadError = computed(() => store.loadError);
    const primarySummary = computed(() => store.primarySummary);

    const activeCount = computed(() => summaries.value.filter((s) => !s.is_archived).length);
    const archivedCount = computed(() => summaries.value.filter((s) => s.is_archived).length);

    // Count of stock items currently Low or Out — used by the empty state
    // and the "Auto-generate from low/out" menu entry. Computed off the
    // stockItem + stockLevel stores so it tracks any concurrent changes
    // (restock, level edit) without us having to re-fetch.
    const lowOrOutCount = computed(() => {
        const lowOutLevelIds = new Set(
            stockLevels.value
                .filter((l) => l.name === 'Low Stock' || l.name === 'Out of Stock')
                .map((l) => l.stock_level_id),
        );
        if (lowOutLevelIds.size === 0) return 0;
        return stockItems.value.filter((s) => lowOutLevelIds.has(s.stock_level_id)).length;
    });

    function remainingCount(list: ShoppingListSummary): number {
        return Math.max(0, list.line_count - list.ticked_count);
    }

    // Primary list dollar stats. The summary DTO is intentionally cheap
    // (no offer joins), so we lazy-fetch the full detail of the primary
    // list to surface remaining/full/savings on its card.
    const primaryStats = ref<{
        remaining: number;
        full: number;
        savings: number;
    } | null>(null);

    async function loadPrimaryStats() {
        const summary = primarySummary.value;
        if (!summary) {
            primaryStats.value = null;
            return;
        }
        primaryStats.value = null;
        try {
            const detail = await api.getDetailAsync(summary.shopping_list_id);
            let remaining = 0;
            let full = 0;
            let savings = 0;
            for (const line of detail.lines) {
                const price = priceOfLine(line);
                full += price;
                if (!line.is_ticked) remaining += price;
                savings += savingsOfLine(line);
            }
            primaryStats.value = { remaining, full, savings };
        } catch {
            // Non-fatal — the card just shows "Loading totals…" indefinitely
            // in this case, which is benign and re-tries on next refresh.
            primaryStats.value = null;
        }
    }

    // Whenever the primary list changes (after a refresh / set-primary
    // action), reload its stats. We key on the id rather than the whole
    // summary object so changes to other lists don't refetch.
    watch(
        () => primarySummary.value?.shopping_list_id ?? null,
        () => {
            void loadPrimaryStats();
        },
    );

    const visibleLists = computed(() =>
        tab.value === 'active'
            ? summaries.value.filter((s) => !s.is_archived)
            : summaries.value.filter((s) => s.is_archived)
    );

    function progressValue(list: ShoppingListSummary): number {
        if (list.line_count === 0) return 0;
        return Math.round((list.ticked_count / list.line_count) * 100);
    }

    function formatDate(iso: string): string {
        try {
            return new Date(iso).toLocaleDateString();
        } catch {
            return iso;
        }
    }

    function openList(id: string) {
        void router.push(`/shopping-lists/${id}`);
    }

    async function onCreate() {
        // First list is auto-primary so the cart button starts working
        // immediately without a "pick a primary" hand-hold.
        const makePrimary = activeCount.value === 0;
        creating.value = true;
        try {
            const { shopping_list_id } = await api.createAsync({
                make_primary: makePrimary,
            });
            await store.refreshAsync();
            void router.push(`/shopping-lists/${shopping_list_id}`);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not create list.',
                caption: describeApiError(err) || '',
            });
        } finally {
            creating.value = false;
        }
    }

    async function runAutogen(
        targetListId: string | null,
        source: 'flagged' | 'low_or_out',
    ) {
        autogenerating.value = true;
        try {
            // X5 — map the legacy two-source quick-pick to the new
            // multi-source endpoint. 'flagged' = essential-and-low;
            // 'low_or_out' = every item that's low or out, regardless.
            const result = await api.autoGenerateAsync({
                merge_into_list_id: targetListId,
                sources:
                    source === 'flagged'
                        ? {
                              low_stock: true,
                              out_of_stock: true,
                              essentials_only_for_low: true,
                              flagged: true,
                          }
                        : { low_stock: true, out_of_stock: true },
            });
            await Promise.all([store.refreshAsync(), loadPrimaryStats()]);
            if (result.nothing_to_add) {
                $q.notify({
                    type: 'info',
                    position: 'bottom-right',
                    message:
                        source === 'flagged'
                            ? 'Nothing to auto-add. Flag essentials on items that are low or out of stock first.'
                            : 'Nothing low or out — stock is in good shape.',
                    timeout: 5000,
                });
                return;
            }
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message:
                    `Auto-generated: ${result.added_count} added` +
                    (result.skipped_already_on_list > 0
                        ? `, ${result.skipped_already_on_list} already on list`
                        : ''),
            });
            if (result.shopping_list_id) {
                void router.push(`/shopping-lists/${result.shopping_list_id}`);
            }
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not auto-generate.',
                caption: describeApiError(err) || '',
            });
        } finally {
            autogenerating.value = false;
        }
    }

    function onAutogenerateNew(source: 'flagged' | 'low_or_out' = 'flagged') {
        void runAutogen(null, source);
    }
    function onAutogenerateOntoPrimary() {
        if (!primarySummary.value) return;
        void runAutogen(primarySummary.value.shopping_list_id, 'flagged');
    }

    // X5 advanced modal — full multi-source picker.
    const advancedOpen = ref(false);
    const mergeOptions = computed(() => [
        { label: 'Create a fresh list', value: null },
        ...summaries.value
            .filter((s) => !s.is_archived)
            .map((s) => ({
                label: s.is_primary ? `${s.name} (primary)` : s.name,
                value: s.shopping_list_id,
            })),
    ]);
    const advanced = reactive({
        low_stock: true,
        out_of_stock: true,
        essentials_only_for_low: false,
        flagged: false,
        frequently_added: false,
        merge_into_list_id: null as string | null,
    });
    function openAdvancedAutogen() {
        advanced.low_stock = true;
        advanced.out_of_stock = true;
        advanced.essentials_only_for_low = false;
        advanced.flagged = false;
        advanced.frequently_added = false;
        advanced.merge_into_list_id =
            primarySummary.value?.shopping_list_id ?? null;
        advancedOpen.value = true;
    }
    async function runAdvancedAutogen(asNew: boolean) {
        autogenerating.value = true;
        try {
            const result = await api.autoGenerateAsync({
                merge_into_list_id: asNew ? null : advanced.merge_into_list_id,
                sources: {
                    low_stock: advanced.low_stock,
                    out_of_stock: advanced.out_of_stock,
                    essentials_only_for_low: advanced.essentials_only_for_low,
                    flagged: advanced.flagged,
                    frequently_added: advanced.frequently_added,
                },
            });
            advancedOpen.value = false;
            await Promise.all([store.refreshAsync(), loadPrimaryStats()]);
            if (result.nothing_to_add) {
                $q.notify({
                    type: 'info',
                    position: 'bottom-right',
                    message: 'Nothing matched the selected sources.',
                });
                return;
            }
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message:
                    `Auto-generated: ${result.added_count} added` +
                    (result.skipped_already_on_list > 0
                        ? `, ${result.skipped_already_on_list} already on list`
                        : ''),
            });
            if (result.shopping_list_id) {
                void router.push(`/shopping-lists/${result.shopping_list_id}`);
            }
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not auto-generate.',
                caption: describeApiError(err) || '',
            });
        } finally {
            autogenerating.value = false;
        }
    }

    // ── Generate from a recipe ───────────────────────────────────────
    // The recipe and meal-plan paths both use the same shape: pick a
    // source entity, derive its stock-item ids, create a fresh list, then
    // add every item. We do it client-side because the existing autogen
    // backend only knows about flagged/low items.
    async function onPickRecipe() {
        let recipes;
        try {
            recipes = (await recipeApi.getAllAsync()).items;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not load recipes.',
                caption: describeApiError(err) || '',
            });
            return;
        }
        if (recipes.length === 0) {
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: 'No recipes saved yet.',
                actions: [
                    { label: 'Go to Recipes', color: 'white', handler: () => { void router.push('/recipes'); } },
                ],
            });
            return;
        }
        const recipeId = await new Promise<string | null>((resolve) => {
            $q.dialog({
                title: 'Generate a list from which recipe?',
                message: 'Every ingredient is added to a new list — duplicates skipped.',
                options: {
                    type: 'radio',
                    model: recipes[0]!.recipe_id,
                    items: recipes.map((r) => ({
                        label: `${r.name}${
                            r.ingredients?.length
                                ? ` (${r.ingredients.length} ingredients)`
                                : ''
                        }`,
                        value: r.recipe_id,
                    })),
                },
                ok: { label: 'Create list', color: 'primary', noCaps: true },
                cancel: { noCaps: true },
            })
                .onOk((v: string) => resolve(v))
                .onCancel(() => resolve(null))
                .onDismiss(() => resolve(null));
        });
        if (!recipeId) return;
        const recipe = recipes.find((r) => r.recipe_id === recipeId);
        if (!recipe) return;
        const ingredients = (recipe.ingredients ?? []).filter(
            (i): i is typeof i & { stock_item_id: string } => Boolean(i.stock_item_id),
        );
        if (ingredients.length === 0) {
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: `"${recipe.name}" has no stock-item ingredients to add.`,
            });
            return;
        }
        await createListFromItems(
            `Shop for ${recipe.name}`,
            ingredients.map((i) => i.stock_item_id),
        );
    }

    // ── Generate from a meal plan ────────────────────────────────────
    async function onPickMealPlan() {
        let plans;
        try {
            plans = (await mealPlanApi.getAllAsync()).items;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not load meal plans.',
                caption: describeApiError(err) || '',
            });
            return;
        }
        if (plans.length === 0) {
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: 'No meal plans yet.',
                actions: [
                    { label: 'Go to Meal Plans', color: 'white', handler: () => { void router.push('/meal-plans'); } },
                ],
            });
            return;
        }
        const planId = await new Promise<string | null>((resolve) => {
            $q.dialog({
                title: 'Generate a list from which meal plan?',
                message:
                    'Aggregates ingredients across every meal in the plan, scaled by servings.',
                options: {
                    type: 'radio',
                    model: plans[0]!.meal_plan_id,
                    items: plans.map((p) => ({
                        label: `${p.name} (${p.entries?.length ?? 0} meals)`,
                        value: p.meal_plan_id,
                    })),
                },
                ok: { label: 'Create list', color: 'primary', noCaps: true },
                cancel: { noCaps: true },
            })
                .onOk((v: string) => resolve(v))
                .onCancel(() => resolve(null))
                .onDismiss(() => resolve(null));
        });
        if (!planId) return;
        const plan = plans.find((p) => p.meal_plan_id === planId);
        let ingredients;
        try {
            ingredients = await mealPlanApi.getIngredientsAsync(planId);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not load meal plan ingredients.',
                caption: describeApiError(err) || '',
            });
            return;
        }
        if (ingredients.length === 0) {
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: `"${plan?.name ?? 'Plan'}" has no ingredients to add.`,
            });
            return;
        }
        await createListFromItems(
            `Shop for ${plan?.name ?? 'meal plan'}`,
            ingredients.map((i) => i.stock_item_id),
        );
    }

    // Shared helper: create a fresh list (primary if none exists), then
    // bulk-add every stock_item_id (skipping duplicates server-side).
    async function createListFromItems(name: string, stockItemIds: string[]) {
        if (stockItemIds.length === 0) return;
        creating.value = true;
        try {
            const { shopping_list_id } = await api.createAsync({
                name,
                make_primary: !primarySummary.value,
            });
            let added = 0;
            let skipped = 0;
            for (const id of stockItemIds) {
                try {
                    const result = await api.addLineAsync(shopping_list_id, {
                        stock_item_id: id,
                    });
                    if (result.already_on_list) skipped++;
                    else added++;
                } catch {
                    // Per-line failures shouldn't blow up the whole batch —
                    // log silently; user will see the partial-count notify.
                    skipped++;
                }
            }
            await Promise.all([store.refreshAsync(), loadPrimaryStats()]);
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message:
                    `Created "${name}". ${added} item${added === 1 ? '' : 's'} added` +
                    (skipped > 0 ? `, ${skipped} skipped` : '') + '.',
            });
            void router.push(`/shopping-lists/${shopping_list_id}`);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not create list.',
                caption: describeApiError(err) || '',
            });
        } finally {
            creating.value = false;
        }
    }

    // ── Archive (without finish) ─────────────────────────────────────
    async function archiveList(list: ShoppingListSummary) {
        const ok = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: `Archive "${list.name}"?`,
                message:
                    'Archived lists are read-only and move to the Archived tab. ' +
                    'No stock levels are bumped — use Finish shopping for that.',
                ok: { label: 'Archive', color: 'primary', noCaps: true },
                cancel: { noCaps: true },
            })
                .onOk(() => resolve(true))
                .onCancel(() => resolve(false))
                .onDismiss(() => resolve(false));
        });
        if (!ok) return;
        try {
            await api.updateAsync(list.shopping_list_id, { is_archived: true });
            await store.refreshAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'List archived.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not archive.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function onPickTemplate() {
        // Load templates lazily on click so the overview page doesn't pay
        // the fetch cost when the user never opens this menu.
        let templates;
        try {
            templates = await templateApi.getAllAsync();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not load templates.',
                caption: describeApiError(err) || '',
            });
            return;
        }
        if (templates.length === 0) {
            $q.dialog({
                title: 'No templates yet',
                message: 'Save a list as a template first (from any list\'s menu), or use the Manage templates page.',
                ok: { label: 'Open templates', noCaps: true, color: 'primary' },
                cancel: { noCaps: true },
            }).onOk(() => { void router.push('/shopping-lists/templates'); });
            return;
        }
        const templateId = await new Promise<string | null>((resolve) => {
            $q.dialog({
                title: 'Use which template?',
                message: 'A new shopping list will be created from the template\'s items.',
                options: {
                    type: 'radio',
                    model: templates[0]!.template_id,
                    items: templates.map((t) => ({
                        label: `${t.name} (${t.line_count} item${
                            t.line_count === 1 ? '' : 's'
                        })`,
                        value: t.template_id,
                    })),
                },
                ok: { label: 'Create list', color: 'primary', noCaps: true },
                cancel: { noCaps: true },
            })
                .onOk((value: string) => resolve(value))
                .onCancel(() => resolve(null))
                .onDismiss(() => resolve(null));
        });
        if (!templateId) return;
        try {
            // If there's no current primary, the freshly instantiated list
            // becomes primary — matches the auto-generate convention.
            const result = await templateApi.instantiateAsync(templateId, {
                make_primary: !primarySummary.value,
            });
            await store.refreshAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Created list with ${result.line_count} item${
                    result.line_count === 1 ? '' : 's'
                }.`,
            });
            if (result.shopping_list_id) {
                void router.push(`/shopping-lists/${result.shopping_list_id}`);
            }
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not create from template.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function setPrimary(id: string) {
        try {
            await api.updateAsync(id, { is_primary: true });
            await store.refreshAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Primary list updated.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update primary.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function copyList(id: string, include: 'all' | 'unticked') {
        try {
            const { shopping_list_id } = await api.copyAsync(id, { include });
            await store.refreshAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'List copied.',
            });
            void router.push(`/shopping-lists/${shopping_list_id}`);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not copy list.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function onDelete(list: ShoppingListSummary) {
        // Active lists require confirmation (per spec); archived ones don't.
        if (!list.is_archived) {
            const ok = await new Promise<boolean>((resolve) => {
                $q.dialog({
                    title: `Delete "${list.name}"?`,
                    message:
                        list.ticked_count < list.line_count
                            ? `${list.line_count - list.ticked_count} item${
                                  list.line_count - list.ticked_count === 1 ? '' : 's'
                              } not yet ticked off. Delete anyway?`
                            : 'This will remove the list and all its lines.',
                    cancel: true,
                })
                    .onOk(() => resolve(true))
                    .onCancel(() => resolve(false))
                    .onDismiss(() => resolve(false));
            });
            if (!ok) return;
        }
        try {
            await api.deleteAsync(list.shopping_list_id);
            await store.refreshAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'List deleted.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not delete.',
                caption: describeApiError(err) || '',
            });
        }
    }

    onMounted(async () => {
        // Kick off everything in parallel — the lists/stock-levels/items are
        // independent and the overview is more useful when all three land.
        const loads: Promise<unknown>[] = [store.refreshAsync()];
        if (stockItems.value.length === 0) loads.push(stockItemStore.getStockItemsAsync());
        if (stockLevels.value.length === 0) loads.push(stockLevelStore.getStockLevelsAsync());
        await Promise.all(loads);
        // Primary stats wait for the lists refresh so primarySummary is set.
        void loadPrimaryStats();
    });
</script>

<style scoped>
    .shopping-list-card {
        transition: transform 120ms ease, box-shadow 120ms ease;
    }
    .shopping-list-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 14px var(--overlay-active);
    }
    .shopping-list-primary {
        border-left: 4px solid var(--q-primary);
    }
    .shopping-list-archived {
        opacity: 0.65;
    }
    .primary-stats {
        background: var(--overlay-hover);
    }
</style>
