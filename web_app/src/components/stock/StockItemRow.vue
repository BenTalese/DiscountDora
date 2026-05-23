<template>
    <q-card
        bordered
        flat
        class="stock-row cursor-pointer"
        :class="{
            'stock-row-dim': levelName === 'Out of Stock',
            'stock-row-selected': peeking,
            'stock-row-focused': focused,
        }"
        @click="emit('click', item.stock_item_id)"
    >
        <q-card-section class="row items-center no-wrap q-py-sm q-gutter-x-sm">
            <q-checkbox
                v-if="bulkMode"
                :model-value="selected"
                @click.stop
                @update:model-value="emit('bulk-toggle', item.stock_item_id)"
            />

            <!-- Identity chip — opens the detail page. -->
            <StockItemChip :stock-item="item" @click.stop />

            <!-- Location chip → bubble up "filter to this location". -->
            <q-chip
                v-if="item.stock_location_id"
                dense
                clickable
                icon="place"
                color="grey-3"
                text-color="grey-9"
                @click.stop="emit('filter-location', item.stock_location_id!)"
            >
                {{ locationName }}
                <q-tooltip>Filter to this location</q-tooltip>
            </q-chip>

            <!-- On N lists chip — opens a menu of those lists. -->
            <q-chip
                v-if="onLists.length > 0"
                dense
                clickable
                icon="shopping_cart"
                color="primary"
                text-color="white"
                @click.stop
            >
                On {{ onLists.length }} {{ onLists.length === 1 ? 'list' : 'lists' }}
                <q-menu auto-close>
                    <q-list dense style="min-width: 200px">
                        <q-item-label header>On these lists</q-item-label>
                        <q-item
                            v-for="l in onLists"
                            :key="l.shopping_list_id"
                            clickable
                            @click="emit('go-to-list', l.shopping_list_id)"
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

            <!-- Expiry / alert dot — push or clear inline. -->
            <q-btn
                flat
                dense
                round
                size="sm"
                :icon="expiry.icon"
                :color="expiry.colour"
                @click.stop
            >
                <q-tooltip>{{ expiry.tooltip }}</q-tooltip>
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
                            @click="clearExpiry"
                        >
                            <q-item-section>Clear expiry</q-item-section>
                        </q-item>
                    </q-list>
                </q-menu>
            </q-btn>

            <!-- Used in N recipes — tooltip with the list, click → recipes. -->
            <q-btn
                v-if="recipesUsingItem.length > 0"
                flat
                dense
                round
                size="sm"
                icon="menu_book"
                color="primary"
                @click.stop="actions.seeRecipesUsing(item.stock_item_id)"
            >
                <q-badge floating color="primary">
                    {{ recipesUsingItem.length }}
                </q-badge>
                <q-tooltip>
                    <div class="text-weight-bold q-mb-xs">Used in recipes</div>
                    <div
                        v-for="r in recipesUsingItem"
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
                :label="levelName || 'Set level'"
                class="text-caption"
                @click.stop
            >
                <q-list dense>
                    <q-item
                        v-for="level in stockLevels"
                        :key="level.stock_level_id"
                        clickable
                        v-close-popup
                        @click.stop="onSetLevel(level.stock_level_id)"
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
                :loading="openBusy"
                @click.stop="onToggleOpen"
            >
                <q-tooltip>
                    {{ item.is_open ? 'Mark as sealed' : 'Mark as open / in-use' }}
                </q-tooltip>
            </q-btn>

            <!-- Cart quick-add -->
            <q-btn
                flat
                dense
                size="sm"
                :icon="cart.icon"
                :color="cart.colour"
                :loading="cartBusy"
                @click.stop="onCartClick"
            >
                <q-tooltip>{{ cart.tooltip }}</q-tooltip>
            </q-btn>
        </q-card-section>
    </q-card>
</template>

<script setup lang="ts">
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import StockItemChip from 'src/components/chips/StockItemChip.vue';
    import { useStockItemActions } from 'src/composables/useStockItemActions';
    import { getStockLevelColour } from 'src/helpers/stockLevelLogic';
    import { cartStateFor, type Membership } from 'src/models/shoppingList';
    import type { StockItem } from 'src/models/stockItem';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { useStockLocationStore } from 'src/stores/stockLocationStore';
    import { computed, ref } from 'vue';

    const props = defineProps<{
        item: StockItem;
        bulkMode?: boolean;
        selected?: boolean;
        focused?: boolean;
        peeking?: boolean;
    }>();

    const emit = defineEmits<{
        (e: 'click', stockItemId: string): void;
        (e: 'bulk-toggle', stockItemId: string): void;
        (e: 'filter-location', stockLocationId: string): void;
        (e: 'go-to-list', shoppingListId: string): void;
    }>();

    const $q = useQuasar();
    const actions = useStockItemActions();

    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const stockLocationStore = useStockLocationStore();
    const shoppingListStore = useShoppingListStore();
    const recipeStore = useRecipeStore();

    const { stockLevels } = storeToRefs(stockLevelStore);
    const { stockLocations } = storeToRefs(stockLocationStore);
    const { recipes } = storeToRefs(recipeStore);

    // ── Level / location names ──────────────────────────────────────────
    const levelName = computed(() => {
        const id = props.item.stock_level_id;
        if (!id) return '';
        return stockLevels.value.find((l) => l.stock_level_id === id)?.name ?? '';
    });
    const locationName = computed(() => {
        const id = props.item.stock_location_id;
        if (!id) return '';
        return stockLocations.value.find((l) => l.stock_location_id === id)?.name ?? '';
    });

    // ── Recipes referencing this item ───────────────────────────────────
    const recipesUsingItem = computed(() => {
        const id = props.item.stock_item_id;
        const out: { recipe_id: string; name: string }[] = [];
        for (const r of recipes.value) {
            if (r.ingredients.some((ing) => ing.stock_item_id === id)) {
                out.push({ recipe_id: r.recipe_id, name: r.name });
            }
        }
        return out;
    });

    // ── Shopping-list membership ────────────────────────────────────────
    const onLists = computed(() => {
        const id = props.item.stock_item_id;
        const m = shoppingListStore.membership as Membership | null;
        const entry = m?.items.find((i) => i.stock_item_id === id);
        const ids = entry?.unticked_list_ids ?? [];
        const lookup = new Map((m?.active_lists ?? []).map((l) => [l.shopping_list_id, l]));
        return ids.map(
            (lid) =>
                lookup.get(lid) ?? { shopping_list_id: lid, name: lid, is_primary: false },
        );
    });

    // ── Expiry derived state ────────────────────────────────────────────
    const expiry = computed(() => {
        const date = props.item.expiry_date;
        if (!date) {
            return {
                icon: 'event_available',
                colour: 'grey-5',
                tooltip: 'No expiry set — click to push or set one',
            };
        }
        const ms = new Date(date).getTime();
        const expired = ms < Date.now();
        const soon = (ms - Date.now()) / 86_400_000 <= 7;
        if (expired) return { icon: 'error', colour: 'negative', tooltip: `Expired ${date}` };
        if (soon)
            return { icon: 'event_busy', colour: 'orange-9', tooltip: `Expires ${date}` };
        return { icon: 'event_available', colour: 'positive', tooltip: `Expires ${date}` };
    });

    async function clearExpiry() {
        try {
            await stockItemStore.updateStockItemAsync({
                stock_item_id: props.item.stock_item_id,
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

    // ── Cart button ─────────────────────────────────────────────────────
    const cart = computed(() => {
        const state = cartStateFor(
            props.item.stock_item_id,
            shoppingListStore.membership as Membership | null,
        );
        if (state === 'none')
            return { icon: 'add_shopping_cart', colour: undefined, tooltip: 'Add to primary list' };
        if (state === 'on_primary')
            return { icon: 'shopping_cart', colour: 'primary', tooltip: 'On your primary list' };
        if (state === 'on_other')
            return { icon: 'shopping_cart', colour: 'accent', tooltip: 'On a non-primary list' };
        return {
            icon: 'shopping_cart_checkout',
            colour: 'amber-9',
            tooltip: 'On multiple lists',
        };
    });

    const cartBusy = ref(false);
    async function onCartClick() {
        cartBusy.value = true;
        try {
            await actions.addToList(props.item.stock_item_id);
        } finally {
            cartBusy.value = false;
        }
    }

    // ── Open / in-use toggle ────────────────────────────────────────────
    const openBusy = ref(false);
    async function onToggleOpen() {
        const next = !props.item.is_open;
        openBusy.value = true;
        try {
            await stockItemStore.updateStockItemAsync({
                stock_item_id: props.item.stock_item_id,
                is_open: next,
            });
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: next
                    ? `Marked "${props.item.name}" as open.`
                    : `Marked "${props.item.name}" as sealed.`,
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update.',
                caption: describeApiError(err) || '',
            });
        } finally {
            openBusy.value = false;
        }
    }

    // ── Stock-level cycle ───────────────────────────────────────────────
    async function onSetLevel(stockLevelId: string) {
        await stockItemStore.updateStockLevelAsync({
            stock_item_id: props.item.stock_item_id,
            stock_level_id: stockLevelId,
        });
    }
</script>

<style scoped>
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
</style>
