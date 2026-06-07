<template>
    <q-chip
        :dense="dense"
        clickable
        class="stock-item-chip"
        :class="{ 'stock-item-chip--alert': hasAlert }"
        @click="actions.openDetail(stockItem.stock_item_id)"
    >
        <q-avatar :color="levelColour" text-color="white" size="22px" class="q-mr-xs">
            <q-icon name="inventory_2" size="14px" />
        </q-avatar>

        <span class="ellipsis stock-item-chip__name">{{ stockItem.name }}</span>

        <!-- Live stock level badge -->
        <q-badge
            v-if="levelName"
            :color="levelColour"
            text-color="white"
            class="q-ml-xs"
        >
            {{ levelShort }}
        </q-badge>

        <!-- On-a-list indicator -->
        <q-icon
            v-if="cartState !== 'none'"
            name="shopping_cart"
            :color="cartColour"
            size="14px"
            class="q-ml-xs"
        >
            <q-tooltip>{{ cartTooltip }}</q-tooltip>
        </q-icon>

        <!-- Attention dot -->
        <q-icon
            v-if="hasAlert"
            name="circle"
            color="negative"
            size="9px"
            class="q-ml-xs"
        >
            <q-tooltip>{{ alertTooltip }}</q-tooltip>
        </q-icon>

        <!-- Overflow menu wired to the cross-feature composable -->
        <q-btn
            flat
            round
            dense
            size="xs"
            :icon="ICONS.more_vert"
            class="q-ml-xs"
            @click.stop
        >
            <q-menu auto-close transition-show="jump-down" transition-hide="jump-up">
                <q-list dense style="min-width: 200px">
                    <q-item clickable @click="actions.addToList(stockItem.stock_item_id)">
                        <q-item-section avatar><q-icon :name="ICONS.add_shopping_cart" /></q-item-section>
                        <q-item-section>Add to primary list</q-item-section>
                    </q-item>
                    <q-item clickable @click="actions.markRestocked(stockItem.stock_item_id)">
                        <q-item-section avatar><q-icon :name="ICONS.refresh" /></q-item-section>
                        <q-item-section>Mark restocked</q-item-section>
                    </q-item>
                    <q-item clickable @click="actions.pushExpiry(stockItem.stock_item_id)">
                        <q-item-section avatar><q-icon :name="ICONS.event" /></q-item-section>
                        <q-item-section>Push expiry +7 days</q-item-section>
                    </q-item>
                    <q-separator />
                    <q-item clickable @click="actions.findSubstitutes(stockItem.stock_item_id)">
                        <q-item-section avatar><q-icon :name="ICONS.swap_horiz" /></q-item-section>
                        <q-item-section>Find substitutes</q-item-section>
                    </q-item>
                    <q-item clickable @click="actions.seeRecipesUsing(stockItem.stock_item_id)">
                        <q-item-section avatar><q-icon :name="ICONS.menu_book" /></q-item-section>
                        <q-item-section>See recipes using this</q-item-section>
                    </q-item>
                    <q-separator />
                    <q-item clickable @click="actions.openDetail(stockItem.stock_item_id)">
                        <q-item-section avatar><q-icon :name="ICONS.open_in_new" /></q-item-section>
                        <q-item-section>Open detail</q-item-section>
                    </q-item>
                </q-list>
            </q-menu>
        </q-btn>
    </q-chip>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useStockItemActions } from 'src/composables/useStockItemActions';
    import { getStockLevelColour } from 'src/helpers/stockLevelLogic';
    import type { StockItem } from 'src/models/stockItem';
    import type { StockLevelName } from 'src/models/stockLevel';
    import type { Membership } from 'src/models/shoppingList';
    import { cartStateFor } from 'src/models/shoppingList';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { computed } from 'vue';

    const props = withDefaults(
        defineProps<{
            stockItem: StockItem;
            dense?: boolean;
        }>(),
        { dense: true },
    );

    const actions = useStockItemActions();
    const stockLevelStore = useStockLevelStore();
    const shoppingListStore = useShoppingListStore();
    const { stockLevels } = storeToRefs(stockLevelStore);
    const { membership } = storeToRefs(shoppingListStore);

    const levelName = computed<StockLevelName | null>(
        () =>
            stockLevels.value.find((l) => l.stock_level_id === props.stockItem.stock_level_id)
                ?.name ?? null,
    );
    const levelColour = computed(() =>
        levelName.value ? getStockLevelColour(levelName.value) : 'grey',
    );
    const levelShort = computed(() => {
        switch (levelName.value) {
            case 'Well-Stocked':
                return 'OK';
            case 'Sufficient Stock':
                return 'Mid';
            case 'Low Stock':
                return 'Low';
            case 'Out of Stock':
                return 'Out';
            default:
                return '';
        }
    });

    const cartState = computed(() =>
        cartStateFor(props.stockItem.stock_item_id, membership.value as Membership | null),
    );
    const cartColour = computed(() => {
        switch (cartState.value) {
            case 'on_target':
                return 'primary';
            case 'on_other':
                return 'accent';
            case 'on_multiple':
                return 'amber-9';
            default:
                return 'grey';
        }
    });
    const cartTooltip = computed(() => {
        switch (cartState.value) {
            case 'on_target':
                return 'On your current draft list';
            case 'on_other':
                return 'On another list';
            case 'on_multiple':
                return 'On multiple lists';
            default:
                return '';
        }
    });

    const expiringSoon = computed(() => {
        const raw = props.stockItem.expiry_date;
        if (!raw) return false;
        const days = (new Date(raw).getTime() - Date.now()) / 86_400_000;
        return days <= 7;
    });
    const lowOrOut = computed(
        () => levelName.value === 'Low Stock' || levelName.value === 'Out of Stock',
    );
    const hasAlert = computed(
        () => lowOrOut.value || expiringSoon.value || props.stockItem.is_flagged === true,
    );
    const alertTooltip = computed(() => {
        const reasons: string[] = [];
        if (lowOrOut.value) reasons.push(levelName.value ?? 'Low');
        if (expiringSoon.value) reasons.push('Expiring soon');
        if (props.stockItem.is_flagged) reasons.push('Essential');
        return reasons.join(' · ');
    });
</script>

<style scoped>
    .stock-item-chip__name {
        max-width: 160px;
    }
    .stock-item-chip--alert {
        outline: 1px solid var(--q-negative);
        outline-offset: -1px;
    }
</style>
