<template>
    <div :class="embedded ? 'q-pa-sm' : 'q-pa-md'">
        <!-- Header + toolbar ──────────────────────────────────────────── -->
        <div class="row items-center q-mb-md q-gutter-sm">
            <BaseButton v-if="!embedded" variant="icon" :icon="ICONS.arrow_back" @click="goBack" />
            <BaseButton v-else variant="icon" :icon="ICONS.close" @click="emit('close')">
                <q-tooltip>Close panel</q-tooltip>
            </BaseButton>
            <div class="text-h5 q-mr-sm" style="min-width: 160px">
                <AppSkeleton v-if="loading && !detail" type="line" width="180px" height="1.6rem" />
                <template v-else>{{ detail?.name || 'Stock item' }}</template>
            </div>
            <q-chip
                v-if="detail?.stock_level_name"
                dense
                :color="getStockLevelColour(detail.stock_level_name as StockLevelName)"
                text-color="white"
            >
                {{ detail.stock_level_name }}
            </q-chip>
            <q-space />
        </div>

        <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-mb-md" dense rounded>
            {{ loadError }}
        </q-banner>

        <FadeTransition mode="out-in">
        <div v-if="loading && !detail" key="sid-loading">
            <!-- Skeleton mirrors the toolbar row + content cards below. -->
            <div class="row q-gutter-sm q-mb-md">
                <AppSkeleton type="rect" width="120px" height="36px" />
                <AppSkeleton type="rect" width="110px" height="36px" />
                <AppSkeleton type="rect" width="130px" height="36px" />
            </div>
            <AppSkeleton type="rect" width="100%" height="160px" class="q-mb-md" />
            <AppSkeleton type="rect" width="100%" height="220px" />
        </div>

        <div v-else-if="detail" key="sid-content">
            <!-- Toolbar actions ─────────────────────────────────────────── -->
            <div class="row q-gutter-sm q-mb-md items-center">
                <BaseButton
                    variant="secondary"
                    :icon="detail.is_open ? 'lock_open' : 'lock'"
                    :label="detail.is_open ? 'Opened' : 'Mark open'"
                    :loading="busy"
                    @click="onToggleOpen"
                />
                <BaseButton variant="secondary" :icon="ICONS.refresh" label="Restock" :loading="busy" @click="onRestock" />
                <BaseButton variant="secondary" :icon="ICONS.event" label="Set expiry" @click="expiryDialogOpen = true" />
                <BaseButton variant="secondary" :icon="ICONS.local_offer" label="Find deals" @click="onFindDeals" />
                <BaseButton variant="primary" :icon="ICONS.add_shopping_cart" label="Add to list" :loading="busy" @click="onAddToList" />
                <q-space />
                <BaseButton
                    v-if="scanningEnabled"
                    variant="secondary"
                    icon="qr_code_2"
                    label="Show QR"
                    @click="showQrOpen = true"
                />
                <BaseButton variant="danger-ghost" :icon="ICONS.delete" label="Delete" @click="confirmDelete" />
            </div>

            <!-- ── QR dialog ────────────────────────────────────────── -->
            <BaseDialog v-model="showQrOpen" card-style="min-width: 280px; max-width: 400px">
                    <q-card-section class="text-center">
                        <div class="text-h6 q-mb-sm">{{ detail.name }}</div>
                        <img
                            :src="qrSrc"
                            alt="QR code"
                            style="width: 256px; height: 256px; max-width: 100%;"
                        />
                    </q-card-section>
                    <q-card-actions align="right">
                        <BaseButton variant="ghost" label="Close" v-close-popup />
                        <BaseButton
                            variant="primary"
                            :icon="ICONS.print"
                            label="Print one"
                            @click="openSingleQrSheet"
                        />
                    </q-card-actions>
            </BaseDialog>

            <q-tabs v-model="tab" dense align="left" class="dora-text-secondary q-mb-sm" no-caps>
                <q-tab name="overview" :icon="ICONS.info" label="Overview" />
                <q-tab name="products" :icon="ICONS.local_offer" :label="`Products (${detail.products.length})`" />
                <q-tab name="recipes" :icon="ICONS.menu_book" :label="`Recipes (${detail.recipes.length})`" />
                <q-tab name="substitutes" :icon="ICONS.swap_horiz" :label="`Substitutes (${detail.substitutes.length})`" />
                <q-tab name="lists" :icon="ICONS.shopping_cart" :label="`Lists (${onLists.length})`" />
                <q-tab name="history" :icon="ICONS.history" label="History" />
            </q-tabs>
            <q-separator />

            <q-tab-panels v-model="tab" animated>
                <!-- ── Overview ───────────────────────────────────────── -->
                <q-tab-panel name="overview">
                    <div class="row q-col-gutter-md">
                        <div class="col-12 col-md-6">
                            <q-list bordered separator class="rounded-borders">
                                <q-item>
                                    <q-item-section>Stock level</q-item-section>
                                    <q-item-section side>
                                        <q-btn-dropdown
                                            outline
                                            dense
                                            no-caps
                                            :color="getStockLevelColour((detail.stock_level_name ?? 'Well-Stocked') as StockLevelName)"
                                            :label="detail.stock_level_name ?? 'Set level'"
                                        >
                                            <q-list dense>
                                                <q-item
                                                    v-for="level in stockLevelStore.stockLevels"
                                                    :key="level.stock_level_id"
                                                    clickable
                                                    v-close-popup
                                                    @click="onChangeStockLevel(level.stock_level_id)"
                                                >
                                                    <q-item-section avatar>
                                                        <q-avatar :color="getStockLevelColour(level.name)" size="16px" />
                                                    </q-item-section>
                                                    <q-item-section>{{ level.name }}</q-item-section>
                                                </q-item>
                                            </q-list>
                                        </q-btn-dropdown>
                                    </q-item-section>
                                </q-item>
                                <q-item>
                                    <q-item-section>Location</q-item-section>
                                    <!-- C-cross Chunk 4 — zone-default
                                         + hover for the full breadcrumb. -->
                                    <q-item-section side class="dora-text-primary">
                                        {{ formatLocation(detail.stock_location_breadcrumb, 'zone') || '—' }}
                                        <q-tooltip v-if="locationHasDetail(detail.stock_location_breadcrumb)">
                                            {{ formatLocation(detail.stock_location_breadcrumb, 'full') }}
                                        </q-tooltip>
                                    </q-item-section>
                                </q-item>
                                <q-item>
                                    <q-item-section>Expiry</q-item-section>
                                    <q-item-section side class="dora-text-primary">
                                        {{ detail.expiry_date || 'Not set' }}
                                    </q-item-section>
                                </q-item>
                                <q-item>
                                    <q-item-section>Open / in-use</q-item-section>
                                    <q-item-section side class="dora-text-primary">
                                        {{ detail.is_open ? `Yes${detail.opened_on ? ' — since ' + detail.opened_on : ''}` : 'Sealed' }}
                                    </q-item-section>
                                </q-item>
                                <q-item>
                                    <q-item-section>Level updated</q-item-section>
                                    <q-item-section side class="dora-text-primary">
                                        {{ relativeTime(detail.stock_level_last_updated) }}
                                    </q-item-section>
                                </q-item>
                            </q-list>
                        </div>

                        <div class="col-12 col-md-6">
                            <!-- C-1 Chunk 6 / FU-033 — image upload + clear.
                                 Reuses the RecipeImageField pattern so the
                                 stock + recipe surfaces look the same.
                                 Saves immediately (no "Save" coupling with
                                 the basics form) — uploading a photo isn't
                                 the same intent as renaming. -->
                            <RecipeImageField
                                :preview-url="imagePreviewUrl"
                                :name="detail?.name"
                                class="q-mb-md"
                                @pick="onPickImage"
                                @clear="onClearImage"
                            />
                            <q-form @submit.prevent="onSaveBasics" class="q-gutter-md">
                                <q-input
                                    v-model="form.name"
                                    outlined
                                    dense
                                    label="Name"
                                    :rules="[(v: string) => (!!v && v.length > 0) || 'Name required']"
                                />
                                <q-select
                                    v-model="form.stock_location_id"
                                    :options="locationOptions"
                                    emit-value
                                    map-options
                                    clearable
                                    outlined
                                    dense
                                    label="Location"
                                />
                                <q-input v-model="form.notes" outlined dense type="textarea" autogrow label="Notes" />
                                <div class="row items-center q-gutter-sm">
                                    <q-toggle
                                        v-model="form.auto_add_when_low"
                                        label="Auto-add when low or out"
                                    />
                                    <q-icon :name="ICONS.info_outline" size="18px" class="dora-text-secondary">
                                        <q-tooltip max-width="320px">
                                            Drops this item onto your primary
                                            shopping list the moment its level
                                            falls to Low or Out — silent, with
                                            an undoable toast. Use for
                                            essentials you never want to run
                                            out of.
                                        </q-tooltip>
                                    </q-icon>
                                </div>
                                <div class="row items-center q-gutter-sm">
                                    <q-toggle
                                        v-model="form.is_flagged"
                                        label="Always include in auto-generated lists"
                                    />
                                    <q-icon :name="ICONS.info_outline" size="18px" class="dora-text-secondary">
                                        <q-tooltip max-width="320px">
                                            Flagged items show up in the
                                            "essentials" auto-generate sources
                                            even when they're well-stocked.
                                            Different from auto-add: this one
                                            only matters when you explicitly
                                            run an auto-generate, not on every
                                            stock change.
                                        </q-tooltip>
                                    </q-icon>
                                </div>
                                <div class="row justify-end q-gutter-sm">
                                    <BaseButton variant="ghost" label="Reset" :disable="!isDirty || savingBasics" @click="resetBasicsForm" />
                                    <BaseButton type="submit" variant="primary" label="Save" :disable="!isDirty" :loading="savingBasics" />
                                </div>
                            </q-form>
                        </div>
                    </div>
                </q-tab-panel>

                <!-- ── Linked products ────────────────────────────────── -->
                <q-tab-panel name="products">
                    <div class="row items-center q-mb-sm">
                        <div class="text-subtitle1">Linked products</div>
                        <q-space />
                        <BaseButton variant="primary" :icon="ICONS.add" label="Link product" @click="openProductPicker" />
                    </div>

                    <div v-if="detail.products.length === 0" class="dora-text-muted text-caption q-pa-md">
                        No products linked yet. Linked products surface deals and prices for this
                        stock item.
                    </div>

                    <div v-else class="row q-col-gutter-md">
                        <div
                            v-for="prod in sortedProducts"
                            :key="prod.product_id"
                            class="col-12 col-md-6"
                        >
                            <q-card bordered flat>
                                <q-card-section class="row items-center no-wrap q-pb-xs">
                                    <MerchantLogo :name="prod.merchant_name" :height="20" :width="34" class="q-mr-sm" />
                                    <div class="col">
                                        <div class="ellipsis text-weight-medium">{{ prod.name }}</div>
                                        <div class="text-caption dora-text-muted">
                                            {{ prod.merchant_name }}
                                            <span v-if="prod.size"> · {{ prod.size }}</span>
                                        </div>
                                    </div>
                                    <q-chip
                                        v-if="discountPct(prod) !== null"
                                        dense
                                        color="negative"
                                        text-color="white"
                                    >
                                        {{ discountPct(prod) }}% off
                                    </q-chip>
                                    <q-btn
                                        flat
                                        dense
                                        round
                                        :icon="detail.preferred_product_id === prod.product_id ? 'star' : 'star_border'"
                                        :color="detail.preferred_product_id === prod.product_id ? 'amber-9' : 'grey'"
                                        @click="togglePreferred(prod.product_id)"
                                    >
                                        <q-tooltip>
                                            {{ detail.preferred_product_id === prod.product_id ? 'Preferred merchant' : 'Set as preferred' }}
                                        </q-tooltip>
                                    </q-btn>
                                </q-card-section>

                                <q-card-section class="row items-center q-py-xs">
                                    <div>
                                        <span v-if="prod.price_now !== null" class="text-h6">
                                            ${{ prod.price_now.toFixed(2) }}
                                        </span>
                                        <span
                                            v-if="prod.price_was !== null && prod.price_now !== null && prod.price_was > prod.price_now"
                                            class="text-caption dora-text-muted strike q-ml-xs"
                                        >
                                            ${{ prod.price_was.toFixed(2) }}
                                        </span>
                                    </div>
                                    <q-space />
                                    <TrendSparkline :values="priceHistory.get(prod.product_id) ?? []" />
                                </q-card-section>

                                <q-separator />
                                <q-card-actions align="right">
                                    <q-btn
                                        v-if="prod.web_url"
                                        flat
                                        dense
                                        round
                                        :icon="ICONS.open_in_new"
                                        :href="prod.web_url"
                                        target="_blank"
                                        rel="noopener"
                                    >
                                        <q-tooltip>Open on {{ prod.merchant_name }}</q-tooltip>
                                    </q-btn>
                                    <BaseButton variant="icon" :icon="ICONS.link_off" class="text-negative" @click="onUnlink(prod.product_id)">
                                        <q-tooltip>Unlink</q-tooltip>
                                    </BaseButton>
                                </q-card-actions>
                            </q-card>
                        </div>
                    </div>

                    <div v-if="cheapestProduct" class="q-mt-md">
                        <q-btn
                            color="primary"
                            no-caps
                            :icon="ICONS.add_shopping_cart"
                            :label="`Add cheapest to list ($${cheapestProduct.price_now?.toFixed(2)} · ${cheapestProduct.merchant_name})`"
                            :loading="busy"
                            @click="onAddCheapest"
                        />
                    </div>
                </q-tab-panel>

                <!-- ── Recipes using this ─────────────────────────────── -->
                <q-tab-panel name="recipes">
                    <div v-if="recipesForDetail.length === 0" class="dora-text-muted text-caption q-pa-md">
                        Not used in any saved recipe.
                    </div>
                    <div v-else class="row q-col-gutter-md">
                        <div
                            v-for="r in recipesForDetail"
                            :key="r.recipe_id"
                            class="col-12 col-sm-6 col-md-4"
                        >
                            <RecipeCard
                                :recipe="r"
                                :highlight-stock-item-ids="[detail.stock_item_id]"
                                @open="goToRecipe"
                                @cook="goToCook"
                                @adjust-meals="onAdjustRecipeMeals"
                                @add-missing="onAddMissing"
                            />
                        </div>
                    </div>
                </q-tab-panel>

                <!-- ── Substitutes ────────────────────────────────────── -->
                <q-tab-panel name="substitutes">
                    <div class="row items-center q-mb-sm">
                        <div class="text-subtitle1">Substitutes</div>
                        <q-space />
                        <q-btn color="primary" dense no-caps :icon="ICONS.add" label="Add substitute" @click="openSubstitutePicker" />
                    </div>

                    <div v-if="detail.substitutes.length === 0" class="dora-text-muted text-caption q-pa-md">
                        No substitutes yet. Add items that can stand in for this one.
                    </div>

                    <q-list v-else separator>
                        <q-item v-for="sub in detail.substitutes" :key="sub.stock_item_id">
                            <q-item-section>
                                <StockItemChip :stock-item="stockItemFor(sub)" :dense="false" />
                            </q-item-section>
                            <q-item-section side>
                                <div class="row q-gutter-xs">
                                    <q-btn
                                        flat
                                        dense
                                        no-caps
                                        :icon="ICONS.swap_horiz"
                                        label="Swap into list"
                                        :loading="busy"
                                        @click="onSwapSubstitute(sub.stock_item_id)"
                                    />
                                    <BaseButton variant="icon" :icon="ICONS.link_off" class="text-negative" @click="onRemoveSubstitute(sub.stock_item_id)">
                                        <q-tooltip>Remove substitute</q-tooltip>
                                    </BaseButton>
                                </div>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-tab-panel>

                <!-- ── On shopping lists ──────────────────────────────── -->
                <q-tab-panel name="lists">
                    <div v-if="onLists.length === 0" class="dora-text-muted text-caption q-pa-md">
                        Not on any active shopping list.
                        <q-btn flat dense no-caps color="primary" label="Add to primary" @click="onAddToList" />
                    </div>
                    <q-list v-else separator>
                        <q-item
                            v-for="l in onLists"
                            :key="l.shopping_list_id"
                            clickable
                            @click="goToList(l.shopping_list_id)"
                        >
                            <q-item-section avatar><q-icon :name="ICONS.shopping_cart" /></q-item-section>
                            <q-item-section>
                                {{ l.name }}
                            </q-item-section>
                            <q-item-section side><q-icon :name="ICONS.open_in_new" size="16px" /></q-item-section>
                        </q-item>
                    </q-list>
                </q-tab-panel>

                <!-- ── History ────────────────────────────────────────── -->
                <q-tab-panel name="history">
                    <div v-if="detail.level_history.length === 0" class="dora-text-muted text-caption q-pa-md">
                        No level changes recorded yet.
                    </div>
                    <q-timeline v-else color="primary">
                        <q-timeline-entry
                            v-for="(h, i) in detail.level_history"
                            :key="i"
                            :title="h.stock_level_name ?? 'Level changed'"
                            :subtitle="formatDateTime(h.changed_at)"
                        />
                    </q-timeline>
                </q-tab-panel>
            </q-tab-panels>
        </div>
        </FadeTransition>

        <!-- ── Set-expiry dialog ──────────────────────────────────────── -->
        <BaseDialog v-model="expiryDialogOpen" card-style="min-width: 320px">
                <q-card-section class="text-h6">Set expiry</q-card-section>
                <q-card-section>
                    <q-date v-model="expiryDraft" mask="YYYY-MM-DD" />
                </q-card-section>
                <q-card-actions align="right">
                    <BaseButton variant="danger-ghost" label="Clear" @click="onSetExpiry(null)" />
                    <q-btn flat no-caps label="Cancel" v-close-popup />
                    <q-btn color="primary" no-caps label="Save" :loading="busy" @click="onSetExpiry(expiryDraft)" />
                </q-card-actions>
        </BaseDialog>

        <!-- ── Link-product picker dialog ─────────────────────────────── -->
        <BaseDialog v-model="pickerOpen" card-style="width: 640px; max-width: 95vw">
                <q-card-section class="row items-center q-pb-none">
                    <div class="text-h6">Link a product</div>
                    <q-space />
                    <q-btn flat dense round :icon="ICONS.close" v-close-popup />
                </q-card-section>
                <q-card-section>
                    <q-input v-model="pickerSearch" outlined dense debounce="150" placeholder="Search saved products" clearable>
                        <template #prepend><q-icon :name="ICONS.search" /></template>
                    </q-input>
                </q-card-section>
                <q-card-section class="q-pt-none" style="max-height: 60vh; overflow: auto">
                    <q-banner v-if="pickerLoading" class="dora-bg-sunken" dense>Loading products…</q-banner>
                    <q-banner v-else-if="pickerCandidates.length === 0" class="dora-bg-sunken" dense>
                        No matching saved products.
                    </q-banner>
                    <q-list v-else separator>
                        <q-item v-for="prod in pickerCandidates" :key="prod.product_id" clickable @click="onLink(prod.product_id)">
                            <q-item-section avatar>
                                <q-avatar rounded size="36px" class="dora-bg-sunken dora-text-secondary">
                                    {{ prod.merchant_name.substring(0, 1).toUpperCase() }}
                                </q-avatar>
                            </q-item-section>
                            <q-item-section>
                                <q-item-label class="ellipsis">{{ prod.name }}</q-item-label>
                                <q-item-label caption>{{ prod.merchant_name }}<span v-if="prod.size"> · {{ prod.size }}</span></q-item-label>
                            </q-item-section>
                            <q-item-section side><q-btn flat round dense :icon="ICONS.add_link" color="primary" /></q-item-section>
                        </q-item>
                    </q-list>
                </q-card-section>
        </BaseDialog>

        <!-- ── Add-substitute picker dialog ───────────────────────────── -->
        <BaseDialog v-model="subPickerOpen" card-style="width: 560px; max-width: 95vw">
                <q-card-section class="row items-center q-pb-none">
                    <div class="text-h6">Add a substitute</div>
                    <q-space />
                    <q-btn flat dense round :icon="ICONS.close" v-close-popup />
                </q-card-section>
                <q-card-section>
                    <q-input v-model="subSearch" outlined dense autofocus debounce="150" placeholder="Search stock items" clearable>
                        <template #prepend><q-icon :name="ICONS.search" /></template>
                    </q-input>
                </q-card-section>
                <q-card-section class="q-pt-none" style="max-height: 60vh; overflow: auto">
                    <q-list separator>
                        <q-item v-for="si in substituteCandidates" :key="si.stock_item_id" clickable @click="onAddSubstitute(si.stock_item_id)">
                            <q-item-section avatar><q-icon name="inventory_2" /></q-item-section>
                            <q-item-section>{{ si.name }}</q-item-section>
                            <q-item-section side><q-btn flat round dense :icon="ICONS.add" color="primary" /></q-item-section>
                        </q-item>
                        <q-item v-if="substituteCandidates.length === 0">
                            <q-item-section class="dora-text-muted">No matching items.</q-item-section>
                        </q-item>
                    </q-list>
                </q-card-section>
        </BaseDialog>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import AppSkeleton from 'src/components/AppSkeleton.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import FadeTransition from 'src/components/transitions/FadeTransition.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import MerchantLogo from 'src/components/MerchantLogo.vue';
    import RecipeCard from 'src/components/RecipeCard.vue';
    import RecipeImageField from 'src/components/recipes/RecipeImageField.vue';
    import TrendSparkline from 'src/components/TrendSparkline.vue';
    import StockItemChip from 'src/components/chips/StockItemChip.vue';
    import { useScanningEnabled } from 'src/composables/useScanningEnabled';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import { useStockItemActions } from 'src/composables/useStockItemActions';
    import { getStockLevelColour } from 'src/helpers/stockLevelLogic';
    import type { Product } from 'src/models/product';
    import type { Recipe } from 'src/models/recipe';
    import type { StockLevelName } from 'src/models/stockLevel';
    import type { LinkedProduct, StockItemDetail, Substitute } from 'src/models/stockItemDetail';
    import type { StockItem } from 'src/models/stockItem';
    import ProductApiService from 'src/services/api/productApiService';
    import { resolveBaseURL, NormalisedApiError } from 'src/services/api/axiosHttpClient';
    import StockItemApiService, { stockItemImageUrl } from 'src/services/api/stockItemApiService';
    import { useProductStore } from 'src/stores/productStore';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { useStockLocationStore } from 'src/stores/stockLocationStore';
    import { formatLocation, locationHasDetail } from 'src/helpers/locationDisplay';
    import { computed, onMounted, reactive, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const props = defineProps<{ idOverride?: string; embedded?: boolean }>();
    const emit = defineEmits<{ (e: 'close'): void }>();

    const route = useRoute();
    const router = useRouter();
    const $q = useQuasar();

    const stockItemApi = new StockItemApiService();
    const productApi = new ProductApiService();

    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const stockLocationStore = useStockLocationStore();
    const productStore = useProductStore();
    const recipeStore = useRecipeStore();
    const shoppingListStore = useShoppingListStore();

    const { stockLocations } = storeToRefs(stockLocationStore);
    const { stockItems } = storeToRefs(stockItemStore);
    const { recipes } = storeToRefs(recipeStore);

    const actions = useStockItemActions();
    const slActions = useShoppingListActions();

    const stockItemId = computed(() => props.idOverride ?? (route.params.id as string));

    const detail = ref<StockItemDetail | null>(null);
    const loading = ref(false);
    const loadError = ref<string | null>(null);
    const busy = ref(false);

    // ── QR labels (gated by the install-wide scanning flag) ──────────
    const { scanningEnabled } = useScanningEnabled();
    const showQrOpen = ref(false);
    const qrSrc = computed(() => {
        const baseUrl = resolveBaseURL('dora');
        // size 512 looks crisp on retina; the dialog box clamps to 256.
        return `${baseUrl}/stock-items/${stockItemId.value}/qr?size=512`;
    });

    function openSingleQrSheet() {
        const baseUrl = resolveBaseURL('dora');
        window.open(
            `${baseUrl}/stock-items/qr/sheet?ids=${stockItemId.value}`,
            '_blank', 'noopener',
        );
    }

    const tab = ref<string>(
        typeof route.query.section === 'string' ? route.query.section : 'overview',
    );

    const locationOptions = computed(() =>
        stockLocations.value.map((l) => ({ label: l.name, value: l.stock_location_id })),
    );

    // ── Basics form ──────────────────────────────────────────────────────
    type BasicsForm = {
        name: string;
        notes: string;
        stock_location_id: string | null;
        auto_add_when_low: boolean;
        is_flagged: boolean;
    };
    const emptyBasics = (): BasicsForm => ({ name: '', notes: '', stock_location_id: null, auto_add_when_low: false, is_flagged: false });
    const form = reactive<BasicsForm>(emptyBasics());
    const savingBasics = ref(false);

    function hydrateForm(d: StockItemDetail) {
        form.name = d.name;
        form.notes = d.notes ?? '';
        form.stock_location_id = d.stock_location_id;
        form.auto_add_when_low = d.auto_add_when_low;
        form.is_flagged = d.is_flagged;
    }
    function resetBasicsForm() {
        if (detail.value) hydrateForm(detail.value);
    }
    const isDirty = computed(() => {
        if (!detail.value) return false;
        return (
            form.name !== detail.value.name ||
            (form.notes ?? '') !== (detail.value.notes ?? '') ||
            form.stock_location_id !== detail.value.stock_location_id ||
            form.auto_add_when_low !== detail.value.auto_add_when_low ||
            form.is_flagged !== detail.value.is_flagged
        );
    });
    // ── Image (C-1 Chunk 6 / FU-033) ────────────────────────────────────
    // Saves immediately — uploading a photo isn't coupled to the basics
    // form's Save button. `imageVersion` busts the <img> cache after a
    // save so the new bytes show without a hard reload.
    const pendingImage = ref<string | null>(null);
    const imageCleared = ref(false);
    const imageVersion = ref(0);
    const imagePreviewUrl = computed<string | null>(() => {
        if (pendingImage.value) return pendingImage.value;
        if (imageCleared.value) return null;
        if (!detail.value?.has_image) return null;
        return stockItemImageUrl(detail.value.stock_item_id, imageVersion.value);
    });
    async function onPickImage(dataUrl: string) {
        if (!detail.value) return;
        pendingImage.value = dataUrl;
        try {
            await stockItemStore.updateStockItemAsync({
                stock_item_id: detail.value.stock_item_id,
                image: dataUrl,
            });
            imageCleared.value = false;
            pendingImage.value = null;
            imageVersion.value++;
            await loadDetail();
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Image updated.' });
        } catch (err) {
            pendingImage.value = null;
            notifyErr('Could not save image.', err);
        }
    }
    async function onClearImage() {
        if (!detail.value) return;
        try {
            await stockItemStore.updateStockItemAsync({
                stock_item_id: detail.value.stock_item_id,
                image: null,
            });
            imageCleared.value = true;
            imageVersion.value++;
            await loadDetail();
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Image removed.' });
        } catch (err) {
            notifyErr('Could not remove image.', err);
        }
    }

    async function onSaveBasics() {
        if (!detail.value) return;
        savingBasics.value = true;
        try {
            await stockItemStore.updateStockItemAsync({
                stock_item_id: detail.value.stock_item_id,
                name: form.name,
                notes: form.notes.length > 0 ? form.notes : null,
                stock_location_id: form.stock_location_id,
                auto_add_when_low: form.auto_add_when_low,
                is_flagged: form.is_flagged,
            });
            await loadDetail();
            $q.notify({ type: 'positive', message: 'Saved.', position: 'bottom-right' });
        } catch (err) {
            notifyErr('Save failed.', err);
        } finally {
            savingBasics.value = false;
        }
    }

    // ── Toolbar actions ──────────────────────────────────────────────────
    async function withBusyReload(fn: () => Promise<void>) {
        busy.value = true;
        try {
            await fn();
            await loadDetail();
        } finally {
            busy.value = false;
        }
    }
    async function onToggleOpen() {
        if (!detail.value) return;
        const next = !detail.value.is_open;
        await withBusyReload(() =>
            stockItemStore.updateStockItemAsync({ stock_item_id: stockItemId.value, is_open: next }),
        );
    }
    async function onRestock() {
        await withBusyReload(() => actions.markRestocked(stockItemId.value));
    }
    async function onAddToList() {
        await withBusyReload(() => actions.addToList(stockItemId.value));
    }
    function onFindDeals() {
        void router.push({ path: '/product-search', query: { q: detail.value?.name ?? '' } });
    }
    async function onChangeStockLevel(stockLevelId: string) {
        await withBusyReload(() =>
            stockItemStore.updateStockLevelAsync({
                stock_item_id: stockItemId.value,
                stock_level_id: stockLevelId,
            }),
        );
    }

    // ── Expiry ───────────────────────────────────────────────────────────
    const expiryDialogOpen = ref(false);
    const expiryDraft = ref<string | null>(null);
    watch(expiryDialogOpen, (open) => {
        if (open) expiryDraft.value = detail.value?.expiry_date ?? null;
    });
    async function onSetExpiry(value: string | null) {
        await withBusyReload(() =>
            stockItemStore.updateStockItemAsync({ stock_item_id: stockItemId.value, expiry_date: value }),
        );
        expiryDialogOpen.value = false;
    }

    // ── Linked products ──────────────────────────────────────────────────
    const priceHistory = ref<Map<string, number[]>>(new Map());

    function discountPct(p: LinkedProduct): number | null {
        if (p.price_now == null || p.price_was == null || p.price_was <= 0 || p.price_now >= p.price_was)
            return null;
        return Math.round(((p.price_was - p.price_now) / p.price_was) * 100);
    }

    // Preferred product first, then cheapest, then by name.
    const sortedProducts = computed(() => {
        const preferred = detail.value?.preferred_product_id;
        return [...(detail.value?.products ?? [])].sort((a, b) => {
            if (a.product_id === preferred) return -1;
            if (b.product_id === preferred) return 1;
            return (a.price_now ?? Infinity) - (b.price_now ?? Infinity);
        });
    });
    const cheapestProduct = computed<LinkedProduct | null>(() => {
        const withPrice = (detail.value?.products ?? []).filter((p) => p.price_now != null);
        if (withPrice.length === 0) return null;
        return withPrice.reduce((min, p) => (p.price_now! < min.price_now! ? p : min));
    });

    async function loadPriceHistories(products: LinkedProduct[]) {
        const map = new Map<string, number[]>();
        await Promise.all(
            products.map(async (p) => {
                try {
                    const h = await productApi.getPriceHistoryAsync(p.product_id);
                    map.set(
                        p.product_id,
                        h.points.map((pt) => pt.price_now ?? 0).filter((n) => n > 0),
                    );
                } catch {
                    // Sparkline just renders empty if history can't be loaded.
                }
            }),
        );
        priceHistory.value = map;
    }

    async function togglePreferred(productId: string) {
        if (!detail.value) return;
        const next = detail.value.preferred_product_id === productId ? null : productId;
        await withBusyReload(() =>
            stockItemStore.updateStockItemAsync({
                stock_item_id: stockItemId.value,
                preferred_product_id: next,
            }),
        );
    }

    async function onAddCheapest() {
        if (!cheapestProduct.value) return;
        const primary = shoppingListStore.quickAddTargetListId;
        busy.value = true;
        try {
            if (primary) {
                await slActions.addItems(primary, [
                    {
                        stock_item_id: stockItemId.value,
                        selected_product_id: cheapestProduct.value.product_id,
                    },
                ]);
            } else {
                await actions.addToList(stockItemId.value);
            }
        } finally {
            busy.value = false;
        }
    }

    // ── Recipes ──────────────────────────────────────────────────────────
    const recipesForDetail = computed<Recipe[]>(() => {
        const ids = new Set((detail.value?.recipes ?? []).map((r) => r.recipe_id));
        return recipes.value.filter((r) => ids.has(r.recipe_id)) as unknown as Recipe[];
    });
    function goToRecipe(recipeId: string) {
        void router.push({ path: '/recipes', query: { recipe: recipeId } });
    }
    function goToCook(recipeId: string) {
        void router.push(`/recipes/${recipeId}/cook`);
    }
    async function onAdjustRecipeMeals(recipeId: string, delta: number) {
        try {
            await recipeStore.adjustMealsAsync(recipeId, delta);
        } catch {
            $q.notify({ type: 'negative', position: 'bottom-right', message: 'Could not update meals.' });
        }
    }
    async function onAddMissing(_recipeId: string, stockItemIds: string[]) {
        const primary = shoppingListStore.quickAddTargetListId;
        if (!primary) {
            await actions.addToList(stockItemIds[0] ?? stockItemId.value);
            return;
        }
        busy.value = true;
        try {
            await slActions.addItems(primary, stockItemIds.map((id) => ({ stock_item_id: id })));
        } finally {
            busy.value = false;
        }
    }

    // ── Substitutes ──────────────────────────────────────────────────────
    function stockItemFor(sub: Substitute): StockItem {
        const full = stockItems.value.find((si) => si.stock_item_id === sub.stock_item_id);
        if (full) return full;
        return {
            stock_item_id: sub.stock_item_id,
            name: sub.name,
            stock_level_id: sub.stock_level_id ?? '',
            stock_location_id: null,
            stock_group_id: null,
        };
    }
    const subPickerOpen = ref(false);
    const subSearch = ref('');
    const substituteCandidates = computed(() => {
        const existing = new Set((detail.value?.substitutes ?? []).map((s) => s.stock_item_id));
        const q = subSearch.value.trim().toLowerCase();
        return stockItems.value
            .filter(
                (si) =>
                    si.stock_item_id !== stockItemId.value &&
                    !existing.has(si.stock_item_id) &&
                    (!q || si.name.toLowerCase().includes(q)),
            )
            .slice(0, 30);
    });
    function openSubstitutePicker() {
        subSearch.value = '';
        subPickerOpen.value = true;
    }
    async function onAddSubstitute(substituteId: string) {
        subPickerOpen.value = false;
        await withBusyReload(() => stockItemApi.addSubstituteAsync(stockItemId.value, substituteId));
    }
    async function onRemoveSubstitute(substituteId: string) {
        await withBusyReload(() => stockItemApi.removeSubstituteAsync(stockItemId.value, substituteId));
    }
    async function onSwapSubstitute(substituteId: string) {
        await withBusyReload(() => actions.addToList(substituteId));
    }

    // ── On shopping lists ────────────────────────────────────────────────
    const onLists = computed(() => {
        const m = shoppingListStore.membership;
        const entry = m?.items.find((i) => i.stock_item_id === stockItemId.value);
        const ids = entry?.unticked_list_ids ?? [];
        const lookup = new Map((m?.active_lists ?? []).map((l) => [l.shopping_list_id, l]));
        return ids.map(
            (lid) => lookup.get(lid) ?? { shopping_list_id: lid, name: lid, status: 'draft' as const },
        );
    });
    function goToList(listId: string) {
        void router.push(`/shopping-lists/${listId}`);
    }

    // ── Link / unlink products ───────────────────────────────────────────
    const pickerOpen = ref(false);
    const pickerSearch = ref('');
    const pickerLoading = ref(false);
    const allSavedProducts = computed<Product[]>(() => [...(productStore.products ?? [])]);
    const pickerCandidates = computed(() => {
        if (!detail.value) return [];
        const linked = new Set(detail.value.products.map((p) => p.product_id));
        const q = pickerSearch.value.trim().toLowerCase();
        return allSavedProducts.value.filter((p) => {
            if (linked.has(p.product_id)) return false;
            if (!q) return true;
            return (
                p.name.toLowerCase().includes(q) ||
                p.merchant_name?.toLowerCase().includes(q) ||
                (p.brand ?? '').toLowerCase().includes(q)
            );
        });
    });
    async function openProductPicker() {
        pickerSearch.value = '';
        pickerOpen.value = true;
        if (allSavedProducts.value.length === 0) {
            pickerLoading.value = true;
            try {
                await productStore.getProductsAsync();
            } finally {
                pickerLoading.value = false;
            }
        }
    }
    async function onLink(productId: string) {
        pickerOpen.value = false;
        await withBusyReload(() => stockItemApi.linkProductAsync(stockItemId.value, productId));
    }
    async function onUnlink(productId: string) {
        await withBusyReload(() => stockItemApi.unlinkProductAsync(stockItemId.value, productId));
    }

    // ── Delete ───────────────────────────────────────────────────────────
    function confirmDelete() {
        if (!detail.value) return;
        const item = detail.value;
        $q.dialog({
            title: 'Delete stock item',
            message: `Delete "${item.name}"?`,
            cancel: true,
        }).onOk(() => void doDelete(item.stock_item_id));
    }
    async function doDelete(id: string) {
        try {
            await stockItemStore.deleteStockItemAsync(id);
            if (props.embedded) emit('close');
            else void router.push('/stock');
        } catch (err) {
            // B4: backend refuses delete when the item is still on a recipe,
            // returning 422 with a structured `blocked_by_recipes` list.
            // Surface the recipe names in a dialog rather than a vague toast
            // so the user knows where to act.
            if (err instanceof NormalisedApiError) {
                const blocked = err.details?.blocked_by_recipes;
                if (Array.isArray(blocked) && blocked.length > 0) {
                    const lines = (blocked as Array<{ name: string }>)
                        .map((r) => `<li>${r.name}</li>`)
                        .join('');
                    $q.dialog({
                        title: 'Still used by recipes',
                        message:
                            `<p>Can't delete this stock item — it's an ingredient on ${blocked.length} recipe(s):</p>` +
                            `<ul>${lines}</ul>` +
                            `<p>Remove it from those recipes first, then try again.</p>`,
                        html: true,
                        ok: { label: 'OK', flat: true },
                    });
                    return;
                }
            }
            notifyErr('Could not delete this stock item.', err);
        }
    }

    // ── Helpers ──────────────────────────────────────────────────────────
    function notifyErr(message: string, err: unknown) {
        $q.notify({ type: 'negative', position: 'bottom-right', message, caption: describeApiError(err) || '' });
    }
    function formatDateTime(iso: string): string {
        if (!iso) return '';
        return new Date(iso).toLocaleString();
    }
    function relativeTime(iso: string): string {
        if (!iso) return '';
        const diffMs = Date.now() - new Date(iso).getTime();
        const mins = Math.floor(diffMs / 60_000);
        if (mins < 1) return 'just now';
        if (mins < 60) return `${mins}m ago`;
        const hours = Math.floor(mins / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        if (days < 7) return `${days}d ago`;
        const weeks = Math.floor(days / 7);
        if (weeks < 5) return `${weeks}w ago`;
        const months = Math.floor(days / 30);
        if (months < 12) return `${months}mo ago`;
        return `${Math.floor(days / 365)}y ago`;
    }

    function goBack() {
        if (window.history.length > 1) router.back();
        else void router.push('/stock');
    }

    async function loadDetail() {
        loading.value = true;
        loadError.value = null;
        try {
            const d = await stockItemApi.getDetailAsync(stockItemId.value);
            detail.value = d;
            hydrateForm(d);
            void loadPriceHistories(d.products);
            // Membership feeds the "on lists" tab and chips.
            void shoppingListStore.refreshAsync();
        } catch (err) {
            loadError.value = 'Could not load this stock item.';
            console.warn('stock-item detail load failed', err);
        } finally {
            loading.value = false;
        }
    }

    watch(stockItemId, () => {
        if (stockItemId.value) void loadDetail();
    });

    onMounted(async () => {
        await Promise.all([
            stockLevelStore.getStockLevelsAsync(),
            stockLocationStore.getStockLocationsAsync(),
            stockItemStore.getStockItemsAsync(),
            recipeStore.getRecipesAsync(),
            shoppingListStore.refreshAsync(),
        ]);
        await loadDetail();
    });
</script>

<style scoped>
    .strike {
        text-decoration: line-through;
    }
</style>
