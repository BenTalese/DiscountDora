<template>
    <q-card flat bordered class="product-search-card column no-wrap full-height">
        <!-- Image + %off badge -->
        <div class="product-search-card__media">
            <q-img
                :src="imageSrc"
                :ratio="1"
                fit="contain"
                class="bg-grey-1"
            >
                <template #error>
                    <div class="absolute-full flex flex-center bg-grey-2 text-grey">
                        <q-icon :name="ICONS.image_not_supported" size="32px" />
                    </div>
                </template>
            </q-img>
            <q-badge
                v-if="discountPct !== null"
                class="product-search-card__discount"
                :style="discountBadgeStyle"
                text-color="white"
            >
                {{ discountPct }}% off
            </q-badge>
            <div v-if="!offer.is_available" class="product-search-card__oos">OUT OF STOCK</div>
            <q-btn
                round
                dense
                size="sm"
                class="product-search-card__fav"
                :icon="saved ? 'favorite' : 'favorite_border'"
                :color="saved ? 'red-12' : 'grey-7'"
                @click="emit('save')"
            >
                <q-tooltip>{{ saved ? 'Saved' : 'Save to My Products' }}</q-tooltip>
            </q-btn>
            <q-checkbox
                :model-value="inComparison"
                class="product-search-card__compare"
                dense
                @update:model-value="emit('toggle-compare')"
            >
                <q-tooltip>Add to comparison</q-tooltip>
            </q-checkbox>
        </div>

        <q-card-section class="q-py-sm col">
            <div class="text-body2 ellipsis-2-lines">
                {{ offer.name }}
                <span v-if="offer.size" class="text-grey">· {{ offer.size }}</span>
            </div>
        </q-card-section>

        <q-card-section class="q-py-none">
            <div class="row items-center no-wrap">
                <template v-if="offer.price_now > 0">
                    <span class="text-h6">${{ offer.price_now.toFixed(2) }}</span>
                    <span
                        v-if="onSpecial"
                        class="text-caption text-grey strike q-ml-xs"
                    >${{ offer.price_was.toFixed(2) }}</span>
                </template>
                <span v-else class="text-caption text-grey">Price unavailable</span>
                <q-space />
                <TrendSparkline v-if="hist.length >= 2" :values="hist" :width="80" :height="24" />
            </div>
            <div class="text-caption text-grey">
                {{ unitLabel ?? offer.price_per_cup ?? '' }}
            </div>
        </q-card-section>

        <q-separator />
        <q-card-actions class="bg-grey-1 items-center">
            <MerchantLogo :name="offer.merchant_name" :height="18" :width="32" />
            <q-space />
            <q-btn
                v-if="offer.web_url"
                flat dense round size="sm" :icon="ICONS.open_in_new"
                :href="offer.web_url" target="_blank" rel="noopener"
            >
                <q-tooltip>Open on {{ offer.merchant_name }}</q-tooltip>
            </q-btn>
            <q-btn flat dense round size="sm" :icon="ICONS.link" @click="emit('link')">
                <q-tooltip>Link to a stock item</q-tooltip>
            </q-btn>
            <q-btn flat dense round size="sm" :icon="ICONS.add_shopping_cart" color="primary" @click="emit('quick-add')">
                <q-tooltip>Quick-add: track it + add to your list</q-tooltip>
            </q-btn>
        </q-card-actions>
    </q-card>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import MerchantLogo from 'src/components/MerchantLogo.vue';
    import TrendSparkline from 'src/components/TrendSparkline.vue';
    import {
        discountPercent,
        isOfferOnSpecial,
        unitPriceLabel,
    } from 'src/helpers/scrapedProductOfferLogic';
    import type { ScrapedProductOffer } from 'src/models/scrapedProductOffer';
    import ImageService from 'src/services/files/imageService';
    import { computed } from 'vue';

    const props = withDefaults(
        defineProps<{
            offer: ScrapedProductOffer;
            saved?: boolean;
            inComparison?: boolean;
            history?: number[];
        }>(),
        { saved: false, inComparison: false, history: () => [] },
    );

    const emit = defineEmits<{
        (e: 'save'): void;
        (e: 'link'): void;
        (e: 'quick-add'): void;
        (e: 'toggle-compare'): void;
    }>();

    const imageService = new ImageService();
    const imageSrc = computed(() => imageService.decodeBase64Image(props.offer.image));

    const hist = computed(() => props.history ?? []);
    const onSpecial = computed(() => isOfferOnSpecial(props.offer));
    const discountPct = computed(() => discountPercent(props.offer));
    const unitLabel = computed(() => unitPriceLabel(props.offer));

    // Scale the badge from amber (small discount) to deep red (half-price+) so
    // the eye is drawn to the best deals.
    const discountBadgeStyle = computed(() => {
        const pct = discountPct.value ?? 0;
        const t = Math.min(pct / 50, 1); // 0 at 0%, 1 at 50%+ off
        const hue = 45 - 45 * t; // 45 (amber) → 0 (red)
        const light = 50 - 8 * t;
        return { backgroundColor: `hsl(${hue}, 90%, ${light}%)` };
    });
</script>

<style scoped>
    .product-search-card__media {
        position: relative;
    }
    .product-search-card__discount {
        position: absolute;
        top: 6px;
        left: 6px;
        font-weight: 700;
    }
    .product-search-card__oos {
        position: absolute;
        bottom: 6px;
        left: 6px;
        background: rgba(0, 0, 0, 0.65);
        color: white;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .product-search-card__fav {
        position: absolute;
        top: 4px;
        right: 4px;
        background: rgba(255, 255, 255, 0.85);
    }
    .product-search-card__compare {
        position: absolute;
        bottom: 4px;
        right: 4px;
        background: rgba(255, 255, 255, 0.85);
        border-radius: 4px;
        padding: 0 2px;
    }
    .strike {
        text-decoration: line-through;
    }
    .ellipsis-2-lines {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        min-height: 2.5em;
    }
</style>
