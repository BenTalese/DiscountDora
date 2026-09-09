<template>
    <q-card
        flat
        bordered
        class="product-card column no-wrap full-height"
        :class="{
            'product-card--selected': selected,
            'product-card--inactive': !product.is_active,
        }"
        @click="onCardClick"
    >
        <!-- ── Top half: opens the store's own product page (OD-1) ──────
             The whole media + identity block is the link, which is what let
             the separate "Open at store" icon go. Suppressed in bulk mode,
             where a card tap means "select". -->
        <component
            :is="topHalfTag"
            class="product-card__top"
            :class="{ 'product-card__top--linked': isTopHalfLink }"
            v-bind="topHalfAttrs"
            @click="onTopHalfClick"
        >
            <div class="product-card__media">
                <ProductThumb
                    fill
                    :product-id="product.product_id"
                    :has-image="product.has_image"
                    :alt="product.name"
                    icon-size="48px"
                />
                <DiscountChip
                    class="product-card__discount"
                    :price-now="product.price_now"
                    :price-was="product.price_was"
                />
                <!-- D-001: out of stock is the escalation state, so it takes
                     the red the discount badge used to be wearing. -->
                <div v-if="!product.is_available" class="product-card__oos">
                    Out of stock
                </div>
                <q-checkbox
                    v-if="bulkMode"
                    :model-value="selected"
                    class="product-card__select"
                    dense
                    @click.stop
                    @update:model-value="emit('toggle-select')"
                />
            </div>

            <q-card-section class="q-py-sm col">
                <div class="text-subtitle2 ellipsis-2-lines">{{ product.name }}</div>
                <div class="text-caption dora-text-muted">
                    <span v-if="product.brand">{{ product.brand }}</span>
                    <span v-if="product.brand && product.size"> · </span>
                    <span v-if="product.size">{{ product.size }}</span>
                </div>
                <div class="row items-baseline q-gutter-xs q-mt-xs">
                    <span class="text-h6">{{ formatMoney(product.price_now ?? 0) }}</span>
                    <span
                        v-if="hasDiscount"
                        class="text-caption dora-text-muted product-card__was"
                    >
                        {{ formatMoney(product.price_was ?? 0) }}
                    </span>
                </div>
                <div class="text-caption dora-text-muted row items-center">
                    <StoreLogo
                        v-if="product.store_name"
                        :name="product.store_name"
                        :store-id="product.store_id"
                        :has-image="false"
                        :height="14"
                        :width="24"
                        class="q-mr-xs"
                    />
                    {{ product.store_name || '—' }}
                </div>
            </q-card-section>
        </component>

        <!-- ── Linked stock item ──────────────────────────────────────── -->
        <q-card-section class="q-py-none">
            <q-chip
                v-if="product.linked_stock_item_id"
                dense
                clickable
                color="primary"
                text-color="white"
                :icon="ICONS.link"
                @click.stop="emit('open-stock-item', product.linked_stock_item_id!)"
            >
                {{ product.linked_stock_item_name ?? 'Stock item' }}
                <BaseTooltip>Open stock item</BaseTooltip>
            </q-chip>
            <span v-else class="text-caption dora-text-muted">Not linked</span>
        </q-card-section>

        <q-separator class="q-mt-sm" />
        <!-- ── Actions: fully flattened, no overflow menu (OD-1) ────────
             Delete is pushed past the q-space so it never sits beside
             add-to-list, and is danger-ghost rather than a peer of the
             neutral icons. -->
        <q-card-actions class="product-card__actions items-center">
            <ProductLinkButton
                :linked="!!product.linked_stock_item_id"
                :stock-item-name="product.linked_stock_item_name"
                @link="emit('link')"
                @unlink="emit('unlink')"
            />
            <ProductActiveButton
                :active="product.is_active"
                @toggle="emit('toggle-active')"
            />
            <AddToListButton
                v-if="product.linked_stock_item_id"
                variant="row"
                :stock-item-id="product.linked_stock_item_id"
                :selected-product-id="product.product_id"
                @click.stop
            />
            <!-- Icon-only here: every other control on this face is an
                 icon, and a lone text button made the unlinked card the odd
                 one out. The variant's tooltip still explains that this adds
                 a product-only line, and linked-vs-unlinked is already
                 carried by the chip above and the link button beside it. -->
            <AddToListButton
                v-else
                variant="inline-product"
                label=""
                :product-id="product.product_id"
                @click.stop
            />
            <BaseButton
                variant="icon"
                :icon="ICONS.show_chart"
                aria-label="View price history"
                @click.stop="emit('price-history')"
            >
                <BaseTooltip>View price history</BaseTooltip>
            </BaseButton>
            <q-space />
            <BaseButton
                variant="danger-icon"
                :icon="ICONS.delete"
                aria-label="Delete product"
                @click.stop="emit('delete')"
            >
                <BaseTooltip>Delete product</BaseTooltip>
            </BaseButton>
        </q-card-actions>
    </q-card>
</template>

<script setup lang="ts">
    import BaseTooltip from 'src/components/BaseTooltip.vue';
    /** Expanded ("cards") view of a saved product — the richer of the two
     *  modes the owner asked for (D-10), paired with `ProductRow`.
     *
     *  Draws on the companion's own `ProductSearchCard`: a square image with
     *  the discount overlaid, an out-of-stock overlay, name + size, price with
     *  the struck-through was-price, and the store logo. The owner's note was
     *  that Dora's card sat "half way between what exists in the companion app
     *  and a compact row design" — this commits to the companion end, and
     *  `ProductRow` commits to the other.
     */
    import { computed } from 'vue';
    import AddToListButton from 'src/components/AddToListButton.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import DiscountChip from 'src/components/chips/DiscountChip.vue';
    import ProductActiveButton from 'src/components/products/ProductActiveButton.vue';
    import ProductLinkButton from 'src/components/products/ProductLinkButton.vue';
    import ProductThumb from 'src/components/products/ProductThumb.vue';
    import StoreLogo from 'src/components/StoreLogo.vue';
    import { formatMoney } from 'src/composables/useMoney';
    import { ICONS } from 'src/style/icons';
    import type { Product } from 'src/models/product';

    const props = defineProps<{
        product: Product;
        bulkMode: boolean;
        selected: boolean;
    }>();

    const emit = defineEmits<{
        (e: 'toggle-select'): void;
        (e: 'open-stock-item', stockItemId: string): void;
        (e: 'link'): void;
        (e: 'unlink'): void;
        (e: 'toggle-active'): void;
        (e: 'price-history'): void;
        (e: 'delete'): void;
    }>();

    const hasDiscount = computed(() => {
        const now = props.product.price_now;
        const was = props.product.price_was;
        return now != null && was != null && was > now;
    });

    // Only a real anchor when there's somewhere to go and we're not selecting.
    // A dead <a href="#"> would look clickable and do nothing.
    const isTopHalfLink = computed(
        () => !props.bulkMode && !!props.product.web_url,
    );
    const topHalfTag = computed(() => (isTopHalfLink.value ? 'a' : 'div'));
    const topHalfAttrs = computed(() =>
        isTopHalfLink.value
            ? {
                href: props.product.web_url,
                target: '_blank',
                rel: 'noopener',
                // The link text is the product name inside; naming the
                // destination keeps the purpose obvious out of context (D-005).
                'aria-label': `Open ${props.product.name} at ${props.product.store_name ?? 'the store'}`,
            }
            : {},
    );

    function onTopHalfClick(event: MouseEvent): void {
        // In bulk mode the tap belongs to selection, not navigation.
        if (props.bulkMode) {
            event.preventDefault();
            event.stopPropagation();
            emit('toggle-select');
        }
    }

    function onCardClick(): void {
        if (props.bulkMode) emit('toggle-select');
    }
</script>

<style scoped>
    .product-card {
        transition: outline-color 120ms ease, box-shadow 120ms ease;
        outline: 2px solid transparent;
        outline-offset: -2px;
    }
    .product-card:hover {
        box-shadow: 0 4px 14px var(--overlay-active);
    }
    .product-card--selected {
        outline-color: var(--q-primary);
    }
    .product-card--inactive {
        opacity: 0.6;
    }

    .product-card__top {
        display: flex;
        flex-direction: column;
        text-decoration: none;
        color: inherit;
        flex: 1 1 auto;
        min-height: 0;
    }
    .product-card__top--linked {
        cursor: pointer;
    }
    .product-card__top--linked:hover .text-subtitle2 {
        text-decoration: underline;
    }

    /* `flex: 0 0 auto` keeps the square media out of the card's height
       negotiation: the card is `full-height` and stretches to the tallest in
       its row, and without this the flex layout tries to distribute that
       forced height into a box whose height comes from its own WIDTH
       (`aspect-ratio`). */
    .product-card__media {
        position: relative;
        flex: 0 0 auto;
        aspect-ratio: 1 / 1;
        background: var(--surface-sunken);
    }
    .product-card__discount {
        position: absolute;
        top: var(--space-2);
        left: var(--space-2);
    }
    .product-card__select {
        position: absolute;
        top: var(--space-1);
        right: var(--space-1);
        background: var(--surface-component);
        border-radius: var(--radius-sm);
    }
    .product-card__oos {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        text-align: center;
        padding: var(--space-1) 0;
        font-size: calc(var(--font-size-xs) * 1rem);
        font-weight: 600;
        color: white;
        background: var(--semantic-negative);
    }
    .product-card__was {
        text-decoration: line-through;
    }

    /* One row, no wrapping — the same rule as `FilterRow` and
       `stock-toolbar__actions`: a control band that reflows changes the card's
       height, and in a grid of equal-height cards that ripples to every
       sibling. At 375px five 44px targets plus gaps fit a ~311px card, so
       there is nothing to wrap in practice. */
    .product-card__actions {
        flex-wrap: nowrap;
        gap: var(--space-1);
    }

    .ellipsis-2-lines {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
</style>
