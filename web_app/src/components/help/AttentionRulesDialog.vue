<template>
    <BaseDialog
        :model-value="modelValue"
        title="What the colours and outlines mean"
        closable
        card-style="width: 720px; max-width: 95vw"
        @update:model-value="emit('update:modelValue', $event)"
    >
        <q-card-section class="dora-attention-help">
            <p class="text-body2 q-mb-md">
                Dora uses three signals on every stock item — the
                <strong>level dot/picker</strong>, the <strong>row outline</strong>,
                and the <strong>row opacity</strong> — to tell you what needs
                acting on. The same rules also drive the
                "<em>Needs attention</em>" count in the footer and its
                matching filter chip, so what you see highlighted is
                exactly what the count is counting.
            </p>

            <!-- ── At-a-glance legend ─────────────────────────────────
                 2026-08-15 feedback: this used to live in the stock
                 overview's filter panel, which is not where a reference
                 belongs — but its visual examples were the good part, so
                 the component moves here intact rather than being
                 reworded into prose.
                 It also replaces the hand-written level table that sat
                 here: that table hardcoded three level names and their
                 colours, so a household that renamed a level (or added a
                 fourth) was read the wrong thing. StockRowLegend derives
                 both from the live level rows via the same
                 `colourForSequence` authority the row itself uses (R-003),
                 so this page cannot drift from what it documents. -->
            <StockRowLegend :levels="stockLevels" />

            <!-- ── Outline & dim ──────────────────────────────────────
                 One tier, not two. This used to describe an amber "warn"
                 outline and a red "alert" one; a hedged alarm gets ignored,
                 and amber sat directly around the amber Low level square.
                 The copy follows the code (D-7) rather than the code being
                 left to disagree with the help page. -->
            <h6 class="q-mt-lg q-mb-sm">Row outline</h6>
            <p class="text-body2 q-mb-sm dora-text-secondary">
                An outlined row needs you. There's one outline, and it means
                one thing — three conditions turn it on:
            </p>

            <q-list bordered separator class="rounded-borders">
                <q-item class="dora-attention-sample dora-attention-sample--alert">
                    <q-item-section>
                        <q-item-label class="text-weight-medium text-negative">
                            Needs attention
                        </q-item-label>
                        <q-item-label caption>
                            The item has <strong>expired</strong>, it's
                            <strong>expiring soon</strong> (your setting decides
                            how soon), or it's flagged <strong>essential</strong>
                            and has run low or out.
                        </q-item-label>
                    </q-item-section>
                </q-item>
            </q-list>

            <p class="text-body2 q-mt-sm dora-text-secondary">
                That's the same set the <em>Needs attention</em> count and its
                filter chip use, and the same set the bell counts — one rule,
                worked out in one place, so the highlighting and the numbers
                can't tell you different things. Turning a kind off under
                Alerts turns off its outline too.
            </p>

            <!-- ── Essential ──────────────────────────────────────── -->
            <h6 class="q-mt-lg q-mb-sm">Essential items</h6>
            <p class="text-body2 q-mb-sm dora-text-secondary">
                Items you mark <strong>essential</strong> get a warning-toned
                stripe on the left edge of the row and a flag icon on the
                right. Essentials are the ONLY items whose stock level
                drives an outline — a non-essential item running Low or Out
                is silent, because the level square already says so and Dora
                shouldn't be loud about things you didn't say mattered.
            </p>
            <q-card flat bordered class="dora-attention-essential-sample">
                <q-card-section class="row items-center">
                    <q-icon :name="ICONS.flag" color="warning" size="20px" class="q-mr-sm" />
                    <span class="text-body2">A flagged item, full opacity, with the left stripe.</span>
                </q-card-section>
            </q-card>

            <!-- ── Dim ────────────────────────────────────────────── -->
            <h6 class="q-mt-lg q-mb-sm">Dimmed rows</h6>
            <p class="text-body2 q-mb-sm dora-text-secondary">
                An item is <strong>faded</strong> when it's Out of stock
                <em>and</em> not flagged essential. The fade quietly says
                "depleted, you don't need to act on it" — your eye skips
                them when scanning for what to do next. Out essentials
                stay full opacity so the loudest "go restock" signal
                isn't quieted by the fade.
            </p>

            <!-- ── Rings (2026-08-15) ─────────────────────────────────
                 These two indicators used to be chips with their own words
                 sitting beside the buttons. They're now rings ON those
                 buttons, so the words have to live somewhere — here, next to
                 the other row-language rules, and in the legend above. -->
            <h6 class="q-mt-lg q-mb-sm">Rings around the buttons</h6>
            <p class="text-body2 q-mb-sm dora-text-secondary">
                A ring means something is being said about the button it
                surrounds — not about the item as a whole. There are two, and
                they never mean the same thing:
            </p>
            <q-list bordered separator class="rounded-borders">
                <q-item>
                    <q-item-section avatar>
                        <q-icon :name="ICONS.inferred_hunch" color="warning" size="22px" />
                    </q-item-section>
                    <q-item-section>
                        <q-item-label class="text-weight-medium">
                            Amber ring on the level box — "Dora thinks…"
                        </q-item-label>
                        <q-item-label caption>
                            Dora works out what you probably have from your
                            purchases, how often you rebuy, and what you've
                            cooked. When that <strong>disagrees</strong> with the
                            level you recorded, the level box gets an amber ring.
                            Open the picker and its header tells you what she
                            thinks and why. She never changes your recorded level
                            — that stays the source of truth — and when she
                            agrees with you she says nothing at all. Turn the
                            hint off in Settings → Assistant.
                        </q-item-label>
                    </q-item-section>
                </q-item>
                <q-item>
                    <q-item-section avatar>
                        <q-icon :name="ICONS.shopping_cart" color="positive" size="22px" />
                    </q-item-section>
                    <q-item-section>
                        <q-item-label class="text-weight-medium">
                            Coloured ring on the cart button — should you buy it?
                        </q-item-label>
                        <q-item-label caption>
                            Green means <strong>worth buying now</strong>, amber
                            <strong>might be worth waiting</strong>, red
                            <strong>probably skip</strong>. It's worked out from
                            your own price history, how fast you get through the
                            item, and what you've thrown away — no outside data.
                            Hover the button for the headline, the reasons, and
                            how confident she is; there's no ring at all when
                            she isn't confident enough to be useful. Turn it off
                            in Settings → Admin → System ("Should I buy?"
                            oracle).
                        </q-item-label>
                    </q-item-section>
                </q-item>
            </q-list>

            <!-- ── Cheat sheet ────────────────────────────────────── -->
            <h6 class="q-mt-lg q-mb-sm">Cheat sheet</h6>
            <table class="dora-attention-table">
                <thead>
                    <tr>
                        <th>State</th>
                        <th>Outline</th>
                        <th>Counts as "Needs attention"</th>
                        <th>Dimmed</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="r in cheatRows" :key="r.state">
                        <td>{{ r.state }}</td>
                        <td>
                            <span v-if="r.outline === 'warn'" class="text-warning text-weight-medium">amber</span>
                            <span v-else-if="r.outline === 'alert'" class="text-negative text-weight-medium">red</span>
                            <span v-else class="dora-text-muted">—</span>
                        </td>
                        <td>
                            <q-icon
                                :name="r.attention ? ICONS.check : ICONS.close"
                                :color="r.attention ? 'positive' : undefined"
                                size="18px"
                            />
                        </td>
                        <td>
                            <q-icon
                                v-if="r.dim"
                                :name="ICONS.check"
                                color="positive"
                                size="18px"
                            />
                            <span v-else class="dora-text-muted">—</span>
                        </td>
                    </tr>
                </tbody>
            </table>
        </q-card-section>

        <template #actions>
            <BaseButton variant="primary" label="Got it" @click="emit('update:modelValue', false)" />
        </template>
    </BaseDialog>
</template>

<script setup lang="ts">
    import { onMounted } from 'vue';
    import { storeToRefs } from 'pinia';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import StockRowLegend from 'src/components/stock/StockRowLegend.vue';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { ICONS } from 'src/style/icons';

    defineProps<{ modelValue: boolean }>();
    const emit = defineEmits<{ (e: 'update:modelValue', value: boolean): void }>();

    // The legend renders the household's REAL level rows (renames included),
    // so this dialog has to have them. Help is reachable without visiting
    // Stock first, so it can't assume the store is already hydrated.
    const stockLevelStore = useStockLevelStore();
    const { stockLevels } = storeToRefs(stockLevelStore);
    onMounted(() => {
        void stockLevelStore.ensureLoadedAsync();
    });

    type CheatRow = {
        state: string;
        outline: 'none' | 'warn' | 'alert';
        attention: boolean;
        dim: boolean;
    };
    const cheatRows: CheatRow[] = [
        { state: 'Stocked, no expiry issue', outline: 'none', attention: false, dim: false },
        { state: 'Low — not essential', outline: 'none', attention: false, dim: false },
        { state: 'Low — essential', outline: 'warn', attention: true, dim: false },
        { state: 'Out — not essential', outline: 'none', attention: false, dim: true },
        { state: 'Out — essential', outline: 'alert', attention: true, dim: false },
        { state: 'Expiring within 7 days (any)', outline: 'warn', attention: true, dim: false },
        { state: 'Expired (any)', outline: 'alert', attention: true, dim: false },
        { state: 'Expired + Out, not essential', outline: 'alert', attention: true, dim: true },
    ];
</script>

<style scoped lang="scss">
    .dora-attention-help h6 {
        font-weight: 600;
    }
    .dora-attention-sample {
        border-left: 4px solid transparent;
    }
    .dora-attention-sample--alert {
        border-left-color: var(--q-negative);
        box-shadow: inset 0 0 0 1px var(--q-negative);
    }
    .dora-attention-essential-sample {
        position: relative;
        overflow: hidden;
    }
    .dora-attention-essential-sample::before {
        content: '';
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        width: 3px;
        background: var(--q-warning);
    }
    .dora-attention-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
    }
    .dora-attention-table th,
    .dora-attention-table td {
        text-align: left;
        padding: 8px 10px;
        border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 8%, transparent);
    }
    .dora-attention-table th {
        font-weight: 600;
        background: color-mix(in srgb, var(--text-primary) 4%, transparent);
    }
</style>
