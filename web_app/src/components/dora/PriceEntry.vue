<template>
    <!--
        FU-227 chunk 3 — the shared "Your prices" entry form (F1 / R-001).
        One component, used by:
          • the stock-overview row "Log a price" button (shelf-price mode)
          • the stock-item detail YourPricesWidget [Log a price] action
          • (chunk 5) the shopping-line at /finish (harvest mode)

        Modes (§6a):
          • shelf  → "I SAW $X for size Y at maybe store Z". Default form
                     is three inputs (price, size, unit) + optional store.
                     The multipack disclosure adds an optional "Count"
                     field (4×125g) — when set, "Size" becomes "Size each"
                     and the form computes total_measure = count × size
                     for the server.
          • harvest → "I BOUGHT N for total $X". Used at /finish to map a
                      line into an observation. Count is read from the line.

        Validation: unit must be on the supported price list
        (volume / mass / count) from `generated/units_table` — kJ, °C, mm
        are rejected (they're recipe-side). The picker groups by dimension
        per B3 (flat global list, last-time prefill via the F2 prefill
        prop — NO smart per-item defaults ever).
    -->
    <div class="dora-price-entry q-gutter-sm">
        <div v-if="prefill?.source_label" class="text-caption dora-text-muted q-mb-xs">
            Prefilled {{ prefill.source_label }}
        </div>

        <div class="row q-gutter-sm items-start">
            <q-input
                v-model.number="totalPrice"
                dense outlined type="number"
                prefix="$"
                class="col"
                :label="mode === 'harvest' ? 'Total paid' : 'Price'"
                :rules="[(v) => (v != null && v > 0) || 'Required']"
                hide-bottom-space
            />
            <q-input
                v-if="mode === 'shelf'"
                v-model.number="perPackSize"
                dense outlined type="number"
                class="col"
                :label="isMultipack ? 'Size each' : 'Size'"
                :rules="[(v) => (v != null && v > 0) || 'Required']"
                hide-bottom-space
            />
            <q-select
                v-model="unit"
                :options="unitOptions"
                dense outlined emit-value map-options
                class="col"
                label="Unit"
                :rules="[(v) => !!v || 'Required']"
                hide-bottom-space
            />
        </div>

        <!-- Multipack disclosure. Hidden by default — the common case is
             single-pack / free-weight. When the user buys "4 × 125g yoghurt",
             they tick this open + enter 4; the form computes total_measure
             server-side (`count × per_pack_size`) and persists pack_count so
             the obs list can later render "4 × 125g". -->
        <div v-if="mode === 'shelf'">
            <BaseButton
                v-if="!packCountVisible"
                variant="ghost"
                dense size="sm"
                :icon="ICONS.add"
                label="Add pack count (multipack)"
                @click="packCountVisible = true"
            />
            <div v-else class="row q-gutter-sm items-start">
                <q-input
                    v-model.number="packCount"
                    dense outlined type="number"
                    class="col"
                    label="Count (packs)"
                    hint="e.g. 4 for a 4-pack of yoghurt"
                    :rules="[(v) => v == null || v > 0 || 'Must be > 0']"
                    hide-bottom-space
                />
                <BaseButton
                    variant="icon"
                    :icon="ICONS.close"
                    aria-label="Clear pack count"
                    @click="clearPackCount"
                />
            </div>
        </div>

        <q-select
            v-if="mode === 'shelf' && storeOptions.length > 0"
            v-model="storeId"
            :options="storeOptions"
            dense outlined emit-value map-options clearable
            label="Store (optional)"
        />

        <!-- Live preview: $X.XX per Y. For multipacks, also surface the
             total ("4 × 125g = 500g total") so the user can sanity-check. -->
        <div
            v-if="perUnitPreview"
            class="dora-bg-sunken dora-text-secondary q-pa-sm rounded-borders text-body2"
        >
            ≈ <strong>${{ perUnitPreview }}</strong> per {{ unit }}
            <span v-if="isMultipack" class="dora-text-muted">
                · {{ packCount }} × {{ perPackSize }}{{ unit }} = {{ totalMeasureDisplay }}{{ unit }} total
            </span>
        </div>

        <div class="row justify-end q-gutter-sm q-mt-sm">
            <BaseButton
                variant="ghost"
                label="Cancel"
                @click="onCancel"
            />
            <BaseButton
                variant="primary"
                :icon="ICONS.add"
                label="Log"
                :disable="!canSubmit || busy"
                @click="onSubmit"
            />
        </div>
    </div>
</template>

<script setup lang="ts">
    import { computed, ref, watch } from 'vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { SUPPORTED_PRICE_UNITS } from 'src/generated/units_table';
    import type { PriceEntryPrefill } from 'src/models/stockItemDetail';
    import type { Store } from 'src/models/store';

    type Mode = 'shelf' | 'harvest';

    const props = withDefaults(
        defineProps<{
            mode?: Mode | undefined;
            prefill?: PriceEntryPrefill | null | undefined;
            stores?: ReadonlyArray<Store> | undefined;
            busy?: boolean | undefined;
        }>(),
        { mode: 'shelf', prefill: null, stores: () => [], busy: false },
    );

    const emit = defineEmits<{
        (e: 'submit', value: {
            total_price: number;
            total_measure: number;
            unit: string;
            store_id: string | null;
            pack_count: number | null;
        }): void;
        (e: 'cancel'): void;
    }>();

    const totalPrice = ref<number | null>(props.prefill?.total_price ?? null);
    // `perPackSize` is the user-visible "Size" field. When multipack is set,
    // it represents the per-pack size and total_measure is derived as
    // `count × perPackSize` at submit time. When multipack is null, it IS
    // the total_measure. Keeping the field single-purpose in the UI but
    // dual-semantic under the hood matches the FU-227 §6a observation
    // that "shelf-price mode never carried a count concept" — the form's
    // empty state stays one number, multipack is a disclosure.
    const perPackSize = ref<number | null>(props.prefill?.total_measure ?? null);
    const unit = ref<string>(props.prefill?.unit ?? '');
    const storeId = ref<string | null>(props.prefill?.store_id ?? null);
    const packCount = ref<number | null>(null);
    const packCountVisible = ref(false);

    // Re-seed when the prefill arrives lazily (row-button case: fetched
    // after the dialog opens). Don't overwrite user typing — only seed if
    // the field is still at its initial empty state.
    watch(() => props.prefill, (p) => {
        if (!p) return;
        if (totalPrice.value == null) totalPrice.value = p.total_price;
        if (perPackSize.value == null) perPackSize.value = p.total_measure;
        if (!unit.value) unit.value = p.unit;
        if (storeId.value == null) storeId.value = p.store_id;
    });

    const isMultipack = computed(() => packCountVisible.value && packCount.value != null && packCount.value > 1);

    // B3 — flat list grouped by dimension. The canonical strings come from
    // the generated table (single source of truth — chunk 1 / R-003), so
    // the picker never drifts from the server's accepted set.
    const unitOptions = computed(() => {
        const groups: Record<string, { canonical: string; label: string }[]> = {};
        for (const u of SUPPORTED_PRICE_UNITS) {
            (groups[u.dimension] ??= []).push({ canonical: u.canonical, label: u.label });
        }
        const order: string[] = ['volume', 'mass', 'count'];
        const out: { value: string; label: string }[] = [];
        for (const dim of order) {
            for (const opt of (groups[dim] ?? [])) {
                out.push({ value: opt.canonical, label: `${dim} — ${opt.label}` });
            }
        }
        return out;
    });

    const storeOptions = computed(() => (props.stores ?? []).map((s) => ({
        value: s.store_id,
        label: s.name,
    })));

    function totalMeasure(): number | null {
        if (perPackSize.value == null || perPackSize.value <= 0) return null;
        if (!isMultipack.value) return perPackSize.value;
        return (packCount.value as number) * perPackSize.value;
    }

    const totalMeasureDisplay = computed(() => {
        const v = totalMeasure();
        return v == null ? '' : v.toString();
    });

    const canSubmit = computed(() => {
        const tm = totalMeasure();
        return totalPrice.value != null && totalPrice.value > 0
            && tm != null && tm > 0
            && !!unit.value;
    });

    const perUnitPreview = computed(() => {
        if (!canSubmit.value) return null;
        const per = (totalPrice.value as number) / (totalMeasure() as number);
        return per.toFixed(2);
    });

    function onSubmit() {
        if (!canSubmit.value) return;
        emit('submit', {
            total_price: totalPrice.value as number,
            total_measure: totalMeasure() as number,
            unit: unit.value,
            store_id: storeId.value,
            pack_count: isMultipack.value ? (packCount.value as number) : null,
        });
    }

    function onCancel() {
        emit('cancel');
    }

    function clearPackCount() {
        packCount.value = null;
        packCountVisible.value = false;
    }
</script>
