<template>
    <!--
        FU-227 chunk 3 — the shared "Your prices" entry form (F1 / R-001).
        One component, used by:
          • the stock-overview row "Log a price" button (shelf-price mode)
          • the stock-item detail YourPricesWidget [Log a price] action
          • (chunk 5) the shopping-line at /finish (harvest mode)

        Modes (§6a):
          • shelf  → "I SAW $X for size Y at maybe store Z". Three inputs
                     (total_price, size, unit) + optional store. No count.
                     One number at a glance.
          • harvest → "I BOUGHT N for total $X". Used at /finish to map a
                      line into an observation. Count is read from the line.
                      Chunk 5 wires this; chunk 3 keeps the mode prop for
                      forwards-compat but only shelf is exercised today.

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
                v-model.number="totalMeasure"
                dense outlined type="number"
                class="col"
                label="Size"
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

        <q-select
            v-if="mode === 'shelf' && storeOptions.length > 0"
            v-model="storeId"
            :options="storeOptions"
            dense outlined emit-value map-options clearable
            label="Store (optional)"
        />

        <!-- Live preview: $X.XX per Y. Empty when inputs incomplete. -->
        <div
            v-if="perUnitPreview"
            class="dora-bg-sunken dora-text-secondary q-pa-sm rounded-borders text-body2"
        >
            ≈ <strong>${{ perUnitPreview }}</strong> per {{ unit }}
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
        }): void;
        (e: 'cancel'): void;
    }>();

    const totalPrice = ref<number | null>(props.prefill?.total_price ?? null);
    const totalMeasure = ref<number | null>(props.prefill?.total_measure ?? null);
    const unit = ref<string>(props.prefill?.unit ?? '');
    const storeId = ref<string | null>(props.prefill?.store_id ?? null);

    // Re-seed when the prefill arrives lazily (row-button case: fetched
    // after the dialog opens). Don't overwrite user typing — only seed if
    // the field is still at its initial empty state.
    watch(() => props.prefill, (p) => {
        if (!p) return;
        if (totalPrice.value == null) totalPrice.value = p.total_price;
        if (totalMeasure.value == null) totalMeasure.value = p.total_measure;
        if (!unit.value) unit.value = p.unit;
        if (storeId.value == null) storeId.value = p.store_id;
    });

    // B3 — flat list grouped by dimension. The canonical strings come from
    // the generated table (single source of truth — chunk 1 / R-003), so
    // the picker never drifts from the server's accepted set.
    const unitOptions = computed(() => {
        const groups: Record<string, { canonical: string; label: string }[]> = {};
        for (const u of SUPPORTED_PRICE_UNITS) {
            (groups[u.dimension] ??= []).push({ canonical: u.canonical, label: u.label });
        }
        // Quasar q-select with `emit-value map-options` reads `{value, label}`.
        // Render as a flat list with dimension prefixes so the user sees
        // "volume — L" rather than a separate "volume" optgroup widget.
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

    const canSubmit = computed(() =>
        totalPrice.value != null && totalPrice.value > 0
        && totalMeasure.value != null && totalMeasure.value > 0
        && !!unit.value,
    );

    const perUnitPreview = computed(() => {
        if (!canSubmit.value) return null;
        const per = (totalPrice.value as number) / (totalMeasure.value as number);
        return per.toFixed(2);
    });

    function onSubmit() {
        if (!canSubmit.value) return;
        emit('submit', {
            total_price: totalPrice.value as number,
            total_measure: totalMeasure.value as number,
            unit: unit.value,
            store_id: storeId.value,
        });
    }

    function onCancel() {
        emit('cancel');
    }
</script>
