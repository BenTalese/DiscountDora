<template>
    <div class="sl-run">
        <!-- Ordering stays available mid-shop — it is the single most useful
             control in a store (walk by aisle, or by the shop you're standing
             in) and it is a view preference, so it costs nothing to keep. -->
        <div class="row items-center q-gutter-xs q-mb-sm">
            <span class="text-caption dora-text-muted q-mr-xs">Order by</span>
            <BaseButton
                v-for="m in SECTION_MODES"
                :key="m"
                :variant="effectiveMode === m ? 'secondary' : 'ghost'"
                dense
                size="sm"
                :label="SECTION_MODE_LABELS[m]"
                :disable="!availableModes[m]"
                @click="emit('update:mode', m)"
            >
                <q-tooltip v-if="!availableModes[m]">
                    Nothing on this list has a {{ SECTION_MODE_LABELS[m].toLowerCase() }} set
                </q-tooltip>
            </BaseButton>
        </div>

        <div
            v-for="section in runSections"
            :key="section.key"
            class="q-mb-md"
        >
            <div
                v-if="section.label && !section.cleared"
                class="row items-center q-gutter-xs q-mb-xs text-subtitle2 dora-text-muted"
            >
                <q-icon :name="sectionIconFor(effectiveMode)" size="16px" />
                {{ section.label }}
                <span class="text-caption">
                    {{ section.picked }}/{{ section.total }}
                </span>
            </div>
            <q-list
                v-if="section.remaining.length > 0"
                bordered
                separator
                class="rounded-borders"
            >
                <!-- The whole row is the tap target: mid-shop the hand is
                     holding a trolley and the gesture repeats forty times.
                     There is exactly one thing a row does here — mark it
                     picked — so nothing competes with it for the tap. -->
                <q-item
                    v-for="line in section.remaining"
                    :key="line.line_id"
                    clickable
                    class="sl-run-row dora-press"
                    :class="{ 'sl-run-row--nested': isNestedChild(line) }"
                    @click="emit('tick', line)"
                >
                    <!-- Decorative on purpose: the row is the control, and a
                         real checkbox here would swallow the tap, emit its own
                         change *and* bubble the row's click — two mutations for
                         one gesture. The q-item is `clickable`, so keyboard
                         activation still works. -->
                    <q-item-section side>
                        <q-icon
                            :name="ICONS.check_box_outline_blank"
                            size="28px"
                            class="dora-text-secondary"
                        />
                    </q-item-section>
                    <q-item-section>
                        <q-item-label class="sl-run-name">
                            <span v-if="(line.quantity ?? 0) > 1" class="sl-run-qty">
                                {{ line.quantity }}×
                            </span>
                            {{ line.stock_item_name }}
                        </q-item-label>
                        <!-- One caption line, and only what a shopper standing
                             in the aisle can act on: the buy hint (which one to
                             grab) and, when sectioning isn't already saying it,
                             where. Provenance, groups and offers are planning
                             information and stay on the plan face. -->
                        <q-item-label v-if="captionFor(line)" caption class="ellipsis">
                            {{ captionFor(line) }}
                        </q-item-label>
                    </q-item-section>
                    <q-item-section v-if="moneyEnabled" side>
                        <!-- Price capture is a deliberate second tap, opening a
                             thumb-height sheet — never an inline field that a
                             mis-aimed tap on a moving trolley can edit. -->
                        <BaseButton
                            variant="ghost"
                            dense
                            :label="priceLabel(line)"
                            class="sl-run-price"
                            :class="{ 'sl-run-price--estimate': line.estimate_source !== 'actual' }"
                            @click.stop="emit('capture-price', line)"
                        >
                            <q-tooltip>
                                {{
                                    line.estimate_source === 'actual'
                                        ? 'The price you entered — tap to change'
                                        : 'Tap to record what you actually paid'
                                }}
                            </q-tooltip>
                        </BaseButton>
                    </q-item-section>
                </q-item>
            </q-list>

            <!-- A cleared section collapses to one line rather than
                 disappearing: vanishing sections make the list feel like it is
                 losing your work, and the count is the reassurance that it
                 isn't. -->
            <div
                v-else-if="section.label"
                class="sl-run-cleared row items-center q-gutter-xs"
            >
                <q-icon :name="ICONS.check_circle" color="positive" size="18px" />
                <span class="text-body2">
                    {{ section.label }} — all {{ section.total }} picked
                </span>
            </div>
        </div>

        <!-- Everything picked. The finish CTA lives in the sticky footer, so
             this is reassurance, not a second call to action. -->
        <div v-if="allPicked" class="text-center q-py-xl dora-text-muted">
            <q-icon :name="ICONS.check_circle" color="positive" size="48px" />
            <div class="text-h6 q-mt-sm">That's everything.</div>
            <div class="text-body2 q-mt-xs">
                Finish &amp; restock when you're through the till.
            </div>
        </div>

        <!-- Nothing to shop at all. Reachable when every line on the list was
             set aside by "Trim to fit" — rare, but the alternative is a blank
             page mid-shop with no explanation. -->
        <div v-else-if="lines.length === 0" class="text-center q-py-xl dora-text-muted">
            <q-icon :name="ICONS.shopping_cart" size="48px" />
            <div class="text-h6 q-mt-sm">Nothing on this list.</div>
            <div class="text-body2 q-mt-xs">
                Add something with <strong>Quick add</strong>, or finish up.
            </div>
        </div>
    </div>
</template>

<script lang="ts" setup>
    /**
     * The run face — the list as it is used in a store.
     *
     * This is a different *composition* of the same list, not the plan face
     * with bigger checkboxes (that was the original defect: "shopping mode is a
     * costume"). Everything that exists to curate a list — drag handles,
     * delete, quantity steppers, buy-hint pickers, offer chips, provenance,
     * suggestions, the budget banner — is absent here, because none of it is a
     * thing you do while holding a trolley. What is left is one row, one
     * gesture, and an optional price.
     *
     * Picked rows leave the list, so it shrinks as the trip progresses — but
     * the *section* stays, collapsed to a one-line "all N picked". A section
     * that vanished outright read as work being lost rather than done.
     */
    import { computed, toRef } from 'vue';
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import { formatMoney } from 'src/composables/useMoney';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import {
        SECTION_MODES, SECTION_MODE_LABELS, isNestedChild, sectionIconFor,
        sectionProgress, useLineSections, type SectionMode,
    } from 'src/composables/useLineSections';
    import type { ShoppingListLine } from 'src/models/shoppingList';

    const props = defineProps<{
        lines: ShoppingListLine[];
        mode: SectionMode;
    }>();

    const emit = defineEmits<{
        'update:mode': [mode: SectionMode];
        /** Mark this line picked. The page owns the mutation and the undo. */
        tick: [line: ShoppingListLine];
        'capture-price': [line: ShoppingListLine];
    }>();

    const { moneyEnabled } = useMoneyEnabled();

    const allLines = toRef(props, 'lines');
    const modeRef = computed({
        get: () => props.mode,
        set: (m: SectionMode) => emit('update:mode', m),
    });
    // Sectioning runs over *every* line, ticked included. The run face still
    // hides picked rows — but it does so per-section, so a section that has
    // emptied survives as its own "all 4 picked" line instead of silently
    // disappearing along with the evidence that you did that aisle.
    const { sections, availableModes, effectiveMode } = useLineSections(allLines, modeRef);

    /** One pass per render: what's left to pick in each section, plus the
     *  progress the header and the collapsed line both read. Derived once
     *  because the template needs all three and `sectionProgress` walks every
     *  line to answer. */
    const runSections = computed(() =>
        sections.value.map((section) => ({
            ...section,
            remaining: section.lines.filter((l) => !l.is_ticked),
            ...sectionProgress(props.lines, section, effectiveMode.value),
        }))
    );

    const allPicked = computed(() =>
        props.lines.length > 0 && props.lines.every((l) => l.is_ticked)
    );

    /** What the shopper can act on, in aisle terms. Location is dropped when
     *  the sectioning already groups by it — repeating the heading on every
     *  row is noise at arm's length. */
    function captionFor(line: ShoppingListLine): string {
        const parts: string[] = [];
        const hint = line.preferred_buys?.find(
            (pb) => pb.preferred_buy_id === line.preferred_buy_id
        );
        if (hint) parts.push(hint.label);
        if (effectiveMode.value !== 'location' && line.stock_location_breadcrumb.length > 0) {
            parts.push(line.stock_location_breadcrumb[0]!);
        }
        if (effectiveMode.value !== 'store' && line.resolved_store_name) {
            parts.push(line.resolved_store_name);
        }
        return parts.join(' · ');
    }

    /** Never re-derive the money ladder client-side (R-003) — the server has
     *  already resolved it and named the rung it used. */
    function priceLabel(line: ShoppingListLine): string {
        if (line.estimated_unit_price == null) return 'Price';
        const money = formatMoney(line.estimated_unit_price);
        return line.estimate_source === 'actual' ? money : `~${money}`;
    }
</script>

<style scoped>
    /* D-016 tap targets: the row is the target, so it is sized for a thumb
       rather than a cursor. */
    .sl-run-row {
        min-height: 60px;
    }
    .sl-run-row--nested {
        padding-left: 32px;
    }
    .sl-run-name {
        font-size: 1.05rem;
        font-weight: 500;
    }
    .sl-run-qty {
        font-variant-numeric: tabular-nums;
        color: var(--text-secondary);
        margin-right: 2px;
    }
    .sl-run-price {
        font-variant-numeric: tabular-nums;
        min-width: 72px;
    }
    .sl-run-price--estimate {
        color: var(--text-secondary);
    }
    .sl-run-cleared {
        padding: 10px 16px;
        border: 1px solid var(--border-default);
        border-radius: var(--radius-md);
        background: var(--surface-sunken);
        color: var(--text-secondary);
    }
</style>
