<template>
    <q-chip
        :dense="dense"
        :clickable="!!product.web_url"
        class="product-chip"
        @click="openLink"
    >
        <q-avatar rounded size="24px" class="q-mr-xs product-chip__img">
            <img v-if="product.image" :src="product.image" :alt="product.name" />
            <q-icon v-else :name="ICONS.shopping_bag" size="16px" />
        </q-avatar>

        <div class="column no-wrap product-chip__text">
            <span class="ellipsis">{{ product.name }}</span>
            <span v-if="product.brand" class="text-caption dora-text-muted ellipsis">
                {{ product.brand }}
            </span>
        </div>

        <StoreLogo
            v-if="product.store_name"
            :name="product.store_name"
            :store-id="product.store_id"
            :has-image="false"
            :height="16"
            :width="28"
            class="q-ml-xs"
        />

        <!-- Deal badge: % off when discounted, otherwise the current price -->
        <q-badge
            v-if="discountPct !== null"
            color="negative"
            text-color="white"
            class="q-ml-xs"
        >
            {{ discountPct }}% off
        </q-badge>
        <q-badge
            v-else-if="product.price_now != null"
            color="grey"
            text-color="white"
            class="q-ml-xs"
        >
            {{ priceLabel }}
        </q-badge>

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
                <q-list dense style="min-width: 180px">
                    <q-item v-if="product.web_url" clickable @click="openLink">
                        <q-item-section avatar><q-icon :name="ICONS.open_in_new" /></q-item-section>
                        <q-item-section>Open at store</q-item-section>
                    </q-item>
                    <q-item clickable @click="emit('add-to-list', product.product_id)">
                        <q-item-section avatar><q-icon :name="ICONS.add_shopping_cart" /></q-item-section>
                        <q-item-section>Add to list</q-item-section>
                    </q-item>
                    <q-item clickable @click="emit('link-stock-item', product.product_id)">
                        <q-item-section avatar><q-icon :name="ICONS.link" /></q-item-section>
                        <q-item-section>Link to stock item</q-item-section>
                    </q-item>
                </q-list>
            </q-menu>
        </q-btn>
    </q-chip>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import StoreLogo from 'src/components/StoreLogo.vue';
    import { computed } from 'vue';

    // Structural type covering both Product and LinkedProduct so the chip works
    // for search results and detail-page linked products alike.
    export type ProductChipModel = {
        product_id: string;
        name: string;
        brand?: string | null;
        image?: string | null;
        store_id?: string | null;
        store_name?: string | null;
        web_url?: string | null;
        price_now?: number | null;
        price_was?: number | null;
    };

    const props = withDefaults(
        defineProps<{
            product: ProductChipModel;
            dense?: boolean;
        }>(),
        { dense: true },
    );

    const emit = defineEmits<{
        (e: 'add-to-list', productId: string): void;
        (e: 'link-stock-item', productId: string): void;
    }>();

    const discountPct = computed(() => {
        const now = props.product.price_now;
        const was = props.product.price_was;
        if (now == null || was == null || was <= 0 || now >= was) return null;
        return Math.round(((was - now) / was) * 100);
    });

    const priceLabel = computed(() =>
        props.product.price_now != null ? `$${props.product.price_now.toFixed(2)}` : '',
    );

    function openLink() {
        if (props.product.web_url) {
            window.open(props.product.web_url, '_blank', 'noopener');
        }
    }
</script>

<style scoped>
    .product-chip__text {
        max-width: 160px;
        line-height: 1.1;
    }
    .product-chip__img img {
        object-fit: contain;
    }
</style>
