<template>
    <div class="q-pa-md">
        <!-- Header bar ───────────────────────────────────────────────── -->
        <div class="row items-center q-mb-md q-gutter-sm">
            <div class="text-h5 q-mr-md">Pantry</div>
            <q-btn color="positive" icon="add" label="New item" no-caps @click="onCreateClick" />
            <q-space />
            <q-input
                ref="searchInputRef"
                v-model="searchText"
                outlined
                dense
                debounce="150"
                placeholder='Search ("tomato pasta" matches either)'
                clearable
                autofocus
                style="min-width: 280px"
            >
                <template #prepend>
                    <q-icon name="search" />
                </template>
            </q-input>
        </div>

        <!-- Quick-info summary banner — at-a-glance pantry health. -->
        <div
            v-if="stockItems.length > 0"
            class="row q-gutter-md items-center q-mb-md stock-summary-banner"
        >
            <div class="stock-summary-stat">
                <div class="text-h6">{{ stockItems.length }}</div>
                <div class="text-caption text-grey">total items</div>
            </div>
            <q-separator vertical />
            <div class="stock-summary-stat">
                <div class="text-h6 text-orange-9">{{ summaryCounts.low }}</div>
                <div class="text-caption text-grey">low stock</div>
            </div>
            <div class="stock-summary-stat">
                <div class="text-h6 text-red-7">{{ summaryCounts.out }}</div>
                <div class="text-caption text-grey">out of stock</div>
            </div>
            <q-separator vertical />
            <div class="stock-summary-stat">
                <div class="text-h6 text-amber-9">{{ summaryCounts.essentials }}</div>
                <div class="text-caption text-grey">essentials</div>
            </div>
            <div class="stock-summary-stat">
                <div class="text-h6 text-secondary">{{ summaryCounts.open }}</div>
                <div class="text-caption text-grey">open / in-use</div>
            </div>
            <q-space />
            <div class="text-caption text-grey">
                {{ filteredStockItems.length }} of {{ stockItems.length }} shown
            </div>
        </div>

        <!-- Quick filters ──────────────────────────────────────────────── -->
        <div class="row q-gutter-sm q-mb-md items-center">
            <q-chip
                v-for="level in stockLevelStore.stockLevels"
                :key="level.stock_level_id"
                clickable
                :selected="levelFilter === level.stock_level_id"
                :color="
                    levelFilter === level.stock_level_id
                        ? getStockLevelColour(level.name)
                        : undefined
                "
                :text-color="levelFilter === level.stock_level_id ? 'white' : undefined"
                outline
                @click="toggleLevelFilter(level.stock_level_id)"
            >
                <q-icon
                    v-if="levelFilter === level.stock_level_id"
                    name="check"
                    class="q-mr-xs"
                />
                {{ level.name }}
                <q-badge floating color="grey-3" text-color="grey-9">
                    {{ countByLevel.get(level.stock_level_id) ?? 0 }}
                </q-badge>
            </q-chip>

            <q-separator vertical class="q-mx-sm" />

            <q-chip
                clickable
                outline
                :selected="essentialsOnly"
                :color="essentialsOnly ? 'amber-9' : undefined"
                :text-color="essentialsOnly ? 'white' : undefined"
                @click="essentialsOnly = !essentialsOnly"
            >
                <q-icon name="flag" size="14px" class="q-mr-xs" />
                Essentials only
            </q-chip>

            <q-chip
                clickable
                outline
                :selected="openOnly"
                :color="openOnly ? 'secondary' : undefined"
                :text-color="openOnly ? 'white' : undefined"
                @click="openOnly = !openOnly"
            >
                <q-icon name="lock_open" size="14px" class="q-mr-xs" />
                Open / in-use
            </q-chip>

            <q-chip
                clickable
                outline
                :selected="hasAlertOnly"
                :color="hasAlertOnly ? 'negative' : undefined"
                :text-color="hasAlertOnly ? 'white' : undefined"
                @click="hasAlertOnly = !hasAlertOnly"
            >
                <q-icon name="warning" size="14px" class="q-mr-xs" />
                Needs attention
            </q-chip>

            <q-chip
                clickable
                outline
                :selected="usedInRecipeOnly"
                :color="usedInRecipeOnly ? 'primary' : undefined"
                :text-color="usedInRecipeOnly ? 'white' : undefined"
                @click="usedInRecipeOnly = !usedInRecipeOnly"
            >
                <q-icon name="menu_book" size="14px" class="q-mr-xs" />
                Used in a recipe
            </q-chip>

            <q-chip
                v-if="cartFilter !== 'all'"
                clickable
                color="primary"
                text-color="white"
                removable
                @remove="cartFilter = 'all'"
            >
                <q-icon name="shopping_cart" size="14px" class="q-mr-xs" />
                {{ cartFilter === 'on_list' ? 'On a list' : 'Not on any list' }}
            </q-chip>

            <q-select
                v-model="locationFilter"
                :options="locationOptions"
                dense
                outlined
                emit-value
                map-options
                clearable
                label="Any location"
                style="min-width: 180px"
            />

            <q-select
                v-model="groupFilter"
                :options="groupOptions"
                dense
                outlined
                emit-value
                map-options
                clearable
                label="Any group"
                style="min-width: 180px"
            />

            <q-select
                v-model="sortBy"
                :options="sortOptions"
                option-value="value"
                option-label="label"
                emit-value
                map-options
                outlined
                dense
                label="Sort by"
                style="min-width: 180px"
            />

            <q-space />

            <q-btn
                v-if="bulkMode"
                flat
                no-caps
                icon="close"
                label="Cancel"
                @click="cancelBulk"
            />
            <q-btn
                v-else
                flat
                no-caps
                icon="checklist"
                label="Bulk select"
                @click="bulkMode = true"
            />
        </div>

        <!-- Bulk action bar ───────────────────────────────────────────── -->
        <q-banner v-if="bulkMode" class="bg-primary text-white q-mb-md" dense rounded>
            <template #avatar>
                <q-icon name="checklist" />
            </template>
            {{ bulkSelection.size }} selected
            <template #action>
                <q-btn flat no-caps label="Select visible" color="white" @click="selectVisible" />
                <q-btn
                    flat
                    no-caps
                    label="Add to list"
                    color="white"
                    :loading="bulkBusy"
                    :disable="bulkSelection.size === 0"
                    @click="bulkAddToPrimary"
                />
                <q-btn
                    flat
                    no-caps
                    label="Move location"
                    color="white"
                    :disable="bulkSelection.size === 0"
                    @click="openMoveDialog"
                />
                <q-btn
                    flat
                    no-caps
                    label="Mark restocked"
                    color="white"
                    :loading="bulkBusy"
                    :disable="bulkSelection.size === 0"
                    @click="bulkRestock"
                />
                <q-btn
                    flat
                    no-caps
                    label="Set substitute"
                    color="white"
                    :disable="bulkSelection.size === 0"
                    @click="bulkSetSubstitute"
                />
            </template>
        </q-banner>

        <!-- Splitter: item list on the left, in-page detail peek on the right -->
        <q-splitter
            v-model="splitPct"
            :limits="[40, 100]"
            :disable="!peekId"
            unit="%"
            class="stock-splitter"
        >
            <template #before>
                <div class="q-pr-md">
                    <q-list v-if="filteredStockItems.length > 0" class="q-gutter-y-sm">
                        <q-card
                            v-for="(item, idx) in filteredStockItems"
                            :key="item.stock_item_id"
                            bordered
                            flat
                            class="stock-row cursor-pointer"
                            :class="{
                                'stock-row-dim':
                                    stockLevelName(item.stock_level_id) === 'Out of Stock',
                                'stock-row-selected': peekId === item.stock_item_id,
                                'stock-row-focused': focusedIndex === idx,
                            }"
                            @click="onRowClick(item.stock_item_id)"
                        >
                            <q-card-section class="row items-center no-wrap q-py-sm q-gutter-x-sm">
                                <q-checkbox
                                    v-if="bulkMode"
                                    :model-value="bulkSelection.has(item.stock_item_id)"
                                    @click.stop
                                    @update:model-value="toggleBulk(item.stock_item_id)"
                                />

                                <!-- Identity (P0 chip) -->
                                <StockItemChip :stock-item="item" @click.stop />

                                <!-- Location chip → filter to this location -->
                                <q-chip
                                    v-if="item.stock_location_id"
                                    dense
                                    clickable
                                    icon="place"
                                    color="grey-3"
                                    text-color="grey-9"
                                    @click.stop="locationFilter = item.stock_location_id"
                                >
                                    {{ locationName(item.stock_location_id) }}
                                    <q-tooltip>Filter to this location</q-tooltip>
                                </q-chip>

                                <!-- On N lists chip → which lists -->
                                <q-chip
                                    v-if="onListsCount(item.stock_item_id) > 0"
                                    dense
                                    clickable
                                    icon="shopping_cart"
                                    color="primary"
                                    text-color="white"
                                    @click.stop
                                >
                                    On {{ onListsCount(item.stock_item_id) }}
                                    {{ onListsCount(item.stock_item_id) === 1 ? 'list' : 'lists' }}
                                    <q-menu auto-close>
                                        <q-list dense style="min-width: 200px">
                                            <q-item-label header>On these lists</q-item-label>
                                            <q-item
                                                v-for="l in listsFor(item.stock_item_id)"
                                                :key="l.shopping_list_id"
                                                clickable
                                                @click="goToList(l.shopping_list_id)"
                                            >
                                                <q-item-section>
                                                    {{ l.name }}
                                                    <span v-if="l.is_primary"> (primary)</span>
                                                </q-item-section>
                                                <q-item-section side>
                                                    <q-icon name="open_in_new" size="16px" />
                                                </q-item-section>
                                            </q-item>
                                        </q-list>
                                    </q-menu>
                                </q-chip>

                                <!-- Expiry / alert dot → push or clear inline -->
                                <q-btn
                                    flat
                                    dense
                                    round
                                    size="sm"
                                    :icon="expiryIcon(item)"
                                    :color="expiryColour(item)"
                                    @click.stop
                                >
                                    <q-tooltip>{{ expiryTooltip(item) }}</q-tooltip>
                                    <q-menu auto-close>
                                        <q-list dense style="min-width: 180px">
                                            <q-item clickable @click="actions.pushExpiry(item.stock_item_id, 7)">
                                                <q-item-section>Push expiry +7 days</q-item-section>
                                            </q-item>
                                            <q-item clickable @click="actions.pushExpiry(item.stock_item_id, 30)">
                                                <q-item-section>Push expiry +30 days</q-item-section>
                                            </q-item>
                                            <q-item
                                                clickable
                                                :disable="!item.expiry_date"
                                                @click="clearExpiry(item.stock_item_id)"
                                            >
                                                <q-item-section>Clear expiry</q-item-section>
                                            </q-item>
                                        </q-list>
                                    </q-menu>
                                </q-btn>

                                <!-- Used in N recipes → hover list, click → recipes -->
                                <q-btn
                                    v-if="recipesUsing(item.stock_item_id).length > 0"
                                    flat
                                    dense
                                    round
                                    size="sm"
                                    icon="menu_book"
                                    color="primary"
                                    @click.stop="actions.seeRecipesUsing(item.stock_item_id)"
                                >
                                    <q-badge floating color="primary">
                                        {{ recipesUsing(item.stock_item_id).length }}
                                    </q-badge>
                                    <q-tooltip>
                                        <div class="text-weight-bold q-mb-xs">Used in recipes</div>
                                        <div
                                            v-for="r in recipesUsing(item.stock_item_id)"
                                            :key="r.recipe_id"
                                        >
                                            {{ r.name }}
                                        </div>
                                    </q-tooltip>
                                </q-btn>

                                <q-space />

                                <!-- Stock-level cycler -->
                                <q-btn-dropdown
                                    flat
                                    dense
                                    no-caps
                                    :label="stockLevelName(item.stock_level_id) || 'Set level'"
                                    class="text-caption"
                                    @click.stop
                                >
                                    <q-list dense>
                                        <q-item
                                            v-for="level in stockLevelStore.stockLevels"
                                            :key="level.stock_level_id"
                                            clickable
                                            v-close-popup
                                            @click.stop="
                                                updateStockLevelAsync({
                                                    stock_item_id: item.stock_item_id,
                                                    stock_level_id: level.stock_level_id,
                                                })
                                            "
                                        >
                                            <q-item-section avatar>
                                                <q-avatar
                                                    :color="getStockLevelColour(level.name)"
                                                    size="14px"
                                                />
                                            </q-item-section>
                                            <q-item-section>{{ level.name }}</q-item-section>
                                        </q-item>
                                    </q-list>
                                </q-btn-dropdown>

                                <!-- Open / in-use toggle -->
                                <q-btn
                                    flat
                                    dense
                                    size="sm"
                                    :icon="item.is_open ? 'lock_open' : 'lock'"
                                    :color="item.is_open ? 'secondary' : undefined"
                                    :loading="openBusyId === item.stock_item_id"
                                    @click.stop="onToggleOpen(item)"
                                >
                                    <q-tooltip>
                                        {{ item.is_open ? 'Mark as sealed' : 'Mark as open / in-use' }}
                                    </q-tooltip>
                                </q-btn>

                                <!-- Cart quick-add (via P0 composable) -->
                                <q-btn
                                    flat
                                    dense
                                    size="sm"
                                    :icon="cartIcon(item.stock_item_id)"
                                    :color="cartColor(item.stock_item_id)"
                                    :loading="cartBusyId === item.stock_item_id"
                                    @click.stop="onCartClick(item.stock_item_id)"
                                >
                                    <q-tooltip>{{ cartTooltip(item.stock_item_id) }}</q-tooltip>
                                </q-btn>
                            </q-card-section>
                        </q-card>
                    </q-list>

                    <!-- Empty state ───────────────────────────────────── -->
                    <q-banner v-else class="bg-grey-2 q-mt-md" rounded>
                        <template v-if="stockItems.length === 0">
                            <div class="text-subtitle1 q-mb-sm">Your pantry is empty.</div>
                            <div class="text-body2 q-mb-md text-grey-8">
                                Start by adding an item, or build your pantry from things you
                                already track elsewhere.
                            </div>
                            <div class="q-gutter-sm">
                                <q-btn color="positive" icon="add" no-caps label="New item" @click="onCreateClick" />
                                <q-btn
                                    outline
                                    color="primary"
                                    no-caps
                                    icon="menu_book"
                                    label="Create from a recipe's ingredients"
                                    @click="goToRecipes"
                                />
                                <q-btn
                                    outline
                                    color="primary"
                                    no-caps
                                    icon="shopping_cart"
                                    label="Import from a shopping list"
                                    @click="goToLists"
                                />
                            </div>
                        </template>
                        <template v-else>
                            No items match the current filters.
                            <q-btn flat dense no-caps label="Clear" @click="clearFilters" />
                        </template>
                    </q-banner>
                </div>
            </template>

            <template #after>
                <div v-if="peekId" class="stock-peek">
                    <StockItemDetailPage
                        :id-override="peekId"
                        embedded
                        @close="peekId = null"
                    />
                </div>
            </template>
        </q-splitter>

        <!-- Create dialog ─────────────────────────────────────────────── -->
        <q-dialog v-model="createDialogOpen" @hide="resetCreateForm">
            <q-card style="width: 600px; max-width: 95vw">
                <q-card-section>
                    <div class="text-h6">Add a stock item</div>
                </q-card-section>
                <q-card-section>
                    <q-form @submit.prevent="onCreateSubmit" class="q-gutter-md">
                        <q-input
                            v-model="createForm.name"
                            outlined
                            autofocus
                            label="Name"
                            :rules="[(v: string) => (!!v && v.length > 0) || 'Name is required']"
                        />
                        <q-select
                            v-model="createForm.stock_level_id"
                            :options="stockLevels"
                            :option-label="(o: StockLevel) => o.name"
                            :option-value="(o: StockLevel) => o.stock_level_id"
                            emit-value
                            map-options
                            outlined
                            label="Stock level"
                            :rules="[(v: string) => !!v || 'Pick a stock level']"
                        >
                            <template #option="scope">
                                <q-item v-bind="scope.itemProps">
                                    <q-item-section avatar>
                                        <q-avatar
                                            :color="getStockLevelColour(scope.opt.name)"
                                            size="16px"
                                        />
                                    </q-item-section>
                                    <q-item-section>{{ scope.opt.name }}</q-item-section>
                                </q-item>
                            </template>
                        </q-select>
                        <q-select
                            v-model="createForm.stock_location_id"
                            :options="stockLocationStore.stockLocations"
                            option-label="name"
                            option-value="stock_location_id"
                            emit-value
                            map-options
                            clearable
                            outlined
                            label="Location (optional)"
                        />

                        <q-card-actions align="right">
                            <q-btn flat label="Cancel" v-close-popup />
                            <q-btn type="submit" color="primary" label="Add" :loading="saving" />
                        </q-card-actions>
                    </q-form>
                </q-card-section>
            </q-card>
        </q-dialog>

        <!-- Bulk move-location dialog ─────────────────────────────────── -->
        <q-dialog v-model="moveDialogOpen">
            <q-card style="width: 480px; max-width: 95vw">
                <q-card-section>
                    <div class="text-h6">Move {{ bulkSelection.size }} item(s)</div>
                </q-card-section>
                <q-card-section>
                    <q-select
                        v-model="moveTargetLocation"
                        :options="locationOptions"
                        emit-value
                        map-options
                        clearable
                        outlined
                        label="Destination location"
                    />
                </q-card-section>
                <q-card-actions align="right">
                    <q-btn flat label="Cancel" v-close-popup />
                    <q-btn
                        color="primary"
                        label="Move"
                        :loading="bulkBusy"
                        @click="bulkMove"
                    />
                </q-card-actions>
            </q-card>
        </q-dialog>
    </div>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import StockItemChip from 'src/components/chips/StockItemChip.vue';
    import StockItemDetailPage from 'src/pages/StockItemDetailPage.vue';
    import { useShortcut } from 'src/composables/useShortcut';
    import { useStockItemActions } from 'src/composables/useStockItemActions';
    import type { QInput } from 'quasar';
    import { getStockLevelColour } from 'src/helpers/stockLevelLogic';
    import { cartStateFor, type CartState, type Membership } from 'src/models/shoppingList';
    import type { StockGroup } from 'src/models/stockGroup';
    import type { StockItem } from 'src/models/stockItem';
    import type { StockLevel } from 'src/models/stockLevel';
    import StockGroupApiService from 'src/services/api/stockGroupApiService';
    import StockItemApiService, {
        type CreateStockItemCommand,
    } from 'src/services/api/stockItemApiService';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { useStockLocationStore } from 'src/stores/stockLocationStore';
    import { computed, onMounted, reactive, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const stockGroupApi = new StockGroupApiService();
    const stockItemApi = new StockItemApiService();

    const router = useRouter();
    const route = useRoute();
    const actions = useStockItemActions();

    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const stockLocationStore = useStockLocationStore();
    const shoppingListStore = useShoppingListStore();
    const recipeStore = useRecipeStore();

    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);
    const { stockLocations } = storeToRefs(stockLocationStore);
    const { recipes } = storeToRefs(recipeStore);
    const { createStockItemAsync, updateStockLevelAsync } = stockItemStore;

    // ── Lookup maps for O(1) name resolution ─────────────────────────────
    const stockLevelById = computed(() => {
        const map = new Map<string, StockLevel>();
        stockLevels.value.forEach((l) => map.set(l.stock_level_id, l));
        return map;
    });
    const stockLocationById = computed(() => {
        const map = new Map<string, string>();
        stockLocations.value.forEach((l) => map.set(l.stock_location_id, l.name));
        return map;
    });

    function stockLevelName(id: string | null): string {
        if (!id) return '';
        return stockLevelById.value.get(id)?.name ?? '';
    }

    function locationName(id: string | null): string {
        if (!id) return '';
        return stockLocationById.value.get(id) ?? '';
    }

    // ── Live cross-feature indexes ───────────────────────────────────────
    // Recipes that reference each stock item (live count + names for hover).
    const recipesByStockItem = computed(() => {
        const map = new Map<string, { recipe_id: string; name: string }[]>();
        for (const r of recipes.value) {
            const seen = new Set<string>();
            for (const ing of r.ingredients) {
                if (seen.has(ing.stock_item_id)) continue;
                seen.add(ing.stock_item_id);
                const arr = map.get(ing.stock_item_id) ?? [];
                arr.push({ recipe_id: r.recipe_id, name: r.name });
                map.set(ing.stock_item_id, arr);
            }
        }
        return map;
    });
    function recipesUsing(id: string) {
        return recipesByStockItem.value.get(id) ?? [];
    }

    // Shopping lists each item sits on (unticked).
    function listsFor(id: string) {
        const m = shoppingListStore.membership;
        const entry = m?.items.find((i) => i.stock_item_id === id);
        const ids = entry?.unticked_list_ids ?? [];
        const lookup = new Map((m?.active_lists ?? []).map((l) => [l.shopping_list_id, l]));
        return ids.map(
            (lid) =>
                lookup.get(lid) ?? { shopping_list_id: lid, name: lid, is_primary: false },
        );
    }
    function onListsCount(id: string) {
        return listsFor(id).length;
    }

    // ── Expiry / attention ───────────────────────────────────────────────
    function isExpiringSoon(item: StockItem): boolean {
        if (!item.expiry_date) return false;
        const days = (new Date(item.expiry_date).getTime() - Date.now()) / 86_400_000;
        return days <= 7;
    }
    function isExpired(item: StockItem): boolean {
        if (!item.expiry_date) return false;
        return new Date(item.expiry_date).getTime() < Date.now();
    }
    function hasAlert(item: StockItem): boolean {
        const n = stockLevelName(item.stock_level_id);
        return (
            n === 'Low Stock' ||
            n === 'Out of Stock' ||
            isExpiringSoon(item) ||
            item.is_flagged === true
        );
    }
    function expiryIcon(item: StockItem): string {
        if (isExpired(item)) return 'error';
        if (isExpiringSoon(item)) return 'event_busy';
        return 'event_available';
    }
    function expiryColour(item: StockItem): string | undefined {
        if (isExpired(item)) return 'negative';
        if (isExpiringSoon(item)) return 'orange-9';
        return item.expiry_date ? 'positive' : 'grey-5';
    }
    function expiryTooltip(item: StockItem): string {
        if (!item.expiry_date) return 'No expiry set — click to push or set one';
        if (isExpired(item)) return `Expired ${item.expiry_date}`;
        return `Expires ${item.expiry_date}`;
    }
    async function clearExpiry(stockItemId: string) {
        try {
            await stockItemStore.updateStockItemAsync({
                stock_item_id: stockItemId,
                expiry_date: null,
            });
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Expiry cleared.' });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not clear expiry.',
                caption: describeApiError(err) || '',
            });
        }
    }

    // ── Filters ──────────────────────────────────────────────────────────
    const searchText = ref('');
    const levelFilter = ref<string | null>(null);
    const locationFilter = ref<string | null>(null);
    const groupFilter = ref<string | null>(null);
    const essentialsOnly = ref(false);
    const openOnly = ref(false);
    const hasAlertOnly = ref(false);
    const usedInRecipeOnly = ref(false);
    const cartFilter = ref<'all' | 'on_list' | 'off_list'>('all');

    const sortOptions = [
        { value: 'name_asc', label: 'Name (A-Z)' },
        { value: 'name_desc', label: 'Name (Z-A)' },
        { value: 'level_lowest', label: 'Stock level (lowest first)' },
        { value: 'level_highest', label: 'Stock level (highest first)' },
        { value: 'updated_recent', label: 'Recently updated' },
        { value: 'updated_oldest', label: 'Stalest first' },
    ];
    const sortBy = ref<string>('name_asc');

    const locationOptions = computed(() =>
        stockLocations.value.map((l) => ({ label: l.name, value: l.stock_location_id })),
    );

    const stockGroups = ref<StockGroup[]>([]);
    const groupOptions = computed(() =>
        stockGroups.value.map((g) => ({ label: g.name, value: g.stock_group_id })),
    );

    function toggleLevelFilter(id: string) {
        levelFilter.value = levelFilter.value === id ? null : id;
    }

    function clearFilters() {
        searchText.value = '';
        levelFilter.value = null;
        locationFilter.value = null;
        groupFilter.value = null;
        essentialsOnly.value = false;
        openOnly.value = false;
        hasAlertOnly.value = false;
        usedInRecipeOnly.value = false;
        cartFilter.value = 'all';
    }

    const summaryCounts = computed(() => {
        let low = 0;
        let out = 0;
        let essentials = 0;
        let open = 0;
        for (const item of stockItems.value) {
            const levelName = stockLevelName(item.stock_level_id);
            if (levelName === 'Low Stock') low++;
            if (levelName === 'Out of Stock') out++;
            if (item.is_flagged) essentials++;
            if (item.is_open) open++;
        }
        return { low, out, essentials, open };
    });

    const countByLevel = computed(() => {
        const map = new Map<string, number>();
        for (const item of stockItems.value) {
            if (!item.stock_level_id) continue;
            map.set(item.stock_level_id, (map.get(item.stock_level_id) ?? 0) + 1);
        }
        return map;
    });

    const levelSequenceById = computed(() => {
        const map = new Map<string, number>();
        stockLevels.value.forEach((l) => map.set(l.stock_level_id, l.sequence ?? 0));
        return map;
    });
    function levelSequence(id: string | null): number {
        if (!id) return -1;
        return levelSequenceById.value.get(id) ?? -1;
    }

    const cartStateById = computed(() => {
        const map = new Map<string, CartState>();
        const membership = shoppingListStore.membership as Membership | null;
        for (const item of stockItems.value) {
            map.set(item.stock_item_id, cartStateFor(item.stock_item_id, membership));
        }
        return map;
    });

    const filteredStockItems = computed(() => {
        const tokens = (searchText.value ?? '')
            .trim()
            .toLowerCase()
            .split(/\s+/)
            .filter((t) => t.length > 0);
        const matches = stockItems.value.filter((item) => {
            if (levelFilter.value && item.stock_level_id !== levelFilter.value) return false;
            if (locationFilter.value && item.stock_location_id !== locationFilter.value)
                return false;
            if (groupFilter.value && item.stock_group_id !== groupFilter.value) return false;
            if (essentialsOnly.value && !item.is_flagged) return false;
            if (openOnly.value && !item.is_open) return false;
            if (hasAlertOnly.value && !hasAlert(item)) return false;
            if (usedInRecipeOnly.value && recipesUsing(item.stock_item_id).length === 0)
                return false;
            if (tokens.length > 0) {
                const haystack = item.name.toLowerCase();
                if (!tokens.some((t) => haystack.includes(t))) return false;
            }
            if (cartFilter.value !== 'all') {
                const state = cartStateById.value.get(item.stock_item_id) ?? 'none';
                const onList = state !== 'none';
                if (cartFilter.value === 'on_list' && !onList) return false;
                if (cartFilter.value === 'off_list' && onList) return false;
            }
            return true;
        });

        const collator = new Intl.Collator('en', { sensitivity: 'base' });
        const sorted = [...matches];
        switch (sortBy.value) {
            case 'name_desc':
                sorted.sort((a, b) => collator.compare(b.name, a.name));
                break;
            case 'level_lowest':
                sorted.sort(
                    (a, b) =>
                        levelSequence(b.stock_level_id) - levelSequence(a.stock_level_id) ||
                        collator.compare(a.name, b.name),
                );
                break;
            case 'level_highest':
                sorted.sort(
                    (a, b) =>
                        levelSequence(a.stock_level_id) - levelSequence(b.stock_level_id) ||
                        collator.compare(a.name, b.name),
                );
                break;
            case 'updated_recent':
                sorted.sort((a, b) =>
                    (b.stock_level_last_updated ?? '').localeCompare(
                        a.stock_level_last_updated ?? '',
                    ),
                );
                break;
            case 'updated_oldest':
                sorted.sort((a, b) =>
                    (a.stock_level_last_updated ?? '').localeCompare(
                        b.stock_level_last_updated ?? '',
                    ),
                );
                break;
            case 'name_asc':
            default:
                sorted.sort((a, b) => collator.compare(a.name, b.name));
                break;
        }
        return sorted;
    });

    // ── Cart button state ────────────────────────────────────────────────
    const cartBusyId = ref<string | null>(null);

    function cartIcon(stockItemId: string): string {
        const state = cartStateById.value.get(stockItemId) ?? 'none';
        if (state === 'none') return 'add_shopping_cart';
        if (state === 'on_multiple') return 'shopping_cart_checkout';
        return 'shopping_cart';
    }
    function cartColor(stockItemId: string): string | undefined {
        const state = cartStateById.value.get(stockItemId) ?? 'none';
        if (state === 'on_primary') return 'primary';
        if (state === 'on_other') return 'accent';
        if (state === 'on_multiple') return 'amber-9';
        return undefined;
    }
    function cartTooltip(stockItemId: string): string {
        const state = cartStateById.value.get(stockItemId) ?? 'none';
        if (state === 'none') return 'Add to primary list';
        if (state === 'on_primary') return 'On your primary list';
        if (state === 'on_other') return 'On a non-primary list';
        return 'On multiple lists';
    }
    async function onCartClick(stockItemId: string) {
        cartBusyId.value = stockItemId;
        try {
            await actions.addToList(stockItemId);
        } finally {
            cartBusyId.value = null;
        }
    }

    // ── Open / in-use marker ─────────────────────────────────────────────
    const openBusyId = ref<string | null>(null);
    async function onToggleOpen(item: { stock_item_id: string; is_open?: boolean; name: string }) {
        const next = !item.is_open;
        openBusyId.value = item.stock_item_id;
        try {
            await stockItemStore.updateStockItemAsync({
                stock_item_id: item.stock_item_id,
                is_open: next,
            });
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: next
                    ? `Marked "${item.name}" as open.`
                    : `Marked "${item.name}" as sealed.`,
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update.',
                caption: describeApiError(err) || '',
            });
        } finally {
            openBusyId.value = null;
        }
    }

    // ── Splitter peek ────────────────────────────────────────────────────
    const peekId = ref<string | null>(null);
    const splitPct = ref(100);
    watch(peekId, (v) => (splitPct.value = v ? 58 : 100));

    function onRowClick(stockItemId: string) {
        if (bulkMode.value) {
            toggleBulk(stockItemId);
            return;
        }
        peekId.value = peekId.value === stockItemId ? null : stockItemId;
    }

    // ── Keyboard shortcuts (S5) ──────────────────────────────────────────
    const searchInputRef = ref<QInput | null>(null);
    const focusedIndex = ref(-1);

    function focusSearch() {
        searchInputRef.value?.focus();
    }
    function moveFocus(delta: number) {
        const count = filteredStockItems.value.length;
        if (count === 0) return;
        focusedIndex.value = Math.max(0, Math.min(count - 1, focusedIndex.value + delta));
    }
    function openFocused() {
        const item = filteredStockItems.value[focusedIndex.value];
        if (item) onRowClick(item.stock_item_id);
    }
    function addFocusedOrSelected() {
        if (bulkSelection.value.size > 0) {
            void bulkAddToPrimary();
            return;
        }
        const item = filteredStockItems.value[focusedIndex.value];
        if (item) void actions.addToList(item.stock_item_id);
    }

    useShortcut([
        { keys: 'n', scope: 'Stock overview', description: 'New stock item', handler: onCreateClick },
        { keys: 'f', scope: 'Stock overview', description: 'Focus the filter/search', handler: focusSearch },
        { keys: '/', scope: 'Stock overview', description: 'Focus the filter/search', handler: focusSearch },
        { keys: 'a', scope: 'Stock overview', description: 'Add focused / selected to primary list', handler: addFocusedOrSelected },
        { keys: 'arrowdown', scope: 'Stock overview', description: 'Focus next item', handler: () => moveFocus(1) },
        { keys: 'arrowup', scope: 'Stock overview', description: 'Focus previous item', handler: () => moveFocus(-1) },
        { keys: 'arrowright', scope: 'Stock overview', description: 'Focus next item', handler: () => moveFocus(1) },
        { keys: 'arrowleft', scope: 'Stock overview', description: 'Focus previous item', handler: () => moveFocus(-1) },
        { keys: 'enter', scope: 'Stock overview', description: 'Open the focused item', handler: openFocused },
    ]);

    // ── Bulk select mode ─────────────────────────────────────────────────
    const bulkMode = ref(false);
    const bulkSelection = ref<Set<string>>(new Set());
    const bulkBusy = ref(false);

    function toggleBulk(id: string) {
        if (bulkSelection.value.has(id)) bulkSelection.value.delete(id);
        else bulkSelection.value.add(id);
        bulkSelection.value = new Set(bulkSelection.value);
    }
    function selectVisible() {
        for (const item of filteredStockItems.value) bulkSelection.value.add(item.stock_item_id);
        bulkSelection.value = new Set(bulkSelection.value);
    }
    function cancelBulk() {
        bulkMode.value = false;
        bulkSelection.value = new Set();
    }

    async function bulkAddToPrimary() {
        if (bulkSelection.value.size === 0) return;
        bulkBusy.value = true;
        try {
            for (const id of bulkSelection.value) await actions.addToList(id);
            cancelBulk();
        } finally {
            bulkBusy.value = false;
        }
    }

    async function bulkRestock() {
        if (bulkSelection.value.size === 0) return;
        bulkBusy.value = true;
        try {
            for (const id of bulkSelection.value) await actions.markRestocked(id);
            cancelBulk();
        } finally {
            bulkBusy.value = false;
        }
    }

    function bulkSetSubstitute() {
        // The substitutes graph arrives with the StockItemDetail revamp (P2).
        $q.notify({
            type: 'info',
            position: 'bottom-right',
            message: 'Setting substitutes arrives with the item detail revamp.',
        });
    }

    // ── Bulk move location ───────────────────────────────────────────────
    const moveDialogOpen = ref(false);
    const moveTargetLocation = ref<string | null>(null);
    function openMoveDialog() {
        moveTargetLocation.value = null;
        moveDialogOpen.value = true;
    }
    async function bulkMove() {
        if (bulkSelection.value.size === 0) return;
        bulkBusy.value = true;
        try {
            for (const id of bulkSelection.value) {
                await stockItemApi.moveAsync(id, moveTargetLocation.value);
            }
            await stockItemStore.getStockItemsAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Items moved.',
            });
            moveDialogOpen.value = false;
            cancelBulk();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not move items.',
                caption: describeApiError(err) || '',
            });
        } finally {
            bulkBusy.value = false;
        }
    }

    // ── Navigation ───────────────────────────────────────────────────────
    function goToList(listId: string) {
        void router.push(`/shopping-lists/${listId}`);
    }
    function goToRecipes() {
        void router.push('/recipes');
    }
    function goToLists() {
        void router.push('/shopping-lists');
    }

    // ── Create form ──────────────────────────────────────────────────────
    const createDialogOpen = ref(false);
    const saving = ref(false);

    const defaultCreateForm = (): CreateStockItemCommand => ({
        name: '',
        stock_level_id: stockLevels.value[0]?.stock_level_id ?? '',
        stock_location_id: null,
    });
    const createForm: CreateStockItemCommand = reactive(defaultCreateForm());

    function onCreateClick() {
        Object.assign(createForm, defaultCreateForm());
        createDialogOpen.value = true;
    }
    function resetCreateForm() {
        Object.assign(createForm, defaultCreateForm());
    }
    async function onCreateSubmit() {
        saving.value = true;
        try {
            await createStockItemAsync({
                name: createForm.name,
                stock_level_id: createForm.stock_level_id,
                stock_location_id: createForm.stock_location_id,
            });
            createDialogOpen.value = false;
        } finally {
            saving.value = false;
        }
    }

    async function loadStockGroups() {
        try {
            stockGroups.value = await stockGroupApi.getAllAsync();
        } catch {
            stockGroups.value = [];
        }
    }

    // Deep-link filter hydration: other screens (e.g. Locations) link here
    // with `?location_id=…&attention=true` to pre-narrow the list. Read those
    // on mount and reactively whenever the query changes (e.g. user uses
    // back/forward).
    function applyQueryFilters() {
        const q = route.query;
        if (typeof q.location_id === 'string' && q.location_id) {
            locationFilter.value = q.location_id;
        }
        if (q.attention === 'true' || q.attention === '1') {
            hasAlertOnly.value = true;
        }
        if (typeof q.level_id === 'string' && q.level_id) {
            levelFilter.value = q.level_id;
        }
    }

    watch(
        () => [route.query.location_id, route.query.attention, route.query.level_id],
        applyQueryFilters,
    );

    // Open the create dialog when ?create=1 lands — works for both initial
    // arrivals (onMounted) and re-navigations from the command palette when
    // the page is already mounted (Vue Router updates query in place without
    // unmounting). The query is replaced away straight after so a refresh
    // doesn't reopen the dialog.
    function maybeOpenCreateFromQuery(): void {
        if (route.query.create === '1') {
            onCreateClick();
            void router.replace({ path: '/stock', query: {} });
        }
    }
    watch(() => route.query.create, () => maybeOpenCreateFromQuery());

    onMounted(async () => {
        await Promise.all([
            stockItemStore.getStockItemsAsync(),
            stockLevelStore.getStockLevelsAsync(),
            stockLocationStore.getStockLocationsAsync(),
            shoppingListStore.refreshAsync(),
            recipeStore.getRecipesAsync(),
            loadStockGroups(),
        ]);
        // Apply *after* the supporting data is loaded so the filter chips
        // visibly snap to the linked-from state on the first render.
        applyQueryFilters();
        maybeOpenCreateFromQuery();
    });
</script>

<style scoped>
    .stock-summary-banner {
        padding: 12px 16px;
        background: rgba(0, 0, 0, 0.02);
        border-radius: 8px;
    }
    .stock-summary-stat {
        text-align: center;
        min-width: 84px;
    }
    .stock-row {
        transition: box-shadow 0.15s ease;
    }
    .stock-row:hover {
        box-shadow: 0 6px 18px -14px rgba(0, 0, 0, 0.4);
    }
    .stock-row-dim {
        opacity: 0.62;
    }
    .stock-row-selected {
        outline: 2px solid var(--q-primary);
        outline-offset: -2px;
    }
    .stock-row-focused {
        outline: 2px dashed var(--q-accent);
        outline-offset: -2px;
    }
    .stock-splitter {
        min-height: 50vh;
    }
    .stock-peek {
        max-height: 80vh;
        overflow-y: auto;
    }
</style>
